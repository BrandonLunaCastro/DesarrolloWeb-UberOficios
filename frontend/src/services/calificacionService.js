const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
// Con VITE_USE_MOCK=true la calificación funciona con datos de ejemplo (sin backend).
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

// ---------- MOCK (misma forma y mismos mensajes de error que el back real) ----------
let seq = 0;
const yaCalificadas = new Set();
// Para probar: localStorage.setItem('calificacionMock', 'error' | 'yaCalificado' | 'noFinalizado' | 'errorFinalizar') y recargar
const modo = () => localStorage.getItem('calificacionMock');
const demora = (fn, ms = 600) => new Promise((ok, no) => setTimeout(() => { try { ok(fn()); } catch (e) { no(e); } }, ms));
const falla = (msg, status = 500) => { const e = new Error(msg); e.status = status; throw e; };

const mock = {
  calificar: (idPostulacion, { puntuacion, comentario }) => demora(() => {
    if (modo() === 'error') falla('No pudimos guardar tu calificación. Intentá de nuevo.');
    if (modo() === 'noFinalizado') falla('Primero debes finalizar el trabajo', 409);
    if (modo() === 'yaCalificado' || yaCalificadas.has(idPostulacion)) falla('Este trabajo ya fue calificado', 409);
    yaCalificadas.add(idPostulacion);
    return { id_calificacion: ++seq, id_postulacion: idPostulacion, id_prestador: 1, puntuacion, comentario: comentario?.trim() || null, fecha: new Date().toISOString() };
  }),
};

// ---------- API REAL ----------
// POST /calificaciones  { id_postulacion, puntuacion (1-5), comentario (opcional, máx. 2000) }
// -> 201 { id_calificacion, id_postulacion, id_prestador, puntuacion, comentario, fecha }
// El back valida: rol cliente (403), postulación aceptada (409), dueño del aviso (403), aviso FINALIZADO (409) y que no esté
// ya calificada (409). Los mensajes llegan en `detail` y se muestran tal cual.
const real = {
  calificar: (idPostulacion, { puntuacion, comentario }) =>
    req('/calificaciones', {
      method: 'POST',
      body: JSON.stringify({ id_postulacion: idPostulacion, puntuacion, comentario: comentario?.trim() || null }),
    }),
};

export const calificacionApi = USE_MOCK ? mock : real;

// ---------- FINALIZAR TRABAJO ----------
// Pasa el aviso a FINALIZADO (condición para poder calificar) y le crea una notificación al prestador.
// POST /avisos/{id_aviso}/finalizar (backend/app/routes/avisos.py). Solo el cliente dueño del aviso, y solo si está EN_PROCESO.
// Responde { id_aviso, estado: 'FINALIZADO' }; si ya estaba finalizado responde lo mismo. Errores 403/404/409 con `detail`.
export const finalizarTrabajo = (idAviso) => (USE_MOCK
  ? demora(() => {
    if (modo() === 'errorFinalizar') falla('El trabajo no tiene un presupuesto aceptado', 409);
    return { id_aviso: idAviso, estado: 'FINALIZADO' };
  })
  : req(`/avisos/${idAviso}/finalizar`, { method: 'POST' }));
