import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

#  Configuración de MySQL (Usando variables de entorno)
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')  # No usar 'root'
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

#  Configuración de correo (Flask-Mail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mysql = MySQL(app)
mail = Mail(app)

#  Landing Page
@app.route('/')
def index():
    return render_template('index.html')

#  Página principal después del login
@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', name=session['name'])  # Enviar `name` en lugar de `username`
    return redirect(url_for('login'))

#  Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT name, username, password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], pwd):
            session['name'] = user[0]  # Guardar `name` en la sesión
            session['username'] = user[1]  # Guardar `username` en la sesión
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

#  Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']  # Captura el nombre del formulario
        username = request.form['username']
        email = request.form['email']
        pwd = request.form['password']
        confirm_pwd = request.form['confirm_password']

        if not name or not username or not email or not pwd or not confirm_pwd:
            return render_template('register.html', error='Todos los campos son obligatorios')

        if pwd != confirm_pwd:
            return render_template('register.html', error="Las contraseñas no coinciden")

        hashed_pwd = generate_password_hash(pwd)

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            return render_template('register.html', error='El nombre de usuario o email ya existen')

        # Guardar el usuario en la base de datos con el campo `name`
        cur.execute("INSERT INTO users (name, username, email, password) VALUES (%s, %s, %s, %s)",
                    (name, username, email, hashed_pwd))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login'))

    return render_template('register.html')

#  Recuperar contraseña
@app.route('/recover', methods=['GET', 'POST'])
def recover():
    if request.method == 'POST':
        email = request.form['email']

        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if user:
            token = str(uuid.uuid4())
            expiry_time = datetime.now(timezone.utc) + timedelta(hours=1)
            reset_link = url_for('reset_password', token=token, _external=True)

            cur.execute("UPDATE users SET reset_token = %s, reset_token_expiry = %s WHERE email = %s", (token, expiry_time, email))
            mysql.connection.commit()
            cur.close()

            msg = Message('Password Reset Request', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f"Hello {user[0]},\n\nClick the link below to reset your password:\n{reset_link}\n\nIf you didn't request this, please ignore this email."

            try:
                mail.send(msg)
            except Exception as e:
                print(f"Error sending email: {e}")
                return render_template('recover.html', error=f'Failed to send email: {e}')

            return render_template('recover.html', message='Check your email for a password reset link.')
        return render_template('recover.html', error='Email not found.')

    return render_template('recover.html')

#  Restablecer contraseña
@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('reset.html', error='Passwords do not match.', token=token)

        cur = mysql.connection.cursor()
        cur.execute("SELECT reset_token_expiry FROM users WHERE reset_token = %s", (token,))
        expiry = cur.fetchone()

        if not expiry or datetime.now(timezone.utc) > expiry[0].replace(tzinfo=timezone.utc):
            return render_template('reset.html', error='Token has expired. Please request a new one.', token=token)

        hashed_pwd = generate_password_hash(new_password)
        cur.execute("UPDATE users SET password = %s, reset_token = NULL, reset_token_expiry = NULL WHERE reset_token = %s", (hashed_pwd, token))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login'))

    return render_template('reset.html', token=token)

#  Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('name', None)  # Asegurar que `name` también se borra de la sesión
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
