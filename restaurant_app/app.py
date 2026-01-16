from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_file
import json
import os
from datetime import datetime
import zipfile
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from banco_integration import banco_integration

# Sistema de usuarios y roles
USUARIOS_PREDETERMINADOS = {
    "mesero1": {"password": "mesero123", "rol": "mesero", "nombre": "Carlos Rodríguez"},
    "mesero2": {"password": "mesero123", "rol": "mesero", "nombre": "María López"},
    "mesero3": {"password": "mesero123", "rol": "mesero", "nombre": "Juan Pérez"},
    "mesero4": {"password": "mesero123", "rol": "mesero", "nombre": "Ana García"},
    "mesero5": {"password": "mesero123", "rol": "mesero", "nombre": "Luis Martínez"},
    "mesero6": {"password": "mesero123", "rol": "mesero", "nombre": "Sofía Fernández"},
    "mesero7": {"password": "mesero123", "rol": "mesero", "nombre": "Diego González"},
    "mesero8": {"password": "mesero123", "rol": "mesero", "nombre": "Laura Sánchez"},
    "gerente1": {"password": "gerente123", "rol": "gerente", "nombre": "Roberto Castro"},
    "gerente2": {"password": "gerente123", "rol": "gerente", "nombre": "Elena Mendoza"},
    "admin": {"password": "1234", "rol": "admin", "nombre": "Administrador Principal"}
}

def autenticar_usuario(username, password):
    """Autenticar usuario y devolver sus datos si es válido"""
    if username in USUARIOS_PREDETERMINADOS:
        if USUARIOS_PREDETERMINADOS[username]["password"] == password:
            # Verificar si el usuario está activo
            db = load_db()
            usuarios_activos = db.get("usuarios_activos", {})
            if usuarios_activos.get(username, True):  # Por defecto está activo
                return {
                    "username": username,
                    "rol": USUARIOS_PREDETERMINADOS[username]["rol"],
                    "nombre": USUARIOS_PREDETERMINADOS[username]["nombre"]
                }
    return None

def obtener_usuario(username):
    """Obtener datos de un usuario"""
    return USUARIOS_PREDETERMINADOS.get(username)

def tiene_permiso(rol, permiso):
    """Verificar si un rol tiene un permiso específico"""
    permisos = {
        "mesero": ["subir_comprobante", "ver_reporte_diario"],
        "gerente": ["subir_comprobante", "validar_pago", "ver_reporte_diario", "gestionar_comprobantes"],
        "admin": ["subir_comprobante", "validar_pago", "ver_reporte_diario", "gestionar_comprobantes", 
                  "gestionar_menu", "gestionar_usuarios"]
    }
    return permiso in permisos.get(rol, [])

def obtener_todos_usuarios():
    """Obtener lista de todos los usuarios"""
    return USUARIOS_PREDETERMINADOS

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'restaurante-secret-key-2024')

