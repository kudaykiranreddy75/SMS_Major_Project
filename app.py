from flask import Flask, session, render_template, request, redirect, flash, send_file, url_for, send_from_directory, \
    jsonify, json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import tempfile
import logging
import json
import pandas as pd
import os
import sqlite3
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Single database for both
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder to store uploaded images
app.config['ALLOWED_EXTENSIONS'] = {'png', 'pdf', 'jpg', 'jpeg', 'gif'}
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'srujanraju340@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'oeoy dekp dlij trhc'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'srujanraju340@gmail.com'
db = SQLAlchemy(app)
mail = Mail(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def from_json(value):
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):  # Corrected exception here
        return None


# Register the custom filter with the Flask app
app.jinja_env.filters['from_json'] = from_json


# ===========================
# Student Details Model
# ===========================

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(200), nullable=True)  # Store the path to the uploaded file
    usn = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    cetrank = db.Column(db.String(100), nullable=True)
    comedk = db.Column(db.String(100), nullable=True)
    aadhaarnumber = db.Column(db.String(12), nullable=False)
    dayscholar = db.Column(db.String(20), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    presentaddress = db.Column(db.String(200), nullable=False)
    permanentaddress = db.Column(db.String(200), nullable=False)
    mobilenumber = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    # Placement Information Fields
    placed_company = db.Column(db.String(200), nullable=True)
    package = db.Column(db.String(50), nullable=True)  # Can store as string to allow for variations (e.g., "6 LPA")
    joining_date = db.Column(db.String(100), nullable=True)
    offer_letter = db.Column(db.String(200), nullable=True)


# ===========================
# Settings Model
# ===========================
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    placement_info_visible = db.Column(db.Boolean, default=False)


# ===========================
# Parent Details Model
# ===========================

class Parent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    father_photo = db.Column(db.String(100), nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    father_occupation = db.Column(db.String(100), nullable=False)
    father_mobile = db.Column(db.String(10), nullable=False)
    father_email = db.Column(db.String(100), nullable=True)
    mother_photo = db.Column(db.String(100), nullable=False)
    mother_name = db.Column(db.String(100), nullable=False)
    mother_occupation = db.Column(db.String(100), nullable=False)
    mother_mobile = db.Column(db.String(10), nullable=False)
    guardian_photo = db.Column(db.String(100), nullable=False)
    guardian_name = db.Column(db.String(100), nullable=False)
    guardian_occupation = db.Column(db.String(100), nullable=False)
    guardian_mobile = db.Column(db.String(10), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))  # Add the foreign key.


class AcademicDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(4), nullable=False)
    classs = db.Column(db.String(50), nullable=False)
    tenth_file = db.Column(db.String(200), nullable=False)
    college = db.Column(db.String(200), nullable=False)
    passyear = db.Column(db.String(4), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    puc_file = db.Column(db.String(200), nullable=False)
    hobby = db.Column(db.String(200), nullable=False)
    achieve = db.Column(db.String(200), nullable=False)
    awards_file = db.Column(db.String(400), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))  # Add the foreign key


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # Default role is student

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Create the database tables for both models

