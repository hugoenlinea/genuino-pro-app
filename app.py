# app.py (VERSIÓN FINAL PARA RENDER)
import os 
import psycopg2 
import psycopg2.extras 
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from whitenoise import WhiteNoise # ¡NUEVO!

# Importaciones para el PDF
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.utils import ImageReader

# --- CONFIGURACIÓN Y APP FLASK ---
app = Flask(__name__)
# ¡NUEVO! Configurar WhiteNoise para servir archivos estáticos (CSS, logos, etc.)
# Busca una carpeta llamada 'static' y la sirve.
app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(os.path.dirname(__file__), 'static'))

# Lee la clave secreta desde las variables de entorno de Render
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'una-clave-secreta-de-respaldo-muy-dificil')

# --- CONFIGURACIÓN DE FLASK-LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicie sesión para acceder.'

# --- CLASE DE USUARIO Y LOADER ---
class User(UserMixin):
    def __init__(self, id, email, fullname, role):
        self.id = id
        self.email = email
        self.fullname = fullname
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) 
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_row = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_row:
        return User(id=user_row['id'], email=user_row['email'], fullname=user_row['fullname'], role=user_row['role'])
    return None

# --- CONEXIÓN A BD (POSTGRESQL) ---
def get_db_connection():
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except psycopg2.Error as err:
        print(f"Error al conectar a PostgreSQL: {err}")
        return None

# --- RUTAS DE AUTENTICACIÓN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_row = cursor.fetchone()
        cursor.close()
        conn.close()
        if user_row and check_password_hash(user_row['password_hash'], password):
            user = User(id=user_row['id'], email=user_row['email'], fullname=user_row['fullname'], role=user_row['role'])
            login_user(user)
            return redirect(url_for('my_quotes_page'))
        else:
            flash('Email o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- RUTAS DEL FRONTEND ---
@app.route('/')
@login_required
def index(): 
    return redirect(url_for('my_quotes_page'))
@app.route('/create-quote')
@login_required 
def create_quote_page():
    return render_template('crear_cotizacion.html')
@app.route('/my-quotes')
@login_required
def my_quotes_page():
    return render_template('my_quotes.html')
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'Jefe de Ventas':
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('index'))
    return render_template('dashboard.html')
@app.route('/admin/users')
@login_required
def manage_users_page():
    if current_user.role != 'Jefe de Ventas':
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('index'))
    return render_template('manage_users.html')
@app.route('/admin/catalog')
@login_required
def manage_catalog_page():
    if current_user.role != 'Jefe de Ventas':
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('index'))
    return render_template('manage_catalog.html')
@app.route('/reports')
@login_required
def reports_page():
    if current_user.role != 'Jefe de Ventas':
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('index'))
    return render_template('reports.html')
@app.route('/client/login')
def client_login_page(): return render_template('client_login.html')
@app.route('/client/portal')
def client_portal_page(): return render_template('client_portal.html')

# Helper para convertir tuplas a diccionarios
def fetchall_dict(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
def fetchone_dict(cursor):
    if cursor.rowcount == 0:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, cursor.fetchone()))

