const hora = new Intl.DateTimeFormat('es-AR', { hour: '2-digit', minute: '2-digit' });
const mismoDia = (a, b) => a.toDateString() === b.toDateString();
const ayer = () => new Date(Date.now() - 864e5);

export const formatoHora = (iso) => hora.format(new Date(iso));

export function etiquetaDia(iso) {
  const d = new Date(iso);
  if (mismoDia(d, new Date())) return 'Hoy';
  if (mismoDia(d, ayer())) return 'Ayer';
  return new Intl.DateTimeFormat('es-AR', { day: 'numeric', month: 'long' }).format(d);
}

// Para la lista: hora si es de hoy, "Ayer", o dd/mm
export function horaOFecha(iso) {
  const d = new Date(iso);
  if (mismoDia(d, new Date())) return formatoHora(iso);
  if (mismoDia(d, ayer())) return 'Ayer';
  return new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: '2-digit' }).format(d);
}

export const iniciales = (nombre = '') =>
  nombre.trim().split(/\s+/).slice(0, 2).map((p) => p[0]).join('').toUpperCase();
