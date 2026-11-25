const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')
  .replace(/\/+$/, '');

async function request(endpoint, body, authenticated = false, method = 'POST') {
  const headers = { 'Content-Type': 'application/json' };
  if (authenticated) {
    const token = localStorage.getItem('jwt');
    if (!token) throw new Error('Tu sesión expiró. Iniciá sesión nuevamente.');
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    method,
    headers,
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    const detail = data.detail;
    const message = Array.isArray(detail)
      ? detail.map((issue) => issue.msg).join(', ')
      : detail;
    const error = new Error(message || `Error ${response.status}`);
    error.status = response.status;
    throw error;
  }

  return data;
}

// Login: devuelve { access_token, token_type }
export const loginUser = (email, contrasena) =>
  request('/auth/login', { email, contrasena });

// Register: los campos corresponden a RegisterRequest del backend.
export const registerUser = ({ nombre, apellido, email, contrasena, rol }) =>
  request('/auth/register', { nombre, apellido, email, contrasena, rol });

export const cambiarRolUsuario = (rol) =>
  request('/auth/me/rol', { rol }, true, 'PUT');
