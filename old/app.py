from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from functools import wraps

# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Configuration MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'mysql+pymysql://root@localhost/scolarite?charset=utf8mb4'  # Supprimé le mot de passe
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 300,
    'pool_pre_ping': True
}

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

# Modèles de données
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(20), unique=True, nullable=False)  # Assurez-vous que cette colonne existe
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # admin, staff, student
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    logs = db.relationship('UserLog', backref='user', lazy=True)  # Relation avec user_logs

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.matricule}>'

class UserLog(db.Model):
    __tablename__ = 'user_logs'
    id = db.Column('LogID', db.Integer, primary_key=True)
    matricule = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column('Action', db.String(255), nullable=False)
    timestamp = db.Column('Timestamp', db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserLog {self.action} at {self.timestamp}>'

class DocumentRequest(db.Model):
    __tablename__ = 'document_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Modifié 'users.id' à 'user.id'
    document_type = db.Column(db.String(50), nullable=False)
    copies = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, rejected
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    student = db.relationship('User', backref='document_requests')

# Décorateur pour les routes nécessitant une authentification
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Décorateur pour les routes réservées aux administrateurs
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'admin':
            flash('Accès refusé : droits insuffisants.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Initialisation de la base de données
def initialize_database():
    """Crée les tables et un compte admin si inexistant."""
    with app.app_context():
        db.create_all()
        
        # Vérifier si l'admin existe déjà
        admin = User.query.filter_by(matricule='admin001').first()
        if not admin:
            admin = User(
                matricule='admin001',
                nom='Admin',
                prenom='System',
                email='admin@example.com',
                user_type='admin',
                is_active=True
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print("Compte administrateur créé avec succès.")

# Routes
@app.route('/')
def app_home():  # Renommé pour éviter le conflit
    return render_template('index.html')  # Affiche le fichier index.html

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricule = request.form.get('matricule')
        password = request.form.get('password')
        
        user = User.query.filter_by(matricule=matricule).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Votre compte est désactivé.', 'danger')
                return redirect(url_for('login'))
            
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            session['user_name'] = f"{user.prenom} {user.nom}"
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next') or url_for('dashboard')
            flash('Connexion réussie!', 'success')
            return redirect(next_page)
        else:
            flash('Matricule ou mot de passe incorrect.', 'danger')
    
    return render_template('login.html')  # Chemin corrigé pour login.html

@app.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    
    if user.user_type == 'admin':
        stats = {
            'users': User.query.count(),
            'active_requests': DocumentRequest.query.filter_by(status='pending').count(),
            'completed_requests': DocumentRequest.query.filter_by(status='completed').count()
        }
        return render_template('dashboard/admin.html', stats=stats)
    elif user.user_type == 'staff':
        requests = DocumentRequest.query.filter_by(student_id=user.id).order_by(DocumentRequest.request_date.desc()).limit(5).all()
        return render_template('dashboard/teacher.html', user=user, requests=requests)
    else:
            requests = DocumentRequest.query.filter_by(student_id=user.id).order_by(DocumentRequest.request_date.desc()).limit(5).all()
            return render_template('dashboard/student.html', user=user, requests=requests)

@app.route('/documents', methods=['GET', 'POST'])
@login_required
def document_requests():
    if request.method == 'POST':
        try:
            request = DocumentRequest(
                student_id=session['user_id'],
                document_type=request.form.get('document_type'),
                copies=int(request.form.get('copies', 1)),
                notes=request.form.get('notes', '')
            )
            db.session.add(request)
            db.session.commit()
            flash('Demande de document soumise avec succès!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la soumission: {str(e)}', 'danger')
    
    requests = DocumentRequest.query.filter_by(student_id=session['user_id']).order_by(DocumentRequest.request_date.desc()).all()
    return render_template('admin/documents.html', requests=requests)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')  # Ajout de la récupération du champ username
            nom = request.form.get('nom')
            prenom = request.form.get('prenom')
            email = request.form.get('email')
            password = request.form.get('password')

            if not username or not nom or not prenom or not email or not password:
                flash('Tous les champs obligatoires doivent être remplis.', 'danger')
                return redirect(url_for('register'))

            user = User(
                username=username,  # Ajout du champ username
                matricule=None,  # Vous pouvez générer un matricule si nécessaire
                nom=nom,
                prenom=prenom,
                email=email,
                user_type='student',  # Par défaut, les nouveaux utilisateurs sont des étudiants
                is_active=True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'inscription: {str(e)}', 'danger')
    
    return render_template('register.html')

# Section Admin
@app.route('/admin/users')
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/requests')
@admin_required
def manage_requests():
    status = request.args.get('status', 'pending')
    requests = DocumentRequest.query.filter_by(status=status).order_by(DocumentRequest.request_date.desc()).all()
    return render_template('admin/requests.html', requests=requests, status=status)

@app.route('/admin/request/<int:request_id>/update', methods=['POST'])
@admin_required
def update_request(request_id):
    request = DocumentRequest.query.get_or_404(request_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'processing', 'completed', 'rejected']:
        request.status = new_status
        if new_status == 'completed':
            request.completion_date = datetime.utcnow()
        db.session.commit()
        flash('Statut de la demande mis à jour.', 'success')
    else:
        flash('Statut invalide.', 'danger')
    
    return redirect(url_for('manage_requests'))

@app.route('/logs')
@admin_required
def view_logs():
    logs = UserLog.query.order_by(UserLog.timestamp.desc()).all()
    return render_template('admin/logs.html', logs=logs)

# Pages statiques
@app.route('/about')
def about():
    return render_template('about.html')  # Corrigé pour utiliser le bon chemin

@app.route('/contact')
def contact():
    return render_template('contact.html')  # Corrigé pour utiliser le bon chemin

# Gestion des erreurs
@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Point d'entrée principal
if __name__ == '__main__':
    initialize_database()
    app.run(host='0.0.0.0', port=5000, debug=True)