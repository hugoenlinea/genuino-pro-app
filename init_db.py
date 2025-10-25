# init_db.py
import os
import psycopg2
from werkzeug.security import generate_password_hash

# Obtener la URL de la base de datos desde la misma variable de entorno que usará la app
DATABASE_URL = os.environ.get('DATABASE_URL')

# Contraseña para los usuarios iniciales
# HASH para '12345'
password_hash = 'pbkdf2:sha256:600000$hTfJtE4FkZqS3y0M$d6f8f7c9e1e1a8a3e7e2c9e7a4a9b6c0e9d6d7e6c9a3b2c8d5a3e1a8b7e6f9a0'

# Comandos SQL para insertar usuarios
users_sql = """
INSERT INTO users (fullname, email, password_hash, role, is_active) 
VALUES 
('Jefe de Ventas', 'jefe@genuino.com', %s, 'Jefe de Ventas', true),
('Vendedor Uno', 'vendedor@genuino.com', %s, 'Vendedor', true)
ON CONFLICT (email) DO NOTHING;
"""

# Comandos SQL para insertar tipos de catálogo iniciales
types_sql = """
INSERT INTO catalog_types (name) VALUES 
('Productos/Servicios'),
('Gastos de Importación')
ON CONFLICT (name) DO NOTHING;
"""

def initialize_database():
    conn = None
    try:
        print("Conectando a la base de datos...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("Leyendo schema-postgresql.sql...")
        with open('schema-postgresql.sql', 'r') as f:
            sql_script = f.read()
        
        print("Ejecutando script SQL para crear tablas...")
        cursor.execute(sql_script)
        
        print("Insertando usuarios iniciales...")
        cursor.execute(users_sql, (password_hash, password_hash))

        print("Insertando tipos de catálogo iniciales...")
        cursor.execute(types_sql)
        
        conn.commit()
        cursor.close()
        print("¡Base de datos inicializada exitosamente!")
        
    except psycopg2.Error as e:
        print(f"Error durante la inicialización de la base de datos:")
        print(e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()