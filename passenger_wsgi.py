import os
import sys

# Añade el directorio de tu app al 'path' de Python
# Asume que passenger_wsgi.py está en la raíz de tu proyecto
sys.path.insert(0, os.path.dirname(__file__))

# Importa el objeto 'app' desde tu archivo 'app.py'
# El servidor lo buscará con el nombre 'application'
from app import app as application