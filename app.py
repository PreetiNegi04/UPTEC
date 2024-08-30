from flask import Flask, request, jsonify, render_template, url_for, redirect, flash
from flask_pymongo import PyMongo

app = Flask(__name__)

app.config['MONGO_URI'] = "mongodb://localhost:27017/mydatabase"
mongo = PyMongo(app)

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

        user_found = mongo.db.user.find_one({'username': username})
        email_found = mongo.db.user.find_one({'email': email})

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
            mongo.db.user.insert_one(user)

            user_data = mongo.db.user.find_one({'username': username})
            new_username = user_data['username']

            return render_template('index.html', username=new_username)
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
            return render_template('index.html', username=username)
        else:
            message = 'Invalid username or password!'

    return render_template('auth-login.html', message=message)

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

        email_found = mongo.db.user.find_one({'email': email})

        if email_found:
            if password != confirm_password:
                message = 'Passwords do not match!'
            else:
                mongo.db.user.update_one({'email': email}, {'$set': {'password': password}})
                message = 'Password updated successfully!'
                return redirect(url_for('login'))
        else:
            message = 'Email doesn\'t exist!'
    return render_template('auth-forgot-password.html', message=message)

@app.route('/success', methods=['POST', 'GET'])
def success():
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

    # Save to MongoDB
    mongo.db.form_data.insert_one(form_data)

    return redirect(url_for('success_page'))

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

if __name__ == '__main__':
    app.run(debug=True)
