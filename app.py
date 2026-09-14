from flask import Flask, render_template, request, redirect, session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "eclinic_secret_key"


# =========================
# DATABASE
# =========================

def create_database():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            doctor TEXT NOT NULL,
            department TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT NOT NULL,
            appointment_code TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================
# PATIENT LOGIN
# =========================

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():

    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, password)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        session["user_id"] = user[0]
        session["first_name"] = user[1]
        session["last_name"] = user[2]
        session["email"] = user[3]

        return redirect("/dashboard")

    return "Invalid email or password. <a href='/'>Try Again</a>"


# =========================
# PATIENT REGISTER
# =========================

@app.route("/register", methods=["POST"])
def register():

    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (first_name, last_name, email, password)
            VALUES (?, ?, ?, ?)
        """, (
            first_name,
            last_name,
            email,
            password
        ))

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return "Email already registered. <a href='/'>Back</a>"

    conn.close()

    return redirect("/")


# =========================
# PATIENT DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    return render_template(
        "dashboard.html",
        first_name=session["first_name"]
    )


# =========================
# BOOK APPOINTMENT
# =========================

@app.route("/appointment", methods=["GET", "POST"])
def appointment():

    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":

        doctor = request.form["doctor"]
        department = request.form["department"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]
        reason = request.form["reason"]

        appointment_code = "EC-" + str(random.randint(100000, 999999))

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO appointments
            (
                user_id,
                doctor,
                department,
                appointment_date,
                appointment_time,
                reason,
                appointment_code,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            doctor,
            department,
            appointment_date,
            appointment_time,
            reason,
            appointment_code,
            "CONFIRMED"
        ))

        conn.commit()
        conn.close()

        return render_template(
            "ticket.html",
            first_name=session["first_name"],
            last_name=session["last_name"],
            email=session["email"],
            doctor=doctor,
            department=department,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            appointment_code=appointment_code
        )

    return render_template("appointment.html")


# =========================
# PATIENT LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ==================================================
# ADMIN LOGIN
# ==================================================

@app.route("/admin")
def admin_login():

    return render_template("admin_login.html")


@app.route("/admin/login", methods=["POST"])
def admin_login_user():

    email = request.form["email"]
    password = request.form["password"]

    if email == "admin@eclinic.com" and password == "admin123":

        session["admin"] = True

        return redirect("/admin/dashboard")

    return "Invalid admin email or password. <a href='/admin'>Try Again</a>"


# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            users.first_name,
            users.last_name,
            users.email,
            appointments.doctor,
            appointments.department,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.reason,
            appointments.appointment_code,
            appointments.status
        FROM appointments
        JOIN users
        ON appointments.user_id = users.id
        ORDER BY appointments.id DESC
    """)

    appointments = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        appointments=appointments
    )


# =========================
# ADMIN LOGOUT
# =========================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/admin")


# =========================
# START
# =========================

create_database()

app.run(host="0.0.0.0", port=5000, debug=True)