# Archivo de Base de Datos
IS_VERCEL = os.environ.get('VERCEL') is not None
DB_FILE = os.environ.get('DB_FILE', '/tmp/restaurant_db.json' if IS_VERCEL else 'restaurant_db.json')
ADMIN_PASSWORD = '1234'  # Contraseña del admin
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/comprobantes_yape' if IS_VERCEL else 'comprobantes_yape')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Crear carpeta de comprobantes si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_db():
    if not os.path.exists(DB_FILE):
        # Datos iniciales por defecto
        default_data = {
            "menu": {
                "1": {"name": "Lomo Saltado", "price": 25.00, "category": "Platos Fuertes"},
                "2": {"name": "Ceviche Mixto", "price": 30.00, "category": "Platos Fuertes"},
                "3": {"name": "Inka Cola", "price": 5.00, "category": "Bebidas"},
                "4": {"name": "Chicha Morada", "price": 4.00, "category": "Bebidas"},
            },
            "orders": [],
            "comprobantes_yape": [],
            "usuarios_activos": {},
            "reportes_diarios": {},
            "transacciones_bancarias": {}
        }
        save_db(default_data)
        return default_data
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"menu": {}, "orders": [], "comprobantes_yape": [], "usuarios_activos": {}, "reportes_diarios": {}, "transacciones_bancarias": {}}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    db = load_db()
    return render_template('index.html', menu=db.get('menu', {}))

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        usuario = autenticar_usuario(username, password)
        if usuario:
            session['usuario_id'] = usuario['username']
            session['usuario_rol'] = usuario['rol']
            session['usuario_nombre'] = usuario['nombre']
            session['username'] = usuario['username']
            session['rol'] = usuario['rol']
            
            # Redirigir según el rol
            if usuario['rol'] == 'admin':
                return redirect(url_for('admin'))
            elif usuario['rol'] == 'gerente':
                return redirect(url_for('gerente'))
            elif usuario['rol'] == 'mesero':
                return redirect(url_for('mesero'))
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    session.pop('usuario_rol', None)
    session.pop('usuario_nombre', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('usuario_id') or not tiene_permiso(session.get('usuario_rol'), 'gestionar_menu'):
        return redirect(url_for('login'))
    db = load_db()
    return render_template('admin.html', menu=db.get('menu', {}), usuario=session.get('usuario_nombre'))

@app.route('/api/add_item', methods=['POST'])
def add_item():
    if 'username' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    db = load_db()
    menu = db.get('menu', {})
    
    name = request.form.get('name')
    price = float(request.form.get('price'))
    category = request.form.get('category')
    
    # Generar nuevo ID
    ids = [int(k) for k in menu.keys()]
    new_id = str(max(ids) + 1) if ids else "1"
    
    new_item = {"name": name, "price": price, "category": category}
    
    # Manejar imagen si se subió
    if 'imagen' in request.files:
        file = request.files['imagen']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"menu_{new_id}_{timestamp}_{filename}"
            
            # Crear carpeta de imágenes del menú si no existe
            menu_images_folder = os.path.join('static', 'menu_images')
            if not os.path.exists(menu_images_folder):
                os.makedirs(menu_images_folder)
            
            filepath = os.path.join(menu_images_folder, filename)
            file.save(filepath)
            new_item['imagen'] = filename
    
    menu[new_id] = new_item
    db['menu'] = menu
    save_db(db)
    
    return redirect(url_for('admin'))

@app.route('/api/delete_item/<item_id>', methods=['POST'])
def delete_item(item_id):
    if 'username' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    db = load_db()
    menu = db.get('menu', {})
    
    if item_id in menu:
        del menu[item_id]
        db['menu'] = menu
        save_db(db)
        
    return redirect(url_for('admin'))

@app.route('/api/calculate_bill', methods=['POST'])
def calculate_bill():
    db = load_db()
    menu = db.get('menu', {})
    
    data = request.json
    items = data.get('items', [])
    total = 0
    details = []
    
    for item_id, quantity in items.items():
        if item_id in menu:
            item = menu[item_id]
            cost = item['price'] * quantity
            total += cost
            details.append({
                "name": item['name'],
                "quantity": quantity,
                "unit_price": item['price'],
                "total": cost
            })
            
    return jsonify({"total": total, "details": details})

@app.route('/api/upload_comprobante', methods=['POST'])
def upload_comprobante():
    if 'username' not in session or session.get('rol') not in ['mesero', 'gerente', 'admin']:
        return jsonify({"error": "No autenticado"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No se seleccionó archivo"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó archivo"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"yape_{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Guardar registro en la base de datos
        db = load_db()
        if 'comprobantes_yape' not in db:
            db['comprobantes_yape'] = []
        
        # Para Yape, el comprobante se marca como validado automáticamente
        # sin necesidad de confirmación bancaria
        comprobante_data = {
            'filename': filename,
            'fecha': datetime.now().strftime("%Y-%m-%d"),
            'hora': datetime.now().strftime("%H:%M:%S"),
            'ruta': filepath,
            'mesero': session.get('username'),
            'mesero_nombre': session.get('usuario_nombre'),
            'estado': 'validado',  # Auto-validado para Yape
            'monto': 0,  # Se puede agregar campo de monto en el formulario si se desea
            'validado_por': 'Sistema Automático',
            'fecha_validacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'tipo_pago': 'yape',
            'auto_validado': True  # Indicador de auto-validación
        }
        
        db['comprobantes_yape'].append(comprobante_data)
        
        # Actualizar reporte diario del mesero para Yape auto-validado
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        mesero_username = session.get('username', 'desconocido')
        
        if 'reportes_diarios' not in db:
            db['reportes_diarios'] = {}
        
        if fecha_actual not in db['reportes_diarios']:
            db['reportes_diarios'][fecha_actual] = {}
        
        if mesero_username not in db['reportes_diarios'][fecha_actual]:
            db['reportes_diarios'][fecha_actual][mesero_username] = {
                'total_comprobantes': 0,
                'comprobantes_validados': 0,
                'monto_total': 0,
                'comprobantes': []
            }
        
        # Actualizar estadísticas del mesero para Yape
        db['reportes_diarios'][fecha_actual][mesero_username]['total_comprobantes'] += 1
        db['reportes_diarios'][fecha_actual][mesero_username]['comprobantes_validados'] += 1
        db['reportes_diarios'][fecha_actual][mesero_username]['comprobantes'].append({
            'filename': filename,
            'monto': 0,
            'fecha_validacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'tipo_pago': 'yape',
            'auto_validado': True
        })
        
        save_db(db)
        
        return jsonify({"message": "Comprobante Yape subido y validado exitosamente"}), 200
    
    return jsonify({"error": "Tipo de archivo no permitido"}), 400

@app.route('/api/descargar_comprobantes')
def descargar_comprobantes():
    if 'username' not in session or session.get('rol') not in ['gerente', 'admin']:
        return jsonify({"error": "Sin permisos"}), 403
    
    db = load_db()
    comprobantes = db.get('comprobantes_yape', [])
    
    if not comprobantes:
        return jsonify({"error": "No hay comprobantes para descargar"}), 404
    
    # Crear archivo ZIP con los comprobantes del día
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    zip_filename = f"comprobantes_yape_{fecha_actual}.zip"
    zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for comprobante in comprobantes:
            if os.path.exists(comprobante['ruta']):
                zipf.write(comprobante['ruta'], comprobante['filename'])
    
    return jsonify({
        "message": "Archivo ZIP creado",
        "filename": zip_filename,
        "descargar_url": f"/api/descargar_zip/{zip_filename}"
    })

@app.route('/mesero')
def mesero():
    if not session.get('usuario_id') or session.get('usuario_rol') != 'mesero':
        return redirect(url_for('login'))
    return render_template('mesero.html', usuario=session.get('usuario_nombre'))

@app.route('/gerente')
def gerente():
    if not session.get('usuario_id') or session.get('usuario_rol') != 'gerente':
        return redirect(url_for('login'))
    db = load_db()
    comprobantes = db.get('comprobantes', [])
    return render_template('gerente.html', comprobantes=comprobantes, usuario=session.get('usuario_nombre'))

@app.route('/api/validar_pago', methods=['POST'])
def validar_pago():
    if not session.get('usuario_id') or session.get('usuario_rol') not in ['gerente', 'admin']:
        return jsonify({"error": "No tiene permisos para validar pagos"}), 403
    
    data = request.json
    filename = data.get('filename')
    numero_operacion = data.get('numero_operacion')
    codigo_seguridad = data.get('codigo_seguridad')
    monto = data.get('monto', 0)
    
    if not all([filename, numero_operacion, codigo_seguridad]):
        return jsonify({"error": "Faltan datos requeridos"}), 400
    
    # Integración con sistema bancario - validar números 935548700 y 19305019234032
    valido, mensaje, datos_bancarios = banco_integration.validar_transaccion(
        numero_operacion, 
        codigo_seguridad, 
        float(monto)
        # Sin especificar número destino, acepta ambos válidos por defecto
    )
    
    if valido:
        db = load_db()
        
        # Buscar el comprobante
        for comprobante in db.get('comprobantes_yape', []):
            if comprobante['filename'] == filename:
                # Actualizar estado del comprobante
                comprobante['estado'] = 'validado'
                comprobante['validado_por'] = session.get('usuario_nombre')
                comprobante['fecha_validacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                comprobante['numero_operacion'] = numero_operacion
                comprobante['codigo_seguridad'] = codigo_seguridad
                comprobante['datos_bancarios'] = datos_bancarios
                
                # Registrar en transacciones bancarias
                if 'transacciones_bancarias' not in db:
                    db['transacciones_bancarias'] = []
                
                db['transacciones_bancarias'].append({
                    'numero_operacion': numero_operacion,
                    'monto': monto,
                    'fecha_validacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'validado_por': session.get('usuario_nombre'),
                    'mesero': comprobante.get('mesero_nombre', 'Desconocido'),
                    'banco_origen': datos_bancarios.get('banco_origen', 'No especificado')
                })
                
                # Actualizar reporte diario del mesero
                fecha_actual = datetime.now().strftime("%Y-%m-%d")
                mesero_username = comprobante.get('mesero', 'desconocido')
                
                if 'reportes_diarios' not in db:
                    db['reportes_diarios'] = {}
                
                if fecha_actual not in db['reportes_diarios']:
                    db['reportes_diarios'][fecha_actual] = {}
                
                if mesero_username not in db['reportes_diarios'][fecha_actual]:
                    db['reportes_diarios'][fecha_actual][mesero_username] = {
                        'total_comprobantes': 0,
                        'comprobantes_validados': 0,
                        'monto_total': 0,
                        'comprobantes': []
                    }
                
                # Actualizar estadísticas del mesero
                db['reportes_diarios'][fecha_actual][mesero_username]['comprobantes_validados'] += 1
                db['reportes_diarios'][fecha_actual][mesero_username]['monto_total'] += float(monto)
                db['reportes_diarios'][fecha_actual][mesero_username]['comprobantes'].append({
                    'filename': filename,
                    'monto': monto,
                    'fecha_validacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'numero_operacion': numero_operacion
                })
                
                save_db(db)
                
                return jsonify({
                    "success": True,
                    "message": "Pago validado exitosamente con integración bancaria",
                    "datos_bancarios": datos_bancarios,
                    "monto_validado": monto
                }), 200
        
        return jsonify({"error": "Comprobante no encontrado"}), 404

@app.route('/api/codigos_prueba_banco')
def codigos_prueba_banco():
    """Obtener códigos de prueba del banco para demostración"""
    if 'username' not in session or session.get('rol') not in ['gerente', 'admin']:
        return jsonify({"error": "Sin permisos"}), 403
    
    # Generar códigos de prueba
    codigos = banco_integration.generar_codigos_para_prueba(5)
    
    return jsonify({
        "codigos_prueba": codigos,
        "mensaje": "Estos códigos son solo para pruebas. En producción se conectaría al sistema bancario real."
    }), 200

@app.route('/api/reporte_diario')
def reporte_diario():
    if not session.get('usuario_id') or not tiene_permiso(session.get('usuario_rol'), 'ver_reporte_diario'):
        return jsonify({"error": "No tiene permisos para ver el reporte"}), 403
    
    db = load_db()
    comprobantes = db.get('comprobantes', [])
    
    # Filtrar comprobantes del día actual
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    comprobantes_hoy = [c for c in comprobantes if c.get('fecha', '').startswith(fecha_actual)]
    
    # Calcular totales
    total_comprobantes = len(comprobantes_hoy)
    comprobantes_validados = len([c for c in comprobantes_hoy if c.get('validado', False)])
    
    reporte = {
        "fecha": fecha_actual,
        "total_comprobantes": total_comprobantes,
        "comprobantes_validados": comprobantes_validados,
        "porcentaje_validacion": (comprobantes_validados / total_comprobantes * 100) if total_comprobantes > 0 else 0,
        "detalles": comprobantes_hoy
    }
    
    return jsonify(reporte), 200

@app.route('/api/comprobantes_pendientes')
def comprobantes_pendientes():
    if not session.get('usuario_id') or session.get('usuario_rol') not in ['gerente', 'admin']:
        return jsonify({"error": "No tiene permisos"}), 403
    
    db = load_db()
    comprobantes = db.get('comprobantes', [])
    
    # Filtrar comprobantes del día actual que no estén validados
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    comprobantes_pendientes = [
        c for c in comprobantes 
        if c.get('fecha', '').startswith(fecha_actual) and not c.get('validado', False)
    ]
    
    return jsonify({"comprobantes": comprobantes_pendientes}), 200

@app.route('/api/todos_comprobantes')
def todos_comprobantes():
    if not session.get('usuario_id') or session.get('usuario_rol') not in ['gerente', 'admin']:
        return jsonify({"error": "No tiene permisos"}), 403
    
    db = load_db()
    comprobantes = db.get('comprobantes', [])
    
    # Filtrar comprobantes del día actual
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    comprobantes_hoy = [c for c in comprobantes if c.get('fecha', '').startswith(fecha_actual)]
    
    return jsonify({"comprobantes": comprobantes_hoy}), 200

@app.route('/api/mis_comprobantes')
def mis_comprobantes():
    if not session.get('usuario_id') or session.get('usuario_rol') != 'mesero':
        return jsonify({"error": "No tiene permisos"}), 403
    
    db = load_db()
    comprobantes = db.get('comprobantes', [])
    
    # Filtrar comprobantes del mesero actual del día
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    nombre_mesero = session.get('usuario_nombre')
    
    # Por ahora mostramos todos los del día, después podemos filtrar por mesero
    comprobantes_mesero = [c for c in comprobantes if c.get('fecha', '').startswith(fecha_actual)]
    
    return jsonify({
        "comprobantes": comprobantes_mesero,
        "mesero": nombre_mesero,
        "fecha": fecha_actual
    }), 200

@app.route('/api/reporte_personal')
def reporte_personal():
    if not session.get('usuario_id') or session.get('usuario_rol') != 'mesero':
        return jsonify({"error": "No tiene permisos"}), 403
    
    db = load_db()
    comprobantes = db.get('comprobantes', [])
    
    # Filtrar comprobantes del día actual
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    nombre_mesero = session.get('usuario_nombre')
    
    # Por ahora mostramos todos los del día, después podemos filtrar por mesero
    comprobantes_hoy = [c for c in comprobantes if c.get('fecha', '').startswith(fecha_actual)]
    
    return jsonify({
        "mesero": nombre_mesero,
        "fecha": fecha_actual,
        "total_comprobantes": len(comprobantes_hoy)
    }), 200

@app.route('/api/ver_comprobante/<filename>')
def ver_comprobante(filename):
    if not session.get('usuario_id'):
        return jsonify({"error": "No autorizado"}), 403
    
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    else:
        return jsonify({"error": "Comprobante no encontrado"}), 404

@app.route('/api/descargar_zip/<filename>')
def descargar_zip(filename):
    if not session.get('usuario_id') or session.get('usuario_rol') not in ['gerente', 'admin']:
        return jsonify({"error": "No autorizado"}), 403
    
    zip_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)
    else:
        return jsonify({"error": "Archivo ZIP no encontrado"}), 404

@app.route('/api/usuarios')
def api_usuarios():
    if 'username' not in session or session.get('rol') != 'admin':
        return jsonify({"error": "Sin permisos"}), 403
    
    db = load_db()
    usuarios = []
    
    for username, datos in USUARIOS_PREDETERMINADOS.items():
        usuarios.append({
            "username": username,
            "nombre": datos["nombre"],
            "rol": datos["rol"],
            "activo": db.get("usuarios_activos", {}).get(username, True)
        })
    
    return jsonify(usuarios)

@app.route('/api/toggle_usuario', methods=['POST'])
def api_toggle_usuario():
    if 'username' not in session or session.get('rol') != 'admin':
        return jsonify({"error": "Sin permisos"}), 403
    
    data = request.get_json()
    username = data.get('username')
    
    if username not in USUARIOS_PREDETERMINADOS:
        return jsonify({"error": "Usuario no existe"}), 404
    
    db = load_db()
    if "usuarios_activos" not in db:
        db["usuarios_activos"] = {}
    
    # Toggle estado
    estado_actual = db["usuarios_activos"].get(username, True)
    db["usuarios_activos"][username] = not estado_actual
    save_db(db)
    
    return jsonify({"success": True, "nuevo_estado": not estado_actual})

@app.route('/api/rechazar_comprobante', methods=['POST'])
def api_rechazar_comprobante():
    if 'username' not in session or session.get('rol') not in ['gerente', 'admin']:
        return jsonify({"error": "Sin permisos"}), 403
    
    data = request.get_json()
    filename = data.get('filename')
    
    db = load_db()
    
    # Buscar y actualizar el comprobante
    for comprobante in db.get("comprobantes_yape", []):
        if comprobante["filename"] == filename:
            comprobante["estado"] = "rechazado"
            comprobante["validado_por"] = session.get('username')
            comprobante["fecha_validacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_db(db)
            return jsonify({"success": True})
    
    return jsonify({"error": "Comprobante no encontrado"}), 404

# Ruta para subir imágenes del menú
@app.route('/api/subir_imagen_menu', methods=['POST'])
def subir_imagen_menu():
    if 'username' not in session or session.get('rol') != 'admin':
        return jsonify({"error": "Sin permisos"}), 403
    
    if 'imagen' not in request.files:
        return jsonify({"error": "No se seleccionó imagen"}), 400
    
    file = request.files['imagen']
    item_id = request.form.get('item_id')
    
    if file.filename == '' or not item_id:
        return jsonify({"error": "Datos incompletos"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"menu_{item_id}_{timestamp}_{filename}"
        
        # Crear carpeta de imágenes del menú si no existe
        menu_images_folder = os.path.join('static', 'menu_images')
        if not os.path.exists(menu_images_folder):
            os.makedirs(menu_images_folder)
        
        filepath = os.path.join(menu_images_folder, filename)
        file.save(filepath)
        
        # Actualizar el item del menú con la imagen
        db = load_db()
        menu = db.get('menu', {})
        
        if item_id in menu:
            menu[item_id]['imagen'] = filename
            db['menu'] = menu
            save_db(db)
            return jsonify({"success": True, "message": "Imagen subida exitosamente"})
        else:
            return jsonify({"error": "Item del menú no encontrado"}), 404
    
    return jsonify({"error": "Tipo de archivo no permitido"}), 400

# Ruta para eliminar imágenes del menú
@app.route('/api/eliminar_imagen_menu', methods=['POST'])
def eliminar_imagen_menu():
    if 'username' not in session or session.get('rol') != 'admin':
        return jsonify({"error": "Sin permisos"}), 403
    
    data = request.get_json()
    item_id = data.get('item_id')
    imagen_nombre = data.get('imagen_nombre')
    
    if not item_id or not imagen_nombre:
        return jsonify({"error": "Datos incompletos"}), 400
    
    # Eliminar el archivo físico
    menu_images_folder = os.path.join('static', 'menu_images')
    filepath = os.path.join(menu_images_folder, imagen_nombre)
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error al eliminar archivo: {e}")
    
    # Actualizar el item del menú eliminando la referencia a la imagen
    db = load_db()
    menu = db.get('menu', {})
    
    if item_id in menu and menu[item_id].get('imagen') == imagen_nombre:
        del menu[item_id]['imagen']
        db['menu'] = menu
        save_db(db)
        return jsonify({"success": True, "message": "Imagen eliminada exitosamente"})
    else:
        return jsonify({"error": "Item del menú no encontrado o imagen no coincide"}), 404

@app.route('/api/descargar_todos_comprobantes')
def descargar_todos_comprobantes():
    if 'username' not in session or session.get('rol') not in ['gerente', 'admin']:
        return jsonify({"error": "Sin permisos"}), 403
    
    db = load_db()
    comprobantes = db.get('comprobantes_yape', [])
    
    if not comprobantes:
        return jsonify({"error": "No hay comprobantes para descargar"}), 404
    
    # Crear archivo ZIP con TODOS los comprobantes históricos
    fecha_actual = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    zip_filename = f"todos_comprobantes_yape_{fecha_actual}.zip"
    zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for comprobante in comprobantes:
            if os.path.exists(comprobante['ruta']):
                zipf.write(comprobante['ruta'], comprobante['filename'])
    
    return jsonify({
        "message": "Archivo ZIP creado con todos los comprobantes",
        "filename": zip_filename,
        "descargar_url": f"/api/descargar_zip/{zip_filename}"
    })

@app.route('/api/descargar_mis_comprobantes')
def descargar_mis_comprobantes():
    if 'username' not in session or session.get('rol') != 'mesero':
        return jsonify({"error": "Sin permisos"}), 403
    
    db = load_db()
    comprobantes = db.get('comprobantes_yape', [])
    
    # Filtrar solo los comprobantes del mesero actual
    mis_comprobantes = [comp for comp in comprobantes if comp.get('mesero') == session.get('username')]
    
    if not mis_comprobantes:
        return jsonify({"error": "No tienes comprobantes para descargar"}), 404
    
    # Crear archivo ZIP con los comprobantes del mesero
    fecha_actual = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    zip_filename = f"mis_comprobantes_yape_{session.get('username')}_{fecha_actual}.zip"
    zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for comprobante in mis_comprobantes:
            if os.path.exists(comprobante['ruta']):
                zipf.write(comprobante['ruta'], comprobante['filename'])
    
    return jsonify({
        "message": "Archivo ZIP creado con tus comprobantes",
        "filename": zip_filename,
        "descargar_url": f"/api/descargar_zip/{zip_filename}"
    })


if __name__ == '__main__':
    # Host 0.0.0.0 allows access from other devices in the network
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