# --- APIs (MODIFICADAS PARA CURSORES DE PSYCOPG2) ---
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, fullname, email, role, is_active FROM users WHERE id != %s ORDER BY fullname", (current_user.id,))
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)
#
# BUSCA Y REEMPLAZA ESTA FUNCIÓN: create_user
#

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    fullname, email, password, role = data.get('fullname'), data.get('email'), data.get('password'), data.get('role')
    if not all([fullname, email, password, role]): return jsonify({'error': 'Todos los campos son requeridos'}), 400
    hashed_password = generate_password_hash(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- ¡CORRECCIÓN! ---
        # PostgreSQL es estricto. 'is_active' debe ser un booleano (True), no un entero (1).
        cursor.execute("INSERT INTO users (fullname, email, password_hash, role, is_active) VALUES (%s, %s, %s, %s, %s)", 
                       (fullname, email, hashed_password, role, True)) # <-- CAMBIADO DE 1 a True
        conn.commit()
    except psycopg2.Error as err:
        conn.rollback(); return jsonify({'error': 'El email ya está registrado'}), 409
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Usuario creado exitosamente'}), 201
@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, fullname, email, role, is_active FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user: return jsonify(user)
    else: return jsonify({'error': 'Usuario no encontrado'}), 404
#
# BUSCA Y REEMPLAZA ESTA FUNCIÓN COMPLETA:
#

#
# BUSCA Y REEMPLAZA ESTA FUNCIÓN: update_user
#

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if current_user.role != 'Jefe de Ventas': 
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    fullname, email, role = data.get('fullname'), data.get('email'), data.get('role')
    
    # --- ¡CORRECCIÓN! ---
    # Asegurarnos de que 'is_active' sea un booleano de Python (True/False)
    # El JSON puede enviar 1, 0, true, false, etc. bool() lo manejará.
    is_active = bool(data.get('is_active')) 
    
    new_password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Comprobar si el email ya está en uso por OTRO usuario
        cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            return jsonify({'error': 'El email ya está en uso por otro usuario'}), 409
        
        # 2. Lógica de actualización
        if new_password:
            hashed_password = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET fullname = %s, email = %s, role = %s, is_active = %s, password_hash = %s WHERE id = %s", 
                           (fullname, email, role, is_active, hashed_password, user_id)) # 'is_active' es ahora un booleano
        else:
            cursor.execute("UPDATE users SET fullname = %s, email = %s, role = %s, is_active = %s WHERE id = %s", 
                           (fullname, email, role, is_active, user_id)) # 'is_active' es ahora un booleano
        
        conn.commit()
        
    except psycopg2.Error as err:
        conn.rollback()
        # Devuelve el error específico de la BD, que es lo que vio el usuario
        return jsonify({'error': f'Error de base de datos: {str(err)}'}), 500
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()
        
    return jsonify({'message': 'Usuario actualizado correctamente'})

#
# BUSCA Y REEMPLAZA ESTA FUNCIÓN: get_my_quotes
#

@app.route('/api/my-quotes', methods=['GET'])
@login_required
def get_my_quotes():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # --- ¡CORRECCIÓN! ---
        # Forzar la conversión a int() para asegurar la coincidencia de tipos
        user_id_int = int(current_user.id)
        
        query = """
        SELECT q.id, q.quote_number, q.created_at, q.total_amount, q.status, 
               c.company_name, q.rejection_reason 
        FROM quotes q 
        JOIN customers c ON q.customer_id = c.id 
        WHERE q.user_id = %s 
        ORDER BY q.created_at DESC
        """
        cursor.execute(query, (user_id_int,))
        quotes = cursor.fetchall()
    except Exception as e:
        print(f"Error en get_my_quotes: {e}") # Esto aparecerá en los logs de Render
        quotes = [] # Devuelve una lista vacía en caso de error
    finally:
        cursor.close()
        conn.close()
        
    return jsonify(quotes)
@app.route('/api/all-quotes', methods=['GET'])
@login_required
def get_all_quotes():
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT q.id, q.quote_number, q.created_at, q.total_amount, q.status, c.company_name, q.rejection_reason, u.fullname as vendedor_name, u.id as user_id FROM quotes q JOIN customers c ON q.customer_id = c.id JOIN users u ON q.user_id = u.id ORDER BY q.created_at DESC")
    quotes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(quotes)
