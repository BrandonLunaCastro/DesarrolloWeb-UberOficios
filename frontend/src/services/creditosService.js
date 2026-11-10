import { obtenerSaldo, mockSumarCreditos } from './postulacionService';

const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
// Con VITE_USE_MOCK=true la pantalla funciona con datos de ejemplo (sin backend).
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

// ---------- Adaptadores: único lugar que conoce los nombres de campos del back ----------
// Clasifica el enum del back (TipoTransaccionEnum) en los 3 tipos que muestra la pantalla.
// TipoTransaccionEnum: RECARGA, CONSUMO_POSTULACION, DEVOLUCION, BONIFICACION.
const clasificar = (tipo, monto) => {
  const t = String(tipo ?? '').toLowerCase();
  if (/bono|bonif|gratis|gratuit|regalo/.test(t)) return 'gratuito';
  if (/devol|reembols/.test(t)) return 'devuelto';
  if (/recarga|compra|adquir/.test(t)) return 'adquirido';
  if (/consum|postul|gasto/.test(t)) return 'consumido';
  return monto < 0 ? 'consumido' : 'adquirido';
};
const ESTADO = { aprobada: 'aprobada', aprobado: 'aprobada', pendiente: 'pendiente', rechazada: 'rechazada', rechazado: 'rechazada', cancelada: 'cancelada', cancelado: 'cancelada' };
const DESCRIPCION = { adquirido: 'Compra de créditos', gratuito: 'Créditos gratuitos', consumido: 'Postulación a un aviso', devuelto: 'Devolución de créditos' };

// paquete_credito: precio_centavos (ARS en centavos) -> se divide por 100 para mostrar
const normPaquete = (p) => ({ id: p.id, nombre: p.nombre, creditos: p.cantidad_creditos, precio: p.precio_centavos / 100, moneda: p.moneda ?? 'ARS' });

// TransaccionCreditoResponse: id, billetera_id, monto, tipo, referencia_id, referencia_tipo, descripcion (puede ser null), fecha_registro.
const normMov = (m) => {
  const monto = m.monto ?? m.cantidad;
  const tipo = clasificar(m.tipo ?? m.tipo_movimiento, monto);
  return {
    id: m.id ?? m.id_movimiento, tipo,
    cantidad: tipo === 'consumido' ? -Math.abs(monto) : Math.abs(monto), // consumidos siempre negativos
    descripcion: m.descripcion ?? DESCRIPCION[tipo], fecha: m.fecha_registro ?? m.fecha_creacion ?? m.fecha_movimiento,
  };
};

// compra_credito: estado PENDIENTE | APROBADA | RECHAZADA | CANCELADA
const normCompra = (c) => ({
  id: c.id, paquete: c.paquete_nombre ?? c.nombre_paquete ?? 'Paquete', creditos: c.cantidad_creditos,
  monto: c.precio_centavos / 100, moneda: c.moneda ?? 'ARS',
  estado: ESTADO[String(c.estado ?? '').toLowerCase()] ?? 'pendiente', fecha: c.fecha_creacion ?? c.fecha_compra,
});

