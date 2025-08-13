📝 Smart Task Tracker
Introduction
The Smart Task Tracker is a lightweight web application designed to help you manage your tasks and deadlines efficiently. It provides a simple interface to add, track, and complete tasks, and a powerful email reminder system to ensure you never miss an important deadline.

Features
Task Management: Add new tasks with titles and specific deadlines.

Status Tracking: Mark tasks as "Pending" or "Completed."

Task Deletion: Easily remove tasks that are no longer needed.

Email Reminders: Automatically sends email alerts 24 hours before a task's deadline.

Intuitive UI/UX: A clean, modern interface for a pleasant user experience.

Technologies Used
Backend:

Flask: A micro web framework for Python.

Flask-SQLAlchemy: An extension for Flask that adds SQLAlchemy support.

Flask-Mail: An extension for Flask to add email sending capabilities.

Frontend:

HTML, CSS

Database:

SQLite

Getting Started
Follow these instructions to get a copy of the project up and running on your local machine.

Prerequisites
You need to have Python installed. You can install project dependencies using pip.

pip install -r requirements.txt

Installation
Clone the repository:

git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

Create the database:
The first time you run the application, it will automatically create the tasks.db file.

Run the application:

python app.py

The application will be accessible at http://127.0.0.1:5000.

Email Configuration
To enable the email reminder feature, you must configure your email settings within the application.

Go to the main page and click on the "⚙ Configure Email Alerts" button.

Provide the following information:

Sender Gmail Address: The email address from which the reminders will be sent.

Gmail App Password: A special password generated for a specific application. You cannot use your regular Gmail password. Click here for instructions on how to create a Gmail App Password.

Recipient Email Address: The email address that will receive the reminders.

Click "Save Email Settings". The background reminder thread will start, and you will begin receiving alerts for tasks due in the next 24 hours.

License
This project is licensed under the MIT License - see the LICENSE file for details.
