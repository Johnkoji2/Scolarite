from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from datetime import datetime, timezone  # Ajout de timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate  # Import Flask-Migrate

# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "temporarysecretkey")

# Configuration MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', #'mysql+pymysql://username:password@localhost/Base?charset=utf8mb4'
    'mysql+pymysql://root@localhost/scolarite?charset=utf8mb4'  # Supprimé le mot de passe
)
# Remplacez `username`, `password`, `localhost`, et `scolarite` par vos informations réelles :
# - `username` : Nom d'utilisateur MySQL
# - `password` : Mot de passe MySQL
# - `localhost` : Adresse de l'hôte (par défaut `localhost`)
# - `scolarite` : Nom de la base de données
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 300,
    'pool_pre_ping': True,
    'connect_args': {
        'connect_timeout': 5,
        'read_timeout': 10,
        'write_timeout': 10
    }
}

# Initialisation de la base de données
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# Modèles de données
class User(db.Model):
    __tablename__ = 'user'  # Modifié de 'users' à 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # admin, staff, student, teacher, alumni
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Mise à jour pour timezone-aware
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    profile_image = db.Column(db.String(200), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(20), unique=True, nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Modifié 'users.id' à 'user.id'
    gender = db.Column(db.String(10), nullable=True)
    nationality = db.Column(db.String(50), nullable=True)
    photo = db.Column(db.String(200), nullable=True)
    registration_date = db.Column(db.Date, nullable=True)
    parent_name = db.Column(db.String(100), nullable=True)
    parent_phone = db.Column(db.String(20), nullable=True)
    parent_email = db.Column(db.String(120), nullable=True)
    is_scholarship = db.Column(db.Boolean, default=False)
    emergency_contact = db.Column(db.String(100), nullable=True)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(64), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Modifié 'users.id' à 'user.id'
    specialization = db.Column(db.String(100), nullable=True)
    hire_date = db.Column(db.Date, nullable=True)
    biography = db.Column(db.Text, nullable=True)
    photo = db.Column(db.String(200), nullable=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    credits = db.Column(db.Integer, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    max_students = db.Column(db.Integer, nullable=True)
    level = db.Column(db.String(50), nullable=True)

class CourseSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, nullable=True)
    building = db.Column(db.String(50), nullable=True)
    floor = db.Column(db.String(10), nullable=True)

class CourseResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(200), nullable=True)
    resource_type = db.Column(db.String(50), nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    weight = db.Column(db.Float, default=1.0)
    is_final = db.Column(db.Boolean, default=False)

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    exam_date = db.Column(db.Date, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    max_score = db.Column(db.Float, default=20.0)
    weight = db.Column(db.Float, default=1.0)

class Absence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    justified = db.Column(db.Boolean, default=False)
    justification_text = db.Column(db.Text, nullable=True)
    justification_document = db.Column(db.String(200), nullable=True)
    notify_parent = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class DocumentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    request_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    copies = db.Column(db.Integer, default=1)
    reason = db.Column(db.Text, nullable=True)
    completion_date = db.Column(db.Date, nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    document_path = db.Column(db.String(200), nullable=True)
    notify_ready = db.Column(db.Boolean, default=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    payment_type = db.Column(db.String(50), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    transaction_id = db.Column(db.String(100), nullable=True)
    invoice_number = db.Column(db.String(50), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    receipt_path = db.Column(db.String(200), nullable=True)

class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    scholarship_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False)
    provider = db.Column(db.String(100), nullable=True)
    requirements = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Mise à jour pour timezone-aware
    read = db.Column(db.Boolean, default=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Modifié 'users.id' à 'user.id'
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Mise à jour pour timezone-aware
    read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(50), nullable=True)
    link = db.Column(db.String(200), nullable=True)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    publish_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Mise à jour pour timezone-aware
    end_date = db.Column(db.DateTime, nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    visibility = db.Column(db.String(50), nullable=True)
    is_important = db.Column(db.Boolean, default=False)

class Forum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Mise à jour pour timezone-aware
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class ForumTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey('forum.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Mise à jour pour timezone-aware
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_sticky = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)

class TeacherEvaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Mise à jour pour timezone-aware
    is_anonymous = db.Column(db.Boolean, default=True)

class LibraryBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), nullable=True)
    publisher = db.Column(db.String(100), nullable=True)
    publish_year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(50), nullable=True)
    cover_image = db.Column(db.String(200), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    available = db.Column(db.Integer, default=1)

class LibraryLoan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('library_book.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    checkout_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    is_renewed = db.Column(db.Boolean, default=False)
    fine_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=True)
    max_participants = db.Column(db.Integer, nullable=True)
    registration_deadline = db.Column(db.Date, nullable=True)
    is_public = db.Column(db.Boolean, default=True)

class EventParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Modifié 'users.id' à 'user.id'
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    attendance_status = db.Column(db.String(20), nullable=True)

class Alumni(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    graduation_date = db.Column(db.Date, nullable=False)
    current_position = db.Column(db.String(100), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    linkedin_profile = db.Column(db.String(200), nullable=True)
    testimonial = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class Internship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    supervisor = db.Column(db.String(100), nullable=True)
    supervisor_email = db.Column(db.String(120), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False)
    contract_path = db.Column(db.String(200), nullable=True)
    report_path = db.Column(db.String(200), nullable=True)
    evaluation_grade = db.Column(db.Float, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)

class Calendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    all_day = db.Column(db.Boolean, default=False)
    calendar_type = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    color = db.Column(db.String(20), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Modifié 'users.id' à 'user.id'
    is_public = db.Column(db.Boolean, default=True)

class UserLog(db.Model):
    __tablename__ = 'user_logs'
    id = db.Column('LogID', db.Integer, primary_key=True)
    matricule = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Updated foreign key reference
    action = db.Column('Action', db.String(255), nullable=False)
    timestamp = db.Column('Timestamp', db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<UserLog {self.action} at {self.timestamp}>'

# Routes
@app.route('/')
def scolarite_home():  # Renommé pour éviter le conflit
    return render_template('index.html')  # Affiche le fichier index.html

@app.route('/about')
def about():
    return render_template('about.html')  # Affiche le fichier about.html

@app.route('/contact')
def contact():
    return render_template('contact.html')  # Affiche le fichier contact.html

def log_action(matricule, action):
    """Ajoute une entrée dans les journaux d'utilisateur."""
    log = UserLog(matricule=matricule, action=action)
    db.session.add(log)
    db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_type'] = user.user_type
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()

            log_action(user.id, "Connexion réussie")  # Journalisation de l'action
            
            flash('Connexion réussie!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_action(session['user_id'], "Déconnexion")  # Journalisation de l'action
    session.clear()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # ...existing code...
        return redirect(url_for('login'))
    return render_template('register.html')  # Chemin corrigé pour register.html

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder au tableau de bord.', 'warning')
        return redirect(url_for('login'))
    
    # Statistiques pour le tableau de bord
    stats = {
        'students': Student.query.count(),
        'teachers': Teacher.query.count(),
        'courses': Course.query.count(),
        'logs': UserLog.query.count()  # Ajout du nombre de journaux
    }
    
    return render_template('dashboard.html', stats=stats)  # Affiche le fichier dashboard.html

@app.route('/student')
def student():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    students = Student.query.all()  # Fetch all students from the database
    return render_template('student.html', students=students)  # Render the student.html template

@app.route('/admin/students')
def admin_students():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    students = Student.query.all()  # Fetch all students from the database
    return render_template('admin/students.html', students=students, user=user)  # Pass the user object to the template

@app.route('/admin/courses')
def admin_courses():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    courses = Course.query.all()  # Fetch all courses from the database
    return render_template('admin/courses.html', courses=courses, user=user)  # Render the courses template

@app.route('/admin/teachers')
def admin_teachers():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    teachers = Teacher.query.all()  # Fetch all teachers from the database
    return render_template('admin/teachers.html', teachers=teachers, user=user)  # Render the teachers template

@app.route('/admin/rooms')
def admin_rooms():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    rooms = Room.query.all()  # Fetch all rooms from the database
    return render_template('admin/rooms.html', rooms=rooms, user=user)  # Render the rooms template

@app.route('/admin/documents')
def admin_documents():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    documents = DocumentRequest.query.all()  # Fetch all document requests from the database
    return render_template('admin/documents.html', documents=documents, user=user)  # Render the documents template

@app.route('/admin/payments')
def admin_payments():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    payments = Payment.query.all()  # Fetch all payments from the database
    return render_template('admin/payments.html', payments=payments, user=user)  # Render the payments template

@app.route('/admin/calendar')
def admin_calendar():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    events = Calendar.query.all()  # Fetch all calendar events from the database
    return render_template('admin/calendar.html', events=events, user=user)  # Render the calendar template

@app.route('/admin/announcements')
def admin_announcements():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    announcements = Announcement.query.all()  # Fetch all announcements from the database
    return render_template('admin/announcements.html', announcements=announcements, user=user)  # Render the announcements template

@app.route('/admin/reports')
def admin_reports():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    return render_template('admin/reports.html', user=user)  # Render the reports template

@app.route('/messages')
def messages():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    messages = Message.query.filter_by(recipient_id=user.id).all()  # Fetch messages for the logged-in user
    return render_template('messages.html', messages=messages, user=user)  # Render the messages template

@app.route('/forums')
def forums():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    forums = Forum.query.all()  # Fetch all forums from the database
    return render_template('forums.html', forums=forums, user=user)  # Render the forums template

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    
    if request.method == 'POST':
        # Handle settings update logic here
        username = request.form.get('username')
        email = request.form.get('email')
        if username:
            user.username = username
        if email:
            user.email = email
        db.session.commit()
        flash('Paramètres mis à jour avec succès.', 'success')
    
    return render_template('settings.html', user=user)  # Render the settings template

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404  # Affiche le fichier 404.html

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500  # Affiche le fichier 500.html

# Initialisation de l'application
if __name__ == '__main__':
    with app.app_context():
        try:
            print("Création des tables dans la base de données...")
            db.create_all()  # Crée les tables définies dans les modèles
            print("Tables créées avec succès.")

            # Créez un utilisateur admin si inexistant
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    user_type='admin',
                    is_active=True,
                    created_at=datetime.now(timezone.utc)  # Mise à jour pour timezone-aware
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("Utilisateur admin créé avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la base de données : {e}")
            app.logger.error(f"Erreur d'initialisation: {str(e)}")

    app.run(host='0.0.0.0', port=5000, debug=True)