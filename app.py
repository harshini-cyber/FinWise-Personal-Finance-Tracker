from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "finwise-secret-key"


# ---------------- DATABASE CONNECTION ---------------- #

def get_db_connection():
    conn = sqlite3.connect("finance.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- CREATE DATABASE TABLES ---------------- #

def create_database():

    conn = get_db_connection()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Transactions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Budgets table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            budget_amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME PAGE ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match."

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute("""
                INSERT INTO users (full_name, email, password)
                VALUES (?, ?, ?)
            """, (
                full_name,
                email,
                hashed_password
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return "Email already registered."

        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]

            return redirect(url_for("dashboard"))

        return "Invalid email or password."

    return render_template("login.html")


# ---------------- ADD TRANSACTION ---------------- #

@app.route("/transaction", methods=["GET", "POST"])
def transaction():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        transaction_type = request.form["type"]
        amount = request.form["amount"]
        category = request.form["category"]
        description = request.form["description"]
        date = request.form["date"]

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO transactions
            (user_id, type, amount, category, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            transaction_type,
            amount,
            category,
            description,
            date
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("transaction.html")


# ---------------- SET BUDGET ---------------- #

@app.route("/budget", methods=["GET", "POST"])
def budget():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        category = request.form["category"]
        budget_amount = request.form["budget_amount"]

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO budgets
            (user_id, category, budget_amount)
            VALUES (?, ?, ?)
        """, (
            session["user_id"],
            category,
            budget_amount
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("budget.html")


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    user_id = session["user_id"]

    # Total income
    income = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ?
        AND type = 'income'
    """, (user_id,)).fetchone()[0]

    # Total expenses
    expenses = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ?
        AND type = 'expense'
    """, (user_id,)).fetchone()[0]

    # Balance
    balance = income - expenses

    # Recent transactions
    recent_transactions = conn.execute("""
        SELECT type, amount, category, description, date
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
    """, (user_id,)).fetchall()

    # Get budgets
    budgets = conn.execute("""
        SELECT category, budget_amount
        FROM budgets
        WHERE user_id = ?
    """, (user_id,)).fetchall()

    budget_status = []

    # Calculate spending for every budget category
    for budget in budgets:

        spent = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = ?
            AND type = 'expense'
            AND LOWER(category) = LOWER(?)
        """, (
            user_id,
            budget["category"]
        )).fetchone()[0]

        remaining = budget["budget_amount"] - spent

        budget_status.append({
            "category": budget["category"],
            "budget": budget["budget_amount"],
            "spent": spent,
            "remaining": remaining
        })

    # Find highest spending category
    highest_category = conn.execute("""
        SELECT category, SUM(amount) AS total_spent
        FROM transactions
        WHERE user_id = ?
        AND type = 'expense'
        GROUP BY category
        ORDER BY total_spent DESC
        LIMIT 1
    """, (user_id,)).fetchone()

    # Personalized insight
    if highest_category:

        category = highest_category["category"]
        amount = highest_category["total_spent"]

        insight = (
            f"Your highest spending category is {category.title()}. "
            f"You have spent ₹{amount:.2f} in this category."
        )

    else:

        insight = (
            "Start adding your income and expenses to receive "
            "personalized financial insights."
        )

    # Budget exceeded alert gets priority
    for budget in budget_status:

        if budget["remaining"] < 0:

            exceeded_amount = abs(budget["remaining"])

            insight = (
                f"⚠️ You have exceeded your {budget['category'].title()} "
                f"budget by ₹{exceeded_amount:.2f}."
            )

            break

    conn.close()

    return render_template(
        "dashboard.html",
        income=income,
        expenses=expenses,
        balance=balance,
        recent_transactions=recent_transactions,
        budget_status=budget_status,
        insight=insight
    )


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ---------------- RUN APPLICATION ---------------- #

if __name__ == "__main__":

    create_database()

    app.run(debug=True)