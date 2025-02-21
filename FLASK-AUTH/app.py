import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')  # Usa variable de entorno

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '701512')
app.config['MYSQL_DB'] = 'flask_users'

mysql = MySQL(app)

# Landing Page
@app.route('/')
def index():
    return render_template('index.html')

# Página principal después de login
@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    else:
        return redirect(url_for('login'))

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT username, password FROM tbl_users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[1], pwd):
            session['username'] = user[0]
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

# Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']
        confirm_pwd = request.form['confirm_password']

        if not username or not pwd or not confirm_pwd:
            return render_template('register.html', error='All fields are required')
        
        if pwd != confirm_pwd:
            return render_template('register.html', error="Passwords do not match")
            
        hashed_pwd = generate_password_hash(pwd)

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tbl_users WHERE username = %s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            return render_template('register.html', error='Username already exists')

        cur.execute("INSERT INTO tbl_users (username, password) VALUES (%s, %s)", (username, hashed_pwd))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

