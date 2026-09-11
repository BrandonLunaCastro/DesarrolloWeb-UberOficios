const API_URL = import.meta.env.VITE_API_URL;
console.log('TODAS LAS ENV:', import.meta.env); // sacar después de confirmar

async function request(endpoint, body) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail || `Error ${response.status}`);
  }

  return data;
}

// Login: devuelve { access_token, token_type }
export const loginUser = (correo, contrasena) =>
  request('/auth/login', { correo, contrasena });

// Register: devuelve { mensaje, id_usuario, nombre_apellido, correo } - SIN token
export const registerUser = ({ nombre_apellido, correo, contrasena }) =>
  request('/auth/register', { nombre_apellido, correo, contrasena });





