// ================================================================
// static/script.js — Lógica del cliente para GameVault
// 
// Este archivo maneja:
//   1. Agregar / eliminar juegos del carrito (fetch API → Flask)
//   2. Actualizar dinámicamente el DOM con el contenido del carrito
//   3. Simular el proceso de pago
//   4. Animaciones y efectos visuales (partículas del hero)
//
// CONCEPTOS CLAVE USADOS:
//   - fetch(): API moderna para hacer peticiones HTTP sin recargar la página
//   - JSON:    Formato de intercambio de datos entre cliente y servidor
//   - DOM:     Document Object Model (árbol de elementos HTML)
//   - async/await: Sintaxis para manejar operaciones asíncronas (promesas)
// ================================================================

// ---------------------------------------------------------------
// SECCIÓN 1: FUNCIONES DEL CARRITO
// ---------------------------------------------------------------

/**
 * Agrega un videojuego al carrito enviando su ID al servidor Flask.
 *
 * @param {number} juegoId - El ID del juego (viene del botón en index.html)
 *
 * Flujo:
 *   1. Envía el ID al endpoint /carrito/agregar via fetch (POST)
 *   2. Flask actualiza la sesión y responde con el carrito actualizado
 *   3. Actualizamos el DOM con la respuesta
 */
async function agregarAlCarrito(juegoId) {
  try {
    // fetch() realiza la petición HTTP al servidor
    // Es "async" porque no sabemos cuánto tardará la red
    const respuesta = await fetch('/carrito/agregar', {
      method: 'POST',                       // Método HTTP POST (envía datos)
      headers: {
        'Content-Type': 'application/json'  // Le dice al servidor que enviamos JSON
      },
      // body: el cuerpo de la petición con el ID del juego serializado a JSON
      body: JSON.stringify({ id: juegoId })
    });

    // Verificar si la petición fue exitosa (código 200-299)
    if (!respuesta.ok) {
      const error = await respuesta.json();
      mostrarNotificacion(error.error || 'Error al agregar el juego', 'error');
      return;
    }

    // Parsear la respuesta JSON del servidor a un objeto JavaScript
    const datos = await respuesta.json();

    // Actualizar la interfaz con el nuevo estado del carrito
    actualizarCarritoDOM(datos.carrito);
    actualizarBadge(datos.total_items);

    // Mostrar notificación visual de éxito al usuario
    mostrarNotificacion('✅ ' + datos.mensaje, 'success');

    // Efecto visual: "sacudir" el ícono del carrito en el navbar
    animarCarritoIcono();

  } catch (error) {
    // El bloque catch captura errores de red (sin internet, servidor caído, etc.)
    console.error('Error en la petición al servidor:', error);
    mostrarNotificacion('❌ Error de conexión. Verifica tu red.', 'error');
  }
}


/**
 * Elimina un juego completamente del carrito.
 *
 * @param {number} juegoId - ID del juego a eliminar
 */
async function eliminarDelCarrito(juegoId) {
  try {
    const respuesta = await fetch('/carrito/eliminar', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ id: juegoId })
    });

    if (!respuesta.ok) {
      mostrarNotificacion('Error al eliminar el juego', 'error');
      return;
    }

    const datos = await respuesta.json();

    // Eliminar el elemento del DOM con animación de desvanecimiento
    const itemElement = document.getElementById(`item-${juegoId}`);
    if (itemElement) {
      // Aplicar clase de animación de salida
      itemElement.style.animation = 'slideOut 0.3s ease forwards';
      // Esperar a que termine la animación antes de eliminar el elemento
      setTimeout(() => {
        actualizarCarritoDOM(datos.carrito);
        actualizarBadge(datos.total_items);
      }, 280);   // 280ms coincide con la duración de la animación CSS
    }

    mostrarNotificacion('🗑️ Juego eliminado del carrito', 'info');

  } catch (error) {
    console.error('Error al eliminar:', error);
    mostrarNotificacion('❌ Error de conexión', 'error');
  }
}


/**
 * Cambia la cantidad de un ítem del carrito.
 * Si la cantidad es 0, elimina el ítem.
 *
 * @param {number} juegoId  - ID del juego
 * @param {number} cantidad - Nueva cantidad deseada
 */
async function cambiarCantidad(juegoId, cantidad) {
  try {
    const respuesta = await fetch('/carrito/actualizar', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ id: juegoId, cantidad: cantidad })
    });

    if (!respuesta.ok) return;

    const datos = await respuesta.json();
    actualizarCarritoDOM(datos.carrito);
    actualizarBadge(datos.total_items);

  } catch (error) {
    console.error('Error al actualizar cantidad:', error);
  }
}


