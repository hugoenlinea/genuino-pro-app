# init_db.py (VERSIÓN CON CORRECCIÓN DE CONTRASEÑA)
import os
import psycopg2
from werkzeug.security import generate_password_hash # ¡IMPORTANTE!

DATABASE_URL = os.environ.get('DATABASE_URL')

# --- ¡NUEVA CONTRASEÑA! ---
# Vamos a generar un hash nuevo para la contraseña: 'admin'
try:
    new_password = 'admin'
    password_hash = generate_password_hash(new_password)
    print(f"Nuevo hash para la contraseña '{new_password}' generado exitosamente.")
except Exception as e:
    print(f"Error fatal: No se pudo importar o usar 'generate_password_hash'. ¿Está 'werkzeug' en requirements.txt? Error: {e}")
    exit(1) # Detiene el script si no se puede generar el hash

# --- ¡SQL MODIFICADO! ---
# ON CONFLICT (email) DO UPDATE ...
# Esto es clave: Si el usuario ya existe, ACTUALIZA su contraseña.
users_sql = """
INSERT INTO users (fullname, email, password_hash, role, is_active) 
VALUES 
('Jefe de Ventas', 'jefe@genuino.com', %s, 'Jefe de Ventas', true),
('Vendedor Uno', 'vendedor@genuino.com', %s, 'Vendedor', true)
ON CONFLICT (email) 
DO UPDATE SET password_hash = EXCLUDED.password_hash;
"""

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
        
        print("Ejecutando script SQL para crear tablas (IF NOT EXISTS)...")
        cursor.execute(sql_script)
        
        print(f"Insertando/Actualizando usuarios con la nueva clave: '{new_password}'...")
        cursor.execute(users_sql, (password_hash, password_hash))

        print("Insertando tipos de catálogo iniciales (ON CONFLICT DO NOTHING)...")
        cursor.execute(types_sql)
        
        conn.commit()
        cursor.close()
        print("¡Base de datos inicializada y contraseñas actualizadas exitosamente!")
        
    except psycopg2.Error as e:
        print(f"Error durante la inicialización de la base de datos:")
        print(e)
    except Exception as e:
        print(f"Un error inesperado ocurrió: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()