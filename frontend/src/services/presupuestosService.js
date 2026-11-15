const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')
  .replace(/\/+$/, '');

async function request(endpoint) {
  const token = localStorage.getItem('jwt');
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((issue) => issue.msg).join('. ')
      : detail;
    const error = new Error(message || `Error ${response.status}`);
    error.status = response.status;
    throw error;
  }

  return data;
}

async function aceptarPresupuesto(idPostulacion) {
  return enviarPost(`/presupuestos/${idPostulacion}/aceptar`);
}

async function enviarPost(endpoint, body) {
  const token = localStorage.getItem('jwt');
  const response = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((issue) => issue.msg).join('. ')
      : detail;
    const error = new Error(message || `Error ${response.status}`);
    error.status = response.status;
    throw error;
  }

  return data;
}

export const presupuestosApi = {
  listarParaCliente: (idCliente) => request(`/clientes/${idCliente}/presupuestos`),
  listarParaPrestador: (idPrestador) => request(`/prestadores/${idPrestador}/presupuestos`),
  aceptar: aceptarPresupuesto,
  calificar: (idPostulacion, datos) => enviarPost('/calificaciones', {
    id_postulacion: idPostulacion,
    ...datos,
  }),
};
