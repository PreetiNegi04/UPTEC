from flask import Flask, request, jsonify, render_template, url_for, redirect
from flask_pymongo import PyMongo

app = Flask(__name__)

app.config['MONGO_URI'] = "mongodb://localhost:27017/mydatabase"
mongo = PyMongo(app).db

@app.route('/')
def index():
    return render_template('auth-login.html')

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
        uname = user_found['username']
        email_found = mongo.user.find_one({'email': email})
        em = email_found['email']

        if uname == username:
            message = 'Username already exists!'
        elif em == email:
            message = 'Email already exists!'
        elif password != confirm_password:
            message = 'Passwords do not match!'
        else:
            user = {
                'username': username,
                'email': email,
                'password': password
            }
            mongo.user.insert_one(user)

            user_data = mongo.user.find_one({'username':username})
            new_username = user_data['username']

            return render_template('index.html', username = new_username)
    return render_template('auth-register.html', message=message)

@app.route('/login', methods=['POST', 'GET'])
def login():
    message = ''
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')

        user_found = mongo.user.find_one({'username': username})
        uname = user_found['username']
        pword = user_found['password']

        if uname == username and pword == password:
            return render_template('index.html', username = uname)
        else:
            message = 'Invalid username or password!'

    return render_template('auth-login.html', message = message)

if __name__ == '__main__':
    app.run(debug=True)