// ---------- MOCK (misma forma que el back real) ----------
const hace = (dias) => new Date(Date.now() - dias * 864e5).toISOString();
const PAQUETES = [
  { id: 1, nombre: 'Inicial', cantidad_creditos: 5, precio_centavos: 300000, moneda: 'ARS' },
  { id: 2, nombre: 'Popular', cantidad_creditos: 15, precio_centavos: 750000, moneda: 'ARS' },
  { id: 3, nombre: 'Profesional', cantidad_creditos: 40, precio_centavos: 1600000, moneda: 'ARS' },
];
const mv = (id, tipo, monto, dias, descripcion) => ({ id, billetera_id: 1, tipo, monto, referencia_id: null, referencia_tipo: null, descripcion, fecha_registro: hace(dias) });
let movs = [ // suman 10, igual que el saldo del mock de postulacionService
  mv(1, 'BONIFICACION', 5, 33, 'Bono mensual gratuito'),
  mv(2, 'CONSUMO_POSTULACION', -1, 30, 'Postulación a "Reparación caño cocina"'),
  mv(3, 'CONSUMO_POSTULACION', -1, 28, 'Postulación a "Instalación de tomacorrientes"'),
  mv(4, 'RECARGA', 5, 12, 'Compra de paquete Inicial (5 créditos)'),
  mv(5, 'CONSUMO_POSTULACION', -1, 9, 'Postulación a "Pintura de living"'),
  mv(6, 'CONSUMO_POSTULACION', -1, 6, 'Postulación a "Corte de luz en el departamento"'),
  mv(7, 'BONIFICACION', 5, 3, 'Bono mensual gratuito'),
  mv(8, 'CONSUMO_POSTULACION', -1, 1, 'Postulación a "Cerradura de puerta"'),
];
let compras = [
  { id: 1, paquete_id: 1, paquete_nombre: 'Inicial', cantidad_creditos: 5, precio_centavos: 300000, moneda: 'ARS', estado: 'APROBADA', fecha_creacion: hace(12) },
  { id: 2, paquete_id: 2, paquete_nombre: 'Popular', cantidad_creditos: 15, precio_centavos: 750000, moneda: 'ARS', estado: 'RECHAZADA', fecha_creacion: hace(14) },
  { id: 3, paquete_id: 1, paquete_nombre: 'Inicial', cantidad_creditos: 5, precio_centavos: 300000, moneda: 'ARS', estado: 'CANCELADA', fecha_creacion: hace(16) },
];
let seq = 100;
// Para probar: localStorage.setItem('creditosMock', 'vacio' | 'error' | 'errorCompra' | 'rechazo') y recargar
const modo = () => localStorage.getItem('creditosMock');
const demora = (fn, ms = 500) => new Promise((ok, no) => setTimeout(() => { try { ok(fn()); } catch (e) { no(e); } }, ms));
const falla = (msg = 'No se pudo conectar con el servidor.') => { const e = new Error(msg); e.status = 500; throw e; };

const mock = {
  saldo: obtenerSaldo,
  paquetes: () => demora(() => { if (modo() === 'error') falla(); return PAQUETES.map(normPaquete); }),
  movimientos: () => demora(() => (modo() === 'vacio' ? [] : [...movs].reverse().map(normMov)), 300),
  compras: () => demora(() => (modo() === 'vacio' ? [] : [...compras].reverse().map(normCompra)), 300),
  comprar: (idPaquete) => demora(() => {
    if (modo() === 'errorCompra') falla('No pudimos iniciar la compra. Intentá de nuevo.');
    const p = PAQUETES.find((x) => x.id === idPaquete);
    const c = { id: ++seq, paquete_id: p.id, paquete_nombre: p.nombre, cantidad_creditos: p.cantidad_creditos, precio_centavos: p.precio_centavos, moneda: p.moneda, estado: 'PENDIENTE', fecha_creacion: new Date().toISOString() };
    compras.push(c);
    // Simula la confirmación del pago (en el back real la hace el aviso del medio de pago)
    setTimeout(() => {
      if (modo() === 'rechazo') { c.estado = 'RECHAZADA'; return; }
      c.estado = 'APROBADA';
      movs.push({ id: ++seq, tipo: 'RECARGA', monto: p.cantidad_creditos, descripcion: `Compra de paquete ${p.nombre} (${p.cantidad_creditos} créditos)`, fecha_registro: new Date().toISOString() });
      mockSumarCreditos(p.cantidad_creditos);
    }, 4000);
    return { id: c.id, estado: 'PENDIENTE', url_pago: null };
  }),
};

// ---------- API REAL ----------
//   ✅ GET /auth/me/saldo        saldo
//   ✅ GET /creditos/paquetes    paquetes activos (id, nombre, cantidad_creditos, precio_centavos, moneda)
//   ✅ GET /creditos/movimientos historial (transaccion_credito)
//   ⏳ GET /creditos/compras     compras del prestador            ← no está en ninguna tarea
//   ⏳ POST /creditos/compras    { paquete_id } -> { id, estado, url_pago }  ← tarea "compra de créditos"
// Los créditos los acredita SIEMPRE el back al confirmarse el pago; el front solo muestra lo que el back informa.
const real = {
  saldo: obtenerSaldo,
  paquetes: () => req('/creditos/paquetes').then((l) => l.map(normPaquete)),
  movimientos: () => req('/creditos/movimientos').then((l) => l.map(normMov)),
  compras: () => req('/creditos/compras').then((l) => l.map(normCompra)),
  comprar: (idPaquete) =>
    req('/creditos/compras', { method: 'POST', body: JSON.stringify({ paquete_id: idPaquete }) })
      .then((r) => ({ ...r, url_pago: r.url_pago ?? r.init_point ?? null })),
};

export const creditosApi = USE_MOCK ? mock : real;
