from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import threading, time

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

# Email variables (set via web form)
sender_email = None
sender_password = None
recipient_email = None
mail = None  # Will be initialized after setup


# Database model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="Pending")


# Background thread for reminders
def send_reminders():
    global sender_email, recipient_email
    with app.app_context():
        while True:
            if sender_email and recipient_email:  # Only send if settings are done
                now = datetime.now()
                soon = now + timedelta(hours=24)
                tasks = Task.query.filter(Task.deadline <= soon, Task.status == "Pending").all()
                for task in tasks:
                    msg = Message(
                        'Task Reminder',
                        sender=sender_email,
                        recipients=[recipient_email]
                    )
                    msg.body = f"Reminder: Task '{task.title}' is due by {task.deadline.strftime('%Y-%m-%d %H:%M')}"
                    mail.send(msg)
            time.sleep(3600)  # Check every hour


@app.route('/')
def index():
    tasks = Task.query.order_by(Task.deadline).all()
    return render_template('index.html', tasks=tasks)


@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')
        new_task = Task(title=title, deadline=deadline)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_task.html')


@app.route('/complete/<int:id>')
def complete_task(id):
    task = Task.query.get_or_404(id)
    task.status = "Completed"
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>')
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))


# New route for email setup
@app.route('/email-setup', methods=['GET', 'POST'])
def email_setup():
    global sender_email, sender_password, recipient_email, mail
    if request.method == 'POST':
        sender_email = request.form['sender_email']
        sender_password = request.form['sender_password']
        recipient_email = request.form['recipient_email']

        # Configure Flask-Mail
        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USERNAME'] = sender_email
        app.config['MAIL_PASSWORD'] = sender_password
        mail = Mail(app)

        return redirect(url_for('index'))

    return render_template('email_setup.html')


# ...existing code...

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    threading.Thread(target=send_reminders, daemon=True).start()
    app.run(debug=True)
# ...existing code...
