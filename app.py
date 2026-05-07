from flask import Flask, render_template, request, redirect, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://loan_user:JP1QeM1oMHsaMRT1tSEiYPuMdUDPQ1jG@dpg-d7u3isnavr4c73d9g2qg-a/loan_db_qb4z'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(100))
    district = db.Column(db.String(100))
    village = db.Column(db.String(100))


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    area_id = db.Column(db.Integer)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer)
    type = db.Column(db.String(20))
    amount = db.Column(db.Float)
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

# ---------------- SECRET KEY ----------------
app.secret_key = "loanappsecret"

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# ---------------- DATABASE ----------------
def init_db():
    with app.app_context():
    db.create_all()
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Areas Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state TEXT,
        district TEXT,
        village TEXT
    )
    ''')

    # Customers Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        area_id INTEGER
    )
    ''')

    # Transactions Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        type TEXT,
        amount REAL,
        date TEXT,
        time TEXT
    )
    ''')

    # Users Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    ''')

    conn.commit()
    conn.close()


init_db()


# ---------------- USER CLASS ----------------
class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = c.fetchone()

        conn.close()

        if user:
            login_user(User(user[0]))
            return redirect('/')

    return render_template('login.html')


# ---------------- LOGOUT ----------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


# ---------------- HOME ----------------
@app.route('/')
@login_required
def home():
    return render_template('home.html')


# ---------------- AREAS ----------------
@app.route('/areas')
@login_required
def areas():

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM areas")

    data = c.fetchall()

    conn.close()

    return render_template('area.html', areas=data)


# ---------------- ADD AREA ----------------
@app.route('/add_area', methods=['POST'])
@login_required
def add_area():

    state = request.form['state']
    district = request.form['district']
    village = request.form['village']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "INSERT INTO areas (state, district, village) VALUES (?, ?, ?)",
        (state, district, village)
    )

    conn.commit()
    conn.close()

    return redirect('/areas')


# ---------------- CUSTOMERS ----------------
@app.route('/customers/<int:area_id>')
@login_required
def customers(area_id):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "SELECT * FROM customers WHERE area_id=? ORDER BY name ASC",
        (area_id,)
    )

    data = c.fetchall()

    conn.close()

    return render_template(
        'customers.html',
        customers=data,
        area_id=area_id
    )


# ---------------- ADD CUSTOMER ----------------
@app.route('/add_customer', methods=['POST'])
@login_required
def add_customer():

    name = request.form['name']
    phone = request.form['phone']
    area_id = request.form['area_id']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "INSERT INTO customers (name, phone, area_id) VALUES (?, ?, ?)",
        (name, phone, area_id)
    )

    conn.commit()
    conn.close()

    return redirect(f'/customers/{area_id}')


# ---------------- CHAT ----------------
@app.route('/chat/<int:customer_id>')
@login_required
def chat(customer_id):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "SELECT * FROM transactions WHERE customer_id=?",
        (customer_id,)
    )

    data = c.fetchall()

    balance = 0

    for t in data:

        if t[2] == 'given':
            balance += t[3]
        else:
            balance -= t[3]

    status = "OPEN"

    if balance == 0 and len(data) > 0:
        status = "CLOSED"

    conn.close()

    return render_template(
        'chat.html',
        data=data,
        customer_id=customer_id,
        balance=balance,
        status=status
    )


# ---------------- ADD TRANSACTION ----------------
@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():

    customer_id = request.form['customer_id']
    amount = float(request.form['amount'])
    t_type = request.form['type']

    now = datetime.now()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
    INSERT INTO transactions (
        customer_id,
        type,
        amount,
        date,
        time
    )
    VALUES (?, ?, ?, ?, ?)
    ''',
    (
        customer_id,
        t_type,
        amount,
        now.date(),
        now.strftime("%H:%M")
    ))

    conn.commit()
    conn.close()

    return redirect(f'/chat/{customer_id}')


# ---------------- SEARCH ----------------
@app.route('/search')
@login_required
def search():

    keyword = request.args.get('q', '')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
    SELECT customers.id,
           customers.name,
           customers.phone,
           areas.village

    FROM customers

    JOIN areas
    ON customers.area_id = areas.id

    WHERE customers.name LIKE ?
    OR customers.phone LIKE ?
    """,
    (
        '%' + keyword + '%',
        '%' + keyword + '%'
    ))

    results = c.fetchall()

    conn.close()

    return render_template(
        'search.html',
        results=results
    )


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
@login_required
def dashboard():

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    today = datetime.now().date()

    c.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='received' AND date=?",
        (today,)
    )

    total = c.fetchone()[0]

    if total is None:
        total = 0

    conn.close()

    return render_template(
        'dashboard.html',
        total=total,
        today=today
    )


# ---------------- STATEMENT ----------------
@app.route('/statement/<int:customer_id>')
@login_required
def statement(customer_id):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "SELECT name FROM customers WHERE id=?",
        (customer_id,)
    )

    result = c.fetchone()

    if not result:
        return "Customer not found"

    name = result[0]

    c.execute(
        '''
        SELECT type, amount, date, time
        FROM transactions
        WHERE customer_id=?
        ORDER BY id ASC
        ''',
        (customer_id,)
    )

    data = c.fetchall()

    conn.close()

    balance = 0

    transactions = []

    for t in data:

        t_type, amount, date, time = t

        if t_type == 'given':
            balance += amount
        else:
            balance -= amount

        transactions.append({
            "type": t_type,
            "amount": amount,
            "date": date,
            "time": time
        })

    status = "OPEN"

    if balance == 0 and len(data) > 0:
        status = "CLOSED"

    return render_template(
        'statement.html',
        name=name,
        transactions=transactions,
        balance=balance,
        status=status
    )


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)