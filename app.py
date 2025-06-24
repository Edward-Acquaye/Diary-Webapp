from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key in production
app.permanent_session_lifetime = timedelta(minutes=30)

# Simulated user data (replace this with a real database in production)
users = {
    "admin": "password",  # In production, store hashed passwords!
}

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # Check if user exists
        if username in users and users[username] == password:
            session.permanent = True
            session["user"] = username
            flash("Login successful!", "info")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Try again.", "danger")
            return render_template("login.html")
    
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return f"Welcome to your diary, {session['user']}! <br><a href='/logout'>Logout</a>"
    else:
        flash("You must log in first.", "warning")
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
