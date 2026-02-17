"""
Users Service
"""
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os, sys
from datetime import datetime

sys.path.insert(0, 'C:/production/shared')
from models import db, User
from config import config

INSTANCE_NAME = os.environ.get('INSTANCE_NAME', 'Users-1')
INSTANCE_PORT = int(os.environ.get('INSTANCE_PORT', 5021))

app = Flask(__name__)
app.config.from_object(config['production'])
db.init_app(app)
JWTManager(app)
CORS(app)
limiter = Limiter(app=app, key_func=get_remote_address, storage_uri="memory://")

stats = {'requests_handled': 0, 'pid': os.getpid(), 'started_at': datetime.now()}

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    stats['requests_handled'] += 1
    return jsonify({
        "service": "Users",
        "instance": INSTANCE_NAME,
        "port": INSTANCE_PORT,
        "pid": stats['pid'],
        "requests_handled": stats['requests_handled']
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "instance": INSTANCE_NAME})

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    stats['requests_handled'] += 1
    data = request.get_json()
    for field in ['username', 'email', 'password']:
        if field not in data:
            return jsonify({"success": False, "error": f"Missing {field}"}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"success": False, "error": "Username already exists"}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"success": False, "error": "Email already exists"}), 400
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({
        "success": True,
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "instance": INSTANCE_NAME
    }), 201

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per hour")
def login():
    stats['requests_handled'] += 1
    data = request.get_json()
    if 'username' not in data or 'password' not in data:
        return jsonify({"success": False, "error": "Username and password required"}), 400
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({
        "success": True,
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "instance": INSTANCE_NAME
    })

@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    stats['requests_handled'] += 1
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=str(user_id))
    return jsonify({"success": True, "access_token": access_token, "instance": INSTANCE_NAME})

@app.route('/api/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    stats['requests_handled'] += 1
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    return jsonify({"success": True, "user": user.to_dict(), "instance": INSTANCE_NAME})

@app.route('/api/users/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    stats['requests_handled'] += 1
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    data = request.get_json()
    if 'email' in data:
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user.id:
            return jsonify({"success": False, "error": "Email already in use"}), 400
        user.email = data['email']
    if 'password' in data:
        user.set_password(data['password'])
    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict(), "instance": INSTANCE_NAME})

if __name__ == "__main__":
    from waitress import serve
    print(f"[{INSTANCE_NAME}] Starting on port {INSTANCE_PORT} (PID: {os.getpid()})")
    serve(app, host='127.0.0.1', port=INSTANCE_PORT, threads=4)