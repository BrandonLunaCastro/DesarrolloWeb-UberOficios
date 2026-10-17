// Misma base que authService.js
const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')
  .replace(/\/+$/, '');

// Con VITE_USE_MOCK=true funciona sin backend (saldo y postulaciones en memoria).
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';
let saldoMock = 10;
const yaPostulados = new Set();
const demora = (v) => new Promise((r) => setTimeout(() => r(v), 400));
const falla = (msg, status) => new Promise((_, rej) => setTimeout(() => { const e = new Error(msg); e.status = status; rej(e); }, 400));

// TODO: traer de la API. Hoy es una constante en el backend (services/postulaciones.py)
// y ningún endpoint la expone. Si cambia allá, hay que cambiarla acá.
export const COSTO_POSTULACION = 1;

async function authRequest(endpoint, options = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('jwt')}`,
    },
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail;
    // 422 => detail es una lista; el resto => string
    const message = Array.isArray(detail)
      ? detail.map((issue) => issue.msg).join('. ')
      : detail;
    const error = new Error(message || `Error ${response.status}`);
    error.status = response.status;
    throw error;
  }

  return data;
}

// GET /auth/me/saldo -> { saldo_creditos }
export const obtenerSaldo = async () => {
  if (USE_MOCK) return demora(saldoMock);
  const data = await authRequest('/auth/me/saldo');
  return Number(data.saldo_creditos);
};

// POST /avisos/{id}/postulaciones -> 201 con la postulación creada
export const postularseAAviso = (idAviso, { presupuesto, comentario }) => {
  if (USE_MOCK) {
    if (yaPostulados.has(idAviso)) return falla('Ya te postulaste a este aviso.', 409);
    if (saldoMock < COSTO_POSTULACION) return falla('No tenés créditos suficientes para postularte.', 400);
    saldoMock -= COSTO_POSTULACION;
    yaPostulados.add(idAviso);
    return demora({ id_aviso: idAviso, presupuesto: Number(presupuesto), comentario: comentario?.trim() || null });
  }
  return authRequest(`/avisos/${idAviso}/postulaciones`, {
    method: 'POST',
    body: JSON.stringify({
      presupuesto: Number(presupuesto),
      comentario: comentario?.trim() || null,
    }),
  });
};
