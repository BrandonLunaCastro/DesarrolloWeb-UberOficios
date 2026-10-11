const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
// Con VITE_USE_MOCK=true en el .env, el feed funciona con datos de ejemplo (sin backend).
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

async function req(path, init = {}) {
  const headers = new Headers(init.headers);
  const token = localStorage.getItem('jwt');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const detail = await res.json().then((j) => j.detail).catch(() => null);
    const err = new Error(typeof detail === 'string' ? detail : `Error ${res.status}`);
    err.status = res.status; // 400 = el prestador no configuró su zona, 404 = no tiene perfil de prestador
    throw err;
  }
  return res.json();
}

// ---------- MOCK ----------
const wait = (v) => new Promise((r) => setTimeout(() => r(structuredClone(v)), 400));
// Respuesta real de GET /avisos/zona: id_aviso, id_cliente, oficio, descripcion, zona, telefono, estado, fecha_creacion.
// `urgencia` y `postulados` NO los devuelve todavía el back: están en el mock para ver el diseño completo.
const AVISOS = [
  { id_aviso: 1, id_cliente: 7, oficio: 'Reparación caño cocina', zona: 'Godoy Cruz', estado: 'abierto', fecha_creacion: '2026-10-09T14:20:00', urgencia: 'media', postulados: 1,
    descripcion: 'Pierde agua debajo de la bacha. Necesito que vengan a mirarlo y arreglarlo hoy si es posible. Zona Plaza Godoy Cruz.' },
  { id_aviso: 2, id_cliente: 9, oficio: 'Instalación de tomacorrientes', zona: 'Godoy Cruz', estado: 'abierto', fecha_creacion: '2026-10-08T10:05:00', urgencia: 'baja', postulados: 0,
    descripcion: 'Necesito agregar tres tomas en el living y revisar la térmica del departamento.' },
  { id_aviso: 3, id_cliente: 12, oficio: 'Corte de luz en todo el departamento', zona: 'Godoy Cruz', estado: 'abierto', fecha_creacion: '2026-10-07T21:40:00', urgencia: 'alta', postulados: 12,
    descripcion: 'Se cortó la luz desde anoche y salta la térmica apenas la subo.' },
];

// Costo de postularse en créditos (según el Figma). ⚠️ Confirmar con el back si es fijo o depende del aviso.
export const COSTO_POSTULACION = 1;

// ---------- API REAL ----------
export const avisosApi = USE_MOCK
  ? { listarPorZona: () => wait(AVISOS), saldo: () => wait(10) }
  : {
      listarPorZona: () => req('/avisos/zona'),
      saldo: () => req('/prestadores/me').then((p) => p.prestador.saldo_creditos), // supuesto: ajustar al endpoint real
    };