@app.route('/api/customers', methods=['GET'])
@login_required
def get_customers():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, company_name, nit_ci FROM customers ORDER BY company_name")
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(customers)
@app.route('/api/customers', methods=['POST'])
@login_required
def create_customer():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO customers (company_name, nit_ci, address, contact_person, contact_email, contact_phone) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id', (data['company_name'], data['nit_ci'], data.get('address'), data.get('contact_person'), data.get('contact_email'), data.get('contact_phone')))
        new_customer_id = cursor.fetchone()[0]
        conn.commit()
    except psycopg2.Error as err:
        conn.rollback(); return jsonify({'error': 'El NIT/CI ya está registrado.'}), 409
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Cliente creado', 'customer': {'id': new_customer_id, 'company_name': data['company_name'], 'nit_ci': data['nit_ci']}}), 201
@app.route('/api/quotes', methods=['POST'])
@login_required
def create_quote():
    data = request.get_json()
    user_id = current_user.id 
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT setting_value FROM app_settings WHERE setting_key = 'approval_threshold'")
    threshold_row = cursor.fetchone()
    approval_threshold = float(threshold_row['setting_value']) if threshold_row else 10000.00
    total_amount = sum(item['quantity'] * item['unit_price'] for item in data['items'])
    status = 'Pendiente de Aprobacion' if total_amount > approval_threshold else 'Aprobada'
    try:
        cursor.execute("SELECT MAX(id) as max_id FROM quotes")
        last_id_result = cursor.fetchone()
        next_id = (last_id_result['max_id'] if last_id_result['max_id'] else 0) + 1
        quote_number = f'COT-2025-{next_id:04d}'
        
        cursor.execute('INSERT INTO quotes (customer_id, user_id, total_amount, status, quote_number) VALUES (%s, %s, %s, %s, %s) RETURNING id', (data['customer_id'], user_id, total_amount, status, quote_number))
        quote_id = cursor.fetchone()['id']
        
        items_to_insert = []
        for item in data['items']:
            items_to_insert.append((
                quote_id, item['type_id'], item.get('code'), item['description'], 
                item['quantity'], item['unit_price'], item['quantity'] * item['unit_price']
            ))
        
        cursor.executemany(
            'INSERT INTO quote_items (quote_id, type_id, code, description, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s, %s, %s)', 
            items_to_insert
        )
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback(); return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': f'Cotización creada con estado: {status}', 'quote_id': quote_id}), 201
@app.route('/api/quotes/pending', methods=['GET'])
@login_required
def get_pending_quotes():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT q.*, c.company_name, u.fullname as vendedor_name FROM quotes q JOIN customers c ON q.customer_id = c.id JOIN users u ON q.user_id = u.id WHERE q.status = 'Pendiente de Aprobacion' ORDER BY q.created_at DESC")
    quotes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(quotes)