/**
 * Simula el proceso de pago enviando los datos al servidor.
 * El servidor vacía el carrito y responde con el total.
 */
async function simularPago() {
  try {
    const respuesta = await fetch('/carrito/pagar', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({})   // Cuerpo vacío (el servidor usa la sesión)
    });

    const datos = await respuesta.json();

    if (!respuesta.ok) {
      // Error del servidor (401: no logueado, 400: carrito vacío)
      mostrarNotificacion('⚠️ ' + datos.error, 'error');
      return;
    }

    // --- PAGO EXITOSO ---

    // 1. Actualizar el carrito en el DOM (vacío)
    actualizarCarritoDOM([]);
    actualizarBadge(0);

    // 2. Cerrar el offcanvas del carrito usando la API de Bootstrap
    const offcanvasElement = document.getElementById('carritoOffcanvas');
    const offcanvasInstance = bootstrap.Offcanvas.getInstance(offcanvasElement);
    if (offcanvasInstance) {
      offcanvasInstance.hide();   // Cerrar el panel lateral
    }

    // 3. Llenar y mostrar el modal de pago exitoso
    document.getElementById('modal-mensaje').textContent = datos.mensaje;
    document.getElementById('modal-total').textContent   = `S/ ${datos.total.toFixed(2)}`;

    // Crear instancia del modal de Bootstrap y mostrarlo
    const modalElement  = document.getElementById('modalPagoExitoso');
    const modalInstance = new bootstrap.Modal(modalElement);
    modalInstance.show();

  } catch (error) {
    console.error('Error en el pago:', error);
    mostrarNotificacion('❌ Error al procesar el pago. Intenta nuevamente.', 'error');
  }
}


// ---------------------------------------------------------------
// SECCIÓN 2: FUNCIONES DE ACTUALIZACIÓN DEL DOM
// ---------------------------------------------------------------

/**
 * Reconstruye el contenido visual del carrito a partir de un array de ítems.
 *
 * @param {Array} carrito - Lista de objetos {id, titulo, precio, cantidad}
 *
 * Esta función "repinta" completamente el área de ítems del carrito
 * cada vez que el estado cambia, para asegurar consistencia.
 */
function actualizarCarritoDOM(carrito) {
  // Obtener el contenedor principal de los ítems del carrito
  const contenedor = document.getElementById('carrito-items');
  if (!contenedor) return;   // Salir si el elemento no existe en esta página

  if (carrito.length === 0) {
    // --- CARRITO VACÍO ---
    // innerHTML reemplaza TODO el contenido del elemento con HTML nuevo
    contenedor.innerHTML = `
      <div class="carrito-vacio" id="carrito-vacio">
        <i class="bi bi-cart-x display-4 mb-3"></i>
        <p>Tu carrito está vacío</p>
        <small>¡Agrega algunos juegos!</small>
      </div>
    `;
    // Actualizar el total a cero
    actualizarTotalCarrito([]);
    return;
  }

  // --- CARRITO CON ÍTEMS ---
  // Construir el HTML de todos los ítems usando map() y join()
  // map() transforma cada ítem en un string HTML
  // join('') une todos los strings en uno solo (sin separador)
  const itemsHTML = carrito.map(item => {
    const subtotal = (item.precio * item.cantidad).toFixed(2);  // toFixed(2): 2 decimales

    // Template literal (backticks): permite HTML multilínea con variables ${...}
    return `
      <div class="carrito-item" id="item-${item.id}">
        <div class="carrito-item-info">
          <p class="carrito-item-titulo">${item.titulo}</p>
          <p class="carrito-item-precio">S/ ${item.precio.toFixed(2)} c/u</p>
        </div>
        <div class="carrito-item-controls">
          <!-- Botón disminuir: llama cambiarCantidad con cantidad - 1 -->
          <button class="btn-qty" onclick="cambiarCantidad(${item.id}, ${item.cantidad - 1})">
            <i class="bi bi-dash"></i>
          </button>
          <span id="qty-${item.id}" class="qty-display">${item.cantidad}</span>
          <!-- Botón aumentar: llama cambiarCantidad con cantidad + 1 -->
          <button class="btn-qty" onclick="cambiarCantidad(${item.id}, ${item.cantidad + 1})">
            <i class="bi bi-plus"></i>
          </button>
          <button class="btn-remove" onclick="eliminarDelCarrito(${item.id})">
            <i class="bi bi-trash3"></i>
          </button>
        </div>
        <p class="carrito-item-subtotal">S/ ${subtotal}</p>
      </div>
    `;
  }).join('');

  // Insertar todos los ítems en el contenedor
  contenedor.innerHTML = itemsHTML;

  // Actualizar el total mostrado en el pie del carrito
  actualizarTotalCarrito(carrito);
}


