from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state TEXT,
        district TEXT,
        village TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        area_id INTEGER
    )
    ''')

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

    conn.commit()
    conn.close()

init_db()

# ---------- HOME ----------
@app.route('/')
def home():
    return render_template('home.html')

# ---------- AREAS ----------
@app.route('/areas')
def areas():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM areas")
    data = c.fetchall()
    conn.close()
    return render_template('area.html', areas=data)

@app.route('/add_area', methods=['POST'])
def add_area():
    state = request.form['state']
    district = request.form['district']
    village = request.form['village']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO areas (state, district, village) VALUES (?, ?, ?)",
              (state, district, village))
    conn.commit()
    conn.close()

    return redirect('/areas')

# ---------- CUSTOMERS ----------
@app.route('/customers/<int:area_id>')
def customers(area_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE area_id=? ORDER BY name ASC", (area_id,))
    data = c.fetchall()
    conn.close()
    return render_template('customers.html', customers=data, area_id=area_id)

@app.route('/add_customer', methods=['POST'])
def add_customer():
    name = request.form['name']
    phone = request.form['phone']
    area_id = request.form['area_id']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO customers (name, phone, area_id) VALUES (?, ?, ?)",
              (name, phone, area_id))
    conn.commit()
    conn.close()

    return redirect(f'/customers/{area_id}')

# ---------- CHAT ----------
@app.route('/chat/<int:customer_id>')
def chat(customer_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM transactions WHERE customer_id=?", (customer_id,))
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

    return render_template('chat.html', data=data, customer_id=customer_id, balance=balance, status=status)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    customer_id = request.form['customer_id']
    amount = float(request.form['amount'])
    t_type = request.form['type']

    now = datetime.now()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
    INSERT INTO transactions (customer_id, type, amount, date, time)
    VALUES (?, ?, ?, ?, ?)
    ''', (customer_id, t_type, amount, now.date(), now.strftime("%H:%M")))

    conn.commit()
    conn.close()

    return redirect(f'/chat/{customer_id}')

# ---------- SEARCH ----------
@app.route('/search')
def search():
    keyword = request.args.get('q', '')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
    SELECT customers.id, customers.name, customers.phone, areas.village
    FROM customers
    JOIN areas ON customers.area_id = areas.id
    WHERE customers.name LIKE ? OR customers.phone LIKE ?
    """, ('%' + keyword + '%', '%' + keyword + '%'))

    results = c.fetchall()
    conn.close()

    return render_template('search.html', results=results)

@app.route('/statement/<int:customer_id>')
def statement(customer_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT name FROM customers WHERE id=?", (customer_id,))
    result = c.fetchone()

    if not result:
        return "Customer not found"

    name = result[0]

    c.execute("SELECT type, amount, date, time FROM transactions WHERE customer_id=? ORDER BY id ASC", (customer_id,))
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

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    today = datetime.now().date()

    c.execute("SELECT SUM(amount) FROM transactions WHERE type='received' AND date=?", (today,))
    total = c.fetchone()[0]

    if total is None:
        total = 0

    conn.close()

    return render_template('dashboard.html', total=total, today=today)

# ---------- RUN ----------
if __name__ == '__main__':
    app.run()