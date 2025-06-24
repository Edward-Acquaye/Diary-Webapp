from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ---------- Helpers ----------

def load_users():
    users = {}
    if os.path.exists("users.txt"):
        with open("users.txt", "r") as f:
            for line in f:
                username, password = line.strip().split(",")
                users[username] = password
    return users

def save_user(username, password):
    with open("users.txt", "a") as f:
        f.write(f"{username},{password}\n")

def diary_path(username):
    return os.path.join("diaries", f"{username}_diary.txt")

# ---------- Routes ----------

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('diary'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        if username in users:
            flash("Username already exists.")
        else:
            save_user(username, password)
            session['username'] = username
            return redirect(url_for('diary'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            session['username'] = username
            return redirect(url_for('diary'))
        else:
            flash("Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/diary', methods=['GET', 'POST'])
def diary():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    path = diary_path(username)

    if request.method == 'POST':
        entry = request.form['entry']
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, 'a') as f:
            f.write(f"[{now}] {entry}\n")

    entries = []
    if os.path.exists(path):
        with open(path, 'r') as f:
            entries = f.readlines()

    return render_template('diary.html', username=username, entries=entries)

# ---------- Start App ----------

if __name__ == "__main__":
    if not os.path.exists("diaries"):
        os.makedirs("diaries")
    app.run(debug=True)
