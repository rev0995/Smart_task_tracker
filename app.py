from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import threading, time
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import stat

app = Flask(__name__)
# A secret key is required for Flask-Login
app.config['SECRET_KEY'] = 'your_super_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Email variables (set via web form)
sender_email = None
sender_password = None
recipient_email = None
mail = None

# User model for authentication
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy=True)


# Task model with a foreign key to the User model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    # Add a new column for the task description
    description = db.Column(db.String(500), nullable=True)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="Pending")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Background thread for sending reminders 4 hours before deadline
def send_reminders():
    global sender_email, recipient_email, mail
    with app.app_context():
        while True:
            if sender_email and recipient_email:
                now = datetime.now()
                soon = now + timedelta(hours=4)
                tasks = Task.query.filter(
                    Task.deadline <= soon,
                    Task.deadline > now,
                    Task.status == "Pending"
                ).all()
                for task in tasks:
                    msg = Message(
                        'Task Reminder',
                        sender=sender_email,
                        recipients=[recipient_email]
                    )
                    msg.body = f"Reminder: Task '{task.title}' is due by {task.deadline.strftime('%Y-%m-%d %H:%M')}"
                    mail.send(msg)
                time.sleep(3600)  # Check every hour
            else:
                time.sleep(60)  # Wait while email not configured

# Routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('That email is already registered. Please login.', 'error')
            return redirect(url_for('signup'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        # Retrieve the new description field from the form data
        description = request.form['description']
        deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')
        # Assign the new task to the current user with the new description
        new_task = Task(title=title, description=description, deadline=deadline, owner=current_user)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_task.html')

@app.route('/complete/<int:id>')
@login_required
def complete_task(id):
    # Only allow users to complete their own tasks
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    task.status = "Completed"
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
@login_required
def delete_task(id):
    # Only allow users to delete their own tasks
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/')
def index():
    if current_user.is_authenticated:
        # Only fetch tasks for the currently logged-in user
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.deadline).all()
        return render_template('index.html', tasks=tasks, datetime=datetime)
    else:
        flash('Please log in to view your tasks.', 'info')
        return redirect(url_for('login'))

@app.route('/email-setup', methods=['GET', 'POST'])
@login_required
def email_setup():
    global sender_email, sender_password, recipient_email, mail
    if request.method == 'POST':
        sender_email = request.form['sender_email']
        sender_password = request.form['sender_password']
        recipient_email = request.form['recipient_email']

        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USERNAME'] = sender_email
        app.config['MAIL_PASSWORD'] = sender_password
        mail = Mail(app)
        return redirect(url_for('index'))
    return render_template('email_setup.html')

# This is a fix for the static file serving issue in the canvas environment.
if not os.path.exists('static'):
    os.makedirs('static')
if not os.path.exists('static/style.css'):
    # Create a dummy file or symbolic link
    open('static/style.css', 'w').close()

if __name__ == '__main__':
    with app.app_context():
        # This will drop any existing tables and then create new ones,
        # ensuring the database schema is always up to date.
        db.drop_all()
        db.create_all()
    threading.Thread(target=send_reminders, daemon=True).start()
    app.run(debug=True)