def update_quote_status(quote_id, new_status, reason=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if reason:
        cursor.execute("UPDATE quotes SET status = %s, rejection_reason = %s WHERE id = %s", (new_status, reason, quote_id))
    else:
        cursor.execute("UPDATE quotes SET status = %s WHERE id = %s", (new_status, quote_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': f'Cotización {quote_id} actualizada a {new_status}'})
@app.route('/api/quotes/<int:quote_id>/approve', methods=['POST'])
@login_required
def approve_quote(quote_id):
    return update_quote_status(quote_id, 'Aprobada')
@app.route('/api/quotes/<int:quote_id>/reject', methods=['POST'])
@login_required
def reject_quote(quote_id):
    data = request.get_json()
    reason = data.get('reason', 'Sin motivo específico.')
    return update_quote_status(quote_id, 'Rechazada', reason)
@app.route('/api/client/login', methods=['POST'])
def client_login():
    data = request.get_json()
    nit_ci = data.get('nit_ci')
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, company_name FROM customers WHERE nit_ci = %s", (nit_ci,))
    client = cursor.fetchone()
    cursor.close()
    conn.close()
    if client: return jsonify(client)
    else: return jsonify({'error': 'Credenciales incorrectas'}), 401


@app.route('/api/client/<int:client_id>/quotes')
def get_client_quotes(client_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        # --- ¡CORRECCIÓN! ---
        # Forzar la conversión a int() para asegurar la coincidencia de tipos
        customer_id_int = int(client_id)
        
        cursor.execute(
            "SELECT id, quote_number, created_at, total_amount, status FROM quotes WHERE customer_id = %s AND status = 'Aprobada' ORDER BY created_at DESC", 
            (customer_id_int,)
        )
        quotes = cursor.fetchall()
    except Exception as e:
        print(f"Error en get_client_quotes: {e}") # Para los logs de Render
        quotes = []
    finally:
        cursor.close()
        conn.close()
    return jsonify(quotes)

#
# BUSCA Y REEMPLAZA ESTA FUNCIÓN: get_client_orders
#

@app.route('/api/client/<int:client_id>/orders')
def get_client_orders(client_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        # --- ¡CORRECCIÓN! ---
        # Forzar la conversión a int() para asegurar la coincidencia de tipos
        customer_id_int = int(client_id)
        
        cursor.execute(
            "SELECT o.id, q.quote_number, q.created_at, o.order_status FROM orders o JOIN quotes q ON o.quote_id = q.id WHERE q.customer_id = %s ORDER BY q.created_at DESC", 
            (customer_id_int,)
        )
        orders = cursor.fetchall()
    except Exception as e:
        print(f"Error en get_client_orders: {e}") # Para los logs de Render
        orders = []
    finally:
        cursor.close()
        conn.close()
    return jsonify(orders)

@app.route('/api/quotes/approved', methods=['GET'])
@login_required
def get_approved_quotes():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT q.*, c.company_name, u.fullname as vendedor_name FROM quotes q JOIN customers c ON q.customer_id = c.id JOIN users u ON q.user_id = u.id WHERE q.status = 'Aprobada' AND q.id NOT IN (SELECT quote_id FROM orders) ORDER BY q.created_at DESC")
    quotes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(quotes)
@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    data = request.get_json()
    quote_id = data.get('quote_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO orders (quote_id, order_status) VALUES (%s, %s)", (quote_id, 'Pedido Confirmado'))
        conn.commit()
    except psycopg2.Error:
        conn.rollback(); return jsonify({'error': 'Este pedido ya fue creado'}), 409
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Pedido creado e iniciado.'}), 201
@app.route('/api/orders/active', methods=['GET'])
@login_required
def get_active_orders():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT o.id, o.order_status, q.quote_number, c.company_name, q.id as quote_id, u.fullname as vendedor_name FROM orders o JOIN quotes q ON o.quote_id = q.id JOIN customers c ON q.customer_id = c.id JOIN users u ON q.user_id = u.id WHERE o.order_status != 'Listo para Entrega' ORDER BY o.last_update DESC")
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(orders)
@app.route('/api/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET order_status = %s, last_update = CURRENT_TIMESTAMP WHERE id = %s", (new_status, order_id))
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Estado del pedido actualizado.'})
def clean_text(text):
    if text is None: return ''
    return str(text)
def _generate_pdf_for_quote(quote_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT q.*, c.company_name, c.nit_ci, c.contact_person, c.contact_email FROM quotes q JOIN customers c ON q.customer_id = c.id WHERE q.id = %s", (quote_id,))
    quote = cursor.fetchone()
    if not quote: 
        cursor.close()
        conn.close()
        return "Cotización no encontrada", 404
    cursor.execute("SELECT * FROM catalog_types ORDER BY id")
    types = cursor.fetchall()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                            rightMargin=0.5*inch, leftMargin=0.5*inch, 
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, fontName='Helvetica'))
    styles.add(ParagraphStyle(name='RightBold', alignment=TA_RIGHT, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='GroupHeader', fontName='Helvetica-Bold', fontSize=12, spaceBefore=12, spaceAfter=6))
    styles['Normal'].fontName = 'Helvetica'
    styles['Heading1'].fontName = 'Helvetica-Bold'
    elements = []
    basedir = os.path.abspath(os.path.dirname(__file__))
    # WhiteNoise sirve desde 'static', así que la ruta base es el directorio de la app
    logo_path = os.path.join(basedir, 'static', 'logo.png')
    if os.path.exists(logo_path):
        try:
            img = ImageReader(logo_path)
            img_width, img_height = img.getSize()
            max_logo_width = 1.5 * inch 
            aspect_ratio = img_height / float(img_width)
            new_logo_width = min(img_width, max_logo_width)
            new_logo_height = new_logo_width * aspect_ratio
            logo = Image(logo_path, width=new_logo_width, height=new_logo_height)
            logo.hAlign = 'LEFT'
            elements.append(logo)
        except Exception as e:
            elements.append(Paragraph("Genuino PRO+ (Error Logo)", styles['Heading1']))
    else:
        elements.append(Paragraph("Genuino PRO+", styles['Heading1']))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph('COTIZACION', styles['Heading1']))
    elements.append(Paragraph(clean_text(quote['quote_number']), styles['Normal']))
    elements.append(Spacer(1, 0.25 * inch))
    data_info = [
        [Paragraph('<b>Empresa:</b>', styles['Normal']), Paragraph('<b>Cliente:</b>', styles['Normal'])],
        ['Genuino Importaciones', Paragraph(clean_text(quote['company_name']), styles['Normal'])],
        ['NIT: 123456789', f"NIT/CI: {clean_text(quote['nit_ci'])}"],
        ['Cochabamba, Bolivia', f"Atn: {clean_text(quote['contact_person'])}"],
    ]
    info_table = Table(data_info, colWidths=[3.5 * inch, 3.5 * inch])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.25 * inch))
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEEEEE')),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'), 
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'), 
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'), 
    ])
    col_widths = [0.8 * inch, 0.5 * inch, 4.2 * inch, 1 * inch, 1 * inch]
    subtotals = {} 
    for c_type in types:
        cursor.execute("SELECT * FROM quote_items WHERE quote_id = %s AND type_id = %s ORDER BY id", (quote_id, c_type['id']))
        items = cursor.fetchall()
        if items:
            elements.append(Paragraph(clean_text(c_type['name']), styles['GroupHeader']))
            data_items = [['Código', 'Cant.', 'Descripción', 'P. Unit.', 'Subtotal']]
            type_subtotal = 0.0
            for item in items:
                subtotal = item['subtotal']
                type_subtotal += subtotal
                data_items.append([
                    clean_text(item['code']),
                    item['quantity'],
                    Paragraph(clean_text(item['description']), styles['Normal']),
                    f"{item['unit_price']:,.2f}", 
                    f"{item['subtotal']:,.2f}"
                ])
            subtotals[c_type['name']] = type_subtotal
            data_items.append([
                '', '', '', 
                Paragraph(f"<b>Subtotal {c_type['name']}</b>", styles['RightBold']), 
                Paragraph(f"<b>{type_subtotal:,.2f}</b>", styles['RightBold'])
            ])
            items_table = Table(data_items, colWidths=col_widths)
            items_table.setStyle(table_style)
            items_table.setStyle(TableStyle([
                ('SPAN', (0, -1), (2, -1)),
                ('ALIGN', (3, -1), (4, -1), 'RIGHT'),
            ]))
            elements.append(items_table)
            elements.append(Spacer(1, 0.1 * inch))
    cursor.close()
    conn.close() 
    elements.append(Spacer(1, 0.25 * inch))
    summary_data = []
    for type_name, amount in subtotals.items():
        summary_data.append([
            Paragraph(f"Total {type_name}", styles['Right']),
            Paragraph(f"{amount:,.2f}", styles['Right'])
        ])
    summary_data.append([
        Paragraph(f"<b>TOTAL GENERAL Bs.</b>", styles['RightBold']), 
        Paragraph(f"<b>{quote['total_amount']:,.2f}</b>", styles['RightBold'])
    ])
    summary_table = Table(summary_data, colWidths=[6.5 * inch, 1 * inch])
    summary_table.setStyle(TableStyle([
        ('BOX', (0, -1), (-1, -1), 1, colors.black), 
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EEEEEE')),
    ]))
    elements.append(summary_table)
    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers.set('Content-Type', 'application/pdf')
    # ¡CORRECCIÓN DE ERROR TIPOGRÁFICO!
    response.headers.set('Content-Disposition', 'inline', filename=f"{clean_text(quote['quote_number'])}.pdf")
    return response
