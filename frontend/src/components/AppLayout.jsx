import { useEffect, useRef, useState } from 'react';
import { avisosApi } from '../services/avisosService';
import './AppLayout.css';
import { Bell, ClipboardList, Home, LogOut, MessageSquare, Pencil, RefreshCw, Search, Settings, User } from 'lucide-react';

const iniciales = (n = '', a = '') => `${n[0] ?? ''}${a[0] ?? ''}`.toUpperCase();

// vista: 'CLIENTE' | 'PRESTADOR' (qué pantalla está viendo). onNavigate('feed' | 'perfilPrestador').
export default function AppLayout({ children, onLogout, onSwitchRole, vista = 'PRESTADOR', onNavigate }) {
  const esCliente = vista === 'CLIENTE';
  const [yo, setYo] = useState(null);
  const [menu, setMenu] = useState(false);
  const ref = useRef(null);

  useEffect(() => { avisosApi.me().then(setYo).catch(() => {}); }, []);
  useEffect(() => {
    const fuera = (e) => ref.current && !ref.current.contains(e.target) && setMenu(false);
    const esc = (e) => e.key === 'Escape' && setMenu(false);
    document.addEventListener('mousedown', fuera); document.addEventListener('keydown', esc);
    return () => { document.removeEventListener('mousedown', fuera); document.removeEventListener('keydown', esc); };
  }, []);

  const nombre = yo ? `${yo.nombre} ${yo.apellido}` : 'Mi cuenta';
  const ini = iniciales(yo?.nombre, yo?.apellido) || '·';

  return (
    <div className="lay">
      <header className="lay-top">
        <span className="lay-logo">UberOficios</span>
        <label className="lay-search"><Search size={14} />
          <input placeholder="Buscar servicios o profesionales..." aria-label="Buscar" /></label>
        <div className="lay-tools" ref={ref}>
          <button className="lay-ic" aria-label="Editar"><Pencil size={15} /></button>
          <button className="lay-ic" aria-label="Notificaciones"><Bell size={15} /><i className="lay-dot" /></button>
          <button className="lay-av" aria-haspopup="menu" aria-expanded={menu} aria-label="Menú de usuario" onClick={() => setMenu(!menu)}>{ini}</button>
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
          <a className="lay-link" onClick={() => onNavigate?.('feed')}><Home size={16} color="#2563eb" /> Inicio</a>
          {!esCliente && <a className="lay-link" onClick={() => onNavigate?.('perfilPrestador')}><User size={16} color="#7c3aed" /> Mi Perfil</a>}
          <a className="lay-link"><ClipboardList size={16} color="#059669" /> Mis Presupuestos</a>
          <a className="lay-link" onClick={() => onNavigate?.('chat')}><MessageSquare size={16} color="#d97706" /> Mensajes</a>
        </nav>
        <main>{children}</main>
        <aside className="lay-act"><h3>ACTIVIDAD RECIENTE</h3><p>No hay novedades por el momento.</p></aside>
      </div>
    </div>
  );
}
