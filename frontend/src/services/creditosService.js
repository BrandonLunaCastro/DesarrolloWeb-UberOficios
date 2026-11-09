const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')
  .replace(/\/+$/, '');

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('jwt')}`,
      ...options.headers,
    },
  });
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((issue) => issue.msg).join(', ')
      : detail?.mensaje || detail;
    const error = new Error(message || `Error ${response.status}`);
    error.compraId = detail?.compra_id;
    throw error;
  }
  return data;
}

export const listarPaquetesCreditos = () => request('/creditos/paquetes');

export const iniciarCompraCreditos = (paqueteId) => request('/creditos/compras', {
  method: 'POST',
  body: JSON.stringify({ paquete_id: paqueteId }),
});

export const consultarCompraCreditos = (compraId) =>
  request(`/creditos/compras/${compraId}`);

export const reintentarCheckoutCreditos = (compraId) =>
  request(`/creditos/compras/${compraId}/checkout`, { method: 'POST' });
