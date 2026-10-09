const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
// Con VITE_USE_MOCK=true en el .env, la pantalla funciona sin backend (datos en memoria).
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

async function req(path, init = {}) {
  const headers = new Headers(init.headers);
  const token = localStorage.getItem('jwt');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const detail = await res.json().then((j) => j.detail).catch(() => null);
    throw new Error(typeof detail === 'string' ? detail : `Error ${res.status}`);
  }
  return res.status === 204 ? undefined : res.json();
}

// ---------- MOCK ----------
const ph = (c) => 'data:image/svg+xml,' + encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='400' height='300'><rect width='100%' height='100%' fill='${c}'/></svg>`);
const ZONAS = ['Capital', 'Godoy Cruz', 'Guaymallén', 'Las Heras', 'Luján de Cuyo', 'Maipú'].map((nombre, i) => ({ id_zona: i + 1, nombre }));
const db = {
  usuario: { nombre: 'Martin', apellido: 'Gomez', foto_perfil: null, fecha_registro: '2026-08-12' },
  prestador: { matricula: '55432', biografia: 'Especialista en instalaciones eléctricas domiciliarias. Trabajo rápido y con garantía. Matrícula N° 55432.', radio_cobertura_km: 15 },
  categoria: 'Electricista',
  zonas: ZONAS.slice(0, 2),
  rating: { promedio: 4.9, total: 32 },
  fotos: ['#cbd5e1', '#475569', '#94a3b8', '#64748b', '#334155'].map((c, i) => ({ id_foto: i + 1, url_imagen: ph(c), descripcion: `Trabajo ${i + 1}` })),
};
const wait = (v) => new Promise((r) => setTimeout(() => r(structuredClone(v)), 400));
const mock = {
  yo: () => wait(db.usuario),
  obtener: () => wait(db),
  zonas: () => wait(ZONAS),
  actualizar: ({ biografia, zonas_ids }) => {
    db.prestador.biografia = biografia;
    db.zonas = ZONAS.filter((z) => zonas_ids.includes(z.id_zona));
    return wait(db);
  },
  subirFotos: (files) => {
    const nuevas = files.map((f, i) => ({ id_foto: Date.now() + i, url_imagen: URL.createObjectURL(f), descripcion: f.name }));
    db.fotos = [...nuevas, ...db.fotos];
    return new Promise((r) => setTimeout(() => r(nuevas), 600));
  },
  borrarFoto: (id) => { db.fotos = db.fotos.filter((f) => f.id_foto !== id); return wait(undefined); },
};

// ---------- API REAL ----------
const real = {
  yo: () => req('/usuarios/me'),
  obtener: () => req('/prestadores/me'),
  zonas: () => req('/zonas'),
  actualizar: (d) => req('/prestadores/me', { method: 'PUT', body: JSON.stringify(d) }),
  subirFotos: (files) => {
    const fd = new FormData();
    files.forEach((f) => fd.append('fotos', f));
    return req('/prestadores/me/fotos', { method: 'POST', body: fd });
  },
  borrarFoto: (id) => req(`/prestadores/me/fotos/${id}`, { method: 'DELETE' }),
};

export const perfilApi = USE_MOCK ? mock : real;
