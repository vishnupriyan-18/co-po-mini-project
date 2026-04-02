"""Flask Application Entry Point"""
from flask import Flask, send_from_directory
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_database
from routes.auth_routes import auth_bp
from routes.course_routes import course_bp
from routes.co_routes import co_bp
from routes.student_routes import student_bp
from routes.internal_routes import internal_bp
from routes.marks_routes import marks_bp

# Frontend folder is one level up from backend/
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
app.secret_key = 'internal-marks-secret-key-2024'

# No flask-cors needed — browser and API are on the same origin now
init_database()

app.register_blueprint(auth_bp)
app.register_blueprint(course_bp)
app.register_blueprint(co_bp)
app.register_blueprint(student_bp)
app.register_blueprint(internal_bp)
app.register_blueprint(marks_bp)


# Serve frontend HTML pages
@app.route('/')
@app.route('/login')
def serve_login():
    return send_from_directory(FRONTEND_DIR, 'login.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    """Serve any frontend file (html, css, js)"""
    filepath = os.path.join(FRONTEND_DIR, filename)
    if os.path.isfile(filepath):
        return send_from_directory(FRONTEND_DIR, filename)
    # Default to login for unknown routes
    return send_from_directory(FRONTEND_DIR, 'login.html')


if __name__ == '__main__':
    print("=" * 60)
    print("Internal Assessment Marks Management System")
    print("=" * 60)
    print("Open your browser and go to:")
    print("  http://localhost:5000")
    print("=" * 60)
    print("Default Credentials:")
    print("  Teacher ID : TCH001")
    print("  Password   : faculty123")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
