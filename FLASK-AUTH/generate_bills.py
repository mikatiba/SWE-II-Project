import random
from datetime import datetime, timedelta
import MySQLdb
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conexión a MySQL usando variables del .env
conn = MySQLdb.connect(
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_USER'),
    passwd=os.getenv('MYSQL_PASSWORD'),
    db=os.getenv('MYSQL_DB'),
    port=int(os.getenv('MYSQL_PORT', 3306))
)

cursor = conn.cursor()

# Usuarios y servicios disponibles
user_ids = [2, 3]               # ID de usuarios reales
service_ids = [1, 2]            # ID de servicios (LUMA, AAA)
statements = ['Pagada', 'Pendiente', 'Vencida']

# Generar 10 facturas aleatorias por usuario
for user_id in user_ids:
    for _ in range(10):
        service_id = random.choice(service_ids)
        amount = round(random.uniform(25.00, 150.00), 2)
        issued = datetime.now() - timedelta(days=random.randint(1, 60))
        due = issued + timedelta(days=30)
        status = random.choice(statements)

        cursor.execute("""
            INSERT INTO Bill (id_user, id_service, total_amount, issued_date, expiring_date, statement)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, service_id, amount, issued.date(), due.date(), status))

conn.commit()
cursor.close()
conn.close()
print("Facturas aleatorias insertadas correctamente.")