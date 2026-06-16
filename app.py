# ==============================================================
# app.py — Servidor principal de GameVault (Tienda de Videojuegos)
# Materia  : Fundamentos de Programación
# Framework: Flask (microframework web de Python)
# Base de datos: SQLite (archivo local, sin instalación extra)
# ==============================================================

# --- IMPORTACIONES ---
from flask import (
    Flask,           # La clase principal que crea la aplicación web
    render_template, # Renderiza archivos HTML de la carpeta 'templates/'
    request,         # Permite leer datos del formulario o del cuerpo HTTP
    redirect,        # Redirige al usuario a otra URL
    url_for,         # Genera URLs a partir del nombre de la función de ruta
    session,         # Almacena datos del usuario entre peticiones (cookie cifrada)
    flash,           # Envía mensajes de una sola vez a la plantilla HTML
    jsonify          # Convierte un diccionario Python a respuesta JSON (para AJAX)
)
import sqlite3       # Módulo estándar de Python para manejar bases de datos SQLite
import os            # Módulo para operaciones del sistema operativo (rutas, etc.)

# ==============================================================
# SECCIÓN 1: CONFIGURACIÓN DE LA APLICACIÓN
# ==============================================================

# Creamos la instancia principal de Flask.
# __name__ le indica a Flask dónde buscar los archivos de la aplicación.
app = Flask(__name__)

# La clave secreta cifra las sesiones de usuario (cookies).
# En un proyecto real esto vendría de una variable de entorno, no del código.
app.secret_key = 'clave_super_secreta_gamevault_2024'

# Nombre del archivo de base de datos SQLite que se creará automáticamente.
DATABASE = 'gamevault.db'

# ==============================================================
# SECCIÓN 2: FUNCIONES DE BASE DE DATOS
# ==============================================================

def get_db():
    """
    Abre y retorna una conexión a la base de datos SQLite.

    row_factory = sqlite3.Row permite acceder a las columnas de la tabla
    usando el nombre de la columna en lugar de un índice numérico.
    Ejemplo: fila['email']  en vez de  fila[2]
    """
    conn = sqlite3.connect(DATABASE)        # Abre (o crea) el archivo .db
    conn.row_factory = sqlite3.Row          # Activa el acceso por nombre de columna
    return conn                             # Retorna la conexión activa