# ============
# login routes
# ============
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role  # Store user role in session
            session.permanent = True
            return redirect(url_for('optionfield'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('index.html', username=username)

    return render_template('index.html')


# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        role = request.form['role']  # Get role from form input

        if User.query.filter_by(username=username).first():
            flash('Username already taken. Try another.', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Try logging in.', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# ===================
# rbac decorum
# ===================
def role_required(*roles):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if 'user_id' not in session or session.get('role') not in roles:
                flash('Access denied !', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)

        wrapper.__name__ = f.__name__  # Preserve function name
        return wrapper

    return decorator


# Option Fields Route
@app.route('/optionfield')
def optionfield():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('optionfield.html', username=session['username'], role=session['role'])


# Admin Panel Route
@app.route('/admin')
@role_required('admin')
def admin_panel():
    return render_template('admin.html')


# Teacher Dashboard Route
@app.route('/teacher')
@role_required('teacher', 'admin')
def teacher_dashboard():
    return render_template('teacher.html')


# Student Dashboard Route
@app.route('/student')
@role_required('student', 'teacher', 'admin')
def student_dashboard():
    return render_template('student.html')


# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# ===========================
# Student Details Routes
# ===========================

@app.route('/form')
def form():
    return render_template('form.html')  # Student form


@app.route('/submit', methods=['POST'])
def submit_form():
    global filename
    if request.method == 'POST':
        # Get student form data (existing fields)
        name = request.form['name']
        photo = request.files['photo']
        usn = request.form['usn']
        dob = request.form['dob']
        gender = request.form['gender']
        cetrank = request.form['cetrank']
        comedk = request.form['comedk']
        aadhaarnumber = request.form['aadhaarnumber']
        dayscholar = request.form['dayscholar']
        branch = request.form['branch']
        presentaddress = request.form['presentaddress']
        permanentaddress = request.form['permanentaddress']
        mobilenumber = request.form['mobilenumber']
        email = request.form['email']

        # Handle image upload (existing logic)
        photo_path = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)

        # Get placement information (these fields will only be present if visible)
        placed_company = request.form.get('placed_company')
        package = request.form.get('package')
        joining_date = request.form.get('joining_date')
        offer_letter_file = request.files.get('offer_letter')
        offer_letter_path = None
        offer_letter = None

        # Handle offer letter upload
        if offer_letter_file and allowed_file(offer_letter_file.filename):
            offer_letter_filename = secure_filename(offer_letter_file.filename)
            offer_letter_path = os.path.join(app.config['UPLOAD_FOLDER'], offer_letter_filename)
            offer_letter_file.save(offer_letter_path)
            offer_letter = offer_letter_filename  # Store filename in the database

        # Save student data to the database
        new_student = Student(
            name=name,
            photo=filename,
            usn=usn,
            dob=dob,
            gender=gender,
            cetrank=cetrank,
            comedk=comedk,
            aadhaarnumber=aadhaarnumber,
            dayscholar=dayscholar,
            branch=branch,
            presentaddress=presentaddress,
            permanentaddress=permanentaddress,
            mobilenumber=mobilenumber,
            email=email,
            placed_company=placed_company,
            package=package,
            joining_date=joining_date,
            offer_letter=offer_letter,
        )
        db.session.add(new_student)
        db.session.commit()
        return redirect('parentdetails')  # Or wherever you redirect after student details


@app.route('/display', methods=['GET', 'POST'])
@role_required('teacher', 'admin')
def display():
    search_query = request.args.get('search', '')
    if search_query:
        # Adjust the filter logic based on your database field names
        students = Student.query.filter(Student.name.contains(search_query) |
                                        Student.usn.contains(search_query) |
                                        Student.branch.contains(search_query)).all()
    else:
        students = Student.query.all()
    return render_template('display.html', students=students, search_query=search_query)


from flask import url_for, redirect


# Replace 'display_students' with the correct function name
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        student.name = request.form['name']
        photo = request.files['photo']
        student.usn = request.form['usn']
        student.dob = request.form['dob']
        student.gender = request.form['gender']
        student.cetrank = request.form['cetrank']
        student.comedk = request.form['comedk']
        student.aadhaarnumber = request.form['aadhaarnumber']
        student.dayscholar = request.form['dayscholar']
        student.branch = request.form['branch']
        student.presentaddress = request.form['presentaddress']
        student.permanentaddress = request.form['permanentaddress']
        student.mobilenumber = request.form['mobilenumber']
        student.email = request.form['email']

        # Handle placement information updates
        student.placed_company = request.form.get('placed_company')
        student.package = request.form.get('package')
        student.joining_date = request.form.get('joining_date')
        offer_letter_file = request.files.get('offer_letter')

        if offer_letter_file and allowed_file(offer_letter_file.filename):
            offer_letter_filename = secure_filename(offer_letter_file.filename)
            offer_letter_path = os.path.join(app.config['UPLOAD_FOLDER'], offer_letter_filename)
            offer_letter_file.save(offer_letter_path)
            student.offer_letter = offer_letter_filename

        if photo and allowed_file(photo.filename):
            if student.photo:
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student.photo)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            student.photo = filename

        db.session.commit()
        return redirect(url_for('display'))
    return render_template('update.html', student=student)


logging.basicConfig(level=logging.DEBUG)


@app.route('/download', methods=['POST'])
def download_searched_data():
    try:
        search_query = request.form.get('search_query', '').strip()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()

        tables = {
            'Student': Student,
            'Parent': Parent,
            'AcademicDetails': AcademicDetails
        }

        with pd.ExcelWriter(temp_file.name, engine='xlsxwriter') as writer:
            for sheet_name, model in tables.items():
                if search_query:
                    if model == Student:
                        data = model.query.filter(
                            (Student.name.ilike(f'%{search_query}%')) |
                            (Student.usn.ilike(f'%{search_query}%')) |
                            (Student.branch.ilike(f'%{search_query}%'))
                        ).all()
                    elif model == Parent:
                        # Find student IDs that match the search query
                        student_ids = Student.query.filter(
                            (Student.name.ilike(f'%{search_query}%')) |
                            (Student.usn.ilike(f'%{search_query}%')) |
                            (Student.branch.ilike(f'%{search_query}%'))
                        ).with_entities(Student.id).all()
                        student_ids = [student_id[0] for student_id in student_ids if student_id]
                        if student_ids:
                            data = model.query.filter(Parent.student_id.in_(student_ids)).all()
                        else:
                            data = []
                    elif model == AcademicDetails:
                        # Find student IDs that match the search query
                        student_ids = Student.query.filter(
                            (Student.name.ilike(f'%{search_query}%')) |
                            (Student.usn.ilike(f'%{search_query}%')) |
                            (Student.branch.ilike(f'%{search_query}%'))
                        ).with_entities(Student.id).all()
                        student_ids = [student_id[0] for student_id in student_ids if student_id]
                        if student_ids:
                            data = model.query.filter(AcademicDetails.student_id.in_(student_ids)).all()
                        else:
                            data = []
                else:
                    data = model.query.all()

                if not data:
                    continue

                headers = [column.name for column in model.__table__.columns]
                data_dicts = [{column: getattr(row, column) for column in headers} for row in data]
                df = pd.DataFrame(data_dicts, columns=headers)
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        return send_file(temp_file.name, as_attachment=True, download_name="searched_data.xlsx")

    except Exception as e:
        return f"An error occurred: {e}", 500


# ===========================
# Parent Details Routes
# ===========================

@app.route('/parentdetails', methods=["GET", "POST"])
def parentdetails():
    if request.method == "POST":
        father_photo = request.files['father_photo']
        mother_photo = request.files['mother_photo']
        guardian_photo = request.files['guardian_photo']
        father_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], father_photo.filename)
        mother_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], mother_photo.filename)
        guardian_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], guardian_photo.filename)
        father_photo.save(father_photo_path)
        mother_photo.save(mother_photo_path)
        guardian_photo.save(guardian_photo_path)

        # Get the latest student BEFORE creating Parent
        student = Student.query.order_by(Student.id.desc()).first()
        if not student:
            print("LOG: No student found condition met!")  # Add this line
            flash("No student found to link with parent details. Fill Student Details First ", "error")
            return redirect(url_for('parentdetails'))

        new_parent = Parent(
            student_id=student.id,
            father_photo=father_photo.filename,
            father_name=request.form['father_name'],
            father_occupation=request.form['father_occupation'],
            father_mobile=request.form['father_mobile'],
            father_email=request.form['father_email'],
            mother_photo=mother_photo.filename,
            mother_name=request.form['mother_name'],
            mother_occupation=request.form['mother_occupation'],
            mother_mobile=request.form['mother_mobile'],
            guardian_photo=guardian_photo.filename,
            guardian_name=request.form['guardian_name'],
            guardian_occupation=request.form['guardian_occupation'],
            guardian_mobile=request.form['guardian_mobile']
        )

        db.session.add(new_parent)
        db.session.commit()

        return redirect(url_for('acadetails'))

    return render_template("parentdetails.html")


