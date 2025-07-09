from flask import Flask, request, jsonify, render_template, url_for, redirect, flash, session
from flask_pymongo import PyMongo
from pymongo import MongoClient
import re
import bcrypt
from datetime import datetime, timedelta
from bson import ObjectId
from flask import jsonify
import calendar
from collections import defaultdict
from flask_mail import Mail, Message
import random


app = Flask(__name__)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'uptec340@gmail.com'         # replace
app.config['MAIL_PASSWORD'] = 'uemhceftizpiyull'            # app password (not Gmail password)

mail = Mail(app)

app.secret_key = 'your_secret_key'

app.config['SESSION_COOKIE_SECURE'] = False  # True if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


client = MongoClient('mongodb://localhost:27017')
db = client['mydatabase']
collection = db['contacts'] 
app.config['MONGO_URI'] = "mongodb://localhost:27017/mydatabase"
mongo = PyMongo(app)

course_list = ["ADCA", "DCA", "O level", "DCAC", "Internship", "New Tech", "Short Term", "Others"]

course_fees = {
    "CCC": ["2 Month", 3000],
    "MS Office And Internet": ["1 Month", 3500],
    "MS Office with Tally Prime" : ["2.5 Month", 7000],
    "Tally Prime" : ["1.5 Month", 5000], 
    "ProE" : ["1 Month", 6000],
    "MATLAB": ["1 Month", 6000],
    "Corel Draw" : ["30 hours", 3000],
    "PageMaker" : ["30 hours", 3000],
    "Adobe Photoshop" : ["30 hours", 3500],
    "Web Page Designing" : ["1.5 Month", 5000], 
    "ASP.NET with MVC , LinQ AND JSON" : ["1.5 Month", 6000],
    "PHP and My SQL" : ["1.5 Month", 6000],
    "Javascript" : ["2 Month", 3000],
    "C" : ["1.5 Month", 8000],
    "C++" : ["1 Month", 4500],
    "App Development" : ["2 Month", 7500],
    "Python" : ["1 Month", 5500],
    "Core JAVA" : ["2 Month", 4500],
    "Advanced JAVA" : ["2 Month", 10500], 
    "Cloud Computing" : ["2 Month", 4500],
    "ADCA" : ["6 month", 14000],
    "DCA" : ["", 0],
    "O level": ["", 0],
    "DCAC" : ["6 month", 12000],
    "Internship" : ["2 month", 6000],
    "Advance Excel": ["",0],
    "Advance Excel With VBA" : ["",0],
    "Digital Marketing" : ["2 Month", 9000],
    "Advance Python With Django" : ["",0],
    "Full Stack Web Development" : ["",0],
    "Node Js" : ["",0],
    "Internet Of Things" : ["1.5 Month", 8000],
    "Data Analytics Using Python" : ["2.5 Month", 12800],
    "Data Analytics Using R Lang " : ["2.5 Month", 11000],
    "Data Science" : ["",0],
    "AI and ML" : ["2 Month", 11000],
    "AI and ML With Python ":["3 Month", 15000]
}

#routes 
@app.route('/', methods=['POST', 'GET'])
def start():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm')

        user_found = mongo.db.user.find_one({'username': username})
        email_found = mongo.db.user.find_one({'email': email})

        if user_found:
            message = 'Username already exists!'
        elif email_found:
            message = 'Email already exists!'
        elif not validate_email(email):
            message = 'Invalid email!'
        elif not validate_username(username):
            message = 'Username must be at least 8 characters long and contain uppercase, lowercase, and digit!'
        elif not validate_password(password):
            message = 'Password must be at least 8 characters long and contain uppercase, lowercase, and digit!'
        elif password != confirm_password:
            message = 'Passwords do not match!'
        else:
            # All validations passed — send OTP
            hashed_password = hash_password(password)
            otp = str(random.randint(100000, 999999))
            session['pending_registration'] = {
                'username': username,
                'email': email,
                'password': hashed_password
            }
            session['otp'] = otp
            session['otp_expiry'] = (datetime.utcnow() + timedelta(minutes=2)).isoformat()

            # Send OTP via email
            msg = Message(subject="OTP Verification - Registration",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email])
            msg.body = f"Your OTP for registration is: {otp}\nIt will expire in 2 minutes."
            mail.send(msg)

            return redirect(url_for('verify_register_otp'))

    return render_template('auth-register.html', message=message)

