import { useEffect, useRef, useState } from 'react';
import { Bell, ClipboardList, Home, LogOut, Pencil, RefreshCw, Search, Settings } from 'lucide-react';
import { perfilApi } from '../services/perfilService';
import './AppLayout.css';

const iniciales = (full = '') => { const p = full.trim().split(/\s+/); return ((p[0]?.[0] ?? '') + (p.length > 1 ? p[p.length - 1][0] : '')).toUpperCase(); };

export default function AppLayout({ children, onLogout, onSwitchRole }) {
  const [yo, setYo] = useState(null);
  const [menu, setMenu] = useState(false);
  const ref = useRef(null);

  useEffect(() => { perfilApi.yo().then(setYo).catch(() => {}); }, []);
  useEffect(() => {
    const fuera = (e) => ref.current && !ref.current.contains(e.target) && setMenu(false);
    const esc = (e) => e.key === 'Escape' && setMenu(false);
    document.addEventListener('mousedown', fuera); document.addEventListener('keydown', esc);
    return () => { document.removeEventListener('mousedown', fuera); document.removeEventListener('keydown', esc); };
  }, []);

  const nombre = yo?.nombre_apellido ?? 'Mi cuenta';
  const ini = iniciales(yo?.nombre_apellido) || '·';

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
              <div className="lay-cur"><span className="lay-av">{ini}</span><div><b>{nombre}</b><small>Perfil de Prestador</small></div></div>
              <button role="menuitem" className="lay-item" onClick={() => { setMenu(false); onSwitchRole?.(); }}>
                <span className="lay-circ"><RefreshCw size={14} /></span>
                <div><b>Cambiar a Cliente</b><small>Buscar y contratar servicios</small></div></button>
              <hr />
              <button role="menuitem" className="lay-item sm"><span className="lay-circ"><Settings size={13} /></span><b>Configuración y privacidad</b></button>
              <button role="menuitem" className="lay-item sm" onClick={onLogout}><span className="lay-circ"><LogOut size={13} /></span><b>Cerrar sesión</b></button>
            </div>
          )}
        </div>
      </header>

      <div className="lay-body">
        <nav className="lay-side" aria-label="Principal">
          <div className="lay-me"><span className="lay-av">{ini}</span><b>{nombre}</b></div>
          <a className="lay-link"><Home size={16} color="#2563eb" /> Inicio</a>
          <a className="lay-link"><ClipboardList size={16} color="#059669" /> Mis Presupuestos</a>
        </nav>
        <main>{children}</main>
        <aside className="lay-act"><h3>ACTIVIDAD RECIENTE</h3><p>No hay novedades por el momento.</p></aside>
      </div>
    </div>
  );
}
