from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.secret_key = '1234'

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '701512' #pon tu password local
app.config['MYSQL_DB'] = 'flask_users'

mysql = MySQL(app)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        pwd = request.form.get('password')
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT username, password FROM tbl_users WHERE username = %s", (username,))
            user = cur.fetchone()
            cur.close()
        except Exception as e:
            flash("Error al conectarse a la base de datos", "danger")
            return render_template('login.html', error="Database error")

        if user and check_password_hash(user[1], pwd):  # Comparación segura
            session['username'] = user[0]
            return redirect(url_for('home'))
        
        flash("Invalid username or password", "danger")
        return render_template('login.html')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']

        # Hashear la contraseña antes de guardarla en la base de datos
        hashed_pwd = generate_password_hash(pwd)

        try:
            cur = mysql.connection.cursor()
            # Verificar si el usuario ya existe
            cur.execute("SELECT username FROM tbl_users WHERE username = %s", (username,))
            existing_user = cur.fetchone()

            if existing_user:
                flash("El nombre de usuario ya está en uso. Prueba otro.", "warning")
                return redirect(url_for('register'))

            # Insertar nuevo usuario
            cur.execute("INSERT INTO tbl_users (username, password) VALUES (%s, %s)", (username, hashed_pwd))
            mysql.connection.commit()
            cur.close()
            
            flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for('login'))
        
        except Exception as e:
            flash("Error al registrar usuario", "danger")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Has cerrado sesión.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
