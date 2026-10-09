import { useEffect, useState } from 'react';
import { Calendar, Camera, MapPin, Pencil, Plus, Star } from 'lucide-react';
import { perfilApi } from '../../services/perfilService';
import EditarPerfilModal from './EditarPerfilModal';
import PortfolioUploader from './PortfolioUploader';
import './perfil.css';

const iniciales = (full = '') => { const p = full.trim().split(/\s+/); return ((p[0]?.[0] ?? '') + (p.length > 1 ? p[p.length - 1][0] : '')).toUpperCase(); };
const mesAnio = (iso) => new Intl.DateTimeFormat('es-AR', { month: 'long', year: 'numeric' }).format(new Date(iso))
  .replace(/^./, (c) => c.toUpperCase()).replace(' de ', ' ');

export default function PerfilPage() {
  const [perfil, setPerfil] = useState(null);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(null);
  const [verTodas, setVerTodas] = useState(false);

  useEffect(() => { perfilApi.obtener().then(setPerfil).catch((e) => setError(e.message)); }, []);

  if (error) return <p className="err" role="alert">{error}</p>;
  if (!perfil) return <div className="perfil-card skeleton" aria-busy="true" />;

  const { usuario, prestador, fotos, rating, zonas } = perfil;
  const visibles = verTodas ? fotos : fotos.slice(0, 3);
  const resto = fotos.length - 3;

  return (
    <article className="perfil-card">
      <div className="cover"><button className="btn sm"><Camera size={14} /> Editar portada</button></div>
      <div className="head">
        <div className="avatar">{usuario.foto_perfil ? <img src={usuario.foto_perfil} alt="" /> : iniciales(usuario.nombre_apellido)}
          <button className="icon-btn cam" aria-label="Cambiar foto de perfil"><Camera size={12} /></button></div>
        <div className="actions">
          <button className="btn primary" onClick={() => setModal('fotos')}><Plus size={16} /> Agregar al portafolio</button>
          <button className="btn" onClick={() => setModal('editar')}><Pencil size={14} /> Editar perfil</button>
        </div>
      </div>

      <div className="body">
        <h1>{usuario.nombre_apellido}</h1>
        <p className="oficio">{perfil.categoria}{prestador.matricula ? ' Matriculado' : ''}</p>
        <p className="meta"><Star size={14} fill="#f59e0b" stroke="#f59e0b" />
          <b className="rating">{rating.promedio?.toFixed(1) ?? '–'}</b> ({rating.total} opiniones de clientes)</p>
        <p className="meta"><Calendar size={14} /> Se unió en {mesAnio(usuario.fecha_registro)}</p>
        <p className="meta"><MapPin size={14} /> Ofrece servicios en <b>{zonas.map((z) => z.nombre).join(', ') || 'sin definir'}</b></p>
        <p className="bio">{prestador.biografia || 'Todavía no agregaste una descripción.'}</p>

        <section className="fotos">
          <div className="row"><h2>Fotos de trabajos</h2>
            {fotos.length > 3 && <button className="perfil-link" onClick={() => setVerTodas(!verTodas)}>{verTodas ? 'Ver menos' : 'Ver todas'}</button>}</div>
          {fotos.length === 0
            ? <p className="vacio">Subí fotos de tus trabajos para generar confianza con los clientes.</p>
            : <div className="grid">{visibles.map((f, i) => (
                <figure key={f.id_foto}><img src={f.url_imagen} alt={f.descripcion ?? 'Trabajo realizado'} loading="lazy" />
                  {!verTodas && i === 2 && resto > 0 && <span className="mas">+{resto}</span>}</figure>))}</div>}
        </section>
      </div>

      {modal === 'editar' && <EditarPerfilModal perfil={perfil} onClose={() => setModal(null)} onSaved={setPerfil} />}
      {modal === 'fotos' && <PortfolioUploader onClose={() => setModal(null)}
        onUploaded={(n) => setPerfil({ ...perfil, fotos: [...n, ...perfil.fotos] })} />}
    </article>
  );
}

