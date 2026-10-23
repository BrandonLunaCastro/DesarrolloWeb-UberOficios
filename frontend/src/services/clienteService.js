// Perfil del Cliente.
//  - Lectura:   GET /auth/me          -> { nombre, apellido, email, telefono, fecha_registro, rol, ... }
//  - Escritura: PUT /usuarios/perfil  -> body { zona?, telefono? }  (el back no permite editar nombre/apellido/email)
//    Respuesta: { mensaje, cliente: { zona, telefono }, prestador: {...} | null }
// NOTA: el back no tiene un GET que devuelva la zona guardada del cliente; solo la devuelve el PUT.
const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

async function req(path, init = {}) {
  const headers = new Headers(init.headers);
  const token = localStorage.getItem('jwt');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (init.body) headers.set('Content-Type', 'application/json');
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const d = data?.detail;
    const msg = Array.isArray(d) ? d.map((i) => i.msg).join('. ') : d;
    const err = new Error(typeof msg === 'string' && msg ? msg : `Error ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

// ---------- MOCK ----------
const wait = (v) => new Promise((r) => setTimeout(() => r(structuredClone(v)), 400));
const dbMock = { nombre: 'Luciana', apellido: 'Cruceño', email: 'luciana@ejemplo.com', telefono: '2615550000', fecha_registro: '2026-09-12T10:00:00', zona: null, rol: 'CLIENTE' };

export const clienteApi = USE_MOCK
  ? {
      obtener: () => wait(dbMock),
      actualizar: (d) => { Object.assign(dbMock, d); return wait({ mensaje: 'Perfil actualizado correctamente', cliente: { zona: dbMock.zona, telefono: dbMock.telefono }, prestador: null }); },
    }
  : {
      obtener: () => req('/auth/me'),
      actualizar: (d) => req('/usuarios/perfil', { method: 'PUT', body: JSON.stringify(d) }),
    };
