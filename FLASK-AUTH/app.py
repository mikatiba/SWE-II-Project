from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL

app = Flask(__name__)  
app.secret_key = '1234'  

# ✅ MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '701512'  
app.config['MYSQL_DB'] = 'flask_users'

mysql = MySQL(app)

#  Landing Page
@app.route('/')
def index():
    return render_template('index.html')

#  Página principal después de login
@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    else:
        return redirect(url_for('login'))  # Si no hay sesión, redirige al login

#  Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']

        cur = mysql.connection.cursor()

        #  Uso de placeholders para evitar inyección SQL
        cur.execute("SELECT username, password FROM tbl_users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and pwd == user[1]:
            session['username'] = user[0]
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

#  Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']

        cur = mysql.connection.cursor()

        # Uso de placeholders para evitar inyección SQL
        cur.execute("INSERT INTO tbl_users (username, password) VALUES (%s, %s)", (username, pwd))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login'))
    return render_template('register.html')

#  Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))  #  Redirige al landing page tras logout

if __name__ == '__main__':
    app.run(debug=True)
