from flask import Flask, request, jsonify, render_template, url_for, redirect
from flask_pymongo import PyMongo
import re
import bcrypt

app = Flask(__name__)

app.config['MONGO_URI'] = "mongodb://localhost:27017/mydatabase"
mongo = PyMongo(app).db

#routes 
@app.route('/', methods=['POST', 'GET'])
def start():
    return redirect(url_for('login'))

@app.route('/register', methods=['POST', 'GET'])
def register():
    message = ''
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data['confirm'] 

        user_found = mongo.user.find_one({'username': username})
        email_found = mongo.user.find_one({'email': email})

        if user_found:
            message = 'Username already exists!'
        elif email_found:
            message = 'Email already exists!'
        elif validate_email(email) == False:
            message = 'Wrong email!'
        elif validate_username(username) == False:
            message = 'Username must be at least 8 characters long and should contain atleast 1 uppercase, 1 lowercase and 1 digit!'
        elif validate_password(password) == False:
            message = 'Password must be at least 8 characters long and should contain atleast 1 uppercase, 1 lowercase and 1 digit!'
        elif password != confirm_password:
            message = 'Passwords do not match!'
        else:
            hashed_password = hash_password(password)
            user = {
                'username': username,
                'email': email,
                'password': hashed_password
            }
            mongo.user.insert_one(user)

            user_data = mongo.user.find_one({'username':username})
            new_username = user_data['username']

            return redirect(url_for('index', username = new_username))
    return render_template('auth-register.html', message=message)

@app.route('/login', methods=['POST', 'GET'])
def login():
    message = ''
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')

        user_found = mongo.user.find_one({'username': username})
        

        if user_found and check_password(user_found['password'], password):
            return redirect(url_for('index' , username = username))
        else:
            message = 'Invalid username or password!'

    return render_template('auth-login.html', message = message)

@app.route('/logout')
def logout():
    return render_template('auth-login.html')

@app.route('/index')
def index():
    username = request.args.get('username')
    return render_template('index.html', username = username)

@app.route('/forget-password', methods=['POST', 'GET'])
def forget_password():
    message = ''
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')
        confirm_password = data['confirm']

        email_found = mongo.user.find_one({'email': email})

        if email_found:
            if password != confirm_password:
                message = 'Passwords do not match!'
            else:
                hashed_password = hash_password(password)
                mongo.user.update_one({'email': email}, {'$set': {'password': hashed_password}})
                message = 'Password updated successfully!'
                return redirect(url_for('login'), message = message)
        else:
            message = 'Email doesn\'t exist!'
    return render_template('auth-forgot-password.html', message = message)

def validate_username(username):
    # Username should be at least 8 characters long, containing at least one uppercase letter, one lowercase letter, and one digit
    if re.fullmatch(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$', username):
        return True
    return False

def validate_password(password):
    # Password should be at least 8 characters long, containing at least one uppercase letter, one lowercase letter, and one digit
    if re.fullmatch(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d@#$%^&+=]{8,}$', password):
        return True
    return False

def validate_email(email):
    # Email should be in a valid format
    if re.fullmatch(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return True
    return False

def hash_password(password):
    # Generate a salt
    salt = bcrypt.gensalt()
    # Hash the password with the salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def check_password(hashed_password, user_password):
    # Check if the provided password matches the hashed password
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

if __name__ == '__main__':
    app.run(debug=True)