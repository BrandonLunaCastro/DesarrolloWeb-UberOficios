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

export const presupuestosApi = {
  listarParaCliente: (idCliente) => request(`/clientes/${idCliente}/presupuestos`),
  listarParaPrestador: (idPrestador) => request(`/prestadores/${idPrestador}/presupuestos`),
};
