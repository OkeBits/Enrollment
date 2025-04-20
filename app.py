from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import os
import random
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'users.db'


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                email TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                fullname TEXT,
                lrn TEXT,
                birthdate TEXT,
                age INTEGER,
                placeofbirth TEXT,
                phone TEXT,
                email TEXT,
                mothername TEXT,
                motheroccupation TEXT,
                fathername TEXT,
                fatheroccupation TEXT,
                year INTEGER,
                course TEXT,
                enroll_type TEXT,
                image_filename TEXT,
                subject TEXT,
                instructor TEXT,
                room TEXT
            )
        ''')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = None
    if user_id:
        db = get_db()
        g.user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()


course_subjects = {
    "ACT": [
        ("Accounting 101", "Prof. Santos"),
        ("Business Math", "Prof. Reyes"),
        ("Taxation", "Dr. Gutierrez"),
        ("Financial Management", "Ms. Delgado")
    ],
    "BSIT": [
        ("Web Dev", "Mr. Randy"),
        ("Data Structures", "Ms. Gomez"),
        ("Cybersecurity", "Engr. Tan"),
        ("Software Engineering", "Prof. Lara"),
        ("Machine Learning", "Dr. Rivera")
    ],
    "BTVTED": [
        ("Teaching Methods", "Dr. Ramos"),
        ("Curriculum Dev", "Ms. David"),
        ("Assessment Techniques", "Prof. Aquino"),
        ("Instructional Media", "Dr. Lim")
    ],
    "BAELS": [
        ("English Lit", "Prof. Villanueva"),
        ("Linguistics", "Dr. Navarro"),
        ("Creative Writing", "Ms. Torres"),
        ("World Literature", "Prof. Mercado")
    ]
}

rooms = ["Block A", "Block B", "Room 201", "Lab 3", "Section C", "Room 102", "Lab 5"]

def assign_subjects_and_instructors(course, year):
    subjects = course_subjects.get(course, [])
    if subjects:
        selected_subject = random.choice(subjects)
        subject_name, instructor = selected_subject
    else:
        subject_name, instructor = "General Studies", "Staff"
    room = random.choice(rooms)
    return subject_name, instructor, room

def generate_student_id():
    return random.randint(100000, 999999)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------- ROUTES --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/forgot')
def forgot():
    return render_template('forgot.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        db = get_db()
        try:
            db.execute('INSERT INTO users (fullname, email, username, password) VALUES (?, ?, ?, ?)',
                       (fullname, email, username, password_hash))
            db.commit()
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return "Username already exists!", 409
    return render_template('register.html')

@app.route('/enroll')
def enroll():
    if g.user:
        return render_template('enroll.html', user=g.user)
    return redirect(url_for('index'))

# File upload config
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submit_enrollment', methods=['POST'])
def submit_enrollment():
    data = request.form
    fullname = data['fullname']
    lrn = data['lrn']
    birthdate = data['date']
    age = data['age']
    placeofbirth = data['placeofbirth']
    phone = data['phone']
    email = data['email']
    mothername = data['mothername']
    motheroccupation = data['motheroccupation']
    fathername = data['fathername']
    fatheroccupation = data['fatheroccupation']
    year = data['year']
    course = data['course']
    enroll_type = data['type']

    image_filename = None
    if 'profile_image' in request.files:
        image = request.files['profile_image']
        if image and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    subject, instructor, room = assign_subjects_and_instructors(course, year)
    student_id = generate_student_id()

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO enrollments (
            student_id, fullname, lrn, birthdate, age, placeofbirth, phone,
            email, mothername, motheroccupation, fathername, fatheroccupation,
            year, course, enroll_type, image_filename, subject, instructor, room
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        student_id, fullname, lrn, birthdate, age, placeofbirth, phone,
        email, mothername, motheroccupation, fathername, fatheroccupation,
        year, course, enroll_type, image_filename, subject, instructor, room
    ))
    conn.commit()
    conn.close()

    return redirect(url_for('student_profile', student_id=student_id))

@app.route('/enrolled')
def enrolled():
    q = request.args.get('q', '')
    db = get_db()
    if q:
        enrollments = db.execute(
            "SELECT * FROM enrollments WHERE fullname LIKE ?",
            (f"%{q}%",)
        ).fetchall()
    else:
        enrollments = db.execute('SELECT * FROM enrollments').fetchall()
    return render_template('enrolled.html', enrollments=enrollments)

@app.route('/student_profile/<int:student_id>')
def student_profile(student_id):
    db = get_db()
    enrollment = db.execute('SELECT * FROM enrollments WHERE student_id = ?', (student_id,)).fetchone()
    if enrollment:
        return render_template('student_profile.html', enrollment=enrollment)
    return redirect(url_for('enrolled'))

@app.route('/delete_enrollment/<int:student_id>', methods=['POST'])
def delete_enrollment(student_id):
    db = get_db()
    db.execute('DELETE FROM enrollments WHERE student_id = ?', (student_id,))
    db.commit()
    return redirect(url_for('enrolled'))

@app.route('/dashboard')
def dashboard():
    if g.user:
        return render_template('dashboard.html', user=g.user)
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))
    return "Invalid username or password", 401

@app.route('/recover', methods=['POST'])
def recover():
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
