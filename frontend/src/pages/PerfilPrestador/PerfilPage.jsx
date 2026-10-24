import { useEffect, useState } from 'react';
import { Calendar, MapPin, Pencil, Star } from 'lucide-react';
import { perfilApi } from '../../services/perfilService';
import EditarPerfilModal from './EditarPerfilModal';
import './perfil.css';

const iniciales = (n = '', a = '') => `${n[0] ?? ''}${a[0] ?? ''}`.toUpperCase();
const mesAnio = (iso) => new Intl.DateTimeFormat('es-AR', { month: 'long', year: 'numeric' }).format(new Date(iso))
  .replace(/^./, (c) => c.toUpperCase()).replace(' de ', ' ');

export default function PerfilPage() {
  const [perfil, setPerfil] = useState(null);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(null);

  useEffect(() => { perfilApi.obtener().then(setPerfil).catch((e) => setError(e.message)); }, []);

  if (error) return <p className="err" role="alert">{error}</p>;
  if (!perfil) return <div className="perfil-card skeleton" aria-busy="true" />;

  const { usuario, prestador, rating, zonas } = perfil;

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
        <p className="meta"><Star size={14} fill="#f59e0b" stroke="#f59e0b" />
          <b className="rating">{rating.promedio?.toFixed(1) ?? '–'}</b> ({rating.total} opiniones de clientes)</p>
        <p className="meta"><Calendar size={14} /> Se unió en {mesAnio(usuario.fecha_registro)}</p>
        <p className="meta"><MapPin size={14} /> Ofrece servicios en <b>{zonas.map((z) => z.nombre).join(', ') || 'sin definir'}</b></p>
        <p className="bio">{prestador.biografia || 'Todavía no agregaste una descripción.'}</p>

        <section className="fotos">
          <div className="row"><h2>Fotos de trabajos</h2></div>
          <p className="vacio">La carga de fotos de trabajos todavía no está disponible.</p>
        </section>
      </div>

      {modal === 'editar' && <EditarPerfilModal perfil={perfil} onClose={() => setModal(null)} onSaved={setPerfil} />}
    </article>
  );
}
