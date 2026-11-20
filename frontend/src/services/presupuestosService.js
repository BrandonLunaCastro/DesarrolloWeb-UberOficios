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

async function actualizarPresupuesto(idPostulacion, presupuesto) {
  const token = localStorage.getItem('jwt');
  const response = await fetch(`${API_URL}/presupuestos/${idPostulacion}/presupuesto`, {
    method: 'PUT',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ presupuesto }),
  });
  return leerRespuesta(response);
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
  return leerRespuesta(response);
}

async function leerRespuesta(response) {
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

async function calificar(idPostulacion, datos) {
  const token = localStorage.getItem('jwt');
  const formulario = new FormData();
  formulario.set('id_postulacion', idPostulacion);
  formulario.set('puntuacion', datos.puntuacion);
  formulario.set('comentario', datos.comentario || '');
  if (datos.fotoComprobante) {
    formulario.set('foto_comprobante', datos.fotoComprobante);
  }
  const response = await fetch(`${API_URL}/calificaciones`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formulario,
  });
  return leerRespuesta(response);
}

export const presupuestosApi = {
  listarParaCliente: (idCliente) => request(`/clientes/${idCliente}/presupuestos`),
  listarParaPrestador: (idPrestador) => request(`/prestadores/${idPrestador}/presupuestos`),
  listarCalificacionesPendientes: () => request('/calificaciones/pendientes'),
  aceptar: aceptarPresupuesto,
  actualizarPresupuesto,
  calificar,
};
