from flask import Flask, request, jsonify, render_template, url_for, redirect, flash, session
from flask_pymongo import PyMongo
from pymongo import MongoClient
import re
import bcrypt
from datetime import datetime, timedelta
from bson import ObjectId
from flask import jsonify
from datetime import datetime
import calendar

app = Flask(__name__)

app.secret_key = 'your_secret_key'

client = MongoClient('mongodb://localhost:27017')
db = client['mydatabase']
collection = db['form_data'] 
app.config['MONGO_URI'] = "mongodb://localhost:27017/mydatabase"
mongo = PyMongo(app)

course_list = ["ADCA", "DCA", "O level", "DCAC", "Internship", "New Tech", "Short Term", "Others"]


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

        if user_found and check_password(user_found['password'], password):
            session['username'] = username
            logged_user = username
            return redirect(url_for('index'))
        else:
            message = 'Invalid username or password!'

    return render_template('auth-login.html', message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/monthlyreport')
def monthlyreport():
    try:
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

        return render_template('monthlyreport.html', report=monthly_report, course_total=course_total, source_total=source_total)

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred"

@app.route('/yearlyreport')
def yearlyreport():
    '''collection = mongo.db["contacts"]

    # Define the current year and next year for the fiscal period
    current_year = datetime.today().year
    next_year = current_year + 1

    # List of months for the report
    months_list = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]

    def generate_report_for_period(start_date, end_date):
        pipeline = [
            {
                "$match": {
                    "date_of_enquiry": {
                        "$gte": start_date.strftime("%Y-%m-%d"),
                        "$lt": end_date.strftime("%Y-%m-%d")
                    }
                }
            },
            {
                "$project": {
                    "actual_month": {
                        "$month": {
                            "$dateFromString": {
                                "dateString": "$date_of_enquiry",
                                "format": "%Y-%m-%d",
                                "onError": None,
                                "onNull": None
                            }
                        }
                    },
                    "course_name": {
                        "$cond": [
                            {"$in": ["$course_name", course_list[:-1]]},
                            "$course_name",
                            "Others"
                        ]
                    },
                    "e": {"$toInt": "$e"},
                    "p": {"$toInt": "$p"},
                    "r": {"$toInt": "$r"},
                    "u": {"$toInt": "$u"}
                }
            },
            {
                "$match": {
                    "actual_month": {"$ne": None}
                }
            },
            {
                "$group": {
                    "_id": {
                        "month": "$actual_month",
                        "course_name": "$course_name"
                    },
                    "e_count": {"$sum": {"$cond": [{"$eq": ["$e", 1]}, 1, 0]}},
                    "p_count": {"$sum": {"$cond": [{"$eq": ["$p", 1]}, 1, 0]}},
                    "r_count": {"$sum": {"$cond": [{"$eq": ["$r", 1]}, 1, 0]}},
                    "u_count": {"$sum": {"$cond": [{"$eq": ["$u", 1]}, 1, 0]}}
                
            }
            },
            {
                "$group": {
                    "_id": "$_id.month",
                    "courses": {
                        "$push": {
                            "course_name": "$_id.course_name",
                            "e_count": "$e_count",
                            "p_count": "$p_count",
                            "r_count": "$r_count",
                            "u_count": "$u_count"
                        }
                    },
                    "total_e": {"$sum": "$e_count"},
                    "total_p": {"$sum": "$p_count"},
                    "total_r": {"$sum": "$r_count"},
                    "total_u": {"$sum": "$u_count"}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]

        return list(collection.aggregate(pipeline))

    # Generate report for April to December (current year)
    start_april = datetime(current_year, 4, 1)
    end_december = datetime(current_year, 12, 31)
    april_to_dec_report = generate_report_for_period(start_april, end_december)

    # Generate report for January to March (next year)
    start_january = datetime(next_year, 1, 1)
    end_march = datetime(next_year, 3, 31)
    jan_to_mar_report = generate_report_for_period(start_january, end_march)

    # Create a default structure for all months (April to March) with zero counts for all courses
    yearly_report = []
    for month in months_list:
        courses_with_zero_counts = [
            {"course_name": course, "e_count": 0, "p_count": 0, "r_count": 0, "u_count": 0} for course in course_list
        ]
        # Add year to each month's report
        report_year = current_year if month >= 4 else next_year
        yearly_report.append({
            "month": month,
            "year": report_year,  # Add year field
            "courses": courses_with_zero_counts,
            "total_e": 0,
            "total_p": 0,
            "total_r": 0,
            "total_u": 0
        })

    # Merge April to December report into the default structure
    for db_report in april_to_dec_report:
        db_month = db_report["_id"]
        fiscal_month = db_month - 4 + 1  # Map April-Dec to 1-9
        month_index = fiscal_month - 1  # Convert to 0-based index
        
        for db_course in db_report["courses"]:
            for report_course in yearly_report[month_index]["courses"]:
                if report_course["course_name"] == db_course["course_name"]:
                    report_course["e_count"] = db_course["e_count"]
                    report_course["p_count"] = db_course["p_count"]
                    report_course["r_count"] = db_course["r_count"]
                    report_course["u_count"] = db_course["u_count"]

        yearly_report[month_index]["total_e"] = db_report["total_e"]
        yearly_report[month_index]["total_p"] = db_report["total_p"]
        yearly_report[month_index]["total_r"] = db_report["total_r"]
        yearly_report[month_index]["total_u"] = db_report["total_u"]

    # Merge January to March report into the default structure
    for db_report in jan_to_mar_report:
        db_month = db_report["_id"]
        fiscal_month = db_month + 9  # Map Jan-Mar to 10-12
        month_index = fiscal_month - 1  # Convert to 0-based index
        
        for db_course in db_report["courses"]:
            for report_course in yearly_report[month_index]["courses"]:
                if report_course["course_name"] == db_course["course_name"]:
                    report_course["e_count"] = db_course["e_count"]
                    report_course["p_count"] = db_course["p_count"]
                    report_course["r_count"] = db_course["r_count"]
                    report_course["u_count"] = db_course["u_count"]

        yearly_report[month_index]["total_e"] = db_report["total_e"]
        yearly_report[month_index]["total_p"] = db_report["total_p"]
        yearly_report[month_index]["total_r"] = db_report["total_r"]
        yearly_report[month_index]["total_u"] = db_report["total_u"]

    # Calculate total summary (assumed function to calculate total)
    total_summary = calculate_total_values(yearly_report)'''


    current_year = datetime.today().year
    current_month = datetime.today().month

    collection = mongo.db["yearly_report"]
    # generate the list of months form April to December in String format
    months = [calendar.month_name[i] for i in range(4, 13)]

    # Fetch the report for the current year form April to December and store it in a list
    yearly_report = []
    for month in months:
        report = collection.find_one({"month": month, "year": current_year})
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
        report = collection.find_one({"month": month, "year": current_year + 1})
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
    return render_template('yearlyreport.html', report=yearly_report, year=current_year, total = total_summary)


@app.route('/table')
def table():
    collection = mongo.db["form_data"]
    # Fetch all documents from the collection
    all_documents = collection.find()

    # Convert the cursor to a list if you need to work with the documents directly
    all_documents = list(all_documents)
    return render_template('table.html', all_documents = all_documents)

@app.route('/contact_table')
def contact_table():
    collection = mongo.db["contacts"]
    # Fetch all documents from the collection
    all_documents = collection.find()

    # Convert the cursor to a list if you need to work with the documents directly
    all_documents = list(all_documents)
    return render_template('contact_table.html', all_documents = all_documents)

@app.route('/dailyreport', methods=['POST', 'GET'])
def dailyreport():
    Olevel_e = mongo.db.contacts.count_documents({"course_name": "O Level", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})
    DCAC_e= mongo.db.contacts.count_documents({"course_name": "DCAC", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})
    DCA_e= mongo.db.contacts.count_documents({"course_name": "DCA", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})
    ADCA_e = mongo.db.contacts.count_documents({"course_name": "ADCA", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})
    Internship_e = mongo.db.contacts.count_documents({"course_name": "Internship", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})
    NewTech_e = mongo.db.contacts.count_documents({"course_name": "New Tech", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})
    ShortTerm_e = mongo.db.contacts.count_documents({"course_name": "Short Term", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})

    Olevel_r = mongo.db.contacts.count_documents({"course_name": "O Level", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    DCAC_r= mongo.db.contacts.count_documents({"course_name": "DCAC", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    DCA_r= mongo.db.contacts.count_documents({"course_name": "DCA", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    ADCA_r = mongo.db.contacts.count_documents({"course_name": "ADCA", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    Internship_r = mongo.db.contacts.count_documents({"course_name": "Internship", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    NewTech_r = mongo.db.contacts.count_documents({"course_name": "New Tech", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    ShortTerm_r = mongo.db.contacts.count_documents({"course_name": "Short Term", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})

    Olevel_p = mongo.db.contacts.count_documents({"course_name": "O Level", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    DCAC_p= mongo.db.contacts.count_documents({"course_name": "DCAC", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    DCA_p= mongo.db.contacts.count_documents({"course_name": "DCA", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    ADCA_p = mongo.db.contacts.count_documents({"course_name": "BCA", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    Internship_p = mongo.db.contacts.count_documents({"course_name": "Internship", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    NewTech_p = mongo.db.contacts.count_documents({"course_name": "New Tech", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    ShortTerm_p = mongo.db.contacts.count_documents({"course_name": "Short Term", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})

    Olevel_u = mongo.db.contacts.count_documents({"course_name": "O Level", "u":"1", "upgrade_date": datetime.today().strftime("%Y-%m-%d")})
    DCAC_u= mongo.db.contacts.count_documents({"course_name": "DCAC", "u":"1", "upgrade_date": datetime.today().strftime("%Y-%m-%d")})
    DCA_u= mongo.db.contacts.count_documents({"course_name": "DCA", "u":"1", "upgrade_date": datetime.today().strftime("%Y-%m-%d")})
    ADCA_u = mongo.db.contacts.count_documents({"course_name": "BCA", "u":"1", "upgrade_date": datetime.today().strftime("%Y-%m-%d")})
    Internship_u = mongo.db.contacts.count_documents({"course_name": "Internship", "u":"1", "upgrade_date": datetime.today().strftime("%Y-%m-%d")})
    NewTech_u = mongo.db.contacts.count_documents({"course_name": "New Tech", "p":"u", "upgrade_date": datetime.today().strftime("%Y-%m-%d")})
    ShortTerm_u = mongo.db.contacts.count_documents({"course_name": "Short Term", "u":"1", "upgrade_date": datetime.today().strftime("%Y-%m-%d")})

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


    specific_date = datetime.today().strftime("%Y-%m-%d")

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

    print(sources)

    reports = report(datetime.today().strftime("%Y-%m-%d"))

    return render_template('dailyreport.html', enquiry = enquiry, registration = registration, prospectus = prospectus, upgrade = upgrade , total = total, sources = sources)


@app.route('/index')
def index():

    username = session.get('username', None)
    coll = mongo.db["contacts"]
    # Get the total number of documents in the collection
    query = {"r" : "1"}
    total_documents = coll.count_documents(query)
    total_enquiries = coll.count_documents({})
    query = {"e": "1", "p": "0", "r": "0"}
    pending = coll.count_documents(query)

    pending_documents = find_pending()

    today_documents = find_today()
  
    area = find_area()
    courses = find_courses()
    # Get the current date and calculate the start and end of today
    today = datetime.today().strftime("%Y-%m-%d")
    # Query to count documents with 'today_date' of today
    query = {"register_date": today, "r" : "1"}
    total_today = coll.count_documents(query)

    prospectus = find_prospectus()
    return render_template('index.html', username = username, total_registration = total_documents, total_today = total_today, total_enquiries = total_enquiries, pending = pending, pending_documents = pending_documents, today_documents = today_documents, area = area, courses = courses, prospectus = prospectus) 

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
            "area": request.form.get('area'),
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
            "e": request.form.get('e'),
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
            if request.form.get('r') == '1':
                registered_date = datetime.today().strftime("%Y-%m-%d")
            else:
                registered_date = None
            if request.form.get('p') == '1':
                prospectus_date = datetime.today().strftime("%Y-%m-%d")
            else:
                prospectus_date = None
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
                "p": request.form.get('p'),
                "e": request.form.get('e'),
                "r": request.form.get('r'),
                "fees": request.form.get('fees'),
                'follow_up_status': {
                        'date': request.form.get('date'),
                        'reason': request.form.get('reason')
                    },
                'register_date': registered_date,
                'prospectus_date': prospectus_date,
                'u' : "0",
                'upgrade_date':upgrade_date,
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

@app.route('/update_contact/<string:id>', methods=['GET', 'POST'])
def update_contact(id):
    collection = mongo.db["contacts"]
    
    # Convert id to ObjectId
    id = ObjectId(id)
    
    if request.method == 'POST':
        # Get the form data
        fees = request.form.get('fees')
        
        # Update the document with the given ID
        collection.update_one({"_id": id}, {"$set": {'r': "1", 'register_date': datetime.today().strftime("%Y-%m-%d"), 'fees': fees}})
    
        target_collection = mongo.db['form_data']
        
        document = collection.find_one({"_id": ObjectId(id)})

        if document:
            # Insert the document into the target collection
            target_collection.insert_one(document)
            
        return redirect(url_for('success'))
    
    # Retrieve the document to display on the update_contact page
    document = collection.find_one({"_id": id})
    
    return render_template('update_contact.html', document=document)

@app.route('/success', methods=['POST', 'GET'])
def success():
    username = session.get('username', None)
    return render_template('success.html') 

@app.route('/document/<string:id>/action/delete')
def delete_document(id):
    # Convert the string id to an ObjectId
    id = ObjectId(id)
    # Delete the document with the given ID
    mongo.db.form_data.delete_one({"_id": id})
    return redirect(url_for('table'))

@app.route('/enquiry/<string:id>/action/delete')
def delete_enquiry(id):
    # Convert the string id to an ObjectId
    id = ObjectId(id)
    # Delete the document with the given ID
    mongo.db.contacts.update_one({"_id": id}, {"$set": {'r': "2"}})
    return redirect(url_for('index'))

@app.route('/enquiry/<string:id>/action/registered')
def registered(id):
    # Redirect to update_contact route, passing the id
    return redirect(url_for('update_contact', id=id))

@app.route('/enquiry/<string:id>/action/prospectus')
def prospectus(id):
    id = ObjectId(id)
    mongo.db.contacts.update_one({"_id": id}, {"$set": {'p': '1', 'prospectus_date': datetime.today().strftime("%Y-%m-%d")}})
    return redirect(url_for('index'))

@app.route('/save', methods=['POST'])
def save_record():
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

"""@app.route('/save_upgrade', methods=['POST'])
def save_upgrade():
    try:
        data = request.json
        print(f"Upgrade data received: {data}")  # Log the incoming data

        record_id = data.get('id')
        updated_data = data.get('data')

        # Validate the ObjectId
        if not ObjectId.is_valid(record_id):
            print(f"Invalid ObjectId: {record_id}")
            return jsonify({'status': 'error', 'message': 'Invalid record ID'}), 400

        # Attempt to update only the course-related fields in the primary collection
        result = collection.update_one(
            {'_id': ObjectId(record_id)},
            {'$set': {
                'course_name': updated_data.get('course_name'),
                'new_tech_course_name': updated_data.get('new_tech_course_name'),
                'short_term_course_name': updated_data.get('short_term_course_name'),
                'fees': updated_data.get('fees')
            }}
        )
        print(f"Primary upgrade result: {result.raw_result}")  # Log result of primary update

        # Update the secondary collection (if required, same as in save)
        r = mongo.db.contacts.update_one({"_id": ObjectId(record_id)}, {"$set": {'u': "1"}})
        print(f"Secondary update result: {r.raw_result}")  # Log result of secondary update

        # Check if any modifications were made
        if result.modified_count > 0 and r.modified_count > 0:
            return jsonify({'status': 'success', 'message': 'Course-related data upgraded successfully!'})
        else:
            return jsonify({'status': 'success', 'message': 'No changes detected, record already up-to-date.'}), 200

    except Exception as e:
        print(f"Error upgrading record: {str(e)}")  # Log the error message
        return jsonify({'status': 'error', 'message': 'Failed to upgrade record: ' + str(e)}), 500"""


@app.route('/save_upgrade', methods=['POST'])
def save_upgrade():
    try:
        # Get the JSON data from the request
        data = request.json
        contact_id = data['id']
        updated_fields = data['data']

        # Step 1: Prepare the update data
        update_data = {
            'course_name': updated_fields.get('course_name'),
            'new_tech_course_name': updated_fields.get('new_tech_course_name'),
            'short_term_course_name': updated_fields.get('short_term_course_name'),
            'fees': updated_fields.get('fees'),
            'u': "1",  # Set 'u' to 1
            'upgrade_date': datetime.today().strftime("%Y-%m-%d")  # Set the current date
        }

        # Step 2: Update the contacts collection
        result_contacts = mongo.db.contacts.update_one(
            {'_id': ObjectId(contact_id)},
            {'$set': update_data}
        )

        # Step 3: Update the form_data collection
        result_form_data = mongo.db.form_data.update_one(
            {'_id': ObjectId(contact_id)},
            {'$set': {
                'course_name': updated_fields.get('course_name'),
                'new_tech_course_name': updated_fields.get('new_tech_course_name'),
                'short_term_course_name': updated_fields.get('short_term_course_name'),
                'fees': updated_fields.get('fees'),
            }}
        )

        # Check if the update was acknowledged for contacts collection
        if result_contacts.modified_count == 0:
            return jsonify({'status': 'error', 'message': 'No records updated in contacts collection.'}), 400

        # Check if the update was acknowledged for form_data collection
        if result_form_data.modified_count == 0:
            return jsonify({'status': 'error', 'message': 'No records updated in form_data collection.'}), 400

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        app.logger.error(f"Error during upgrade: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/delete', methods=['POST'])
def delete_record():
    try:
        data = request.json
        record_id = data.get('id')
        collection = mongo.db["form_data"]
        result = collection.delete_one({'_id': ObjectId(record_id)})

        if result.deleted_count > 0:
            return jsonify({'status': 'success', 'message': 'Record deleted successfully!'})
        else:
            print(f"Error no record")
            return jsonify({'status': 'error', 'message': 'No record was deleted'}), 500
    except Exception as e:
        print(f"Error deleting record: {e}")
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
        if result.modified_count > 0 or r.modified_count > 0:
            return jsonify({'status': 'success', 'message': 'Record updated successfully!'})
        else:
            # If no modifications were made, consider it successful
            return jsonify({'status': 'success', 'message': 'Record was already up-to-date.'}), 200

    except Exception as e:
        print(f"Error updating record: {str(e)}")  # Print the full error message
        return jsonify({'status': 'error', 'message': 'Failed to update record: ' + str(e)}), 500




    try:
        data = request.json
        print(f"Data received: {data}")  # Log the incoming data

        record_id = data.get('id')
        updated_data = data.get('data')

        # Validate the ObjectId
        if not ObjectId.is_valid(record_id):
            print(f"Invalid ObjectId: {record_id}")
            return jsonify({'status': 'error', 'message': 'Invalid record ID'}), 400

        # Log the existing record before updating
        existing_record = collection.find_one({'_id': ObjectId(record_id)})
        if not existing_record:
            print(f"No record found with ID: {record_id}")
            return jsonify({'status': 'error', 'message': 'Record not found'}), 404

        print(f"Existing record before update: {existing_record}")

        # Prepare the update query, ensuring nested fields are updated properly
        update_query = {'$set': {
            'name': updated_data['name'],
            'contact_number': updated_data['contact_number'],
            'type_of_enquiry': updated_data['type_of_enquiry'],
            'course_name': updated_data['course_name'],
            'address': updated_data['address'],
            'area': updated_data['area'],
            'qualification': updated_data['qualification'],
            'college_name': updated_data['college_name'],
            'follow_up_status.date': updated_data['follow_up_status']['date'],
            'follow_up_status.reason': updated_data['follow_up_status']['reason']
        }}

        # Attempt to update the primary collection
        result = mongo.db.contacts.update_one({'_id': ObjectId(record_id)}, update_query)
        print(f"Primary update result: {result.raw_result}")  # Log result of primary update

        if result.modified_count > 0:
            return jsonify({'status': 'success', 'message': 'Record updated successfully!'}), 200
        else:
            return jsonify({'status': 'success', 'message': 'Record was already up-to-date.'}), 200

    except Exception as e:
        print(f"Error updating record: {str(e)}")  # Print the full error message
        return jsonify({'status': 'error', 'message': 'Failed to update record: ' + str(e)}), 500


@app.route('/enquiry/delete', methods=['POST'])
def deleteEnquiry():
    try:
        data = request.json
        record_id = data.get('id')
        collection = mongo.db["contacts"]
        result = collection.update_one({'_id': ObjectId(record_id)}, {'$set': {'r': "2"}})

        if result.modified_count > 0:
            return jsonify({'status': 'success', 'message': 'Record deleted successfully!'})
        else:
            print(f"Error no record")
            return jsonify({'status': 'error', 'message': 'No record was deleted'}), 500
    except Exception as e:
        print(f"Error deleting record: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to delete record'}), 500

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
    collection = mongo.db["contacts"]
    query = {
    "e": "1",
    "p": "0",
    "r": "0"
    }
    # Get the documents that match the query
    pending_documents = collection.find(query).sort("follow_up_status.date", 1)
    return list(pending_documents)


def find_today():
    collection = mongo.db["contacts"]
    # Get the current date and calculate the start and end of today
    today = datetime.today().strftime("%Y-%m-%d")

    query = {"follow_up_status.date": today,"e": "1","p": "0","r": "0"}
    # Get the documents that match the query
    today_documents = collection.find(query).sort("follow_up_status.date", 1)
    return list(today_documents)

def find_area():
    collection = mongo.db['contacts']
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
    collection = mongo.db['contacts']

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
    collection = mongo.db["contacts"]
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
    collection = mongo.db["contacts"]
    
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
        "e": "1",  # Checking if 'u' is 1
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
        "r": "1",  # Checking if 'u' is 1
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

    Olevel_u = mongo.db.contacts.count_documents({"course_name": "O Level", "u":"1", "upgrade_date": specific_date})
    DCAC_u= mongo.db.contacts.count_documents({"course_name": "DCAC", "u":"1", "upgrade_date": specific_date})
    DCA_u= mongo.db.contacts.count_documents({"course_name": "DCA", "u":"1", "upgrade_date": specific_date})
    ADCA_u = mongo.db.contacts.count_documents({"course_name": "BCA", "u":"1", "upgrade_date": specific_date})
    Internship_u = mongo.db.contacts.count_documents({"course_name": "Internship", "u":"1", "upgrade_date": specific_date})
    NewTech_u = mongo.db.contacts.count_documents({"course_name": "New Tech", "p":"u", "upgrade_date": specific_date})
    ShortTerm_u = mongo.db.contacts.count_documents({"course_name": "Short Term", "u":"1", "upgrade_date": specific_date})
    others_u = mongo.db.contacts.count_documents({
        "course_name": {"$nin": course_list},  # Courses not in the predefined list
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
    collection = mongo.db["yearly_report"]
    #check the year and month from the argument passed which is an dictionary if they exist update the record else insert
    year = month_report["year"]
    month = month_report["month"]

    #check if the record exists
    record = collection.find_one({"year": year, "month": month})
    if record:
        #update the record
        collection.update_one({"_id": record["_id"]}, {"$set": month_report})
    else:
        #insert the record
        collection.insert_one(month_report)

if __name__ == '__main__':
    app.run(debug=True)
