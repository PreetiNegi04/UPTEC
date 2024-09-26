from flask import Flask, request, jsonify, render_template, url_for, redirect, flash, session
from flask_pymongo import PyMongo
from pymongo import MongoClient
import re
import bcrypt
from datetime import datetime, timedelta
from bson import ObjectId

app = Flask(__name__)

app.secret_key = 'your_secret_key'

client = MongoClient('mongodb://localhost:27017')
db = client['mydatabase']
collection = db['form_data'] 
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

@app.route('/Weeklyreport')
def Weeklyreport():
    return render_template('Weeklyreport.html')

@app.route('/yearlyreport')
def yearlyreport():
    return render_template('yearlyreport.html')

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
    BCA_e = mongo.db.contacts.count_documents({"course_name": "BCA", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})
    CCNA_e = mongo.db.contacts.count_documents({"course_name": "CCNA", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})
    NewTech_e = mongo.db.contacts.count_documents({"course_name": "New Tech", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})
    ShortTerm_e = mongo.db.contacts.count_documents({"course_name": "Short Term", "e":"1", "date_of_enquiry": datetime.today().strftime("%Y-%m-%d")})

    Olevel_r = mongo.db.contacts.count_documents({"course_name": "O Level", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    DCAC_r= mongo.db.contacts.count_documents({"course_name": "DCAC", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    BCA_r = mongo.db.contacts.count_documents({"course_name": "BCA", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    CCNA_r = mongo.db.contacts.count_documents({"course_name": "CCNA", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    NewTech_r = mongo.db.contacts.count_documents({"course_name": "New Tech", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})
    ShortTerm_r = mongo.db.contacts.count_documents({"course_name": "Short Term", "r":"1", "register_date": datetime.today().strftime("%Y-%m-%d")})

    Olevel_p = mongo.db.contacts.count_documents({"course_name": "O Level", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    DCAC_p= mongo.db.contacts.count_documents({"course_name": "DCAC", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    BCA_p = mongo.db.contacts.count_documents({"course_name": "BCA", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    CCNA_p = mongo.db.contacts.count_documents({"course_name": "CCNA", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    NewTech_p = mongo.db.contacts.count_documents({"course_name": "New Tech", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})
    ShortTerm_p = mongo.db.contacts.count_documents({"course_name": "Short Term", "p":"1", "prospectus_date": datetime.today().strftime("%Y-%m-%d")})

    total_e = Olevel_e + DCAC_e + BCA_e + CCNA_e + NewTech_e + ShortTerm_e
    total_r = Olevel_r + DCAC_r + BCA_r + CCNA_r + NewTech_r + ShortTerm_r
    total_p = Olevel_p + DCAC_p + BCA_p + CCNA_p + NewTech_p + ShortTerm_p

    total = {
        "total_e": total_e,
        "total_r": total_r,
        "total_p": total_p
    }
    enquiry = {"Olevel_e": Olevel_e, "DCAC_e": DCAC_e, "BCA_e": BCA_e, "CCNA_e": CCNA_e, "NewTech_e": NewTech_e, "ShortTerm_e": ShortTerm_e}
    registration = {"Olevel_r": Olevel_r, "DCAC_r": DCAC_r, "BCA_r": BCA_r, "CCNA_r": CCNA_r, "NewTech_r": NewTech_r, "ShortTerm_r": ShortTerm_r}
    prospectus = {"Olevel_p": Olevel_p, "DCAC_p": DCAC_p, "BCA_p": BCA_p, "CCNA_p": CCNA_p, "NewTech_p": NewTech_p, "ShortTerm_p": ShortTerm_p}
    today = datetime.today().strftime("%Y-%m-%d")

    # Aggregation query
    pipeline = [
        {
            "$match": {
                "e": "1",  # Assuming 'e' is stored as a string
                "date_of_enquiry": today
            }
        },
        {
        "$unwind": "$source"  # Unwind the source array to separate its values
        },
        {
            "$group": {
                "_id": {
                    "$cond": {
                    "if": { "$in": [ { "$trim": { "input": "$source" } }, ["friends", "hoarding", "websites"] ] },  # Check if source is in the list after trimming whitespace
                    "then": "$source",  # Keep the source as is
                    "else": "Others"  # Group under 'Others'
                }
                },
                "count": {"$sum": 1}  # Count the number of records
            }
        },
        {
        "$addFields": {
            "sortOrder": {
                "$switch": {
                    "branches": [
                        { "case": { "$eq": ["$_id", "friends"] }, "then": 1 },
                        { "case": { "$eq": ["$_id", "hoarding"] }, "then": 2 },
                        { "case": { "$eq": ["$_id", "websites"] }, "then": 3 }
                    ],
                    "default": 4  # Others come last
                    }
                }
            }
        },
        {
        "$sort": { "sortOrder": 1 }  # Sort by the custom sort order
        },
        {
            # Ensure all predefined categories have a count (including those with 0)
            "$facet": {
                "counts": [
                    { "$match": { "_id": { "$in": ["friends", "hoarding", "websites", "Others"] } } },
                    { "$sort": { "sortOrder": 1 } }
                ],
                "defaults": [
                    {
                        "$set": {
                            "sources": [
                                { "_id": "friends", "count": 0, "sortOrder": 1 },
                                { "_id": "hoarding", "count": 0, "sortOrder": 2 },
                                { "_id": "websites", "count": 0, "sortOrder": 3 },
                                { "_id": "Others", "count": 0, "sortOrder": 4 }
                            ]
                        }
                    },
                    { "$unwind": "$sources" }
                ]
            }
        },
        {
            # Combine the actual counts with defaults and handle missing ones
            "$project": {
                "final": {
                    "$concatArrays": [
                        "$defaults.sources",  # Default sources with 0 count
                        "$counts"  # Actual counted sources
                    ]
                }
            }
        },
        {
            "$unwind": "$final"  # Unwind the final array for a flat result
        },
        {
            "$group": {
                "_id": "$final._id",
                "count": { "$max": "$final.count" },  # Take the maximum between 0 and actual count
                "sortOrder": { "$first": "$final.sortOrder" }
            }
        },
        {
            "$sort": { "sortOrder": 1 }  # Sort by the custom sort order
        }
    ]

    # Execute the aggregation query and convert to a list
    result = list(mongo.db.contacts.aggregate(pipeline))
    return render_template('dailyreport.html', enquiry = enquiry, registration = registration, prospectus = prospectus, total = total, sources = result)


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
                'prospectus_date': prospectus_date
                }
            
            '''# Check if all fields are provided (additional checks can be added as needed)
            if not contact_data['follow_up_status']['date'] or not contact_data['follow_up_status']['reason']:
                flash("All fields are required!", "error")
                print("All fields are required!")
                return redirect(url_for('contact'))'''

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
        record_id = data.get('id')
        updated_data = data.get('data')

        result = collection.update_one({'_id': ObjectId(record_id)}, {'$set': updated_data})

        if result.modified_count > 0:
            return jsonify({'status': 'success', 'message': 'Record updated successfully!'})
        else:
            return jsonify({'status': 'error', 'message': 'No record was updated'}), 500
    except Exception as e:
        print(f"Error updating record: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update record'}), 500


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
        record_id = data.get('id')
        updated_data = data.get('data')
        collection = mongo.db["contacts"]
        result = collection.update_one({'_id': ObjectId(record_id)}, {'$set': updated_data})

        if result.modified_count > 0:
            return jsonify({'status': 'success', 'message': 'Record updated successfully!'})
        else:
            return jsonify({'status': 'error', 'message': 'No record was updated'}), 500
    except Exception as e:
        print(f"Error updating record: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update record'}), 500

@app.route('/enquiry/delete', methods=['POST'])
def deleteEnquiry():
    try:
        data = request.json
        record_id = data.get('id')
        collection = mongo.db["contacts"]
        result = collection.delete_one({'_id': ObjectId(record_id)})

        if result.deleted_count > 0:
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

if __name__ == '__main__':
    app.run(debug=True)