@app.route("/family")
@role_required('teacher', 'admin')
def family():
    search_query = request.args.get('search', '')  # Get the search query from URL
    if search_query:
        # Filter parents based on the search query
        parents = Parent.query.filter(
            (Parent.father_name.ilike(f"%{search_query}%")) |
            (Parent.mother_name.ilike(f"%{search_query}%")) |
            (Parent.guardian_name.ilike(f"%{search_query}%"))
        ).all()
    else:
        parents = Parent.query.all()
    return render_template("family.html", parents=parents, search_query=search_query)


@app.route("/update_parent/<int:id>", methods=["GET", "POST"])
def update_parent(id):
    parent = Parent.query.get_or_404(id)
    if request.method == "POST":
        parent.father_name = request.form['father_name']
        parent.father_occupation = request.form['father_occupation']
        parent.father_mobile = request.form['father_mobile']
        parent.father_email = request.form['father_email']
        parent.mother_name = request.form['mother_name']
        parent.mother_occupation = request.form['mother_occupation']
        parent.mother_mobile = request.form['mother_mobile']
        parent.guardian_name = request.form['guardian_name']
        parent.guardian_occupation = request.form['guardian_occupation']
        parent.guardian_mobile = request.form['guardian_mobile']

        # Handle file uploads for photos if changed
        father_photo = request.files['father_photo']
        mother_photo = request.files['mother_photo']
        guardian_photo = request.files['guardian_photo']

        if father_photo and allowed_file(father_photo.filename):
            father_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], father_photo.filename)
            father_photo.save(father_photo_path)
            parent.father_photo = father_photo.filename

        if mother_photo and allowed_file(mother_photo.filename):
            mother_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], mother_photo.filename)
            mother_photo.save(mother_photo_path)
            parent.mother_photo = mother_photo.filename

        if guardian_photo and allowed_file(guardian_photo.filename):
            guardian_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], guardian_photo.filename)
            guardian_photo.save(guardian_photo_path)
            parent.guardian_photo = guardian_photo.filename

        db.session.commit()
        return redirect(url_for('family'))

    return render_template("update_parent.html", parent=parent)


