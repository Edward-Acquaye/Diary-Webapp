import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# --- App and Database Setup ---
app = Flask(__name__)

# ✅ Use PostgreSQL on Render or fallback to SQLite locally
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///diary.db')

# ✅ Fix Render's postgres:// URI
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_dev_secret')

db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    entries = db.relationship('JournalEntry', backref='author', lazy=True)

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ✅ Ensure tables are created even on Render
with app.app_context():
    db.create_all()

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

    username = session.get('username', 'User')
    return render_template('dashboard.html', username=username)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

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

# --- Shell Context (Optional Debugging) ---
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'JournalEntry': JournalEntry}

# --- Run App Locally ---
if __name__ == '__main__':
    app.run(debug=True)
