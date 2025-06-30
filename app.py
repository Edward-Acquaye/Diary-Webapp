import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

# --- App and Database Setup ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///diary.db')

# ✅ Fix Render's postgres:// URI
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_dev_secret')

# ✅ File upload config
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_picture = db.Column(db.String(200), nullable=True)  # ✅ Added this line
    entries = db.relationship('JournalEntry', backref='author', lazy=True)

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ✅ Ensure tables are created
with app.app_context():
    db.create_all()

# --- Helper function ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access your dashboard.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', username=user.username, profile_picture=user.profile_picture)

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if 'user_id' not in session:
        flash('Please log in to view your journal.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        new_entry = JournalEntry(title=title, content=content, user_id=session['user_id'])
        db.session.add(new_entry)
        db.session.commit()
        flash('Journal entry added!', 'success')
        return redirect(url_for('journal'))

    entries = JournalEntry.query.filter_by(user_id=session['user_id']).order_by(JournalEntry.timestamp.desc()).all()
    return render_template('journal.html', entries=entries)

@app.route('/upload_profile', methods=['GET', 'POST'])
def upload_profile():
    if 'user_id' not in session:
        flash('Please log in to upload a profile picture.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'profile_pic' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['profile_pic']

        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"user_{session['user_id']}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            user = User.query.get(session['user_id'])
            user.profile_picture = filename
            db.session.commit()

            flash('Profile picture uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid file type. Please upload an image file.', 'danger')

    return render_template('upload_profile.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# --- Shell Context ---
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'JournalEntry': JournalEntry}

# --- Run App Locally ---
if __name__ == '__main__':
    app.run(debug=True)
