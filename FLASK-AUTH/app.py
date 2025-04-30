import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from dotenv import load_dotenv
from datetime import datetime
from flask_mail import Message, Mail
from itsdangerous import URLSafeTimedSerializer
import json

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
        username = request.form.get('username')
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']  # Asegúrate que este campo esté en tu HTML

        # Validar que las contraseñas coincidan
        if password != confirm_password:
            error = "Las contraseñas no coinciden."
            return render_template('register.html', error=error)

        cur = mysql.connection.cursor()

        # Verificar si el username o el email ya existen
        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            error = "El nombre de usuario o correo electrónico ya está registrado."
            return render_template('register.html', error=error)

        # Insertar nuevo usuario
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

        session['username'] = username
        session['id_user'] = id_user

        return redirect(url_for('home'))

    return render_template('register.html')
      
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        cur = mysql.connection.cursor()
        cur.execute("SELECT id_user FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user:
            session['username'] = username
            session['id_user'] = user[0]
            return redirect(url_for('home'))
        else:
            return render_template('error.html', mensaje="Usuario no encontrado")

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

            # Redirige de vuelta al perfil con mensaje de éxito
            return redirect(url_for('perfil', mensaje='enlace_enviado'))

        else:
            # Enviar error visible en la vista recover tradicional
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

@app.route('/recover_username', methods=['GET', 'POST'])
def recover_username():
    if request.method == 'POST':
        email = request.form['email']

        # Verificar si el correo existe en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if user:
            username = user[0]
            
            # Enviar el nombre de usuario al correo del usuario
            msg = Message("Username Recovery", sender="mifacturapr@gmail.com", recipients=[email])
            msg.body = f"Your username is: {username}"
            mail.send(msg)

            return render_template('recover_username.html', message="Your username has been sent to your email.")

        else:
            return render_template('recover_username.html', error="Email not found!")

    return render_template('recover_username.html')

@app.route('/eliminar_usuario', methods=['POST'])
def eliminar_usuario():
    if 'id_user' not in session:
        return redirect(url_for('login'))

    id_user = session['id_user']

    cur = mysql.connection.cursor()

    # Borrar pagos
    cur.execute("DELETE FROM Payment WHERE id_user = %s", (id_user,))

    # Borrar facturas
    cur.execute("DELETE FROM Bill WHERE id_user = %s", (id_user,))

    # Borrar cuentas
    cur.execute("DELETE FROM Account WHERE id_user = %s", (id_user,))

    # Borrar usuario
    cur.execute("DELETE FROM users WHERE id_user = %s", (id_user,))

    mysql.connection.commit()
    cur.close()

    session.clear()
    return redirect(url_for('index'))  # o mostrar una página de despedida

@app.route('/home')
def home():
    if 'username' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT name FROM users WHERE username = %s", (session['username'],))
        user = cur.fetchone()
        cur.close()

        if user:
            # Elimina espacios extra y extrae solo el primer nombre
            first_name = user[0].strip().split()[0]
            return render_template('home.html', name=first_name)
    return redirect(url_for('login'))

@app.route('/cuentas')
def cuentas():
    if 'username' not in session:
        return redirect(url_for('login'))

    id_user = session['id_user']
    cur = mysql.connection.cursor()

    # Obtener cuentas
    cur.execute("SELECT account_number FROM Account WHERE id_user = %s", (id_user,))
    cuentas = [row[0] for row in cur.fetchall()]

    # Obtener totales por servicio
    cur.execute("""
        SELECT S.service_name, SUM(P.amount)
        FROM Payment P
        JOIN Service S ON P.id_service = S.id_service
        WHERE P.id_user = %s
        GROUP BY S.service_name
    """, (id_user,))
    rows = cur.fetchall()
    cur.close()

    labels = [row[0] for row in rows]
    data = [float(row[1]) for row in rows]

    # Asignar colores según servicio
    color_map = {
        'AAA': 'rgba(54, 162, 235, 0.7)',    # Azul
        'LUMA': 'rgba(75, 192, 75, 0.7)'      # Verde
    }
    colors = [color_map.get(service, 'rgba(153, 102, 255, 0.7)') for service in labels]

    return render_template('cuentas.html', cuentas=cuentas, labels=labels, data=data, colors=colors)

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

from flask import request, redirect, url_for, session, flash
import re

@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    if 'username' not in session:
        return redirect(url_for('login'))

    id_user = session.get('id_user')
    numero_tarjeta = request.form.get('card_number', '').replace(' ', '')
    fecha_expiracion = request.form.get('expiry_date', '')
    monto = request.form.get('amount', '')
    servicio = request.form.get('servicio', 'LUMA')

    # ✅ Validaciones
    if not numero_tarjeta.isdigit() or len(numero_tarjeta) != 16:
        flash("El número de tarjeta debe tener exactamente 16 dígitos.")
        return redirect(url_for('facturas'))

    cvv = request.form.get('cvv', '')
    if not cvv.isdigit() or len(cvv) not in [3, 4]:
        flash("El CVV debe tener 3 o 4 dígitos.")
        return redirect(url_for('facturas'))

    if not fecha_expiracion or not re.match(r'^\d{2}/\d{2}$', fecha_expiracion):
        flash("Fecha de expiración inválida. Use el formato MM/AA.")
        return redirect(url_for('facturas'))

    try:
        monto = float(monto)
    except ValueError:
        flash("Monto inválido.")
        return redirect(url_for('facturas'))

    # ✅ Buscar ID del servicio
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_service FROM Service WHERE service_name = %s", (servicio,))
    service_row = cur.fetchone()
    if not service_row:
        cur.close()
        flash("Servicio no encontrado.")
        return redirect(url_for('facturas'))

    id_service = service_row[0]

    # ✅ Insertar el pago
    cur.execute("""
        INSERT INTO Payment (id_user, id_service, amount, payment_method, expiration_date, payment_number, payment_date)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """, (id_user, id_service, monto, 'Credit Card', fecha_expiracion, numero_tarjeta))

    # ✅ Actualizar la factura como pagada
    cur.execute("""
        UPDATE Bill
        SET statement = 'Pagada'
        WHERE id_user = %s AND id_service = %s AND statement != 'Pagada'
        ORDER BY expiring_date ASC
        LIMIT 1
    """, (id_user, id_service))

    mysql.connection.commit()
    cur.close()

    flash("Pago realizado exitosamente.")
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

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/contactos')
def contactos():
    return render_template('contactos.html')

@app.route('/perfil')
def perfil():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    cur = mysql.connection.cursor()
    cur.execute("SELECT email FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()

    mensaje = request.args.get('mensaje')  # 👈 recibe parámetro opcional

    if user:
        return render_template('perfil.html', email=user[0], mensaje=mensaje)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)