import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from dotenv import load_dotenv
from datetime import datetime
from flask_mail import Message, Mail
from itsdangerous import URLSafeTimedSerializer

load_dotenv()

# Configuración de la aplicación
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

# Configuración de MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

mysql = MySQL(app)

# Inicializar el generador de tokens
s = URLSafeTimedSerializer(os.getenv('FLASK_SECRET_KEY'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute("""
            INSERT INTO users (username, name, email, password)
            VALUES (%s, %s, %s, %s)
        """, (username, name, email, password))
        mysql.connection.commit()

        cur.execute("SELECT id_user FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        if user:
            id_user = user[0]
            numero_cuenta = ''.join(random.choices(string.digits, k=10))
            cur.execute("""
                INSERT INTO Account (account_number, id_user)
                VALUES (%s, %s)
            """, (numero_cuenta, id_user))
            mysql.connection.commit()

        cur.close()

        # Iniciar sesión inmediatamente después de registrarse
        session['username'] = username
        session['id_user'] = id_user

        return redirect(url_for('facturas'))

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

@app.route('/recover', methods=['GET', 'POST'])
def recover():
    if request.method == 'POST':
        email = request.form['email']

        # Verificar si el correo existe
        cur = mysql.connection.cursor()
        cur.execute("SELECT id_user FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if user:
            # Crear token de recuperación
            token = s.dumps(email, salt='recover-password')

            # Crear enlace de recuperación
            reset_link = url_for('reset_password', token=token, _external=True)

            # Enviar correo con el enlace
            msg = Message("Password Reset Request", sender="mifacturapr@gmail.com", recipients=[email])
            msg.body = f"Please click the following link to reset your password: {reset_link}"
            mail.send(msg)

            return render_template('recover.html', message="A password reset link has been sent to your email.")

        else:
            return render_template('recover.html', error="Email not found!")

    return render_template('recover.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Verificar el token
        email = s.loads(token, salt='recover-password', max_age=3600)  # El token expira en 1 hora
    except Exception as e:
        return "The link has expired or is invalid."

    if request.method == 'POST':
        new_password = request.form['new_password']

        # Actualizar la contraseña del usuario
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, email))
        mysql.connection.commit()

        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', name=session['username'])
    return redirect(url_for('login'))

@app.route('/cuentas')
def cuentas():
    if 'username' not in session:
        return redirect(url_for('login'))

    id_user = session['id_user']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT account_number
        FROM Account
        WHERE id_user = %s
    """, (id_user,))
    cuentas = [row[0] for row in cur.fetchall()]
    cur.close()

    return render_template('cuentas.html', name=session['username'], cuentas=cuentas)

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

@app.route('/ver_facturas_cuenta', methods=['POST'])
def ver_facturas_cuenta():
    if 'username' not in session:
        return redirect(url_for('login'))

    numero_cuenta = request.form.get('numero_cuenta')
    id_user = session.get('id_user')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT B.id_bill, B.total_amount, B.expiring_date, S.service_name, S.provider
        FROM Bill B
        JOIN Service S ON B.id_service = S.id_service
        WHERE B.id_user = %s AND B.account_number = %s
        ORDER BY B.expiring_date ASC
    """, (id_user, numero_cuenta))

    facturas = cur.fetchall()
    cur.close()

    return render_template('facturas.html', name=session['username'], facturas=facturas)

if __name__ == '__main__':
    app.run(debug=True)