/**
 * Calcula y muestra el total del carrito en el DOM.
 *
 * @param {Array} carrito - Lista de ítems con precio y cantidad
 */
function actualizarTotalCarrito(carrito) {
  const elementoTotal = document.getElementById('carrito-total');
  if (!elementoTotal) return;

  // reduce() acumula la suma de todos los subtotales
  // Valor inicial del acumulador (acc) = 0
  const total = carrito.reduce((acc, item) => acc + (item.precio * item.cantidad), 0);

  // toFixed(2): formatea el número con exactamente 2 decimales
  elementoTotal.textContent = `S/ ${total.toFixed(2)}`;
}


/**
 * Actualiza el badge (contador) del ícono del carrito en el navbar.
 *
 * @param {number} cantidad - Número total de ítems en el carrito
 */
function actualizarBadge(cantidad) {
  const badge = document.getElementById('cart-badge');
  if (!badge) return;

  if (cantidad > 0) {
    badge.textContent = cantidad;          // Mostrar el número
    badge.classList.remove('d-none');      // Quitar clase que lo oculta (Bootstrap)
  } else {
    badge.classList.add('d-none');         // Ocultar cuando no hay ítems
  }
}


// ---------------------------------------------------------------
// SECCIÓN 3: NOTIFICACIONES Y EFECTOS VISUALES
// ---------------------------------------------------------------

/**
 * Muestra una notificación temporal tipo "toast" en la esquina.
 *
 * @param {string} mensaje - Texto a mostrar
 * @param {string} tipo    - 'success' | 'error' | 'info'
 */
function mostrarNotificacion(mensaje, tipo) {
  // Determinar el color según el tipo de notificación
  const colores = {
    success: '#39ff14',   // Verde neón
    error:   '#ef4444',   // Rojo
    info:    '#00d4ff'    // Cian neón
  };
  const color = colores[tipo] || colores.info;

  // Crear el elemento div de la notificación dinámicamente
  const notif = document.createElement('div');

  // Aplicar estilos directamente al elemento (Inline CSS para el toast)
  Object.assign(notif.style, {
    position:     'fixed',
    bottom:       '2rem',
    right:        '1.5rem',
    background:   '#0d1117',
    border:       `1px solid ${color}`,
    borderLeft:   `4px solid ${color}`,
    color:        '#f0f4f8',
    padding:      '0.85rem 1.25rem',
    borderRadius: '10px',
    fontFamily:   "'Rajdhani', sans-serif",
    fontWeight:   '600',
    fontSize:     '0.9rem',
    zIndex:       '9999',
    boxShadow:    `0 0 20px ${color}40`,   // 40 = opacidad 25% en hex
    animation:    'slideInRight 0.3s ease',
    maxWidth:     '320px'
  });

  notif.textContent = mensaje;

  // Agregar la notificación al final del body
  document.body.appendChild(notif);

  // Eliminar la notificación después de 3 segundos
  setTimeout(() => {
    notif.style.opacity   = '0';                     // Desvanecer
    notif.style.transform = 'translateX(30px)';      // Deslizar fuera
    notif.style.transition = 'all 0.3s ease';
    // Esperar la transición antes de eliminar del DOM
    setTimeout(() => notif.remove(), 300);
  }, 3000);
}


/**
 * Aplica un efecto de "sacudida" al ícono del carrito en el navbar.
 * Se llama cuando el usuario agrega un ítem exitosamente.
 */
function animarCarritoIcono() {
  const btnCarrito = document.querySelector('.btn-cart');
  if (!btnCarrito) return;

  // Agregar la clase CSS que tiene la animación keyframes
  btnCarrito.classList.add('cart-shake');

  // Quitar la clase después de que termine la animación (600ms)
  setTimeout(() => btnCarrito.classList.remove('cart-shake'), 600);
}