def init_db():
    """
    Crea las tablas 'usuarios', 'productos' y 'servicios' si no existen.
    Inyecta datos de prueba estáticos de manera automática si las tablas están vacías.
    """
    conn = get_db()
    
    # 1. Tabla de Usuarios
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre   TEXT    NOT NULL,
            email    TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL
        )
    ''')
    
    # 2. Tabla de Productos (Videojuegos)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo      TEXT NOT NULL,
            genero      TEXT NOT NULL,
            precio      REAL NOT NULL,
            imagen      TEXT NOT NULL,
            color_card  TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            plataforma  TEXT NOT NULL,
            rating      REAL NOT NULL
        )
    ''')
    
    # 3. Tabla de Servicios
    conn.execute('''
        CREATE TABLE IF NOT EXISTS servicios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            precio      REAL NOT NULL,
            color_card  TEXT NOT NULL
        )
    ''')
    
    # --- Inyección de Videojuegos Iniciales ---
    cursor = conn.execute('SELECT COUNT(*) FROM productos')
    if cursor.fetchone()[0] == 0:
        juegos_iniciales = [
            ('Cyberpunk 2077', 'RPG / Acción', 39.99, 'cyberpunk.jpg', '#ff2d55', 'Sumérgete en Night City, un mundo abierto donde la tecnología y el crimen se mezclan.', 'PC / PS5 / Xbox', 4.1),
            ('Hollow Knight', 'Metroidvania', 14.99, 'hollow_knight.jpg', '#00d4ff', 'Explora un vasto reino subterráneo de insectos, misterios y peligros antiguos.', 'PC / Switch / PS4', 4.8),
            ('Among Us', 'Deducción Social', 9.99, 'among_us.jpg', '#c840e9', 'Trabaja con tu tripulación… o traiciona a todos como impostor.', 'PC / Mobile', 4.2),
            ('Stardew Valley', 'Simulación / RPG', 14.99, 'stardew.jpg', '#39ff14', 'Hereda una granja y construye una vida en el encantador valle de Pelican Town.', 'PC / Switch / Mobile', 4.9),
            ('Red Dead Redemption 2', 'Aventura / Acción', 49.99, 'rdr2.jpg', '#ff7b00', 'Una épica historia sobre honor y supervivencia en el ocaso del Salvaje Oeste.', 'PC / PS4 / Xbox', 4.9),
            ('Hades', 'Roguelike / Acción', 24.99, 'hades.jpg', '#ff4500', 'Escapa del Inframundo con la ayuda de los dioses del Olimpo en este roguelike épico.', 'PC / Switch / PS4', 4.8),
            ('Terraria', 'Sandbox / Aventura', 9.99, 'terraria.jpg', '#00ff88', 'Explora, construye y sobrevive en un mundo 2D lleno de tesoros y criaturas.', 'PC / Mobile / Consola', 4.7),
            ('Disco Elysium', 'RPG / Narrativo', 29.99, 'disco_elysium.jpg', '#ffd700', 'Un detective en crisis existencial investiga un crimen en una ciudad decadente.', 'PC / PS4 / Xbox', 4.7)
        ]
        conn.executemany('''
            INSERT INTO productos (titulo, genero, precio, imagen, color_card, descripcion, plataforma, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', juegos_iniciales)

    # --- Inyección de Servicios Iniciales ---
    cursor = conn.execute('SELECT COUNT(*) FROM servicios')
    if cursor.fetchone()[0] == 0:
        servicios_iniciales = [
            ('Mantenimiento Premium', 'Limpieza profunda de componentes, cambio de pasta térmica y calibración de software.', 45.00, '#00d4ff'),
            ('Pase de Temporada Vault', 'Acceso prioritario a torneos de la comunidad, preventas exclusivas y eventos especiales.', 19.99, '#e040fb'),
            ('Soporte Técnico Técnico', 'Asistencia remota avanzada para optimización de hardware y problemas con launchers.', 25.00, '#39ff14')
        ]
        conn.executemany('''
            INSERT INTO servicios (nombre, descripcion, precio, color_card)
            VALUES (?, ?, ?, ?)
        ''', servicios_iniciales)

    conn.commit()
    conn.close()


# ==============================================================
# SECCIÓN 4: RUTAS DE LA APLICACIÓN (Controladores)
# ==============================================================
# En Flask, una "ruta" es la URL que el navegador visita.
# El decorador @app.route('/url') conecta una URL con una función Python.

# ---------------------------------------------------------------
# RUTA: Página Principal (catálogo de juegos)
# ---------------------------------------------------------------
@app.route('/')
def index():
    carrito = session.get('carrito', [])
    total_items = sum(item['cantidad'] for item in carrito)
    
    # Consultar productos dinámicamente desde SQLite
    conn = get_db()
    productos_db = conn.execute('SELECT * FROM productos').fetchall()
    servicios_db = conn.execute('SELECT * FROM servicios').fetchall()
    conn.close()
    
    # Conversión a diccionario para mantener compatibilidad exacta con las claves en index.html
    juegos = [dict(row) for row in productos_db]
    servicios = [dict(row) for row in servicios_db]
    total_pagar = sum(item['precio'] * item['cantidad'] for item in carrito)

    return render_template(
        'index.html',
        juegos      = juegos, 
        servicios   = servicios,   
        carrito     = carrito,         
        total_items = total_items,
        total_pagar = total_pagar
    )


# ---------------------------------------------------------------
# RUTA: Registro de usuario
# ---------------------------------------------------------------
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """
    Maneja el formulario de registro.

    GET  → Muestra la página con el formulario vacío.
    POST → Procesa los datos del formulario e intenta crear el usuario.

    methods=['GET', 'POST'] indica que esta ruta acepta ambos verbos HTTP.
    """
    if request.method == 'POST':
        # request.form.get() lee el campo con ese 'name' del formulario HTML
        # .strip() elimina espacios en blanco al inicio y al final del texto
        nombre   = request.form.get('nombre',   '').strip()
        email    = request.form.get('email',    '').strip()
        password = request.form.get('password', '').strip()

        # --- Validación básica del lado del servidor ---
        # Aunque el HTML también valida, es buena práctica validar en el servidor.
        if not nombre or not email or not password:
            # flash() envía un mensaje que se muestra UNA SOLA VEZ en el HTML
            flash('⚠️ Por favor completa todos los campos.', 'danger')
            return redirect(url_for('registro'))    # Regresa al formulario

        if len(password) < 6:
            flash('⚠️ La contraseña debe tener al menos 6 caracteres.', 'danger')
            return redirect(url_for('registro'))

        # --- Insertar el nuevo usuario en la base de datos ---
        try:
            conn = get_db()
            conn.execute(
                # Los signos '?' son parámetros enlazados (evitan inyección SQL)
                'INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)',
                (nombre, email, password)
            )
            conn.commit()   # Confirma la inserción
            conn.close()    # Cierra la conexión

            flash('✅ ¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))       # Redirige al login

        except sqlite3.IntegrityError:
            # Este error ocurre si el email ya existe (columna UNIQUE en la BD)
            flash('⚠️ Ese correo ya está registrado. Usa otro o inicia sesión.', 'warning')
            return redirect(url_for('registro'))

    # Si el método es GET, simplemente muestra el formulario de registro
    return render_template('registro.html')


# ---------------------------------------------------------------
# RUTA: Login de usuario
# ---------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja el inicio de sesión.

    GET  → Muestra el formulario de login.
    POST → Verifica las credenciales y crea la sesión si son correctas.
    """
    if request.method == 'POST':
        email    = request.form.get('email',    '').strip()
        password = request.form.get('password', '').strip()

        # Consultar la BD buscando un usuario con ese email Y contraseña
        conn    = get_db()
        usuario = conn.execute(
            'SELECT * FROM usuarios WHERE email = ? AND password = ?',
            (email, password)
        ).fetchone()    # fetchone() retorna la primera fila encontrada (o None)
        conn.close()

        if usuario:
            # --- INICIO DE SESIÓN EXITOSO ---
            # Guardamos datos del usuario en la sesión (cookie cifrada)
            session['usuario_id']     = usuario['id']       # ID único del usuario
            session['usuario_nombre'] = usuario['nombre']   # Nombre para mostrar
            session['usuario_email']  = usuario['email']    # Email para mostrar 

            flash(f'✅ ¡Bienvenido de vuelta, {usuario["nombre"]}!', 'success')
            return redirect(url_for('index'))   # Redirige a la página principal

        else:
            # Credenciales incorrectas: no revelar cuál campo está mal (seguridad)
            flash('❌ Email o contraseña incorrectos. Intenta de nuevo.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


# ---------------------------------------------------------------
# RUTA: Logout (cerrar sesión)
# ---------------------------------------------------------------
@app.route('/logout')
def logout():
    """
    Elimina los datos del usuario de la sesión (cierra sesión).
    session.pop() elimina una clave de la sesión si existe.
    El segundo argumento (None) es el valor por defecto si la clave no existe.
    """
    session.pop('usuario_id',     None)
    session.pop('usuario_nombre', None)
    # Nota: el carrito se mantiene para que el usuario no pierda sus ítems

    flash('👋 Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('index'))


# ==============================================================
# SECCIÓN 5: RUTAS DEL CARRITO DE COMPRAS (API JSON)
# ==============================================================
# Estas rutas son llamadas por JavaScript (fetch/AJAX), no por el navegador
# directamente. Retornan JSON en lugar de HTML.

# ---------------------------------------------------------------
# RUTA: Agregar un juego al carrito (Corregida para SQLite)
# ---------------------------------------------------------------
@app.route('/carrito/agregar', methods=['POST'])
def agregar_al_carrito():
    """
    Recibe el ID de un videojuego en formato JSON y lo agrega al carrito
    buscando la información directamente en la base de datos SQLite.
    """
    # request.get_json() deserializa el cuerpo de la petición HTTP de JSON a dict
    datos    = request.get_json()
    juego_id = datos.get('id')      # Extrae el ID del juego del JSON recibido

    # --- CORRECCIÓN: Consulta relacional a SQLite en lugar de la lista en memoria ---
    conn = get_db()
    # Ejecutamos un SELECT con un filtro WHERE para traer solo el juego que coincida con el ID
    fila_juego = conn.execute('SELECT * FROM productos WHERE id = ?', (juego_id,)).fetchone()
    conn.close()

    # Si la base de datos no devuelve ninguna fila, el juego no existe
    if not fila_juego:
        return jsonify({'error': 'Videojuego no encontrado en el catálogo'}), 404

    # Convertimos la fila (sqlite3.Row) a un diccionario estándar de Python
    # Esto mantiene una compatibilidad exacta con el resto de tu lógica del carrito
    juego = dict(fila_juego)

    # Obtener el carrito actual de la sesión (o lista vacía si no existe)
    carrito = session.get('carrito', [])

    # --- Verificar si el juego ya existe en el carrito ---
    for item in carrito:
        if item['id'] == juego_id:
            item['cantidad'] += 1               # Incrementar la cantidad en 1
            session['carrito']  = carrito       # Guardar el carrito actualizado
            session.modified    = True          # Avisar a Flask que la sesión cambió
            total_items         = sum(i['cantidad'] for i in carrito)
            return jsonify({
                'mensaje':     'Cantidad actualizada',
                'carrito':     carrito,
                'total_items': total_items
            })

    # --- El juego NO estaba → agregarlo como nuevo ítem ---
    nuevo_item = {
        'id':       juego['id'],
        'titulo':   juego['titulo'],
        'precio':   juego['precio'],
        'cantidad': 1               # Empieza con cantidad 1
    }
    carrito.append(nuevo_item)      # Agregar al final de la lista

    session['carrito'] = carrito    # Guardar la lista actualizada en sesión
    session.modified   = True       # Marcar sesión como modificada

    total_items = sum(i['cantidad'] for i in carrito)

    return jsonify({
        'mensaje':     '¡Juego agregado al carrito!',
        'carrito':     carrito,
        'total_items': total_items
    })

# ---------------------------------------------------------------
# RUTA: Eliminar un juego del carrito
# ---------------------------------------------------------------
@app.route('/carrito/eliminar', methods=['POST'])
def eliminar_del_carrito():
    """
    Recibe el ID de un juego y lo elimina completamente del carrito.
    Usa comprensión de lista para filtrar y excluir el ítem con ese ID.
    """
    datos    = request.get_json()
    juego_id = datos.get('id')

    carrito = session.get('carrito', [])

    # Comprensión de lista: construye una nueva lista SIN el ítem eliminado.
    # Es equivalente a un filtro: solo quedan los items cuyo id ≠ juego_id
    carrito = [item for item in carrito if item['id'] != juego_id]

    session['carrito'] = carrito
    session.modified   = True

    total_items = sum(i['cantidad'] for i in carrito)

    return jsonify({
        'mensaje':     'Juego eliminado del carrito',
        'carrito':     carrito,
        'total_items': total_items
    })


# ---------------------------------------------------------------
# RUTA: Actualizar cantidad de un ítem del carrito
# ---------------------------------------------------------------
@app.route('/carrito/actualizar', methods=['POST'])
def actualizar_cantidad():
    """
    Actualiza la cantidad de un ítem específico del carrito.
    Si la cantidad nueva es 0 o menor, elimina el ítem.
    """
    datos     = request.get_json()
    juego_id  = datos.get('id')
    nueva_qty = datos.get('cantidad', 1)    # Cantidad nueva recibida del frontend

    carrito = session.get('carrito', [])

    for item in carrito:
        if item['id'] == juego_id:
            if nueva_qty <= 0:
                # Si la cantidad es 0, eliminar el ítem del carrito
                carrito = [i for i in carrito if i['id'] != juego_id]
            else:
                item['cantidad'] = nueva_qty    # Actualizar la cantidad
            break   # Salir del bucle al encontrar el ítem

    session['carrito'] = carrito
    session.modified   = True

    total_items = sum(i['cantidad'] for i in carrito)

    return jsonify({
        'mensaje':     'Carrito actualizado',
        'carrito':     carrito,
        'total_items': total_items
    })


# ---------------------------------------------------------------
# RUTA: Simular pago
# ---------------------------------------------------------------
@app.route('/carrito/pagar', methods=['POST'])
def pagar():
    """
    Simula el proceso de pago.

    Validaciones:
    1. El usuario debe estar logueado.
    2. El carrito no puede estar vacío.

    En una aplicación real aquí iría la integración con una pasarela
    de pagos como PayPal, Stripe o MercadoPago.
    """
    # Verificar que el usuario haya iniciado sesión
    if 'usuario_id' not in session:
        return jsonify({'error': 'Debes iniciar sesión para realizar el pago.'}), 401

    carrito = session.get('carrito', [])

    if not carrito:
        return jsonify({'error': 'El carrito está vacío. Agrega juegos primero.'}), 400

    # Calcular el total: precio × cantidad para cada ítem, luego sumar todo
    total = sum(item['precio'] * item['cantidad'] for item in carrito)

    # Contar el número total de juegos comprados
    cantidad_total = sum(item['cantidad'] for item in carrito)

    # Vaciar el carrito después del "pago exitoso"
    session['carrito'] = []     # Lista vacía → carrito vacío
    session.modified   = True

    # Retornar confirmación con el total calculado
    return jsonify({
        'mensaje':  f'¡Compra realizada con éxito! Adquiriste {cantidad_total} juego(s).',
        'total':    round(total, 2),    # round() para evitar errores de punto flotante
        'usuario':  session.get('usuario_nombre', 'Jugador')
    })

# ---------------------------------------------------------------
# RUTA: Procesar Solicitud de Servicio Técnico
# ---------------------------------------------------------------
@app.route('/servicio/solicitar', methods=['POST'])
def solicitar_servicio():
    """
    Recibe los datos del formulario modal de servicios.
    Verifica que el usuario haya iniciado sesión antes de permitir la solicitud.
    """
    # 1. Seguridad: Verificar si el usuario está logueado
    if 'usuario_id' not in session:
        flash('⚠️ Debes iniciar sesión o registrarte para solicitar un servicio técnico.', 'warning')
        return redirect(url_for('index'))

    # 2. Capturar los datos del formulario
    servicio_nombre = request.form.get('servicio_nombre')
    detalles = request.form.get('detalles')
    usuario_actual = session.get('usuario_nombre')

    # Aquí en un futuro se guardaría en la base de datos o se enviaría un email.
    # Por ahora, simulamos el éxito de la operación.
    
    mensaje_exito = f'✅ ¡Solicitud recibida, {usuario_actual}! Nuestro equipo evaluará tu caso de "{servicio_nombre}" y te contactaremos pronto.'
    flash(mensaje_exito, 'success')
    
    return redirect(url_for('index'))

# ==============================================================
# SECCIÓN 6: CONTROLADORES DEL PANEL ADMINISTRATIVO (CRUD)
# ==============================================================

def comprobar_permisos_admin():
    """Retorna True si el usuario en sesión es el administrador autorizado."""
    return session.get('usuario_email') == 'admin@gamevault.com'

@app.route('/admin')
def admin_panel():
    """Renderiza el panel de control central si el usuario es administrador."""
    if not comprobar_permisos_admin():
        flash('❌ Acceso denegado. Se requieren credenciales de administrador.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db()
    productos = conn.execute('SELECT * FROM productos').fetchall()
    servicios = conn.execute('SELECT * FROM servicios').fetchall()
    usuarios  = conn.execute('SELECT id, nombre, email FROM usuarios WHERE email != "admin@gamevault.com"').fetchall()
    conn.close()

    # --- NUEVO: Cálculos matemáticos para el Dashboard (KPIs) ---
    # Contamos la longitud de las listas para obtener los totales
    kpis = {
        'total_usuarios': len(usuarios),
        'total_productos': len(productos),
        'total_servicios': len(servicios),
        # Sumamos el precio de todos los juegos para saber cuánto vale el inventario
        'valor_inventario': sum(p['precio'] for p in productos) if productos else 0
    }

    # NUEVO GRÁFICO: Extraemos los títulos, los ratings y los colores de cada juego
    nombres_juegos = [p['titulo'] for p in productos]
    ratings_juegos = [p['rating'] for p in productos]
    colores_juegos = [p['color_card'] for p in productos]
    
    return render_template('admin.html', 
                        productos=productos, 
                        servicios=servicios, 
                        usuarios=usuarios,
                        kpis=kpis,
                        nombres_juegos=nombres_juegos,   # 👈 Enviamos los nombres
                        ratings_juegos=ratings_juegos,   # 👈 Enviamos las puntuaciones
                        colores_juegos=colores_juegos)   # 👈 Enviamos los colores neón

# --- OPERACIONES CRUD: VIDEOJUEGOS ---

@app.route('/admin/producto/nuevo', methods=['POST'])
def producto_nuevo():
    if not comprobar_permisos_admin(): return redirect(url_for('index'))
    
    titulo = request.form.get('titulo')
    genero = request.form.get('genero')
    precio = float(request.form.get('precio', 0.0))
    imagen = request.form.get('imagen', 'default.jpg')
    color_card = request.form.get('color_card', '#00d4ff')
    descripcion = request.form.get('descripcion')
    plataforma = request.form.get('plataforma')
    rating = float(request.form.get('rating', 5.0))
    
    conn = get_db()
    conn.execute('''
        INSERT INTO productos (titulo, genero, precio, imagen, color_card, descripcion, plataforma, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (titulo, genero, precio, imagen, color_card, descripcion, plataforma, rating))
    conn.commit()
    conn.close()
    flash('✅ Videojuego incorporado exitosamente al catálogo.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/producto/editar/<int:id>', methods=['POST'])
def producto_editar(id):
    if not comprobar_permisos_admin(): return redirect(url_for('index'))
    
    titulo = request.form.get('titulo')
    genero = request.form.get('genero')
    precio = float(request.form.get('precio', 0.0))
    imagen = request.form.get('imagen')
    color_card = request.form.get('color_card')
    descripcion = request.form.get('descripcion')
    plataforma = request.form.get('plataforma')
    rating = float(request.form.get('rating', 5.0))
    
    conn = get_db()
    conn.execute('''
        UPDATE productos 
        SET titulo=?, genero=?, precio=?, imagen=?, color_card=?, descripcion=?, plataforma=?, rating=?
        WHERE id=?
    ''', (titulo, genero, precio, imagen, color_card, descripcion, plataforma, rating, id))
    conn.commit()
    conn.close()
    flash('✅ Datos del videojuego actualizados correctamente.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/producto/eliminar/<int:id>', methods=['POST'])
def producto_eliminar(id):
    if not comprobar_permisos_admin(): return redirect(url_for('index'))
    conn = get_db()
    conn.execute('DELETE FROM productos WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('🗑️ Videojuego removido del sistema de forma permanente.', 'info')
    return redirect(url_for('admin_panel'))

# --- OPERACIONES CRUD: SERVICIOS ---

@app.route('/admin/servicio/nuevo', methods=['POST'])
def servicio_nuevo():
    if not comprobar_permisos_admin(): return redirect(url_for('index'))
    
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = float(request.form.get('precio', 0.0))
    color_card = request.form.get('color_card', '#e040fb')
    
    conn = get_db()
    conn.execute('''
        INSERT INTO servicios (nombre, descripcion, precio, color_card)
        VALUES (?, ?, ?, ?)
    ''', (nombre, descripcion, precio, color_card))
    conn.commit()
    conn.close()
    flash('✅ Nuevo servicio operacional registrado.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/servicio/editar/<int:id>', methods=['POST'])
def servicio_editar(id):
    if not comprobar_permisos_admin(): return redirect(url_for('index'))
    
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    precio = float(request.form.get('precio', 0.0))
    color_card = request.form.get('color_card')
    
    conn = get_db()
    conn.execute('''
        UPDATE servicios SET nombre=?, descripcion=?, precio=?, color_card=? WHERE id=?
    ''', (nombre, descripcion, precio, color_card, id))
    conn.commit()
    conn.close()
    flash('✅ Parámetros del servicio modificados.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/servicio/eliminar/<int:id>', methods=['POST'])
def servicio_eliminar(id):
    if not comprobar_permisos_admin(): return redirect(url_for('index'))
    conn = get_db()
    conn.execute('DELETE FROM servicios WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('🗑️ Servicio eliminado de la oferta comercial.', 'info')
    return redirect(url_for('admin_panel'))

# --- OPERACIONES CRUD: CLIENTES ---

@app.route('/admin/usuario/eliminar/<int:id>', methods=['POST'])
def usuario_eliminar(id):
    if not comprobar_permisos_admin(): return redirect(url_for('index'))
    conn = get_db()
    conn.execute('DELETE FROM usuarios WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('🗑️ Registro del cliente revocado del sistema central.', 'info')
    return redirect(url_for('admin_panel'))

# ==============================================================
# PUNTO DE ENTRADA DEL PROGRAMA
# ==============================================================
# Este bloque solo se ejecuta cuando corres: python app.py
# No se ejecuta si el archivo es importado por otro módulo.

if __name__ == '__main__':
    init_db()               # Crear la tabla en SQLite si no existe
    print("🎮 GameVault arrancando en http://127.0.0.1:5000")
    app.run(debug=True)     # debug=True → recarga automática al guardar cambios