@app.route('/verify_register_otp', methods=['GET', 'POST'])
def verify_register_otp():
    message = ''
    if request.method == 'POST':
        input_otp = request.form.get('otp')
        real_otp = session.get('otp')
        expiry = session.get('otp_expiry')

        if not session.get('pending_registration'):
            message = 'Session expired. Please register again.'
            return redirect(url_for('register'))

        if datetime.utcnow() > datetime.fromisoformat(expiry):
            session.clear()
            message = 'OTP expired. Please register again.'
            return redirect(url_for('register'))

        if input_otp == real_otp:
            user_data = session.get('pending_registration')
            mongo.db.user.insert_one(user_data)
            session['username'] = 'Admin123'  # log the user in
            session.pop('pending_registration', None)
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            return redirect(url_for('index'))
        else:
            message = 'Invalid OTP!'

    return render_template('verify_otp.html', message=message)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    message = ''
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')

        user = mongo.db.user.find_one({'username': username})

        if user and check_password(user['password'], password):
            session['temp_user'] = str(user['_id'])  # Save user id temporarily

            # Generate and save OTP
            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['otp_expiry'] = (datetime.utcnow() + timedelta(minutes=2)).isoformat()

            # Send OTP
            msg = Message('Your OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[user['email']])
            msg.body = f"Your OTP is: {otp}\nIt will expire in 2 minutes."
            mail.send(msg)

            return redirect(url_for('verify_otp'))
        else:
            message = 'Invalid username or password!'

    return render_template('auth-login.html', message=message)


@app.route('/logout')
def logout():
    print(dict(session))
    session.pop('username', None)
    session.pop('otp', None)
    session.pop('otp_expiry', None)
    session.pop('temp_user', None)
    session.clear()
    print(dict(session))
    return redirect(url_for('login'))


@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'username' in session:
        return redirect(url_for('index'))
    message = ''
    if request.method == 'POST':
        input_otp = request.form.get('otp')
        stored_otp = session.get('otp')
        expiry = session.get('otp_expiry')

        if datetime.utcnow() > datetime.fromisoformat(expiry):
            message = 'OTP expired. Please login again.'
            session.clear()
            return redirect(url_for('login'))

        if input_otp == stored_otp:
            session['username'] = mongo.db.user.find_one({'_id': ObjectId(session['temp_user'])})['username']
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            session.pop('temp_user', None)
            return redirect(url_for('index'))
        else:
            message = 'Invalid OTP!'
    return render_template('verify_otp.html', message=message)

@app.route('/admin/delete_user', methods=['POST'])
def delete_user():
    if session.get('username') != "Admin123":
        flash("Unauthorized access")
        return redirect(url_for('index'))

    username_to_delete = request.form.get('username')
    if username_to_delete == 'Admin123':
        flash("Cannot delete admin user!")
    else:
        result = mongo.db.user.delete_one({'username': username_to_delete})
        if result.deleted_count > 0:
            flash(f"User '{username_to_delete}' deleted successfully.")
        else:
            flash(f"User '{username_to_delete}' not found.")

    return redirect(url_for('index'))


@app.route('/monthlyreport', methods=['POST', 'GET'])
def monthlyreport():
    try:
        if request.method == 'POST':
            data = request.form
            current_date = data.get('today_date') 
            # Convert string to datetime object
            current_date = datetime.strptime(current_date, "%Y-%m-%d")
            get_short_term_course_report(current_date)
        else:
            current_date = datetime.today()
        year = current_date.year
        month = current_date.month

        # Define the start and end of the current month
        start_of_month = datetime(year, month, 1)  # Starting from the 1st of the month
        end_of_month = datetime(year, month, calendar.monthrange(year, month)[1])  # Ending on the last day of the month

        # Create a list of all dates in the current month
        all_dates = [
            (start_of_month + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range((end_of_month - start_of_month).days + 1)
        ]

        # Initialize the result structure
        monthly_report = []


        for date_str in all_dates:
            mydict = {}
            mydict[date_str] = report(date_str) 
            monthly_report.append(mydict)

        course_total , source_total = calculate_column_totals(monthly_report)
        #extract month and year from the current date
        month = current_date.strftime("%B")
        year = current_date.year
        yearly_report = {
            "month": month,
            "year": year,
            "courses": course_total
        }

        insert_into_table(yearly_report)

        return render_template('monthlyreport.html', report=monthly_report, course_total=course_total, source_total=source_total, month = month, year = year)

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred"

@app.route('/yearlyreport', methods=['POST', 'GET'] )
def yearlyreport():
    if request.method == 'POST':
        data = request.form
        current_date = data.get('today_date') 
        print(type(current_date))
        # Convert string to datetime object
        current_date = datetime.strptime(current_date, "%Y-%m-%d")
    else:
        current_date = datetime.today()
    current_year = current_date.year
    current_month = current_date.month

    year_col = mongo.db["yearly_report"]
    # generate the list of months form April to December in String format
    months = [calendar.month_name[i] for i in range(4, 13)]

    # Fetch the report for the current year form April to December and store it in a list
    yearly_report = []
    for month in months:
        report = year_col.find_one({"month": month, "year": current_year})
        if report:
            yearly_report.append(report)
        else:
            yearly_report.append({
                "month": month,
                "year": current_year,
                "courses": {
                    "O level": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "DCAC": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "ADCA": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "DCA": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "Internship": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "New Tech": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "Short Term": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "Others": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "Total": {"e": 0, "p": 0, "r": 0, "u": 0, "tr": 0}
                    },
                "sources": {
                    "friends": 0,
                    "hoarding": 0,
                    "website": 0,
                    "Others": 0
                    }
            })

        # generate month list for the next year from January to March
    months = [calendar.month_name[i] for i in range(1, 4)]
    for month in months:
        report = year_col.find_one({"month": month, "year": current_year + 1})
        if report:
            yearly_report.append(report)
        else:
            yearly_report.append({
                "month": month,
                "year": current_year + 1,
                "courses": {
                    "O level": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "DCAC": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "ADCA": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "DCA": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "Internship": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "New Tech": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "Short Term": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "Others": {"e": 0, "p": 0, "r": 0, "u": 0},
                    "Total": {"e": 0, "p": 0, "r": 0, "u": 0, "tr": 0}
                    },
                "sources": {
                    "friends": 0,
                    "hoarding": 0,
                    "website": 0,
                    "Others": 0
                    }
            })
            
    total_summary = calculate_total_values(yearly_report)
    return render_template('yearlyreport.html', report=yearly_report, year=current_year, total = total_summary, year1 = current_year, year2 = current_year + 1)


@app.route('/table')
def table():
    
    # Fetch all documents from the collection
    all_documents = mongo.db.contacts.find({"r": "1"})

    # Convert the cursor to a list if you need to work with the documents directly
    all_documents = list(all_documents)
    return render_template('table.html', all_documents = all_documents)

@app.route('/contact_table')
def contact_table():
    # Fetch all documents from the collection
    all_documents = collection.find()

    # Convert the cursor to a list if you need to work with the documents directly
    all_documents = list(all_documents)
    return render_template('contact_table.html', all_documents = all_documents)

@app.route('/dailyreport', methods=['POST', 'GET'])
def dailyreport():
    if request.method == 'POST':
        data = request.form
        today = data.get('today_date')
    else:
        today = datetime.today().strftime("%Y-%m-%d")
    Olevel_e = mongo.db.contacts.count_documents({"course_name": "O Level", "e":"1", "date_of_enquiry": today})
    DCAC_e= mongo.db.contacts.count_documents({"course_name": "DCAC", "e":"1", "date_of_enquiry": today})
    DCA_e= mongo.db.contacts.count_documents({"course_name": "DCA", "e":"1", "date_of_enquiry": today})
    ADCA_e = mongo.db.contacts.count_documents({"course_name": "ADCA", "e":"1", "date_of_enquiry": today})
    Internship_e = mongo.db.contacts.count_documents({"course_name": "Internship", "e":"1", "date_of_enquiry": today})
    NewTech_e = mongo.db.contacts.count_documents({"course_name": "New Tech", "e":"1", "date_of_enquiry": today})
    ShortTerm_e = mongo.db.contacts.count_documents({"course_name": "Short Term", "e":"1", "date_of_enquiry": today})

    Olevel_r = mongo.db.contacts.count_documents({"course_name": "O Level", "r":"1", "register_date": today})
    DCAC_r= mongo.db.contacts.count_documents({"course_name": "DCAC", "r":"1", "register_date": today})
    DCA_r= mongo.db.contacts.count_documents({"course_name": "DCA", "r":"1", "register_date": today})
    ADCA_r = mongo.db.contacts.count_documents({"course_name": "ADCA", "r":"1", "register_date": today})
    Internship_r = mongo.db.contacts.count_documents({"course_name": "Internship", "r":"1", "register_date": today})
    NewTech_r = mongo.db.contacts.count_documents({"course_name": "New Tech", "r":"1", "register_date": today})
    ShortTerm_r = mongo.db.contacts.count_documents({"course_name": "Short Term", "r":"1", "register_date": today})

    Olevel_p = mongo.db.contacts.count_documents({"course_name": "O Level", "p":"1", "prospectus_date": today})
    DCAC_p= mongo.db.contacts.count_documents({"course_name": "DCAC", "p":"1", "prospectus_date": today})
    DCA_p= mongo.db.contacts.count_documents({"course_name": "DCA", "p":"1", "prospectus_date": today})
    ADCA_p = mongo.db.contacts.count_documents({"course_name": "BCA", "p":"1", "prospectus_date": today})
    Internship_p = mongo.db.contacts.count_documents({"course_name": "Internship", "p":"1", "prospectus_date": today})
    NewTech_p = mongo.db.contacts.count_documents({"course_name": "New Tech", "p":"1", "prospectus_date": today})
    ShortTerm_p = mongo.db.contacts.count_documents({"course_name": "Short Term", "p":"1", "prospectus_date": today})

    Olevel_u = mongo.db.contacts.count_documents({"upgrade_course": "O Level", "u":"1", "upgrade_date": today})
    DCAC_u= mongo.db.contacts.count_documents({"upgrade_course": "DCAC", "u":"1", "upgrade_date": today})
    DCA_u= mongo.db.contacts.count_documents({"upgrade_course": "DCA", "u":"1", "upgrade_date": today})
    ADCA_u = mongo.db.contacts.count_documents({"upgrade_course": "BCA", "u":"1", "upgrade_date": today})
    Internship_u = mongo.db.contacts.count_documents({"upgrade_course": "Internship", "u":"1", "upgrade_date": today})
    NewTech_u = mongo.db.contacts.count_documents({"upgrade_course": "New Tech", "p":"u", "upgrade_date": today})
    ShortTerm_u = mongo.db.contacts.count_documents({"upgrade_course": "Short Term", "u":"1", "upgrade_date": today})

    total_e = Olevel_e + DCAC_e +DCA_e+ ADCA_e+ Internship_e + NewTech_e + ShortTerm_e
    total_r = Olevel_r + DCAC_r +DCA_r +ADCA_r+ Internship_r+ NewTech_r + ShortTerm_r
    total_p = Olevel_p + DCAC_p +DCA_p+ ADCA_p + Internship_p+ NewTech_p + ShortTerm_p
    total_u = Olevel_u + DCAC_u +DCA_u+ ADCA_u + Internship_u+ NewTech_u + ShortTerm_u

    total = {
        "total_e": total_e,
        "total_r": total_r,
        "total_p": total_p,
        "total_u": total_u
    }
    enquiry = {"Olevel_e": Olevel_e, "DCAC_e": DCAC_e,"DCA_e": DCA_e, "ADCA_e":ADCA_e, "Internship_e":Internship_e, "NewTech_e": NewTech_e, "ShortTerm_e": ShortTerm_e}
    registration = {"Olevel_r": Olevel_r, "DCAC_r": DCAC_r,"DCA_r": DCA_r,  "ADCA_r": ADCA_r,"Internship_r":Internship_r, "NewTech_r": NewTech_r, "ShortTerm_r": ShortTerm_r}
    prospectus = {"Olevel_p": Olevel_p, "DCAC_p": DCAC_p,"DCA_p": DCA_p,  "ADCA_p": ADCA_p, "Internship_p":Internship_p,"NewTech_p": NewTech_p, "ShortTerm_p": ShortTerm_p}
    upgrade = {"Olevel_u": Olevel_u, "DCAC_u": DCAC_u,"DCA_u": DCA_u,  "ADCA_u": ADCA_u, "Internship_u":Internship_u,"NewTech_u": NewTech_u, "ShortTerm_u": ShortTerm_u}

    friend = mongo.db.contacts.count_documents({"source": "friends", "e": "1", "date_of_enquiry": today})
    hoarding = mongo.db.contacts.count_documents({"source": "hoarding", "e": "1", "date_of_enquiry": today})
    website = mongo.db.contacts.count_documents({"source": "website", "e": "1", "date_of_enquiry": today})
    others = mongo.db.contacts.count_documents({
        "source": {"$nin": ["friends", "hoarding", "website"]},  # Sources not in the predefined list
        "e": "1",  # Checking if 'e' is 1
        "date_of_enquiry": today  # Ensure the enquiry_date matches the specific date
    })

    sources = {
        "friends": friend,
        "hoarding": hoarding,
        "website": website,
        "Others": others
    }

    #reports = report(today)

    return render_template('dailyreport.html', enquiry = enquiry, registration = registration, prospectus = prospectus, upgrade = upgrade , total = total, sources = sources, date = today)


@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    # Get the total number of documents in the collection
    is_admin = session.get('username') == "Admin123"
    query = {"r" : "1"}
    total_documents = collection.count_documents(query)
    total_enquiries = collection.count_documents({})
    query = {"e": "1", "p": "0", "r": "0"}
    pending = collection.count_documents(query)

    pending_documents = find_pending()

    today_documents = find_today()
  
    area = find_area()
    courses = find_courses()
    # Get the current date and calculate the start and end of today
    today = datetime.today().strftime("%Y-%m-%d")
    # Query to count documents with 'today_date' of today
    query = {"register_date": today, "r" : "1"}
    total_today = collection.count_documents(query)

    prospectus = find_prospectus()
    return render_template('index.html',  username = session['username'], total_registration = total_documents, total_today = total_today, total_enquiries = total_enquiries, pending = pending, pending_documents = pending_documents, today_documents = today_documents, area = area, courses = courses, prospectus = prospectus, course_fees = course_fees, is_admin = is_admin) 

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


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            # Extract data from the form
            contact_data = {
                'date_of_enquiry': request.form.get('today-date'),
                'type_of_enquiry': request.form.get('type_of_enquiry'),
                'name': request.form.get('uname'),
                'contact_number': request.form.get('contact'),
                "whatsapp": request.form.get('whatsapp'),
                "address": request.form.get('address'),
                "area": request.form.get('area'),
                "qualification": request.form.get('qualification'),
                "college_name":request.form.get('college_name'),
                "objectives": request.form.getlist('objectives'),
                "source": request.form.getlist('source'),
                "specific_source": request.form.get('newspaperRadioText'),
                "course_name": request.form.get('coursename'),
                "new_tech_course_name": request.form.get('newTechCourseName'),
                "short_term_course_name": request.form.get('shortTermCourseName'),
                "p": '0',
                "e": '1',
                "r": '0',
                "fees": request.form.get('fees'),
                'follow_up_status': {
                        'date': request.form.get('date'),
                        'reason': request.form.get('reason')
                    },
                'register_date': None,
                'prospectus_date': None,
                'u' : "0",
                'upgrade_date': None,
                'upgrade_course': "",
                'upgrade_short_term_course': ""
            }

            mongo.db.contacts.insert_one(contact_data)
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

@app.route('/document/<string:id>/action/delete')
def delete_document(id):
    username = session.get('username')
    if username == "Admin123":
        # Convert the string id to an ObjectId
        id = ObjectId(id)
        record = mongo.db.contacts.find_one({"_id": id})
        mongo.db.contacts.delete_one({"_id": id})
        mongo.db.form_data.insert_one(record)

    else:
        # If the user is not "Admin123", redirect to the index page
        flash("You do not have permission to delete this document.", "error")
    return redirect(url_for('table'))

@app.route('/enquiry/<string:id>/action/delete')
def delete_enquiry(id):
    username = session.get('username')
    if username == "Admin123":
        # Convert the string id to an ObjectId
        id = ObjectId(id)
        # Delete the document with the given ID
        record = mongo.db.contacts.find_one({"_id": id})
        mongo.db.contacts.delete_one({"_id": id})
        mongo.db.form_data.insert_one(record)

    else:
        # If the user is not "Admin123", redirect to the index page
        flash("You do not have permission to delete this document.", "error")
    return redirect(url_for('index'))


@app.route('/register_student', methods=['POST', 'GET'])
def register_student():
    try:
        print('inside the function')
        student_id = request.form['student_id']
        obj_id = ObjectId(student_id)

        payment_type = request.form.get('payment_type')
        update_data = {
            "r": "1",
            "register_date": datetime.today().strftime("%Y-%m-%d"),
            "payment_type": payment_type,
            "fees" : request.form.get('totalFees'),
            "duration" : request.form.get('courseDuration')
        }

        if payment_type == 'full':
            update_data["admission_fee"] = int(request.form.get('admission_fee'))
        elif payment_type == 'installment':
            update_data["admission_fee"] = int(request.form.get('admission_fee_i'))
            update_data["no_of_installments"] = int(request.form.get('no_of_installments'))
            update_data["first_installment"] = int(request.form.get('first_installment'))
            update_data["monthly_installment"] = int(request.form.get('monthly_installment'))
            

        collection.update_one({"_id": obj_id}, {"$set": update_data})
        print("Updated")
        flash("Registered Student information saved successfully!", "success")
        return redirect(url_for('index'))  # Replace with actual route
    except Exception as e:
        flash("An error occurred while saving info.", "danger")
        return redirect(url_for('index'))


@app.route('/prospectus_update', methods=['POST'])
def prospectus_update():
    try:
        student_id = request.form['student_id']
        obj_id = ObjectId(student_id)

        p_prefix = request.form.get('prospectus')
        p_number = request.form.get('prospectus_number')
        full_number = p_prefix + p_number

        mongo.db.contacts.update_one(
            {"_id": obj_id},
            {"$set": {
                'p': '1',
                'prospectus_date': datetime.today().strftime("%Y-%m-%d"),
                'prospectus_number': full_number
            }}
        )

        flash("Prospectus information saved successfully!", "success")
        return redirect(url_for('index'))  # Replace with actual route
    except Exception as e:
        flash("An error occurred while saving prospectus info.", "danger")
        return redirect(url_for('index')) 


@app.route('/save', methods=['POST'])
def save_record():
    try:
        data = request.json
        print(f"Data received: {data}")  # Log the incoming data

        record_id = data.get('id')
        updated_data = data.get('data')

        id = ObjectId(record_id)
        mongo.db.contacts.update_one({"_id": id}, {"$set": updated_data})

        # Validate the ObjectId
        if not ObjectId.is_valid(record_id):
            print(f"Invalid ObjectId: {record_id}")
            return jsonify({'status': 'error', 'message': 'Invalid record ID'}), 400

        # Attempt to update the primary collection
        result = collection.update_one({'_id': ObjectId(record_id)}, {'$set': updated_data})
        print(f"Primary update result: {result.raw_result}")  # Log result of primary update

        # Attempt to update the secondary collection
        r = mongo.db.contacts.update_one({"_id": ObjectId(record_id)}, {"$set": {'u': "1"}})
        print(f"Secondary update result: {r.raw_result}")  # Log result of secondary update

        # Check for modifications
        if result.modified_count > 0 and r.modified_count > 0:
            return jsonify({'status': 'success', 'message': 'Record updated successfully!'})
        else:
            # If no modifications were made, consider it successful
            return jsonify({'status': 'success', 'message': 'Record was already up-to-date.'}), 200

    except Exception as e:
        print(f"Error updating record: {str(e)}")  # Print the full error message
        return jsonify({'status': 'error', 'message': 'Failed to update record: ' + str(e)}), 500

@app.route('/save_upgrade', methods=['POST', 'GET'])
def save_upgrade():
    try:
        # Get the JSON data from the request
        data = request.json
        contact_id = data['id']
        updated_fields = data['data']

        # Step 1: Prepare the update data
        update_data = {
            'upgrade_course': updated_fields.get('course_name'),
            'new_tech_course_name': updated_fields.get('new_tech_course_name'),
            'upgrade_short_term_course': updated_fields.get('short_term_course_name'),
            'fees': updated_fields.get('fees'),
            'u': "1",  # Set 'u' to 1
            'upgrade_date': datetime.today().strftime("%Y-%m-%d")  # Set the current date
        }

        # Step 2: Update the contacts collection
        result_contacts = mongo.db.contacts.update_one(
            {'_id': ObjectId(contact_id)},
            {'$set': update_data}
        )

        # Check if the update was acknowledged for contacts collection
        if result_contacts.modified_count == 0:
            return jsonify({'status': 'error', 'message': 'No records updated in contacts collection.'}), 400

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        app.logger.error(f"Error during upgrade: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/delete', methods=['POST'])
def delete_record():
    username = session.get('username')
    if username != "Admin123":
        return jsonify({'status': 'error', 'message': 'You do not have permission to delete this record.'}), 403
    else:
        try:
            data = request.json
            record_id = data.get('id')
            data = mongo.db.contacts.find_one({'_id': ObjectId(record_id)})
            result = collection.delete_one({'_id': ObjectId(record_id)})
            mongo.db.form_data.insert_one(data)

            if result.deleted_count > 0:
                return jsonify({'status': 'success', 'message': 'Record deleted successfully!'})
            else:
                return jsonify({'status': 'error', 'message': 'No record was deleted'}), 500
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Failed to delete record'}), 500


@app.route('/enquiry/save', methods=['POST'])
def save_enquiry():
    try:
        data = request.json
        print(f"Data received: {data}")  # Log the incoming data

        record_id = data.get('id')
        updated_data = data.get('data')

        # Validate the ObjectId
        if not ObjectId.is_valid(record_id):
            print(f"Invalid ObjectId: {record_id}")
            return jsonify({'status': 'error', 'message': 'Invalid record ID'}), 400

        # Attempt to update the primary collection
        result = mongo.db.contacts.update_one({'_id': ObjectId(record_id)}, {'$set': updated_data})

        # Check for modifications
        if result.modified_count > 0:
            return jsonify({'status': 'success', 'message': 'Record updated successfully!'})
        else:
            # If no modifications were made, consider it successful
            return jsonify({'status': 'success', 'message': 'Record was already up-to-date.'}), 200

    except Exception as e:
        print(f"Error updating record: {str(e)}")  # Print the full error message
        return jsonify({'status': 'error', 'message': 'Failed to update record: ' + str(e)}), 500

@app.route('/short_term_report', methods=['POST', 'GET'])
def get_short_term_course_report():
    course_list = ["CCC", "MS Office And Internet", "MS Office with Tally Prime", "Tally Prime", 
                  "ProE", "MATLAB", "Corel Draw", "PageMaker", "Adobe Photoshop", "Web Page Designing", 
                  "ASP.NET with MVC , LinQ AND JSON", "PHP and My SQL", "Javascript", "C", "C++", "App Development", 
                  "Python", "Core JAVA", "Advanced JAVA", "Cloud Computing"]
    known_sources = ["friends", "hoarding", "website"]

    try:
        if request.method == 'POST':
            current_date = datetime.strptime(request.form['today_date'], "%Y-%m-%d")
        else:
            current_date = datetime.today()

        year = current_date.year
        month = current_date.month
        num_days = calendar.monthrange(year, month)[1]
        
        # Create UTC date range boundaries
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, num_days, 23, 59, 59)

        # Aggregation pipeline for daily course data
        pipeline_courses = [
            {"$addFields": {
                "course": {
                    "$cond": [
                        {"$and": [
                            {"$ifNull": ["$short_term_course_name", False]},
                            {"$in": ["$short_term_course_name", course_list]}
                        ]},
                        "$short_term_course_name",
                        "Others"
                    ]
                },
                "upgrade_course": {
                    "$cond": [
                        {"$and": [
                            {"$ifNull": ["$upgrade_short_term_course", False]},
                            {"$in": ["$upgrade_short_term_course", course_list]}
                        ]},
                        "$upgrade_short_term_course",
                        "Others"
                    ]
                },
                "e": {"$cond": [{"$eq": ["$e", "1"]}, 1, 0]},
                "p": {"$cond": [{"$eq": ["$p", "1"]}, 1, 0]},
                "r": {"$cond": [{"$eq": ["$r", "1"]}, 1, 0]},
                "u": {"$cond": [{"$eq": ["$u", "1"]}, 1, 0]},
                "e_date": {"$dateFromString": {"dateString": "$date_of_enquiry"}},
                "p_date": {"$dateFromString": {"dateString": "$prospectus_date"}},
                "r_date": {"$dateFromString": {"dateString": "$register_date"}},
                "u_date": {"$dateFromString": {"dateString": "$upgrade_date"}}
            }},
            {"$match": {
                "$or": [
                    {"e_date": {"$gte": start_date, "$lte": end_date}},
                    {"p_date": {"$gte": start_date, "$lte": end_date}},
                    {"r_date": {"$gte": start_date, "$lte": end_date}},
                    {"u_date": {"$gte": start_date, "$lte": end_date}}
                ]
            }},
            {"$facet": {
                "enquiries": [
                    {"$match": {"e": 1}},
                    {"$addFields": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$e_date"}}
                    }},
                    {"$group": {
                        "_id": {"date": "$date", "course": "$course"},
                        "count": {"$sum": 1}
                    }}
                ],
                "prospectus": [
                    {"$match": {"p": 1}},
                    {"$addFields": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$p_date"}}
                    }},
                    {"$group": {
                        "_id": {"date": "$date", "course": "$course"},
                        "count": {"$sum": 1}
                    }}
                ],
                "registrations": [
                    {"$match": {"r": 1}},
                    {"$addFields": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$r_date"}}
                    }},
                    {"$group": {
                        "_id": {"date": "$date", "course": "$course"},
                        "count": {"$sum": 1}
                    }}
                ],
                "upgrades": [
                    {"$match": {"u": 1}},
                    {"$addFields": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$u_date"}}
                    }},
                    {"$group": {
                        "_id": {"date": "$date", "course": "$upgrade_course"},
                        "count": {"$sum": 1}
                    }}
                ]
            }}
        ]

        # Aggregation pipeline for daily source data (unchanged)
        pipeline_sources = [
            {"$match": {
                "date_of_enquiry": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")},
                "e": "1"
            }},
            {"$addFields": {
                "source": {
                    "$let": {
                        "vars": {
                            "first_source": {"$arrayElemAt": ["$source", 0]}
                        },
                        "in": {
                            "$cond": [
                                {"$in": ["$$first_source", known_sources]},
                                "$$first_source",
                                "Others"
                            ]
                        }
                    }
                },
                "date_obj": {"$dateFromString": {"dateString": "$date_of_enquiry"}}
            }},
            {"$match": {
                "date_obj": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date_obj"}},
                    "source": "$source"
                },
                "count": {"$sum": 1}
            }}
        ]

        # Execute aggregations
        course_data = list(mongo.db.contacts.aggregate(pipeline_courses))[0]
        source_results = mongo.db.contacts.aggregate(pipeline_sources)

        # Initialize daily data structure
        date_strings = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") 
                       for i in range(num_days)]
        daily_data = {
            d: {
                "courses": {course: {"e": 0, "p": 0, "r": 0, "u": 0} 
                           for course in course_list + ["Others"]},
                "sources": {source: 0 for source in known_sources + ["Others"]},
                "total": {"e": 0, "p": 0, "r": 0, "u": 0, "tr": 0}
            }
            for d in date_strings
        }

        # Process course data
        for category in ['enquiries', 'prospectus', 'registrations', 'upgrades']:
            event_type = category[0]  # e, p, r, u
            for doc in course_data.get(category, []):
                date_str = doc['_id']['date']
                course = doc['_id']['course']
                count = doc['count']
                
                if date_str in daily_data:
                    if course in daily_data[date_str]['courses']:
                        daily_data[date_str]['courses'][course][event_type] += count
                        daily_data[date_str]['total'][event_type] += count

        # Process source data
        for doc in source_results:
            date_str = doc['_id']['date']
            source = doc['_id']['source']
            count = doc['count']
            
            if date_str in daily_data:
                daily_data[date_str]['sources'][source] += count

        # Calculate daily TR and ensure all dates exist
        for date_str in date_strings:
            daily_data[date_str]['total']['tr'] = (
                daily_data[date_str]['total']['r'] + 
                daily_data[date_str]['total']['u']
            )

        # Convert to sorted list
        sorted_dates = sorted(daily_data.items(), key=lambda x: x[0])

        # Calculate monthly totals
        monthly_course_totals = {course: {"e": 0, "p": 0, "r": 0, "u": 0} 
                               for course in course_list + ["Others", "Total"]}
        monthly_source_totals = {source: 0 for source in known_sources + ["Others"]}

        for date_str, data in sorted_dates:
            for course in course_list + ["Others"]:
                for event in ['e', 'p', 'r', 'u']:
                    monthly_course_totals[course][event] += data['courses'][course][event]
                    monthly_course_totals['Total'][event] += data['courses'][course][event]
            
            for source in known_sources + ["Others"]:
                monthly_source_totals[source] += data['sources'][source]

        monthly_course_totals['Total']['tr'] = (
            monthly_course_totals['Total']['r'] + 
            monthly_course_totals['Total']['u']
        )

        return render_template(
            'short_term_report.html',
            report=sorted_dates,
            course_total=monthly_course_totals,
            source_total=monthly_source_totals,
            month=current_date.strftime("%B"),
            year=year,
            course_list=course_list
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        return "An error occurred", 500

@app.route('/college_report', methods=['GET', 'POST'])
def college_report():
    course_list = ["ADCA", "DCA", "O level", "DCAC", "Internship", "New Tech", "Short Term"]

    try:
        # Date handling
        if request.method == 'POST':
            selected_date = datetime.strptime(request.form['report_month'], "%Y-%m")
        else:
            selected_date = datetime.today()

        year = selected_date.year
        month = selected_date.month
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)

        # Get top colleges without Others
        college_pipeline = [
            {"$match": {
                "date_of_enquiry": {"$gte": start_date.strftime("%Y-%m-%d"), 
                                   "$lte": end_date.strftime("%Y-%m-%d")},
                "e": "1",
                "college_name": {"$exists": True, "$ne": ""}
            }},
            {"$group": {
                "_id": "$college_name",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]

        college_results = list(mongo.db.contacts.aggregate(college_pipeline))
        colleges = [doc["_id"] for doc in college_results if doc["_id"]]

        # Main aggregation pipeline
        report_pipeline = [
            {"$match": {
                "date_of_enquiry": {"$gte": start_date.strftime("%Y-%m-%d"), 
                                   "$lte": end_date.strftime("%Y-%m-%d")},
                "e": "1",
                "college_name": {"$in": colleges}
            }},
            {"$project": {
                "college": "$college_name",
                "course": {
                    "$cond": [
                        {"$in": ["$course_name", course_list]},
                        "$course_name",
                        "Others"
                    ]
                }
            }},
            {"$group": {
                "_id": {
                    "college": "$college",
                    "course": "$course"
                },
                "count": {"$sum": 1}
            }},
            {"$group": {
                "_id": "$_id.college",
                "courses": {"$push": {"course": "$_id.course", "count": "$count"}}
            }}
        ]

        report_results = list(mongo.db.contacts.aggregate(report_pipeline))

        # Initialize report data
        report_data = {college: {course: 0 for course in course_list + ["Others"]} 
                      for college in colleges}
        totals = {
            "college_totals": {college: 0 for college in colleges},
            "course_totals": {course: 0 for course in course_list + ["Others"]},
            "grand_total": 0
        }

        # Populate data
        for college_data in report_results:
            college = college_data["_id"]
            if college not in report_data:
                continue
                
            for course_entry in college_data["courses"]:
                course = course_entry["course"]
                count = course_entry["count"]
                if course in report_data[college]:
                    report_data[college][course] = count
                    totals["college_totals"][college] += count
                    totals["course_totals"][course] += count
                    totals["grand_total"] += count

        return render_template(
            'college_report.html',
            colleges=colleges,
            courses=course_list + ["Others"],
            report_data=report_data,
            totals=totals,
            month_name=start_date.strftime("%B %Y"),
            current_month=datetime.today().strftime("%Y-%m")
        )

    except Exception as e:
        print(f"Error generating college report: {str(e)}")
        return "Error generating report", 500
    
@app.route('/area_report', methods=['GET', 'POST'])
def area_report():
    course_list = ["ADCA", "DCA", "O level", "DCAC", "Internship", "New Tech", "Short Term"]
    try:
        # Date handling
        selected_date = datetime.today()
        if request.method == 'POST':
            if 'report_month' in request.form:
                selected_date = datetime.strptime(request.form['report_month'], "%Y-%m")
        
        year = selected_date.year
        month = selected_date.month
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)

        # Get top areas
        area_pipeline = [
            {"$match": {
                "date_of_enquiry": {"$gte": start_date.strftime("%Y-%m-%d"), 
                                   "$lte": end_date.strftime("%Y-%m-%d")},
                "e": "1",
                "area": {"$exists": True, "$ne": ""}
            }},
            {"$group": {
                "_id": "$area",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 15}
        ]

        area_results = list(mongo.db.contacts.aggregate(area_pipeline))
        areas = [doc["_id"] for doc in area_results if doc.get("_id")]

        # Main pipeline
        report_data = {}
        totals = {
            "area_totals": defaultdict(int),
            "course_totals": defaultdict(int),
            "grand_total": 0
        }

        if areas:
            report_pipeline = [
                {"$match": {
                    "date_of_enquiry": {"$gte": start_date.strftime("%Y-%m-%d"), 
                                      "$lte": end_date.strftime("%Y-%m-%d")},
                    "e": "1",
                    "area": {"$in": areas}
                }},
                {"$project": {
                    "area": "$area",
                    "course": {
                        "$cond": [
                            {"$in": ["$course_name", course_list]},
                            "$course_name",
                            "Others"
                        ]
                    }
                }},
                {"$group": {
                    "_id": {"area": "$area", "course": "$course"},
                    "count": {"$sum": 1}
                }}
            ]

            report_results = list(mongo.db.contacts.aggregate(report_pipeline))

            # Initialize report data
            report_data = {area: {course: 0 for course in course_list + ["Others"]} 
                         for area in areas}

            # Populate data
            for doc in report_results:
                area = doc["_id"]["area"]
                course = doc["_id"]["course"]
                count = doc["count"]
                
                if area in report_data and course in report_data[area]:
                    report_data[area][course] = count
                    totals["area_totals"][area] += count
                    totals["course_totals"][course] += count
                    totals["grand_total"] += count

        return render_template(
            'area_report.html',
            areas=areas,
            courses=course_list + ["Others"],
            report_data=report_data,
            totals=totals,
            month_name=start_date.strftime("%B %Y"),
            current_month=datetime.today().strftime("%Y-%m")
        )

    except Exception as e:
        print(f"Error generating area report: {str(e)}")
        return render_template('error.html', error_message=str(e)), 500

@app.route('/enquiry/delete', methods=['POST'])
def deleteEnquiry():
    username = session.get('username')
    if username != "Admin123":
        return jsonify({'status': 'error', 'message': 'You do not have permission to delete this record.'}), 403
    else:
        try:
            data = request.json
            record_id = data.get('id')
            data = mongo.db.contacts.find_one({'_id': ObjectId(record_id)})
            result = mongo.db.contacts.delete_one({'_id': ObjectId(record_id)})
            mongo.db.form_data.insert_one({data})

            if result.deleted_count > 0:
                return jsonify({'status': 'success', 'message': 'Record deleted successfully!'})
            else:
                print(f"Error no record")
                return jsonify({'status': 'error', 'message': 'No record was deleted'}), 500
        except Exception as e:
            print(f"Error deleting record: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to delete record'}), 500

# Yearly Area Report Route
@app.route('/yearly_area_report', methods=['GET', 'POST'])
def yearly_area_report():
    course_list = ["ADCA", "DCA", "O level", "DCAC", "Internship", "New Tech", "Short Term"]

    try:
        selected_year = datetime.today().year
        if request.method == 'POST' and 'report_year' in request.form:
            selected_year = int(request.form['report_year'])
        
        start_date = datetime(selected_year, 1, 1)
        end_date = datetime(selected_year, 12, 31, 23, 59, 59)

        # Get areas
        area_pipeline = [
            {"$match": {
                "date_of_enquiry": {"$gte": start_date.strftime("%Y-%m-%d"), 
                                   "$lte": end_date.strftime("%Y-%m-%d")},
                "e": "1",
                "area": {"$exists": True, "$ne": ""}
            }},
            {"$group": {
                "_id": "$area",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 15}
        ]

        area_results = list(mongo.db.contacts.aggregate(area_pipeline))
        areas = [doc["_id"] for doc in area_results if doc.get("_id")]

        # Main report data
        report_data = {area: {course: 0 for course in course_list + ["Others"]} 
                      for area in areas}
        totals = {
            "area_totals": {area: 0 for area in areas},
            "course_totals": {course: 0 for course in course_list + ["Others"]},
            "grand_total": 0
        }

        if areas:
            report_pipeline = [
                {"$match": {
                    "date_of_enquiry": {"$gte": start_date.strftime("%Y-%m-%d"), 
                                      "$lte": end_date.strftime("%Y-%m-%d")},
                    "e": "1",
                    "area": {"$in": areas}
                }},
                {"$project": {
                    "area": "$area",
                    "course": {
                        "$cond": [
                            {"$in": ["$course_name", course_list]},
                            "$course_name",
                            "Others"
                        ]
                    }
                }},
                {"$group": {
                    "_id": {"area": "$area", "course": "$course"},
                    "count": {"$sum": 1}
                }}
            ]

            report_results = list(mongo.db.contacts.aggregate(report_pipeline))

            for doc in report_results:
                area = doc["_id"]["area"]
                course = doc["_id"]["course"]
                count = doc["count"]
                
                if area in report_data and course in report_data[area]:
                    report_data[area][course] = count
                    totals["area_totals"][area] += count
                    totals["course_totals"][course] += count
                    totals["grand_total"] += count

        return render_template(
            'yearly_area_report.html',
            areas=areas,
            courses=course_list + ["Others"],
            report_data=report_data,
            totals=totals,
            year=selected_year,
            current_year=datetime.today().year
        )

    except Exception as e:
        print(f"Yearly Area Report Error: {str(e)}")
        return "Error generating report", 500

@app.route('/qualification_report', methods=['GET', 'POST'])
def qualification_report():
    course_list = ["ADCA", "DCA", "O level", "DCAC", "Internship", "New Tech", "Short Term"]
    qualifications = ["High School", "Undergraduate", "Graduate", "Postgraduate"]

    try:
        # Date handling
        if request.method == 'POST':
            selected_date = datetime.strptime(request.form['report_month'], "%Y-%m")
        else:
            selected_date = datetime.today()
        
        year = selected_date.year
        month = selected_date.month
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)

        # Aggregation pipeline
        pipeline = [
            {"$match": {
                "date_of_enquiry": {
                    "$gte": start_date.strftime("%Y-%m-%d"),
                    "$lte": end_date.strftime("%Y-%m-%d")
                },
                "e": "1"
            }},
            {"$project": {
                "qualification": {
                    "$cond": [
                        {"$in": ["$qualification", qualifications]},
                        "$qualification",
                        "Others"
                    ]
                },
                "course": {
                    "$cond": [
                        {"$in": ["$course_name", course_list]},
                        "$course_name",
                        "Others"
                    ]
                }
            }},
            {"$group": {
                "_id": {
                    "qualification": "$qualification",
                    "course": "$course"
                },
                "count": {"$sum": 1}
            }}
        ]

        results = list(mongo.db.contacts.aggregate(pipeline))

        # Initialize data structures
        report_data = {q: {c: 0 for c in course_list + ["Others"]} 
                      for q in qualifications + ["Others"]}
        col_totals = {course: 0 for course in course_list + ["Others"]}
        row_totals = {qual: 0 for qual in qualifications + ["Others"]}
        grand_total = 0

        # Populate data from results
        for doc in results:
            qual = doc["_id"]["qualification"]
            course = doc["_id"]["course"]
            count = doc["count"]
            
            if qual in report_data and course in report_data[qual]:
                report_data[qual][course] = count
                row_totals[qual] += count
                col_totals[course] += count
                grand_total += count

        return render_template(
            'qualification_report.html',
            qualifications=qualifications,
            courses=course_list + ["Others"],
            report_data=report_data,
            month_name=start_date.strftime("%B %Y"),
            current_month=datetime.today().strftime("%Y-%m"),
            row_totals=row_totals,
            col_totals=col_totals,
            grand_total=grand_total
        )

    except Exception as e:
        print(f"Error generating qualification report: {str(e)}")
        return "Error generating report", 500
    
# Yearly Qualification Report Route
@app.route('/yearly_qualification_report', methods=['GET', 'POST'])
def yearly_qualification_report():
    course_list = ["ADCA", "DCA", "O level", "DCAC", "Internship", "New Tech", "Short Term"]
    qualifications = ["High School", "Undergraduate", "Graduate", "Postgraduate"]

    try:
        selected_year = datetime.today().year
        if request.method == 'POST' and 'report_year' in request.form:
            selected_year = int(request.form['report_year'])
        
        start_date = datetime(selected_year, 1, 1)
        end_date = datetime(selected_year, 12, 31, 23, 59, 59)

        # Main report pipeline
        report_data = {q: {c: 0 for c in course_list + ["Others"]} 
                      for q in qualifications + ["Others"]}
        totals = {
            "qualification_totals": {q: 0 for q in qualifications + ["Others"]},
            "course_totals": {c: 0 for c in course_list + ["Others"]},
            "grand_total": 0
        }

        report_pipeline = [
            {"$match": {
                "date_of_enquiry": {"$gte": start_date.strftime("%Y-%m-%d"), 
                                   "$lte": end_date.strftime("%Y-%m-%d")},
                "e": "1"
            }},
            {"$project": {
                "qualification": {
                    "$cond": [
                        {"$in": ["$qualification", qualifications]},
                        "$qualification",
                        "Others"
                    ]
                },
                "course": {
                    "$cond": [
                        {"$in": ["$course_name", course_list]},
                        "$course_name",
                        "Others"
                    ]
                }
            }},
            {"$group": {
                "_id": {
                    "qualification": "$qualification",
                    "course": "$course"
                },
                "count": {"$sum": 1}
            }}
        ]

        report_results = list(mongo.db.contacts.aggregate(report_pipeline))

        for doc in report_results:
            qual = doc["_id"]["qualification"]
            course = doc["_id"]["course"]
            count = doc["count"]
            
            if qual in report_data and course in report_data[qual]:
                report_data[qual][course] = count
                totals["qualification_totals"][qual] += count
                totals["course_totals"][course] += count
                totals["grand_total"] += count

        return render_template(
            'yearly_qualification_report.html',
            qualifications=qualifications,
            courses=course_list + ["Others"],
            report_data=report_data,
            totals=totals,
            year=selected_year,
            current_year=datetime.today().year
        )

    except Exception as e:
        print(f"Yearly Qualification Report Error: {str(e)}")
        return "Error generating report", 500

@app.route('/yearly_college_report', methods=['GET', 'POST'])
def yearly_college_report():
    course_list = ["ADCA", "DCA", "O level", "DCAC", "Internship", "New Tech", "Short Term"]

    try:
        selected_year = datetime.today().year
        if request.method == 'POST' and 'report_year' in request.form:
            selected_year = int(request.form['report_year'])
        
        start_date = datetime(selected_year, 1, 1)
        end_date = datetime(selected_year, 12, 31, 23, 59, 59)

        # Get colleges (same pattern as monthly reports)
        college_pipeline = [
            {"$match": {
                "date_of_enquiry": {"$gte": start_date.strftime("%Y-%m-%d"), 
                                   "$lte": end_date.strftime("%Y-%m-%d")},
                "e": "1",
                "college_name": {"$exists": True, "$ne": ""}
            }},
            {"$group": {
                "_id": "$college_name",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 15}
        ]

        college_results = list(mongo.db.contacts.aggregate(college_pipeline))
        colleges = [doc["_id"] for doc in college_results if doc.get("_id")]

        # Main report pipeline (same as monthly pattern)
        report_data = {college: {course: 0 for course in course_list + ["Others"]} 
                      for college in colleges}
        totals = {
            "college_totals": {college: 0 for college in colleges},
            "course_totals": {course: 0 for course in course_list + ["Others"]},
            "grand_total": 0
        }

        if colleges:
            report_pipeline = [
                {"$match": {
                    "date_of_enquiry": {"$gte": start_date.strftime("%Y-%m-%d"), 
                                      "$lte": end_date.strftime("%Y-%m-%d")},
                    "e": "1",
                    "college_name": {"$in": colleges}
                }},
                {"$project": {
                    "college": "$college_name",
                    "course": {
                        "$cond": [
                            {"$in": ["$course_name", course_list]},
                            "$course_name",
                            "Others"
                        ]
                    }
                }},
                {"$group": {
                    "_id": {"college": "$college", "course": "$course"},
                    "count": {"$sum": 1}
                }}
            ]

            report_results = list(mongo.db.contacts.aggregate(report_pipeline))

            for doc in report_results:
                college = doc["_id"]["college"]
                course = doc["_id"]["course"]
                count = doc["count"]
                
                if college in report_data and course in report_data[college]:
                    report_data[college][course] = count
                    totals["college_totals"][college] += count
                    totals["course_totals"][course] += count
                    totals["grand_total"] += count

        return render_template(
            'yearly_college_report.html',
            colleges=colleges,
            courses=course_list + ["Others"],
            report_data=report_data,
            totals=totals,
            year=selected_year,
            current_year=datetime.today().year
        )

    except Exception as e:
        print(f"Yearly College Report Error: {str(e)}")
        return "Error generating report", 500
    

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

def find_pending():
    query = {
    "e": "1",
    "p": "0",
    "r": "0"
    }
    # Get the documents that match the query
    pending_documents = collection.find(query).sort("follow_up_status.date", 1)
    return list(pending_documents)


def find_today():
    # Get the current date and calculate the start and end of today
    today = datetime.today().strftime("%Y-%m-%d")

    query = {"follow_up_status.date": today,"e": "1","p": "0","r": "0"}
    # Get the documents that match the query
    today_documents = collection.find(query).sort("follow_up_status.date", 1)
    return list(today_documents)

def find_area():
    pipeline = [
        {
            "$group": {
                "_id": "$area",  # Group by area (replace 'area' with the actual field name)
                "total_students": { "$sum": 1 }
            }
        },
        { "$sort": { "total_students": -1 } } 
    ]


    # Execute the aggregation pipeline
    result = collection.aggregate(pipeline)
    return result

def find_courses():

    # MongoDB aggregation query to count students in each distinct area
    pipeline = [
        {
            "$group": {
                "_id": "$course_name",  # Group by the 'address' or 'area' field
                "total_students": { "$sum": 1 }  # Count the number of students in each area
            }
        },
        {
            "$sort": { "total_students": -1 }  # Sort by total students in descending order
        }
    ]

    # Execute the aggregation pipeline
    result = collection.aggregate(pipeline)
    return result

def find_prospectus():
    query = {"p": "1", "r" : "0"}
    total_prospectus = collection.find(query).sort("follow_up_status.date", 1)
    return list(total_prospectus)


def calculate_total_values(data):
    # Initialize total sums
    totals = {
        'ADCA': {'e': 0, 'p': 0, 'r': 0, 'u':0},
        'DCAC': {'e': 0, 'p': 0, 'r': 0, 'u':0},
        'DCA': {'e': 0, 'p': 0, 'r': 0, 'u':0},
        'O level': {'e': 0, 'p': 0, 'r': 0, 'u':0},
        'New Tech': {'e': 0, 'p': 0, 'r': 0, 'u':0},
        'Short Term': {'e': 0, 'p': 0, 'r': 0,'u':0 },
        'Internship': {'e': 0, 'p': 0, 'r': 0, 'u':0},
        'Others': {'e': 0, 'p': 0, 'r': 0,'u':0},
        'total' : {'e': 0, 'p': 0, 'r': 0, 'u': 0, 'tr': 0}
    }
     #Iterate over each day report in the monthly report
    for month in data:
        for course, value in month['courses'].items():
                if course != "Total":
                    totals[course]["e"] += month["courses"][course]["e"]
                    totals[course]["p"] += month["courses"][course]["p"]
                    totals[course]["r"] += month["courses"][course]["r"]
                    totals[course]["u"] += month["courses"][course]["u"]
                else:
                    totals["total"]["e"] += month["courses"]["Total"]["e"]
                    totals["total"]["p"] += month["courses"]["Total"]["p"]
                    totals["total"]["r"] += month["courses"]["Total"]["r"]
                    totals["total"]["u"] += month["courses"]["Total"]["u"]
                    totals["total"]["tr"] += month["courses"]["Total"]["tr"]

    return totals


def report(date):
    
    # Specify the date you want to filter by (input date)
    specific_date = date

    Olevel_e = mongo.db.contacts.count_documents({"course_name": "O Level", "e":"1", "date_of_enquiry": specific_date})
    DCAC_e= mongo.db.contacts.count_documents({"course_name": "DCAC", "e":"1", "date_of_enquiry": specific_date})
    DCA_e= mongo.db.contacts.count_documents({"course_name": "DCA", "e":"1", "date_of_enquiry": specific_date})
    ADCA_e = mongo.db.contacts.count_documents({"course_name": "ADCA", "e":"1", "date_of_enquiry": specific_date})
    Internship_e = mongo.db.contacts.count_documents({"course_name": "Internship", "e":"1", "date_of_enquiry": specific_date})
    NewTech_e = mongo.db.contacts.count_documents({"course_name": "New Tech", "e":"1", "date_of_enquiry": specific_date})
    ShortTerm_e = mongo.db.contacts.count_documents({"course_name": "Short Term", "e":"1", "date_of_enquiry": specific_date})
    others_e = mongo.db.contacts.count_documents({
        "course_name": {"$nin": course_list},  # Courses not in the predefined list
        "e": "1",  # Checking if 'e' is 1
        "enquiry_date": specific_date  # Ensure the upgrade_date matches the specific date
    })

    Olevel_r = mongo.db.contacts.count_documents({"course_name": "O Level", "r":"1", "register_date": specific_date})
    DCAC_r= mongo.db.contacts.count_documents({"course_name": "DCAC", "r":"1", "register_date": specific_date})
    DCA_r= mongo.db.contacts.count_documents({"course_name": "DCA", "r":"1", "register_date": specific_date})
    ADCA_r = mongo.db.contacts.count_documents({"course_name": "ADCA", "r":"1", "register_date": specific_date})
    Internship_r = mongo.db.contacts.count_documents({"course_name": "Internship", "r":"1", "register_date": specific_date})
    NewTech_r = mongo.db.contacts.count_documents({"course_name": "New Tech", "r":"1", "register_date": specific_date})
    ShortTerm_r = mongo.db.contacts.count_documents({"course_name": "Short Term", "r":"1", "register_date": specific_date})
    others_r = mongo.db.contacts.count_documents({
        "course_name": {"$nin": course_list},  # Courses not in the predefined list
        "r": "1",  # Checking if 'r' is 1
        "register_date": specific_date  # Ensure the upgrade_date matches the specific date
    })

    Olevel_p = mongo.db.contacts.count_documents({"course_name": "O Level", "p":"1", "prospectus_date": specific_date})
    DCAC_p= mongo.db.contacts.count_documents({"course_name": "DCAC", "p":"1", "prospectus_date": specific_date})
    DCA_p= mongo.db.contacts.count_documents({"course_name": "DCA", "p":"1", "prospectus_date": specific_date})
    ADCA_p = mongo.db.contacts.count_documents({"course_name": "BCA", "p":"1", "prospectus_date": specific_date})
    Internship_p = mongo.db.contacts.count_documents({"course_name": "Internship", "p":"1", "prospectus_date": specific_date})
    NewTech_p = mongo.db.contacts.count_documents({"course_name": "New Tech", "p":"1", "prospectus_date": specific_date})
    ShortTerm_p = mongo.db.contacts.count_documents({"course_name": "Short Term", "p":"1", "prospectus_date": specific_date})
    others_p = mongo.db.contacts.count_documents({
        "course_name": {"$nin": course_list},  # Courses not in the predefined list
        "p": "1",  # Checking if 'u' is 1
        "prospectus_date": specific_date  # Ensure the upgrade_date matches the specific date
    })

    Olevel_u = mongo.db.contacts.count_documents({"upgrade_course": "O Level", "u":"1", "upgrade_date": specific_date})
    DCAC_u= mongo.db.contacts.count_documents({"upgrade_course": "DCAC", "u":"1", "upgrade_date": specific_date})
    DCA_u= mongo.db.contacts.count_documents({"upgrade_course": "DCA", "u":"1", "upgrade_date": specific_date})
    ADCA_u = mongo.db.contacts.count_documents({"upgrade_course": "BCA", "u":"1", "upgrade_date": specific_date})
    Internship_u = mongo.db.contacts.count_documents({"upgrade_course": "Internship", "u":"1", "upgrade_date": specific_date})
    NewTech_u = mongo.db.contacts.count_documents({"upgrade_course": "New Tech", "p":"u", "upgrade_date": specific_date})
    ShortTerm_u = mongo.db.contacts.count_documents({"upgrade_course": "Short Term", "u":"1", "upgrade_date": specific_date})
    others_u = mongo.db.contacts.count_documents({
        "upgrade_course": {"$nin": course_list},  # Courses not in the predefined list
        "u": "1",  # Checking if 'u' is 1
        "upgrade_date": specific_date  # Ensure the upgrade_date matches the specific date
    })

    total_e = Olevel_e + DCAC_e + DCA_e + ADCA_e + Internship_e + NewTech_e + ShortTerm_e + others_e
    total_r = Olevel_r + DCAC_r + DCA_r + ADCA_r + Internship_r + NewTech_r + ShortTerm_r + others_r
    total_p = Olevel_p + DCAC_p + DCA_p + ADCA_p + Internship_p + NewTech_p + ShortTerm_p + others_p
    total_u = Olevel_u + DCAC_u + DCA_u + ADCA_u + Internship_u + NewTech_u + ShortTerm_u + others_u
    total_tr = total_u + total_r


    courses = {
        "O level": {"e": Olevel_e, "r": Olevel_r, "p": Olevel_p, "u": Olevel_u},
        "DCAC": {"e": DCAC_e, "r": DCAC_r, "p": DCAC_p, "u": DCAC_u},
        "DCA": {"e": DCA_e, "r": DCA_r, "p": DCA_p, "u": DCA_u},
        "ADCA": {"e": ADCA_e, "r": ADCA_r, "p": ADCA_p, "u": ADCA_u},
        "Internship": {"e": Internship_e, "r": Internship_r, "p": Internship_p, "u": Internship_u},
        "New Tech": {"e": NewTech_e, "r": NewTech_r, "p": NewTech_p, "u": NewTech_u},
        "Short Term": {"e": ShortTerm_e, "r": ShortTerm_r, "p": ShortTerm_p, "u": ShortTerm_u},
        "Others": {"e": others_e, "r": others_r, "p": others_p, "u": others_u},
        "Total" : {"e": total_e, "r": total_r, "p": total_p, "u": total_u, "tr": total_tr}
    }

    friend = mongo.db.contacts.count_documents({"source": "friends", "e": "1", "date_of_enquiry": specific_date})
    hoarding = mongo.db.contacts.count_documents({"source": "hoarding", "e": "1", "date_of_enquiry": specific_date})
    website = mongo.db.contacts.count_documents({"source": "website", "e": "1", "date_of_enquiry": specific_date})
    others = mongo.db.contacts.count_documents({
        "source": {"$nin": ["friends", "hoarding", "website"]},  # Sources not in the predefined list
        "e": "1",  # Checking if 'e' is 1
        "date_of_enquiry": specific_date  # Ensure the enquiry_date matches the specific date
    })

    sources = {
        "friends": friend,
        "hoarding": hoarding,
        "website": website,
        "Others": others
    }

    # Merge both course and source into one dictionary
    merged_result = {
        "courses": courses,
        "sources": sources
    }

    # Return the merged result
    return merged_result

def calculate_column_totals(monthly_report):
    # Initialize totals dictionary for each course
    course_totals = {
        "O level": {"e": 0, "p": 0, "r": 0, "u": 0},
        "DCAC": {"e": 0, "p": 0, "r": 0, "u": 0},
        "ADCA": {"e": 0, "p": 0, "r": 0, "u": 0},
        "DCA": {"e": 0, "p": 0, "r": 0, "u": 0},
        "Internship": {"e": 0, "p": 0, "r": 0, "u": 0},
        "New Tech": {"e": 0, "p": 0, "r": 0, "u": 0},
        "Short Term": {"e": 0, "p": 0, "r": 0, "u": 0},
        "Others": {"e": 0, "p": 0, "r": 0, "u": 0},
        "Total": {"e": 0, "p": 0, "r": 0, "u": 0, "tr": 0}
    }

    # Initialize totals for sources
    source_totals = {
        "friends": 0,
        "hoarding": 0,
        "website": 0,
        "Others": 0
    }

    # Iterate over each day report in the monthly report
    for day_report in monthly_report:
        for day, day_report in day_report.items():
            # Iterate over each course and update the totals
            for course in day_report["courses"]:
                if course != "Total":
                    course_totals[course]["e"] += day_report["courses"][course]["e"]
                    course_totals[course]["p"] += day_report["courses"][course]["p"]
                    course_totals[course]["r"] += day_report["courses"][course]["r"]
                    course_totals[course]["u"] += day_report["courses"][course]["u"]
                else:
                    course_totals["Total"]["e"] += day_report["courses"]["Total"]["e"]
                    course_totals["Total"]["p"] += day_report["courses"]["Total"]["p"]
                    course_totals["Total"]["r"] += day_report["courses"]["Total"]["r"]
                    course_totals["Total"]["u"] += day_report["courses"]["Total"]["u"]
                    course_totals["Total"]["tr"] += day_report["courses"]["Total"]["tr"]
            source_totals["friends"] += day_report["sources"]["friends"]
            source_totals["hoarding"] += day_report["sources"]["hoarding"]
            source_totals["website"] += day_report["sources"]["website"]
            source_totals["Others"] += day_report["sources"]["Others"]

    return course_totals, source_totals

def insert_into_table(month_report):
    year_col = mongo.db["yearly_report"]
    #check the year and month from the argument passed which is an dictionary if they exist update the record else insert
    year = month_report["year"]
    month = month_report["month"]

    #check if the record exists
    record = year_col.find_one({"year": year, "month": month})
    if record:
        #update the record
        year_col.update_one({"_id": record["_id"]}, {"$set": month_report})
    else:
        #insert the record
        year_col.insert_one(month_report)

if __name__ == '__main__':
    app.run(debug=True)


@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
