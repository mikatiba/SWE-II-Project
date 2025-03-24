import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de la aplicación
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

# Configuración de la base de datos usando las variables de entorno
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

mysql = MySQL(app)

def cargar_facturas():
    with app.app_context():
        cur = mysql.connection.cursor()

        # Obtener todas las cuentas
        cur.execute("SELECT account_number FROM Account")
        cuentas = cur.fetchall()

        # Definir algunos valores para las facturas
        servicios = [("LUMA", 1), ("AAA", 2)]
        
        for cuenta in cuentas:
            account_number = cuenta[0]

            # Generar una factura para cada cuenta
            for servicio, id_service in servicios:
                total_amount = random.uniform(50, 150)  # Monto aleatorio entre 50 y 150
                issued_date = datetime.now()
                expiring_date = issued_date + timedelta(days=random.randint(30, 60))  # Factura con vencimiento entre 30 y 60 días

                # Insertar la factura en la base de datos
                cur.execute("""
                    INSERT INTO Bill (id_user, id_service, account_number, total_amount, issued_date, expiring_date, statement)
                    VALUES (
                        (SELECT id_user FROM Account WHERE account_number = %s LIMIT 1),
                        %s, %s, %s, %s, %s, 'Pendiente'
                    )
                """, (account_number, id_service, account_number, total_amount, issued_date, expiring_date))

        mysql.connection.commit()
        cur.close()
        print("Facturas cargadas exitosamente.")

# Ejecutar la función de carga de facturas dentro del contexto de la app
if __name__ == '__main__':
    with app.app_context():
        cargar_facturas()