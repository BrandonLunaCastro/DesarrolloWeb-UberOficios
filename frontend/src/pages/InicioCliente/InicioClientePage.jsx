import { useEffect, useState } from 'react';
import { MapPin } from 'lucide-react';
import { avisosApi } from '../../services/avisosService';
import { SERVICIOS_RAPIDOS } from '../../constants/catalogos';
import PublicarSolicitudModal from './PublicarSolicitudModal';
import './inicioCliente.css';

// Pantalla "Cliente - Inicio" del Figma: buscador + PUBLICAR GRATIS, servicios rápidos y seguimiento de avisos.
export default function InicioClientePage({ onUnauthorized }) {
  const [yo, setYo] = useState(null);
  const [texto, setTexto] = useState('');
  const [modal, setModal] = useState(null); // null | { oficio, descripcion }
  const [publicados, setPublicados] = useState([]); // avisos creados en esta sesión

  useEffect(() => { avisosApi.me().then(setYo).catch(() => {}); }, []);

  const abrir = (datos = {}) => setModal({ oficio: '', descripcion: '', ...datos });

  return (
    <section className="ic">
      <form className="ic-hero" onSubmit={(e) => { e.preventDefault(); abrir({ descripcion: texto.trim() }); }}>
        <h2>{`¿Qué necesitás solucionar${yo?.nombre ? `, ${yo.nombre}` : ''}?`}</h2>
        <p>Publicá tu problema y recibí presupuestos de profesionales de tu zona.</p>
        <div className="ic-bar">
          <input value={texto} onChange={(e) => setTexto(e.target.value)} aria-label="Qué necesitás"
            placeholder="Escribí acá lo que necesitás (ej. Fuga de agua)..." />
          <button type="submit">PUBLICAR GRATIS</button>
        </div>
      </form>

      <h3 className="ic-sub">SERVICIOS RÁPIDOS</h3>
      <div className="ic-rapidos">
        {SERVICIOS_RAPIDOS.map((s) => (
          <button key={s.oficio} onClick={() => abrir({ oficio: s.oficio })}><span aria-hidden>{s.emoji}</span>{s.oficio}</button>
        ))}
      </div>

      <h3 className="ic-sub">SEGUIMIENTO DE AVISOS</h3>
      {publicados.length === 0 ? (
        <p className="feed-msg">Todavía no publicaste ninguna solicitud.</p>
      ) : (
        <div className="feed-list">
          {publicados.map((a) => (
            <article key={a.id_aviso} className="ic-card">
              <div className="ic-top"><span className="ic-tag">{a.oficio}</span><span className="ic-activa">● {a.estado === 'abierto' ? 'Activa' : a.estado}</span></div>
              <b>{a.descripcion.length > 60 ? `${a.descripcion.slice(0, 60)}…` : a.descripcion}</b>
              <p>{a.descripcion}</p>
              <small><MapPin size={12} /> {a.zona} · Publicado hace un momento</small>
            </article>
          ))}
        </div>
      )}

      {modal && (
        <PublicarSolicitudModal
          telefono={yo?.telefono ?? ''}
          oficioInicial={modal.oficio}
          descripcionInicial={modal.descripcion}
          onClose={() => setModal(null)}
          onSuccess={(a) => setPublicados((p) => [a, ...p])}
          onUnauthorized={onUnauthorized}
        />
      )}
    </section>
  );
}
