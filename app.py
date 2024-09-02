from flask import Flask, request, jsonify, render_template, url_for, redirect, flash
from flask_pymongo import PyMongo
import re
import bcrypt

app = Flask(__name__)

app.config['MONGO_URI'] = "mongodb://localhost:27017/mydatabase"
mongo = PyMongo(app)

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

        user_found = mongo.db.user.find_one({'username': username})
        email_found = mongo.db.user.find_one({'email': email})

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
            mongo.db.user.insert_one(user)

            user_data = mongo.db.user.find_one({'username': username})
            new_username = user_data['username']

            return redirect(url_for('index', username = username))
    return render_template('auth-register.html', message=message)

@app.route('/login', methods=['POST', 'GET'])
def login():
    message = ''
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')

        user_found = mongo.db.user.find_one({'username': username})

        if user_found and user_found['password'] == password:
            return render_template('index.html', username = uname)
        else:
            message = 'Invalid username or password!'

    return render_template('auth-login.html', message=message)

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

        email_found = mongo.db.user.find_one({'email': email})

        if email_found:
            if password != confirm_password:
                message = 'Passwords do not match!'
            else:
                mongo.user.update_one({'email': email}, {'$set': {'password': password}})
                message = 'Password updated successfully!'
                return redirect(url_for('login'))
        else:
            message = 'Email doesn\'t exist!'
    return render_template('auth-forgot-password.html', message=message)

@app.route('/student_registration', methods=['POST', 'GET'])
def student_registration():
    if request.method == 'POST':
        # Get form data
        form_data = {
            "name": request.form.get('uname'),
            "programme": request.form.get('prog'),
            "address": request.form.get('address'),
            "centre": request.form.get('centre'),
            "hours": request.form.get('hours'),
            "ampm": request.form.get('ampm'),
            "today_date": request.form.get('today-date'),
            "mobile": request.form.get('mobile'),
            "whatsapp": request.form.get('whatsapp'),
            "email": request.form.get('email'),
            "dob": request.form.get('dob'),
            "marital_status": request.form.get('mstatus'),
            "qualification": request.form.get('qualification'),
            "college_status": request.form.get('college-status'),
            "current_college": request.form.get('current-college'),
            "previous_college": request.form.get('previous-college'),
            "ews": request.form.get('ews'),
            "father_name": request.form.get('gname'),
            "occupation": request.form.get('occupation'),
            "organization_address": request.form.get('addoforg'),
            "designation": request.form.get('desg'),
            "family_mobile": request.form.get('mobile'),
            "objectives": request.form.getlist('objectives'),
            "source": request.form.getlist('source'),
            "specific_source": request.form.get('newspaperRadioText'),
            "course_name": request.form.get('coursename'),
            "new_tech_course_name": request.form.get('newTechCourseName'),
            "short_term_course_name": request.form.get('shortTermCourseName'),
            "course_mode": request.form.get('course_mode'),
            "course_duration": request.form.get('course_duration'),
            "fees": request.form.get('fees'),
            "secfees": request.form.get('secfees'),
            "course_advised": request.form.get('courseadv'),
            "p": request.form.get('p'),
            "t": request.form.get('t'),
            "r": request.form.get('r'),
            "approved": request.form.get('approved'),
            "fremark": request.form.get('fremark'),
        }
        try:
            # Save to MongoDB
            mongo.db.form_data.insert_one(form_data)
            return redirect(url_for('success'))  # Replace 'success' with the name of the route you want to redirect to
        except Exception as e:
            app.logger.error(f"Error occurred while saving student registration data: {e}")
            flash("An error occurred while saving your data. Please try again later.", "error")
            return redirect(url_for('student_registration'))

    # If it's a GET request, render the student registration form
    return render_template('student_registration.html')
        # Save to MongoDB
         # Replace with the actual template you are using

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            # Extract data from the form
            contact_data = {
                'date_of_enquiry': request.form.get('dateoe'),
                'name': request.form.get('uname'),
                'contact_number': request.form.get('contact'),
                'type_of_enquiry': request.form.get('type_of_enquiry'),
                'course_to_enquire': request.form.get('course'),
                'follow_up_status': {
                    'date': request.form.get('date'),
                    'reason': request.form.get('reason')
                },
                'enquiry_status': request.form.get('estatus'),
                'remark': request.form.get('status')
            }
            
            # Check if all fields are provided (additional checks can be added as needed)
            if not all(contact_data.values()) or not contact_data['follow_up_status']['date'] or not contact_data['follow_up_status']['reason']:
                flash("All fields are required!", "error")
                return redirect(url_for('contact'))

            # Insert the data into MongoDB collection
            mongo.db.contacts.insert_one(contact_data)

            # Redirect to the success page
            return redirect(url_for('success'))
        
        except Exception as e:
            # Log the error and return a generic error message
            app.logger.error(f"Error occurred: {e}")
            flash("An error occurred while saving your data. Please try again later.", "error")
            return redirect(url_for('contact'))
    
    # If GET request, render the contact form
    return render_template('contact.html')


@app.route('/success', methods=['POST', 'GET'])
def success():
    return render_template('success.html') 


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
