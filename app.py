from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime
import os
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_for_dev')

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client.stoner_rock_band
users_collection = db.users
merch_collection = db.merch
orders_collection = db.orders

# Helper for getting current user
def get_current_user():
    if 'user_id' in session:
        return users_collection.find_one({'_id': ObjectId(session['user_id'])})
    return None

@app.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if users_collection.find_one({'username': username}):
            flash('Username already exists!')
            return redirect(url_for('register'))

        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')

        hashed_password = generate_password_hash(password)
        hashed_answer = generate_password_hash(security_answer.lower())

        users_collection.insert_one({
            'username': username,
            'password': hashed_password,
            'role': 'user',
            'security_question': security_question,
            'security_answer': hashed_answer,
            'cart': [],
            'created_at': datetime.utcnow()
        })
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    user = get_current_user()
    return render_template('register.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = users_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            flash('Logged in successfully!')
            return redirect(url_for('index'))

        flash('Invalid username or password!')

    user = get_current_user()
    return render_template('login.html', user=user)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    user = get_current_user()
    if request.method == 'POST':
        username = request.form.get('username')
        security_answer = request.form.get('security_answer')
        new_password = request.form.get('new_password')

        user = users_collection.find_one({'username': username})
        if user and user.get('security_answer') and check_password_hash(user['security_answer'], security_answer.lower()):
            hashed_password = generate_password_hash(new_password)
            users_collection.update_one(
                {'_id': user['_id']},
                {'$set': {'password': hashed_password}}
            )
            flash('Password successfully reset! Please login.')
            return redirect(url_for('login'))
        else:
            flash('Invalid username or security answer.')

    return render_template('reset_password.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!')
    return redirect(url_for('index'))

@app.route('/merch')
def merch():
    user = get_current_user()
    items = list(merch_collection.find())
    return render_template('merch.html', user=user, items=items)

@app.route('/add_to_cart/<item_id>', methods=['POST'])
def add_to_cart(item_id):
    if 'user_id' not in session:
        flash('Please login to add items to your cart.')
        return redirect(url_for('login'))

    users_collection.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$push': {'cart': ObjectId(item_id)}}
    )
    flash('Item added to cart!')
    return redirect(url_for('merch'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please login to view your cart.')
        return redirect(url_for('login'))

    user = get_current_user()
    cart_items = []
    total = 0

    for item_id in user.get('cart', []):
        item = merch_collection.find_one({'_id': item_id})
        if item:
            cart_items.append(item)
            total += item['price']

    return render_template('cart.html', user=user, cart_items=cart_items, total=total)

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = get_current_user()
    if not user.get('cart'):
        flash('Your cart is empty.')
        return redirect(url_for('merch'))

    # Calculate total and gather items
    cart_items = []
    total = 0
    for item_id in user['cart']:
        item = merch_collection.find_one({'_id': item_id})
        if item:
            cart_items.append({'item_id': item['_id'], 'name': item['name'], 'price': item['price']})
            total += item['price']

    # Save order
    orders_collection.insert_one({
        'user_id': user['_id'],
        'username': user['username'],
        'items': cart_items,
        'total': total,
        'created_at': datetime.utcnow()
    })

    # Clear cart
    users_collection.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'cart': []}}
    )
    flash('Order placed successfully! Keep rocking.')
    return redirect(url_for('index'))

# Staff Routes
def is_staff():
    user = get_current_user()
    return user and user.get('role') == 'staff'

@app.route('/staff')
def staff_dashboard():
    if not is_staff():
        flash('Unauthorized access.')
        return redirect(url_for('index'))

    user = get_current_user()
    users = list(users_collection.find())
    orders = list(orders_collection.find().sort('created_at', -1))
    items = list(merch_collection.find())

    total_sales = sum(order['total'] for order in orders)

    return render_template('staff_dashboard.html',
                           user=user,
                           users=users,
                           orders=orders,
                           items=items,
                           total_sales=total_sales)

@app.route('/staff/add_item', methods=['POST'])
def staff_add_item():
    if not is_staff():
        return redirect(url_for('index'))

    name = request.form.get('name')
    description = request.form.get('description')
    price = float(request.form.get('price'))
    image_url = request.form.get('image_url')

    merch_collection.insert_one({
        'name': name,
        'description': description,
        'price': price,
        'image_url': image_url
    })
    flash('Item added successfully.')
    return redirect(url_for('staff_dashboard'))

@app.route('/staff/delete_item/<item_id>', methods=['POST'])
def staff_delete_item(item_id):
    if not is_staff():
        return redirect(url_for('index'))

    merch_collection.delete_one({'_id': ObjectId(item_id)})
    flash('Item deleted successfully.')
    return redirect(url_for('staff_dashboard'))

@app.route('/staff/delete_user/<user_id>', methods=['POST'])
def staff_delete_user(user_id):
    if not is_staff():
        return redirect(url_for('index'))

    user_to_delete = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_to_delete and user_to_delete.get('role') == 'staff':
        flash('Cannot delete staff accounts.')
    else:
        users_collection.delete_one({'_id': ObjectId(user_id)})
        flash('User deleted successfully.')

    return redirect(url_for('staff_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
