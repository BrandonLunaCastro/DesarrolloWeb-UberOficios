import { obtenerSaldo } from './postulacionService';

const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
// Con VITE_USE_MOCK=true en el .env, el feed funciona con datos de ejemplo (sin backend).
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

async function req(path, init = {}) {
  const headers = new Headers(init.headers);
  const token = localStorage.getItem('jwt');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (init.body) headers.set('Content-Type', 'application/json');
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const detail = await res.json().then((j) => j.detail).catch(() => null);
    const msg = Array.isArray(detail) ? detail.map((i) => i.msg).join('. ') : detail;
    const err = new Error(typeof msg === 'string' && msg ? msg : `Error ${res.status}`);
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
const AVISOS_PROPIOS = [];

// Mock de POST /avisos (misma forma que la respuesta real) y de GET /auth/me.
const crearMock = async ({ oficio, descripcion, zona, telefono }) => {
  const aviso = await wait({
    mensaje: 'Solicitud de trabajo creada correctamente',
    id_aviso: Date.now(), id_cliente: 1, oficio, descripcion, zona,
    telefono: telefono ?? null, estado: 'abierto', fecha_creacion: new Date().toISOString(),
  });
  AVISOS_PROPIOS.unshift(aviso);
  return aviso;
};
const meMock = () => wait({ nombre: 'Luciana', apellido: 'Cruceño', telefono: '2615550000', rol: 'CLIENTE' });
let meRequestToken = null;
let meRequest = null;
const obtenerMe = () => {
  const token = localStorage.getItem('jwt');
  if (meRequest && meRequestToken === token) return meRequest;

  meRequestToken = token;
  meRequest = req('/auth/me').catch((error) => {
    if (meRequestToken === token) {
      meRequestToken = null;
      meRequest = null;
    }
    throw error;
  });
  return meRequest;
};

// ---------- API REAL ----------
// El saldo y el costo de postularse viven en postulacionService (misma fuente que el formulario).
export const avisosApi = USE_MOCK
  ? {
      listarPorZona: () => wait(AVISOS),
      listarMios: () => wait(AVISOS_PROPIOS),
      saldo: obtenerSaldo,
      crear: crearMock,
      me: meMock,
    }
  : {
      listarPorZona: () => req('/avisos/zona'),
      listarMios: () => req('/avisos/mios'),
      saldo: obtenerSaldo,
      // POST /avisos -> 201. Body (AvisoCreate): oficio, descripcion, zona (obligatorios), telefono (opcional).
      crear: (datos) => req('/avisos', { method: 'POST', body: JSON.stringify(datos) }),
      // GET /auth/me -> { nombre, apellido, telefono, rol: 'CLIENTE' | 'PRESTADOR', ... }
      me: obtenerMe,
    };
