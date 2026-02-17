"""
Initialize database with sample data
"""

import sys
sys.path.insert(0, 'C:/production/shared')

from flask import Flask
from models import db, User, Product
from config import config

app = Flask(__name__)
app.config.from_object(config['production'])
db.init_app(app)

with app.app_context():
    # Create tables
    db.create_all()
    print("✅ Database tables created")
    
    # Check if data already exists
    if User.query.first() or Product.query.first():
        print("⚠️  Database already contains data")
        response = input("Clear and reinitialize? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted")
            exit()
        
        db.drop_all()
        db.create_all()
        print("✅ Database cleared and recreated")
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    print("✅ Admin user created (username: admin, password: admin123)")
    
    # Create test user
    test_user = User(
        username='testuser',
        email='test@example.com'
    )
    test_user.set_password('test123')
    db.session.add(test_user)
    print("✅ Test user created (username: testuser, password: test123)")
    
    # Create sample products
    products = [
        Product(name='Laptop', description='High-performance laptop', price=999.99, stock=10, category='electronics'),
        Product(name='Smartphone', description='Latest model smartphone', price=699.99, stock=25, category='electronics'),
        Product(name='Headphones', description='Noise-cancelling headphones', price=199.99, stock=50, category='electronics'),
        Product(name='T-Shirt', description='Cotton t-shirt', price=19.99, stock=100, category='clothing'),
        Product(name='Jeans', description='Denim jeans', price=49.99, stock=75, category='clothing'),
        Product(name='Running Shoes', description='Comfortable running shoes', price=79.99, stock=40, category='footwear'),
        Product(name='Coffee Maker', description='Automatic coffee maker', price=89.99, stock=20, category='appliances'),
        Product(name='Blender', description='High-speed blender', price=59.99, stock=30, category='appliances'),
        Product(name='Backpack', description='Durable backpack', price=39.99, stock=60, category='accessories'),
        Product(name='Water Bottle', description='Insulated water bottle', price=24.99, stock=80, category='accessories'),
    ]
    
    for product in products:
        db.session.add(product)
    
    db.session.commit()
    print(f"✅ Created {len(products)} sample products")
    
    print("\n" + "=" * 60)
    print("Database initialized successfully!")
    print("=" * 60)