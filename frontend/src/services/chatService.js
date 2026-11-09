const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
// Con VITE_USE_MOCK=true el chat funciona con datos ficticios (sin backend).
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

async function req(path, init = {}) {
  const headers = new Headers(init.headers);
  const token = localStorage.getItem('jwt');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (init.body) headers.set('Content-Type', 'application/json');
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data?.detail;
    const err = new Error(Array.isArray(detail) ? detail.map((i) => i.msg).join('. ') : detail || `Error ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

// ---------- Adaptadores: ÚNICO lugar que conoce los nombres de campos del back ----------
// Si el modelo del back cambia, solo se tocan estas dos funciones.
const normMsg = (m) => ({
  id: m.id_mensaje, idConversacion: m.conversacion_id ?? m.id_conversacion,
  idRemitente: m.remitente_id ?? m.id_remitente,
  identificadorUnico: m.identificador_unico ?? null,
  texto: m.contenido, fecha: m.fecha_envio,
});
const normConv = (c) => ({
  id: c.id_conversacion, idAviso: c.id_aviso, oficio: c.oficio, estado: c.estado ?? 'en_proceso',
  otro: { id: c.otro_participante.id_usuario, nombre: `${c.otro_participante.nombre} ${c.otro_participante.apellido}` },
  ultimo: c.ultimo_mensaje ? { texto: c.ultimo_mensaje.contenido, fecha: c.ultimo_mensaje.fecha_envio } : null,
});

// ---------- MOCK ----------
const hace = (min) => new Date(Date.now() - min * 60000).toISOString();
const YO = 1;
let seq = 100;
const oyentes = new Map(); // id_conversacion -> Set de { onMensaje, onEstado }
const m = (id, rem, contenido, min) => ({ id_mensaje: id, id_conversacion: 1, id_remitente: rem, contenido, fecha_envio: hace(min) });
const db = {
  conversaciones: [
    { id_conversacion: 1, id_aviso: 2, oficio: 'Instalación de tomacorrientes', estado: 'en_proceso', otro_participante: { id_usuario: 7, nombre: 'Martín', apellido: 'Gómez' } },
    { id_conversacion: 2, id_aviso: 1, oficio: 'Reparación caño cocina', estado: 'en_proceso', otro_participante: { id_usuario: 9, nombre: 'Sofía', apellido: 'Ledesma' } },
  ],
  mensajes: {
    1: [
      m(1, 7, 'Hola Luciana, soy Martín. Gracias por elegir mi presupuesto para los tomacorrientes.', 60 * 26),
      m(2, YO, 'Hola Martín! ¿Cuándo podrías pasar a verlo?', 60 * 26 - 3),
      m(3, 7, 'Puedo mañana a las 10. ¿Te queda bien?', 60 * 25),
      m(4, YO, 'Perfecto, te espero. Es en Plaza Godoy Cruz, San Martín 1450.', 60 * 3),
      m(5, 7, 'Genial, llevo los materiales. Cualquier cosa te escribo por acá.', 60 * 2),
    ],
    2: [], // conversación vacía, para ver ese estado
  },
};
// Para probar estados desde la consola: localStorage.setItem('chatMock', 'vacio' | 'error' | 'errorEnvio' | 'errorEliminar'); y recargar
const modo = () => localStorage.getItem('chatMock');
const demora = (fn, ms = 500) => new Promise((ok, no) => setTimeout(() => { try { ok(fn()); } catch (e) { no(e); } }, ms));
const fallo = () => { const e = new Error('No se pudo conectar con el servidor.'); e.status = 500; throw e; };

const mock = {
  obtenerYo: () => demora(() => ({ id: YO }), 200),
  listarConversaciones: () => demora(() => {
    if (modo() === 'error') fallo();
    if (modo() === 'vacio') return [];
    return db.conversaciones.map((c) => normConv({ ...c, ultimo_mensaje: db.mensajes[c.id_conversacion].at(-1) }));
  }),
  obtenerMensajes: (id) => demora(() => { if (modo() === 'error') fallo(); return db.mensajes[id].map(normMsg); }),
  enviarMensaje: (id, texto, identificadorUnico) => demora(() => {
    if (modo() === 'errorEnvio') fallo();
    const existente = db.mensajes[id].find(
      (mensaje) => mensaje.identificador_unico === identificadorUnico,
    );
    if (existente) return normMsg(existente);
    const nuevo = { id_mensaje: ++seq, id_conversacion: id, id_remitente: YO, contenido: texto, fecha_envio: new Date().toISOString() };
    nuevo.identificador_unico = identificadorUnico;
    db.mensajes[id].push(nuevo);
    // Simula una respuesta en tiempo real del otro participante
    const otro = db.conversaciones.find((c) => c.id_conversacion === id).otro_participante.id_usuario;
    setTimeout(() => {
      const resp = { id_mensaje: ++seq, id_conversacion: id, id_remitente: otro, contenido: 'Perfecto, quedamos así. ¡Gracias!', fecha_envio: new Date().toISOString() };
      db.mensajes[id].push(resp);
      oyentes.get(id)?.forEach((h) => h.onMensaje(normMsg(resp)));
    }, 1800);
    return normMsg(nuevo);
  }, 400),
  eliminarConversacion: (id) => demora(() => {
    if (modo() === 'errorEliminar') fallo();
    db.conversaciones = db.conversaciones.filter((c) => c.id_conversacion !== id);
    delete db.mensajes[id];
  }),
  suscribir: (id, h) => {
    if (!oyentes.has(id)) oyentes.set(id, new Set());
    oyentes.get(id).add(h);
    setTimeout(() => h.onEstado?.('conectado'), 0);
    return () => oyentes.get(id)?.delete(h);
  },
};

// ---------- API REAL ----------
// ⚠️ Endpoints propuestos: confirmar con el back (tareas 2, 3 y 4 del sprint).
const real = {
  obtenerYo: () => req('/auth/me').then((u) => ({ id: u.id_usuario })),
  listarConversaciones: () => req('/conversaciones').then((l) => l.map(normConv)),
  obtenerMensajes: (id, afterId = 0) => req(`/conversaciones/${id}/mensajes?after_id=${afterId}`).then((l) => l.map(normMsg)),
  enviarMensaje: (id, texto, identificadorUnico) => req(`/conversaciones/${id}/mensajes`, {
    method: 'POST',
    body: JSON.stringify({ contenido: texto, identificador_unico: identificadorUnico }),
  }).then(normMsg),
  eliminarConversacion: (id) => req(`/conversaciones/${id}`, { method: 'DELETE' }),
  suscribir: (id, h, lastMessageId = 0) => {
    const token = localStorage.getItem('jwt');
    let cursor = Number(lastMessageId) || 0;
    let retryDelay = 1000;
    let retryTimer;
    let socket;
    let stopped = false;

    const conectar = () => {
      if (stopped) return;
      const url = new URL(`${BASE}/conversaciones/${id}/ws`);
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      if (token) url.searchParams.set('token', token);
      url.searchParams.set('after_id', String(cursor));

      h.onEstado?.('reconectando');
      socket = new WebSocket(url);
      socket.onopen = () => {
        retryDelay = 1000;
        h.onEstado?.('conectado');
      };
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type !== 'message' || !data.message) return;
        const mensaje = normMsg(data.message);
        cursor = Math.max(cursor, Number(mensaje.id) || 0);
        h.onMensaje(mensaje);
      };
      socket.onclose = (event) => {
        if (stopped) return;
        if (event.code === 4401) {
          h.onEstado?.('desconectado');
          h.onError?.(Object.assign(new Error('La sesión no es válida.'), { status: 401 }));
          return;
        }
        if (event.code === 4403 || event.code === 4404) {
          h.onEstado?.('desconectado');
          const status = event.code === 4403 ? 403 : 404;
          const message = event.code === 4403
            ? 'No tenés acceso a esta conversación.'
            : 'La conversación ya no existe.';
          h.onError?.(Object.assign(new Error(message), { status }));
          return;
        }
        h.onEstado?.('reconectando');
        retryTimer = setTimeout(conectar, retryDelay);
        retryDelay = Math.min(retryDelay * 2, 30000);
      };
    };

    conectar();
    return () => {
      stopped = true;
      clearTimeout(retryTimer);
      socket?.close(1000, 'Chat cerrado');
    };
  },
};

export const chatApi = USE_MOCK ? mock : real;
