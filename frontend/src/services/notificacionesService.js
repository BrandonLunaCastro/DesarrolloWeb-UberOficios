const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
// Con VITE_USE_MOCK=true las notificaciones son de ejemplo (sin backend).
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

const listenersRealtime = new Set();
let socketRealtime = null;
let temporizadorReconectar = null;
let temporizadorPing = null;
let demoraReconectar = 1000;

function emitirEventoRealtime(evento) {
  listenersRealtime.forEach((listener) => listener(evento));
}

function conectarRealtime() {
  if (socketRealtime || listenersRealtime.size === 0) return;
  const token = localStorage.getItem('jwt');
  if (!token) return;

  const url = new URL(`${BASE}/notificaciones/ws`);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.searchParams.set('token', token);

  const socket = new WebSocket(url);
  socketRealtime = socket;
  socket.onopen = () => {
    demoraReconectar = 1000;
    emitirEventoRealtime({ type: 'conectado' });
    temporizadorPing = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) socket.send('ping');
    }, 25000);
  };
  socket.onmessage = ({ data }) => {
    try {
      emitirEventoRealtime(JSON.parse(data));
    } catch (error) {
      console.error('No se pudo interpretar un evento realtime de notificaciones.', error);
    }
  };
  socket.onclose = (event) => {
    clearInterval(temporizadorPing);
    temporizadorPing = null;
    if (socketRealtime === socket) socketRealtime = null;
    if (listenersRealtime.size === 0) return;
    if (event.code === 4401) {
      emitirEventoRealtime({ type: 'no_autorizado' });
      return;
    }
    temporizadorReconectar = setTimeout(conectarRealtime, demoraReconectar);
    demoraReconectar = Math.min(demoraReconectar * 2, 30000);
  };
  socket.onerror = () => socket.close();
}

function suscribirRealtime(listener) {
  listenersRealtime.add(listener);
  conectarRealtime();
  return () => {
    listenersRealtime.delete(listener);
    if (listenersRealtime.size > 0) return;
    clearTimeout(temporizadorReconectar);
    clearInterval(temporizadorPing);
    temporizadorReconectar = null;
    temporizadorPing = null;
    if (socketRealtime) {
      const socket = socketRealtime;
      socketRealtime = null;
      socket.close(1000, 'Sin suscriptores');
    }
  };
}

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

// Adaptador: único lugar que conoce los nombres de campos del back.
const norm = (n) => ({ id: n.id_notificacion, tipo: n.tipo, texto: n.mensaje, fecha: n.fecha_creacion, leida: n.leida });

// ---------- MOCK ----------
const hace = (min) => new Date(Date.now() - min * 60000).toISOString();
let datos = [
  { id_notificacion: 1, tipo: 'mensaje', mensaje: 'Martín Gómez te envió un mensaje.', fecha_creacion: hace(5), leida: false },
  { id_notificacion: 2, tipo: 'presupuesto', mensaje: 'Recibiste un nuevo presupuesto para "Reparación caño cocina".', fecha_creacion: hace(120), leida: false },
  { id_notificacion: 3, tipo: 'aviso', mensaje: 'Tu aviso "Instalación de tomacorrientes" pasó a En proceso.', fecha_creacion: hace(60 * 26), leida: true },
];
// Para probar: localStorage.setItem('notifMock', 'vacio' | 'error') y recargar
const modo = () => localStorage.getItem('notifMock');
const demora = (fn) => new Promise((ok, no) => setTimeout(() => { try { ok(fn()); } catch (e) { no(e); } }, 400));
const mock = {
  listar: () => demora(() => {
    if (modo() === 'error') { const e = new Error('No se pudo conectar con el servidor.'); e.status = 500; throw e; }
    return modo() === 'vacio' ? [] : datos.map(norm);
  }),
  marcarLeida: (id) => demora(() => { datos = datos.map((n) => (n.id_notificacion === id ? { ...n, leida: true } : n)); }),
  marcarTodasLeidas: () => demora(() => { datos = datos.map((n) => ({ ...n, leida: true })); }),
  suscribir: () => () => {},
};

// ---------- API REAL ----------
const real = {
  listar: () => req('/notificaciones').then((l) => l.map(norm)),
  marcarLeida: (id) => req(`/notificaciones/${id}/leida`, { method: 'PATCH' }),
  marcarTodasLeidas: () => req('/notificaciones/leidas', { method: 'PATCH' }),
  suscribir: suscribirRealtime,
};

export const notificacionesApi = USE_MOCK ? mock : real;