// Agregar la animación de shake con JavaScript (inyectar en <style>)
// Se hace aquí para no depender de que esté en el CSS externo
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
  @keyframes cart-shake {
    0%, 100% { transform: rotate(0deg); }
    20%       { transform: rotate(-15deg); }
    40%       { transform: rotate(15deg); }
    60%       { transform: rotate(-10deg); }
    80%       { transform: rotate(10deg); }
  }
  .cart-shake { animation: cart-shake 0.6s ease; }
  @keyframes slideInRight {
    from { opacity: 0; transform: translateX(30px); }
    to   { opacity: 1; transform: translateX(0); }
  }
  @keyframes slideOut {
    from { opacity: 1; transform: translateX(0); max-height: 100px; }
    to   { opacity: 0; transform: translateX(20px); max-height: 0; }
  }
`;
document.head.appendChild(shakeStyle);


// ---------------------------------------------------------------
// SECCIÓN 4: PARTÍCULAS DECORATIVAS DEL HERO
// ---------------------------------------------------------------

/**
 * Genera partículas animadas en el hero section para un efecto visual.
 * Crea divs pequeños con clase .particle y los posiciona aleatoriamente.
 */
function generarParticulas() {
  const contenedor = document.getElementById('heroParticles');
  if (!contenedor) return;   // No está en esta página (login/registro)

  const CANTIDAD_PARTICULAS = 30;    // Número de partículas a crear

  for (let i = 0; i < CANTIDAD_PARTICULAS; i++) {
    const particula = document.createElement('div');
    particula.className = 'particle';

    // Posición aleatoria dentro del contenedor (porcentaje)
    const posX = Math.random() * 100;   // Entre 0% y 100%
    const posY = Math.random() * 100;

    // Duración de animación aleatoria entre 4 y 12 segundos
    const duracion = 4 + Math.random() * 8;

    // Retraso para que no todas empiecen al mismo tiempo
    const retraso = Math.random() * 5;

    // Tamaño aleatorio entre 2 y 6 píxeles
    const tamaño = 2 + Math.random() * 4;

    // Colores alternados entre cian y magenta
    const colores = ['#00d4ff', '#e040fb', '#39ff14'];
    const color = colores[Math.floor(Math.random() * colores.length)];

    // Aplicar los estilos calculados
    Object.assign(particula.style, {
      left:            `${posX}%`,
      top:             `${posY}%`,
      width:           `${tamaño}px`,
      height:          `${tamaño}px`,
      background:      color,
      animationDuration: `${duracion}s`,
      animationDelay:  `${retraso}s`,
      boxShadow:       `0 0 ${tamaño * 2}px ${color}`   // Halo de luz
    });

    contenedor.appendChild(particula);
  }
}


// ---------------------------------------------------------------
// SECCIÓN 5: INICIALIZACIÓN
// ---------------------------------------------------------------

/**
 * DOMContentLoaded: se dispara cuando el HTML fue cargado y parseado
 * completamente, pero antes de que carguen imágenes y hojas de estilo.
 * Es el momento correcto para ejecutar JavaScript que manipula el DOM.
 */
document.addEventListener('DOMContentLoaded', function() {

  // Generar las partículas del hero (solo si el contenedor existe)
  generarParticulas();

  // Efecto: revelar las tarjetas del catálogo con animación escalonada
  const tarjetas = document.querySelectorAll('.game-card');
  // querySelectorAll retorna un NodeList de todos los elementos con esa clase

  tarjetas.forEach(function(tarjeta, indice) {
    // Aplicar un retraso incremental a cada tarjeta (efecto cascada)
    tarjeta.style.opacity   = '0';
    tarjeta.style.transform = 'translateY(30px)';
    tarjeta.style.transition = `opacity 0.5s ease ${indice * 0.05}s, transform 0.5s ease ${indice * 0.05}s`;

    // Usar Intersection Observer para animar al entrar en el viewport
    const observador = new IntersectionObserver(function(entradas) {
      entradas.forEach(function(entrada) {
        if (entrada.isIntersecting) {
          // Cuando la tarjeta entra en pantalla, revelarla
          tarjeta.style.opacity   = '1';
          tarjeta.style.transform = 'translateY(0)';
          observador.unobserve(tarjeta);   // Dejar de observar (una vez es suficiente)
        }
      });
    }, { threshold: 0.1 });   // 0.1 = activar cuando el 10% es visible

    observador.observe(tarjeta);
  });

  // Cerrar las alertas flash automáticamente después de 4 segundos
  const alertas = document.querySelectorAll('.alert-gamer');
  alertas.forEach(function(alerta) {
    setTimeout(function() {
      // bootstrap.Alert maneja el cierre con animación
      const instancia = bootstrap.Alert.getOrCreateInstance(alerta);
      instancia.close();
    }, 4000);
  });

  console.log('🎮 GameVault Script cargado correctamente.');
});
