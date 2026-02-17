"""
Products Service - Single file, master spawns multiple copies
"""

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os
import sys
from datetime import datetime

sys.path.insert(0, 'C:/production/shared')
from models import db, Product
from config import config

# Instance info comes from environment variables
# Master sets these automatically for each worker
INSTANCE_NAME = os.environ.get('INSTANCE_NAME', 'Products-1')
INSTANCE_PORT = int(os.environ.get('INSTANCE_PORT', 5001))

app = Flask(__name__)
app.config.from_object(config['production'])
db.init_app(app)
JWTManager(app)
CORS(app)
limiter = Limiter(app=app, key_func=get_remote_address, storage_uri="memory://")

stats = {
    'requests_handled': 0,
    'started_at': datetime.now(),
    'pid': os.getpid()
}

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    stats['requests_handled'] += 1
    return jsonify({
        "service": "Products",
        "instance": INSTANCE_NAME,
        "port": INSTANCE_PORT,
        "pid": stats['pid'],
        "requests_handled": stats['requests_handled'],
        "uptime_seconds": (datetime.now() - stats['started_at']).seconds
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "instance": INSTANCE_NAME})

@app.route('/api/products', methods=['GET'])
def get_products():
    stats['requests_handled'] += 1
    category = request.args.get('category')
    query = Product.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)
    products = query.all()
    return jsonify({
        "success": True,
        "products": [p.to_dict() for p in products],
        "total": len(products),
        "instance": INSTANCE_NAME
    })

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    stats['requests_handled'] += 1
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404
    return jsonify({"success": True, "product": product.to_dict(), "instance": INSTANCE_NAME})

@app.route('/api/products/search', methods=['GET'])
def search_products():
    stats['requests_handled'] += 1
    q = request.args.get('q', '')
    if not q:
        return jsonify({"success": False, "error": "Query required"}), 400
    products = Product.query.filter(
        db.or_(Product.name.ilike(f'%{q}%'), Product.description.ilike(f'%{q}%')),
        Product.is_active == True
    ).all()
    return jsonify({
        "success": True,
        "query": q,
        "products": [p.to_dict() for p in products],
        "total": len(products),
        "instance": INSTANCE_NAME
    })

@app.route('/api/products', methods=['POST'])
@jwt_required()
def create_product():
    stats['requests_handled'] += 1
    data = request.get_json()
    if 'name' not in data or 'price' not in data:
        return jsonify({"success": False, "error": "Name and price required"}), 400
    product = Product(
        name=data['name'],
        description=data.get('description', ''),
        price=float(data['price']),
        stock=int(data.get('stock', 0)),
        category=data.get('category', 'general')
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"success": True, "product": product.to_dict(), "instance": INSTANCE_NAME}), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    stats['requests_handled'] += 1
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404
    data = request.get_json()
    for field in ['name', 'description', 'price', 'stock', 'category', 'is_active']:
        if field in data:
            setattr(product, field, data[field])
    db.session.commit()
    return jsonify({"success": True, "product": product.to_dict(), "instance": INSTANCE_NAME})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    stats['requests_handled'] += 1
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404
    product.is_active = False
    db.session.commit()
    return jsonify({"success": True, "message": "Product deleted", "instance": INSTANCE_NAME})

if __name__ == "__main__":
    from waitress import serve
    print(f"[{INSTANCE_NAME}] Starting on port {INSTANCE_PORT} (PID: {os.getpid()})")
    serve(app, host='127.0.0.1', port=INSTANCE_PORT, threads=4, channel_timeout=60)