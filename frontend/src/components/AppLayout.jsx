import { useEffect, useRef, useState } from 'react';
import './AppLayout.css';
import { ClipboardList, Coins, Home, LogOut, MessageSquare, RefreshCw, Settings, User } from 'lucide-react';
import NotificationsMenu from './NotificationsMenu';

const iniciales = (n = '', a = '') => `${n[0] ?? ''}${a[0] ?? ''}`.toUpperCase();

// vista: 'CLIENTE' | 'PRESTADOR' (qué pantalla está viendo).
export default function AppLayout({ children, usuario, onLogout, onSwitchRole, vista = 'PRESTADOR', pantalla, onNavigate }) {
  const esCliente = vista === 'CLIENTE';
  const [menu, setMenu] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const fuera = (e) => ref.current && !ref.current.contains(e.target) && setMenu(false);
    const esc = (e) => e.key === 'Escape' && setMenu(false);
    document.addEventListener('mousedown', fuera); document.addEventListener('keydown', esc);
    return () => { document.removeEventListener('mousedown', fuera); document.removeEventListener('keydown', esc); };
  }, []);

  const nombre = usuario ? `${usuario.nombre} ${usuario.apellido}` : 'Mi cuenta';
  const ini = iniciales(usuario?.nombre, usuario?.apellido) || '·';

  return (
    <div className="lay">
      <header className="lay-top">
        <span className="lay-logo">OficiosYa</span>
        <div className="lay-tools" ref={ref}>
         <NotificationsMenu onNavigate={onNavigate} onOpen={() => setMenu(false)} onUnauthorized={onLogout} />          <button className="lay-av" aria-haspopup="menu" aria-expanded={menu} aria-label="Menú de usuario" onClick={() => setMenu(!menu)}>{ini}</button>
          {menu && (
            <div className="lay-menu" role="menu">
              <div className="lay-cur"><span className="lay-av">{ini}</span><div><b>{nombre}</b><small>{esCliente ? 'Perfil de Cliente' : 'Perfil de Prestador'}</small></div></div>
              <button role="menuitem" className="lay-item" onClick={() => { setMenu(false); onSwitchRole?.(); }}>
                <span className="lay-circ"><RefreshCw size={14} /></span>
                <div><b>{esCliente ? 'Cambiar a Prestador de Servicios' : 'Cambiar a Cliente'}</b><small>{esCliente ? 'Gestionar presupuestos y saldo' : 'Buscar y contratar servicios'}</small></div></button>
              <hr />
              <button role="menuitem" className="lay-item sm"><span className="lay-circ"><Settings size={13} /></span><b>Configuración y privacidad</b></button>
              <button role="menuitem" className="lay-item sm" onClick={onLogout}><span className="lay-circ"><LogOut size={13} /></span><b>Cerrar sesión</b></button>
            </div>
          )}
        </div>
      </header>

            <div className="lay-body">
        <nav className="lay-side" aria-label="Principal">
          <button type="button" className="lay-me" onClick={() => onNavigate?.(esCliente ? 'perfilCliente' : 'perfilPrestador')} aria-label="Ver mi perfil"><span className="lay-av">{ini}</span><b>{nombre}</b></button>
          <a className={`lay-link ${pantalla === 'feed' ? 'active' : ''}`} onClick={() => onNavigate?.('feed')}><Home size={16} color="#2563eb" /> Inicio</a>
          {!esCliente && <a className={`lay-link ${pantalla === 'perfilPrestador' ? 'active' : ''}`} onClick={() => onNavigate?.('perfilPrestador')}><User size={16} color="#7c3aed" /> Mi Perfil</a>}
          <a className={`lay-link ${pantalla === 'presupuestos' ? 'active' : ''}`} onClick={() => onNavigate?.('presupuestos')}><ClipboardList size={16} color="#059669" /> Mis Presupuestos</a>
          {!esCliente && <a className={`lay-link ${pantalla === 'creditos' ? 'active' : ''}`} onClick={() => onNavigate?.('creditos')}><Coins size={16} color="#d97706" /> Mis Créditos</a>}
          <a className={`lay-link ${pantalla === 'chat' ? 'active' : ''}`} onClick={() => onNavigate?.('chat')}><MessageSquare size={16} color="#d97706" /> Mensajes</a>
        </nav>
        <main>{children}</main>
      </div>
    </div>
  );
}
