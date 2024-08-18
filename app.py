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
        email_found = mongo.user.find_one({'email': email})

        if user_found:
            message = 'Username already exists!'
        elif email_found:
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
        

        if user_found and user_found['password'] == password:
            return render_template('index.html', username = uname)
        else:
            message = 'Invalid username or password!'

    return render_template('auth-login.html', message = message)

@app.route('/logout')
def logout():
    return render_template('auth-login.html')

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
                mongo.user.update_one({'email': email}, {'$set': {'password': password}})
                message = 'Password updated successfully!'
                return redirect(url_for('login'), message = message)
        else:
            message = 'Email doesn\'t exist!'
    return render_template('auth-forgot-password.html', message = message)

if __name__ == '__main__':
    app.run(debug=True)