import { useEffect, useState } from 'react';
import { Calendar, MapPin, Pencil, Star } from 'lucide-react';
import { perfilApi } from '../../services/perfilService';
import EditarPerfilModal from './EditarPerfilModal';
import CompraCreditos from './CompraCreditos';
import './perfil.css';

const iniciales = (n = '', a = '') => `${n[0] ?? ''}${a[0] ?? ''}`.toUpperCase();
const fechaCorta = (iso) => new Intl.DateTimeFormat('es-AR', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(iso));
const nombreCorto = (c) => (c ? `${c.nombre ?? ''} ${(c.apellido ?? '')[0] ? `${c.apellido[0]}.` : ''}`.trim() : '') || 'Cliente';

// Cinco estrellas grises con una capa amarilla encima cuyo ancho depende del promedio (ej.: 4,3 => 86 %).
function Estrellas({ valor = 0, size = 16 }) {
  const pct = Math.max(0, Math.min(5, Number(valor) || 0)) / 5 * 100;
  const fila = (color) => [1, 2, 3, 4, 5].map((n) => <Star key={n} size={size} fill={color} stroke={color} />);
  return (
    <span className="estrellas" role="img" aria-label={`${Number(valor || 0).toFixed(1)} de 5 estrellas`}>
      <span className="estrellas-base">{fila('#e2e8f0')}</span>
      <span className="estrellas-fill" style={{ width: `${pct}%` }}>{fila('#f59e0b')}</span>
    </span>
  );
}

const mesAnio = (iso) => new Intl.DateTimeFormat('es-AR', { month: 'long', year: 'numeric' }).format(new Date(iso))
  .replace(/^./, (c) => c.toUpperCase()).replace(' de ', ' ');

export default function PerfilPage() {
  const [perfil, setPerfil] = useState(null);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(null);

  useEffect(() => {
    const cargar = () => perfilApi.obtener().then(setPerfil).catch((e) => setError(e.message));
    cargar();
    // Si llega una calificación nueva mientras el perfil está abierto, se actualiza al volver a esta pestaña.
    const alVolver = () => { if (document.visibilityState === 'visible') cargar(); };
    document.addEventListener('visibilitychange', alVolver);
    return () => document.removeEventListener('visibilitychange', alVolver);
  }, []);

  if (error) return <p className="err" role="alert">{error}</p>;
  if (!perfil) return <div className="perfil-card skeleton" aria-busy="true" />;

  const { usuario, prestador, zonas } = perfil;
  const calificaciones = perfil.calificaciones ?? [];
  const rating = perfil.rating ?? { promedio: 0, total: calificaciones.length };
  const hayOpiniones = rating.total > 0;

  return (
    <article className="perfil-card">
      <div className="cover" />
      <div className="head">
        <div className="avatar">{usuario.foto_perfil ? <img src={usuario.foto_perfil} alt="" /> : iniciales(usuario.nombre, usuario.apellido)}</div>
        <div className="actions">
          <button className="btn" onClick={() => setModal('editar')}><Pencil size={14} /> Editar perfil</button>
        </div>
      </div>

      <div className="body">
        <h1>{usuario.nombre} {usuario.apellido}</h1>
        <p className="oficio">{perfil.categoria}{prestador.matricula ? ' Matriculado' : ''}</p>
        <p className="meta">
          <Estrellas valor={rating.promedio} />
          <b className="rating">{hayOpiniones ? Number(rating.promedio).toFixed(1).replace('.', ',') : '–'}</b>
          {' '}({rating.total} {rating.total === 1 ? 'opinión' : 'opiniones'} de clientes)
        </p>
        <p className="meta"><Calendar size={14} /> Se unió en {mesAnio(usuario.fecha_registro)}</p>
        <p className="meta"><MapPin size={14} /> Ofrece servicios en <b>{zonas.map((z) => z.nombre).join(', ') || 'sin definir'}</b></p>
        <p className="bio">{prestador.biografia || 'Todavía no agregaste una descripción.'}</p>

        <section className="opiniones" aria-labelledby="titulo-opiniones">
          <div className="row"><h2 id="titulo-opiniones">Opiniones de clientes</h2></div>
          {hayOpiniones && (
            <div className="resumen-rating">
              <b className="rating-grande">{Number(rating.promedio).toFixed(1).replace('.', ',')}</b>
              <div>
                <Estrellas valor={rating.promedio} size={18} />
                <p className="vacio">{rating.total} {rating.total === 1 ? 'calificación recibida' : 'calificaciones recibidas'}</p>
              </div>
            </div>
          )}
          {calificaciones.length === 0 ? (
            <p className="vacio">{hayOpiniones ? 'Los clientes todavía no dejaron comentarios.' : 'Todavía no recibiste calificaciones. Aparecerán acá cuando un cliente califique un trabajo.'}</p>
          ) : (
            <ul className="lista-opiniones">
              {calificaciones.map((c) => (
                <li key={c.id_calificacion} className="opinion">
                  <div className="row">
                    <b>{nombreCorto(c.cliente)}</b>
                    <time dateTime={c.fecha}>{fechaCorta(c.fecha)}</time>
                  </div>
                  <Estrellas valor={c.puntuacion} size={13} />
                  {c.comentario && <p>{c.comentario}</p>}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="fotos">
          <div className="row"><h2>Fotos de trabajos</h2></div>
          <p className="vacio">La carga de fotos de trabajos todavía no está disponible.</p>
        </section>
        <CompraCreditos />
      </div>

      {modal === 'editar' && <EditarPerfilModal perfil={perfil} onClose={() => setModal(null)} onSaved={setPerfil} />}
    </article>
  );
}