# =========================================
# academic details route
# =========================================
@app.route('/acadetails', methods=['GET', 'POST'])
def acadetails():
    if request.method == 'POST':
        # Retrieve form data
        school = request.form['school']
        year = request.form['year']
        classs = request.form['classs']
        college = request.form['college']
        passyear = request.form['passyear']
        grade = request.form['grade']
        hobby = request.form.get('hobby', '')
        achieve = request.form.get('achieve', '')

        # Handle file uploads
        files = {}
        for key in ['tenth_file', 'puc_file']:
            file = request.files.get(key)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
                file.save(file_path)
                files[key] = filename
            else:
                files[key] = None

        awards_files = request.files.getlist('awards_file')
        award_filenames = []
        for file in awards_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace("\\", "/")
                file.save(file_path)
                award_filenames.append(filename)

        # Find the latest student
        student = Student.query.order_by(Student.id.desc()).first()
        if not student:
            flash("No student found to associate with academic details.Fill Student and Parent Details First", "error")
            return redirect(url_for('acadetails'))

        # Create and associate AcademicDetails entry
        new_entry = AcademicDetails(
            student_id=student.id,
            school=school,
            year=year,
            classs=classs,
            college=college,
            passyear=passyear,
            grade=grade,
            hobby=hobby,
            achieve=achieve,
            tenth_file=files.get('tenth_file'),
            puc_file=files.get('puc_file'),
            awards_file=json.dumps(award_filenames) if award_filenames else None
        )

        db.session.add(new_entry)
        db.session.commit()

        return redirect(url_for('optionfield'))

    return render_template("acadetails.html")


