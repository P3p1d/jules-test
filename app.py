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

        hashed_password = generate_password_hash(password)
        users_collection.insert_one({
            'username': username,
            'password': hashed_password,
            'cart': [],
            'created_at': datetime.utcnow()
        })
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

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
    return render_template('login.html')

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

    # In a real app, process payment here
    users_collection.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'cart': []}}
    )
    flash('Order placed successfully! Keep rocking.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
