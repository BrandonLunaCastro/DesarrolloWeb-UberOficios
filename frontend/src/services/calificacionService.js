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

// ---------- MOCK ----------
let seq = 0;
const yaCalificados = new Set();
// Para probar: localStorage.setItem('calificacionMock', 'error' | 'yaCalificado') y recargar
const modo = () => localStorage.getItem('calificacionMock');
const demora = (fn, ms = 600) => new Promise((ok, no) => setTimeout(() => { try { ok(fn()); } catch (e) { no(e); } }, ms));
const falla = (msg, status = 500) => { const e = new Error(msg); e.status = status; throw e; };

const mock = {
  calificar: (idAviso, { puntuacion, comentario }) => demora(() => {
    if (modo() === 'error') falla('No pudimos guardar tu calificación. Intentá de nuevo.');
    if (modo() === 'yaCalificado' || yaCalificados.has(idAviso)) falla('Ya calificaste este trabajo.', 409);
    yaCalificados.add(idAviso);
    return { id_calificacion: ++seq, id_aviso: idAviso, puntuacion, comentario: comentario?.trim() || null, fecha_calificacion: new Date().toISOString() };
  }),
};

// ---------- API REAL ----------
// ⚠️ Ruta propuesta, confirmar con el back (sigue el estilo de /avisos/{id}/postulaciones). Un trabajo se califica una sola vez.
// Las validaciones (dueño del aviso, prestador elegido, trabajo finalizado, sin duplicados) las hace SIEMPRE el back.
const real = {
  calificar: (idAviso, { puntuacion, comentario }) =>
    req(`/avisos/${idAviso}/calificacion`, {
      method: 'POST',
      body: JSON.stringify({ puntuacion, comentario: comentario?.trim() || null }),
    }),
};

export const calificacionApi = USE_MOCK ? mock : real;