@app.route('/acadisplay', methods=['GET', 'POST'])
@role_required('teacher', 'admin')
def acadisplay():
    if request.method == 'POST':
        search_query = request.form.get('search', '').strip()
        # Filter records based on the search query
        records = AcademicDetails.query.filter(
            (AcademicDetails.school.ilike(f'%{search_query}%')) |
            (AcademicDetails.college.ilike(f'%{search_query}%')) |
            (AcademicDetails.hobby.ilike(f'%{search_query}%'))
        ).all()
    else:
        # Fetch all records if no search query
        records = AcademicDetails.query.all()

    return render_template('acadisplay.html', records=records)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Serve uploaded files by passing the filename, no need for extra "/uploads/"
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/update_record/<int:id>', methods=['GET', 'POST'])
def update_record(id):
    record = AcademicDetails.query.get_or_404(id)

    if request.method == 'POST':
        # Update fields from form data
        record.school = request.form.get('school', record.school)
        record.year = request.form.get('year', record.year)
        record.classs = request.form.get('classs', record.classs)
        record.college = request.form.get('college', record.college)
        record.passyear = request.form.get('passyear', record.passyear)
        record.grade = request.form.get('grade', record.grade)
        record.hobby = request.form.get('hobby', record.hobby)
        record.achieve = request.form.get('achieve', record.achieve)

        # Handle file uploads if updated
        for key, field in [('tenth_file', 'tenth_file'),
                           ('puc_file', 'puc_file'),
                           ('awards_file', 'awards_file')]:
            file = request.files.get(key)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)  # Secure the filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)  # Save the file to the uploads folder
                setattr(record, field, filename)  # Update the record field with the filename

        # Save changes to the database
        try:
            db.session.commit()
            flash("Record updated successfully!", "success")
            return redirect(url_for('acadisplay'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(request.url)

    # Render the update form with the current record
    return render_template('acaupdate.html', record=record)


# delete routes
@app.route('/delete_all/<int:student_id>')
def delete_all(student_id):
    student = Student.query.get(student_id)

    if not student:
        print(f"Student with ID {student_id} not found.")
        return redirect(url_for('display'))

    print(f"Deleting student with ID {student_id}")

    # Delete student photo if exists
    if student.photo:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student.photo)
        if os.path.exists(photo_path):
            os.remove(photo_path)
            print(f"Deleted student photo: {photo_path}")

    # Delete associated parent info
    parent = Parent.query.filter_by(student_id=student_id).first()  # Assuming FK relationship
    if parent:
        for photo_attr in ['father_photo', 'mother_photo', 'guardian_photo']:
            photo_path = getattr(parent, photo_attr)
            if photo_path:
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    print(f"Deleted {photo_attr}: {full_path}")
        db.session.delete(parent)

    # Delete associated academic details
    records = AcademicDetails.query.filter_by(student_id=student_id).all()  # Assuming FK relationship
    for record in records:
        for file_attr in ['tenth_file', 'puc_file', 'awards_file']:
            file_path = getattr(record, file_attr)
            if file_path:
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    print(f"Deleted {file_attr}: {full_path}")
        db.session.delete(record)

    # Finally delete the student
    db.session.delete(student)
    db.session.commit()

    print(f"Deleted all data related to student {student.name}")
    return redirect(url_for('display'))


@app.route('/view/<int:student_id>')
@role_required('teacher', 'admin')
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    parent = Parent.query.filter_by(student_id=student_id).first()
    academic_details = AcademicDetails.query.filter_by(student_id=student_id).first()
    return render_template('view.html', student=student, parent=parent, academic_details=academic_details)


@app.route('/send_notification', methods=['POST'])
# @role_required('teacher', 'admin') # Uncomment if you have role-based access control
def send_notification():
    message = request.form.get('message')
    student_ids_str = request.form.get('student_ids')
    files = request.files.getlist('files')  # Get a list of uploaded files

    if not message or not student_ids_str:
        return jsonify({'error': 'Message and student IDs are required'}), 400

    try:
        student_ids = [int(id) for id in student_ids_str.split(',')]
    except ValueError:
        return jsonify({'error': 'Invalid student IDs format'}), 400

    students_to_notify = Student.query.filter(Student.id.in_(student_ids)).all()

    if not students_to_notify:
        return jsonify({'message': 'No students found with the provided IDs'}), 200

    sent_count = 0
    with mail.connect():
        for student in students_to_notify:
            msg = Message(f'Notification from KSSEM ECE',
                          recipients=[student.email])
            msg.body = message

            # Attach files if any
            for file in files:
                if file:
                    msg.attach(file.filename, file.content_type, file.read())

            try:
                mail.send(msg)
                print(f"Sent message to: {student.name} ({student.email}) with attachments")
                sent_count += 1
            except Exception as e:
                print(f"Error sending email to {student.email}: {e}")

    return jsonify({
                       'message': f'Message sent to {sent_count} out of {len(students_to_notify)} students with attachments (if any)'}), 200


@app.route('/api/toggle-placement-permission', methods=['POST'])
@role_required('teacher', 'admin')
def toggle_placement_permission():
    settings = Settings.query.first()
    if not settings:
        settings = Settings(placement_info_visible=True)  # Default to True on first toggle by admin
        db.session.add(settings)
    else:
        settings.placement_info_visible = not settings.placement_info_visible
    db.session.commit()
    return jsonify({'success': True, 'isVisible': settings.placement_info_visible})


@app.route('/api/placement-info-status')
def get_placement_info_status():
    settings = Settings.query.first()
    if not settings:
        # Initialize settings if they don't exist
        settings = Settings(placement_info_visible=False)
        db.session.add(settings)
        db.session.commit()
    return jsonify({'isVisible': settings.placement_info_visible})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(port=5000, debug=True)
