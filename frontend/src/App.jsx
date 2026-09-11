import { Mail, Lock, User, Eye, EyeOff, Search, Settings, Sparkles } from 'lucide-react';
import { FcGoogle } from 'react-icons/fc';
import { FaApple } from 'react-icons/fa';
import { useState } from 'react';
import { loginUser, registerUser } from './services/authService';
import './App.css';

export default function App() {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [role, setRole] = useState('client'); // 'client' | 'provider'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [token, setToken] = useState(localStorage.getItem('jwt') || '');

  const switchMode = (m) => {
    setMode(m);
    setError('');
  };

const handleSubmit = async (e) => {
  e.preventDefault();
  setError('');

  if (mode === 'register' && !acceptedTerms) {
    setError('Tenés que aceptar los Términos y la Política de Privacidad.');
    return;
  }

  setLoading(true);
  try {
    if (mode === 'login') {
      const data = await loginUser(email, password);
      localStorage.setItem('jwt', data.access_token);
      setToken(data.access_token);
    } else {
      // 1. Registramos (esto no devuelve token)
      await registerUser({ 
        nombre_apellido: name,
        correo: email,
        contrasena: password });

        alert("cuenta creada correctamente")
        /*
        teporalmente desactivo para probar registro en la db
        // 2. Logueamos automáticamente para obtener el JWT
        const loginData = await loginUser(email, password);
        localStorage.setItem('jwt', loginData.access_token);
        setToken(loginData.access_token);
      */
      }
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};

  const handleLogout = () => {
    localStorage.removeItem('jwt');
    setToken('');
  };

  if (token) {
    return (
      <div className="page">
        <div className="card session-active">
          <p style={{ color: '#059669', fontWeight: 600 }}>✓ Sesión activa</p>
          <div className="token-box"><strong>JWT:</strong> {token}</div>
          <button className="logout-btn" onClick={handleLogout}>Cerrar Sesión</button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="card">
        <div className="tabs">
          <button
            className={`tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => switchMode('login')}
            type="button"
          >
            → Iniciar Sesión
          </button>
          <button
            className={`tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => switchMode('register')}
            type="button"
          >
               Crear Cuenta
          </button>
        </div>

        {mode === 'register' && (
          <>
            <label style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>
              ¿Qué uso le darás a la plataforma?
            </label>
            <div className="role-select">
              <div
                className={`role-card ${role === 'client' ? 'selected' : ''}`}
                onClick={() => setRole('client')}
              >
                <div className="role-title"><Search size={14} /> Soy Cliente</div>
                <div className="role-sub">Busco profesionales</div>
              </div>
              <div
                className={`role-card ${role === 'provider' ? 'selected' : ''}`}
                onClick={() => setRole('provider')}
              >
                <div className="role-title"><Settings size={14} /> Soy prestador</div>
                <div className="role-sub">Ofrezco mis servicios</div>
              </div>
            </div>

            {role === 'provider' && (
              <div className="banner">
                 ¡Al registrarte recibís 10 créditos gratis para enviar tus primeros presupuestos!
              </div>
            )}
          </>
        )}

        <h2 className="title">{mode === 'login' ? '¡Hola de nuevo!' : 'Crea tu cuenta'}</h2>
        {mode === 'login' && (
          <p className="subtitle">
            Ingresá tus credenciales para acceder a tus presupuestos y servicios.
          </p>
        )}

        <div className="oauth-row">
          <button className="oauth-btn" type="button" disabled>
           <FcGoogle size={18} /> Google
          </button>
          <button className="oauth-btn" type="button" disabled>
           <FaApple size={18} /> Apple
          </button>
        </div>

        <div className="divider">O MEDIANTE CORREO</div>

        {error && <div className="error">{error}</div>}

        <form onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div className="field">
              <label>Nombre y Apellido</label>
              <div className="input-wrap">
                <span className="icon-left">
                    <User size={16} />
                    </span>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="ej: Pedro González"
                  required
                />
              </div>
            </div>
          )}

          <div className="field">
            <label>Correo Electrónico</label>
            <div className="input-wrap">
              <span className="icon-left">
              <Mail size={16} />
                </span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nombre@ejemplo.com"
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="field">
            <div className="field-header">
              <label>Contraseña</label>
              {mode === 'login' && (
                <button type="button" className="link">¿La olvidaste?</button>
              )}
            </div>
            <div className="input-wrap">
              <span className="icon-left">
              <Lock size={16} />
              </span>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
              />
                <button
                  type="button"
                  className="icon-right"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
            </div>
          </div>

          {mode === 'login' ? (
            <div className="checkbox-row">
              <input type="checkbox" id="remember" />
              <label htmlFor="remember">Mantener mi sesión iniciada en este dispositivo</label>
            </div>
          ) : (
            <div className="checkbox-row">
              <input
                type="checkbox"
                id="terms"
                checked={acceptedTerms}
                onChange={(e) => setAcceptedTerms(e.target.checked)}
              />
              <label htmlFor="terms">
                Acepto los <a href="#" className="link">Términos de Servicio</a> y{' '}
                <a href="#" className="link">Políticas de Privacidad</a>.
              </label>
            </div>
          )}

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading
              ? 'Cargando...'
              : mode === 'login' ? 'Iniciar Sesión →' : 'Crear mi cuenta →'}
          </button>
        </form>

        <p className="footer-text">
          Tus datos personales nunca se compartirán sin tu permiso previo.
        </p>
      </div>
    </div>
  );
}