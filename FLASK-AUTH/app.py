import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

mysql = MySQL(app)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        cur = mysql.connection.cursor()
        cur.execute("SELECT id_user FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user:
            session['username'] = username
            session['id_user'] = user[0]
            return redirect(url_for('facturas'))
        else:
            return "Usuario no encontrado", 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/recover')
def recover():
    return render_template('recover.html')

@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', name=session['username'])
    return redirect(url_for('login'))

@app.route('/cuentas')
def cuentas():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('cuentas.html')

@app.route('/facturas')
def facturas():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    cur = mysql.connection.cursor()

    cur.execute("SELECT id_user, name FROM users WHERE username = %s", (username,))
    user = cur.fetchone()

    if not user:
        return redirect(url_for('login'))

    id_user, name = user

    # ✅ Mostrar solo facturas NO pagadas
    cur.execute("""
        SELECT B.id_bill, B.total_amount, B.expiring_date, S.service_name, S.provider
        FROM Bill B
        JOIN Service S ON B.id_service = S.id_service
        WHERE B.id_user = %s AND B.statement != 'Pagada'
        ORDER BY B.expiring_date ASC
    """, (id_user,))
    facturas = cur.fetchall()
    cur.close()

    return render_template('facturas.html', name=name, facturas=facturas)

@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'username' not in session:
        return redirect(url_for('login'))

    id_user = session.get('id_user')
    numero_tarjeta = request.form['card_number']
    fecha_expiracion = request.form['expiry_date']
    cvv = request.form['cvv']
    monto = float(request.form['amount'])
    servicio = request.form.get('servicio', 'LUMA')

    cur = mysql.connection.cursor()
    cur.execute("SELECT id_service FROM Service WHERE service_name = %s", (servicio,))
    service_row = cur.fetchone()
    if not service_row:
        cur.close()
        return "Servicio no encontrado", 404

    id_service = service_row[0]

    cur.execute("""
        INSERT INTO Payment (id_user, id_service, amount, payment_method, expiration_date, payment_number, payment_date)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """, (id_user, id_service, monto, 'Credit Card', fecha_expiracion, numero_tarjeta))

    cur.execute("""
        UPDATE Bill
        SET statement = 'Pagada'
        WHERE id_user = %s AND id_service = %s AND statement != 'Pagada'
        ORDER BY expiring_date ASC
        LIMIT 1
    """, (id_user, id_service))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('historial'))

@app.route('/historial')
def historial():
    if 'username' not in session:
        return redirect(url_for('login'))

    id_user = session.get('id_user')
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            P.amount AS total_amount,
            P.payment_date AS issued_date,
            S.service_name AS servicio,
            'Pagada' AS statement
        FROM Payment P
        JOIN Service S ON P.id_service = S.id_service
        WHERE P.id_user = %s
        ORDER BY P.payment_date DESC
    """, (id_user,))

    historial = [dict(zip([col[0] for col in cur.description], row)) for row in cur.fetchall()]
    cur.close()

    return render_template('historial.html', historial=historial)

if __name__ == '__main__':
    app.run(debug=True)