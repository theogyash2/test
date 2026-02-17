"""
Orders Service
"""
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os, sys
from datetime import datetime

sys.path.insert(0, 'C:/production/shared')
from models import db, Order, OrderItem, Product
from config import config

INSTANCE_NAME = os.environ.get('INSTANCE_NAME', 'Orders-1')
INSTANCE_PORT = int(os.environ.get('INSTANCE_PORT', 5011))

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
        "service": "Orders",
        "instance": INSTANCE_NAME,
        "port": INSTANCE_PORT,
        "pid": stats['pid'],
        "requests_handled": stats['requests_handled']
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "instance": INSTANCE_NAME})

@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    stats['requests_handled'] += 1
    user_id = int(get_jwt_identity())
    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify({
        "success": True,
        "orders": [o.to_dict() for o in orders],
        "total": len(orders),
        "instance": INSTANCE_NAME
    })

@app.route('/api/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    stats['requests_handled'] += 1
    user_id = int(get_jwt_identity())
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
    return jsonify({"success": True, "order": order.to_dict(), "instance": INSTANCE_NAME})

@app.route('/api/orders', methods=['POST'])
@jwt_required()
def create_order():
    stats['requests_handled'] += 1
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if 'items' not in data or not data['items']:
        return jsonify({"success": False, "error": "Items required"}), 400

    total = 0
    order_items = []

    for item in data['items']:
        product = Product.query.get(item['product_id'])
        if not product:
            return jsonify({"success": False, "error": f"Product {item['product_id']} not found"}), 404
        if product.stock < item['quantity']:
            return jsonify({"success": False, "error": f"Insufficient stock for {product.name}"}), 400
        total += product.price * item['quantity']
        order_items.append({'product': product, 'quantity': item['quantity'], 'price': product.price})

    order = Order(user_id=user_id, total_amount=round(total, 2), status='pending')
    db.session.add(order)
    db.session.flush()

    for item in order_items:
        oi = OrderItem(order_id=order.id, product_id=item['product'].id, quantity=item['quantity'], price=item['price'])
        db.session.add(oi)
        item['product'].stock -= item['quantity']

    db.session.commit()
    return jsonify({"success": True, "order": order.to_dict(), "instance": INSTANCE_NAME}), 201

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    stats['requests_handled'] += 1
    user_id = int(get_jwt_identity())
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
    data = request.get_json()
    valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
    if data.get('status') not in valid_statuses:
        return jsonify({"success": False, "error": "Invalid status"}), 400
    order.status = data['status']
    db.session.commit()
    return jsonify({"success": True, "order": order.to_dict(), "instance": INSTANCE_NAME})

if __name__ == "__main__":
    from waitress import serve
    print(f"[{INSTANCE_NAME}] Starting on port {INSTANCE_PORT} (PID: {os.getpid()})")
    serve(app, host='127.0.0.1', port=INSTANCE_PORT, threads=4)