@app.route('/api/quote/<int:quote_id>/pdf')
@login_required
def generate_quote_pdf(quote_id):
    return _generate_pdf_for_quote(quote_id)
@app.route('/api/client/<int:client_id>/quote/<int:quote_id>/pdf')
def generate_client_quote_pdf_secure(client_id, quote_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM quotes WHERE id = %s AND customer_id = %s AND status = 'Aprobada'", (quote_id, client_id))
    quote = cursor.fetchone()
    cursor.close()
    conn.close()
    if quote:
        return _generate_pdf_for_quote(quote_id)
    else:
        return "Acceso denegado: La cotización no se encuentra o no está aprobada.", 403
@app.route('/api/settings/approval_threshold', methods=['GET'])
@login_required
def get_approval_threshold():
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT setting_value FROM app_settings WHERE setting_key = 'approval_threshold'")
    threshold_row = cursor.fetchone()
    cursor.close()
    conn.close()
    current_threshold = float(threshold_row['setting_value']) if threshold_row else 10000.00
    return jsonify({'threshold': current_threshold})
@app.route('/api/settings/approval_threshold', methods=['POST'])
@login_required
def update_approval_threshold():
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    new_threshold = data.get('threshold')
    if new_threshold is None: return jsonify({'error': 'Falta el valor del límite'}), 400
    try: new_threshold_float = float(new_threshold)
    except ValueError: return jsonify({'error': 'El valor debe ser numérico'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO app_settings (setting_key, setting_value) VALUES (%s, %s) 
        ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value
        """
        cursor.execute(query, ('approval_threshold', str(new_threshold_float)))
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Límite de aprobación actualizado correctamente'})
@app.route('/api/reports/sales-by-month')
@login_required
def report_sales_by_month():
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT to_char(created_at, 'YYYY-MM') as month, SUM(total_amount) as total_sales FROM quotes WHERE status = 'Aprobada' GROUP BY month ORDER BY month ASC")
    sales_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'labels': [row['month'] for row in sales_data], 'data': [row['total_sales'] for row in sales_data]})
@app.route('/api/reports/sales-by-month-by-vendor')
@login_required
def report_sales_by_month_by_vendor():
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = """
        SELECT 
            to_char(q.created_at, 'YYYY-MM') as month, 
            u.fullname as vendor_name, 
            SUM(q.total_amount) as total_sales 
        FROM quotes q 
        JOIN users u ON q.user_id = u.id 
        WHERE q.status = 'Aprobada' 
        GROUP BY month, vendor_name 
        ORDER BY month, vendor_name
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    months = sorted(list(set([row['month'] for row in rows])))
    vendors = sorted(list(set([row['vendor_name'] for row in rows])))
    sales_map = {vendor: {month: 0 for month in months} for vendor in vendors}
    for row in rows:
        sales_map[row['vendor_name']][row['month']] = row['total_sales']
    datasets = []
    for vendor in vendors:
        dataset_data = [sales_map[vendor][month] for month in months]
        datasets.append({
            "label": vendor,
            "data": dataset_data
        })
    return jsonify({"labels": months, "datasets": datasets})
@app.route('/api/reports/quotes-by-vendor')
@login_required
def report_quotes_by_vendor():
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT u.fullname as vendor_name, COUNT(q.id) as quote_count FROM quotes q JOIN users u ON q.user_id = u.id GROUP BY u.fullname ORDER BY quote_count DESC")
    vendor_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'labels': [row['vendor_name'] for row in vendor_data], 'data': [row['quote_count'] for row in vendor_data]})

@app.route('/api/reports/rejections-by-vendor')
@login_required
def report_rejections_by_vendor():
    # --- ¡CORRECCIÓN! ---
    # El rol es 'Jefe de Ventas', no 'JVentas'.
    if current_user.role != 'Jefe de Ventas': 
        return jsonify({'error': 'No autorizado'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT u.fullname as vendor_name, COUNT(q.id) as rejection_count 
            FROM quotes q 
            JOIN users u ON q.user_id = u.id 
            WHERE q.status = 'Rechazada' 
            GROUP BY u.fullname 
            ORDER BY rejection_count DESC
        """)
        rejection_data = cursor.fetchall()
    except Exception as e:
        print(f"Error en report_rejections_by_vendor: {e}")
        rejection_data = []
    finally:
        cursor.close()
        conn.close()
        
    return jsonify({
        'labels': [row['vendor_name'] for row in rejection_data], 
        'data': [row['rejection_count'] for row in rejection_data]
    })
@app.route('/api/catalog-types', methods=['GET'])
@login_required
def get_catalog_types():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM catalog_types ORDER BY name")
    types = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(types)
@app.route('/api/catalog-types', methods=['POST'])
@login_required
def create_catalog_type():
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    name = data.get('name')
    if not name: return jsonify({'error': 'El nombre es requerido'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO catalog_types (name) VALUES (%s)", (name,))
        conn.commit()
    except psycopg2.Error:
        conn.rollback(); return jsonify({'error': 'Ese tipo ya existe'}), 409
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Tipo creado'}), 201
@app.route('/api/catalog-types/<int:type_id>', methods=['PUT'])
@login_required
def update_catalog_type(type_id):
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    name = data.get('name')
    if not name: return jsonify({'error': 'El nombre es requerido'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE catalog_types SET name = %s WHERE id = %s", (name, type_id))
        conn.commit()
    except psycopg2.Error:
        conn.rollback(); return jsonify({'error': 'Ese tipo ya existe'}), 409
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Tipo actualizado'})
@app.route('/api/catalog-types/<int:type_id>', methods=['DELETE'])
@login_required
def delete_catalog_type(type_id):
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM catalog WHERE type_id = %s", (type_id,))
        items = cursor.fetchone()
        if items:
            return jsonify({'error': 'No se puede eliminar. Hay ítems de catálogo usando este tipo.'}), 409
        cursor.execute("DELETE FROM catalog_types WHERE id = %s", (type_id,))
        conn.commit()
    except psycopg2.Error:
         conn.rollback(); return jsonify({'error': 'No se puede eliminar. Hay cotizaciones usando este tipo.'}), 409
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Tipo eliminado'})
@app.route('/api/catalog', methods=['GET'])
@login_required
def get_catalog_items():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT c.*, ct.name as type_name FROM catalog c JOIN catalog_types ct ON c.type_id = ct.id ORDER BY ct.name, c.description")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(items)
@app.route('/api/catalog', methods=['POST'])
@login_required
def create_catalog_item():
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    type_id, code, description, unit_price = data.get('type_id'), data.get('code'), data.get('description'), data.get('unit_price')
    if not type_id or not code or not description or unit_price is None:
        return jsonify({'error': 'Tipo, Código, Descripción y Precio son requeridos'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO catalog (type_id, code, description, unit_price) VALUES (%s, %s, %s, %s)", (type_id, code, description, unit_price))
        conn.commit()
    except psycopg2.Error:
        conn.rollback(); return jsonify({'error': 'El código ya existe para este tipo de ítem. Debe ser único.'}), 409
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Ítem de catálogo creado'}), 201
@app.route('/api/catalog/<int:item_id>', methods=['GET'])
@login_required
def get_catalog_item(item_id):
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM catalog WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    cursor.close()
    conn.close()
    if item: return jsonify(item)
    else: return jsonify({'error': 'Ítem no encontrado'}), 404
@app.route('/api/catalog/<int:item_id>', methods=['PUT'])
@login_required
def update_catalog_item(item_id):
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    type_id, code, description, unit_price = data.get('type_id'), data.get('code'), data.get('description'), data.get('unit_price')
    if not type_id or not code or not description or unit_price is None: 
        return jsonify({'error': 'Tipo, Código, Descripción y Precio son requeridos'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE catalog SET type_id = %s, code = %s, description = %s, unit_price = %s WHERE id = %s", (type_id, code, description, unit_price, item_id))
        conn.commit()
    except psycopg2.Error:
        conn.rollback(); return jsonify({'error': 'El código ya existe para este tipo de ítem. Debe ser único.'}), 409
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Ítem actualizado correctamente'})
@app.route('/api/catalog/<int:item_id>', methods=['DELETE'])
@login_required
def delete_catalog_item(item_id):
    if current_user.role != 'Jefe de Ventas': return jsonify({'error': 'No autorizado'}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM catalog WHERE id = %s", (item_id,))
        conn.commit()
    except Exception as e:
        conn.rollback(); return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Ítem eliminado'})

# (El código de inicialización de BD se movió a init_db.py)