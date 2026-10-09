const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')
  .replace(/\/+$/, '');

async function request(endpoint, body) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    const detail = data.detail;
    const message = Array.isArray(detail)
      ? detail.map((issue) => issue.msg).join(', ')
      : detail;
    throw new Error(message || `Error ${response.status}`);
  }

  return data;
}

// Login: devuelve { access_token, token_type }
export const loginUser = (email, contrasena) =>
  request('/auth/login', { email, contrasena });

// Register: los campos corresponden a RegisterRequest del backend.
export const registerUser = ({ nombre, apellido, email, contrasena, rol }) =>
  request('/auth/register', { nombre, apellido, email, contrasena, rol });
