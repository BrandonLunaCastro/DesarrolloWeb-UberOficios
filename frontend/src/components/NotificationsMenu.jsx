import { useEffect, useRef, useState } from 'react';
import { Bell, Briefcase, ClipboardList, MessageSquare } from 'lucide-react';
import { notificacionesApi } from '../services/notificacionesService';
import './NotificationsMenu.css';

// destino = pantalla a la que lleva (la que se pasa a onNavigate). "presupuesto" todavía no tiene pantalla.
const TIPOS = {
  mensaje: { Icono: MessageSquare, color: '#d97706', destino: 'chat' },
  presupuesto: { Icono: ClipboardList, color: '#059669' },
  aviso: { Icono: Briefcase, color: '#2563eb', destino: 'feed' },
};

function hace(iso) {
  const min = Math.round((Date.now() - new Date(iso)) / 60000);
  if (min < 1) return 'ahora';
  if (min < 60) return `hace ${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `hace ${h} h`;
  const d = Math.round(h / 24);
  return d === 1 ? 'ayer' : `hace ${d} días`;
}

export default function NotificationsMenu({ onNavigate, onOpen, onUnauthorized }) {
  const [lista, setLista] = useState(null); // null = todavía sin datos
  const [error, setError] = useState(null);
  const [abierto, setAbierto] = useState(false);
  const ref = useRef(null);

  // Carga al montar (para saber si hay sin leer) y se actualiza cada 60 s
  useEffect(() => {
    let vivo = true;
    const cargar = () =>
      notificacionesApi.listar()
        .then((l) => { if (vivo) { setLista(l); setError(null); } })
        .catch((e) => { if (!vivo) return; if (e.status === 401) onUnauthorized?.(); setError(e); });
    cargar();
    const t = setInterval(cargar, 60000);
    return () => { vivo = false; clearInterval(t); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const fuera = (e) => ref.current && !ref.current.contains(e.target) && setAbierto(false);
    const esc = (e) => e.key === 'Escape' && setAbierto(false);
    document.addEventListener('mousedown', fuera);
    document.addEventListener('keydown', esc);
    return () => { document.removeEventListener('mousedown', fuera); document.removeEventListener('keydown', esc); };
  }, []);

  const noLeidas = lista ? lista.filter((n) => !n.leida).length : 0;

  const alternar = () => { if (!abierto) onOpen?.(); setAbierto(!abierto); };
  const reintentar = () => { setError(null); notificacionesApi.listar().then(setLista).catch(setError); };
  const marcarTodas = () => {
    setLista((p) => p.map((n) => ({ ...n, leida: true })));
    notificacionesApi.marcarTodasLeidas().catch(() => {});
  };
  const abrirNotificacion = (n) => {
    if (!n.leida) {
      setLista((p) => p.map((x) => (x.id === n.id ? { ...x, leida: true } : x)));
      notificacionesApi.marcarLeida(n.id).catch(() => {});
    }
    setAbierto(false);
    const destino = TIPOS[n.tipo]?.destino;
    if (destino) onNavigate?.(destino);
  };

  return (
    <div className="nt" ref={ref}>
      <button className="lay-ic" aria-haspopup="true" aria-expanded={abierto}
        aria-label={noLeidas ? `Notificaciones (${noLeidas} sin leer)` : 'Notificaciones'} onClick={alternar}>
        <Bell size={15} />{noLeidas > 0 && <i className="lay-dot" />}
      </button>

      {abierto && (
        <div className="nt-panel" role="region" aria-label="Notificaciones">
          <header>
            <b>Notificaciones</b>
            {noLeidas > 0 && <button className="nt-link" onClick={marcarTodas}>Marcar todas como leídas</button>}
          </header>
          {lista === null && error ? (
            <div className="nt-msg" role="alert"><p>No se pudieron cargar las notificaciones.</p><button className="nt-link" onClick={reintentar}>Reintentar</button></div>
          ) : lista === null ? (
            <div className="nt-msg" aria-busy="true">Cargando…</div>
          ) : lista.length === 0 ? (
            <div className="nt-msg">No tenés notificaciones por el momento.</div>
          ) : (
            <ul>
              {lista.map((n) => {
                const { Icono, color } = TIPOS[n.tipo] ?? { Icono: Bell, color: '#64748b' };
                return (
                  <li key={n.id}>
                    <button className={`nt-item ${n.leida ? '' : 'nueva'}`} onClick={() => abrirNotificacion(n)}>
                      <span className="nt-ic" style={{ color }}><Icono size={15} /></span>
                      <span className="nt-txt"><span>{n.texto}</span><small>{hace(n.fecha)}</small></span>
                      {!n.leida && <i className="nt-punto" aria-label="Sin leer" />}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
