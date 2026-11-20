import { useEffect, useState } from 'react';
import { ArrowLeft, MapPin, Star } from 'lucide-react';
import { perfilApi } from '../services/perfilService';
import './perfilPrestadorPublico.css';

const iniciales = (nombre = '', apellido = '') => `${nombre[0] ?? ''}${apellido[0] ?? ''}`.toUpperCase();
const fechaMiembro = (fecha) => {
  if (!fecha) return null;
  const parsed = new Date(fecha);
  if (Number.isNaN(parsed.getTime())) return null;
  return new Intl.DateTimeFormat('es-AR', { month: 'long', year: 'numeric' }).format(parsed);
};

function Estrellas({ valor = 0 }) {
  return (
    <span className="perfil-publico-estrellas" aria-label={`${Number(valor || 0).toFixed(1)} de 5 estrellas`}>
      {[1, 2, 3, 4, 5].map((estrella) => (
        <Star
          key={estrella}
          size={15}
          fill={estrella <= Math.round(Number(valor) || 0) ? 'currentColor' : 'none'}
        />
      ))}
    </span>
  );
}

export default function PerfilPrestadorPublicoPage({ idPrestador, onVolver }) {
  const [perfil, setPerfil] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let vigente = true;
    perfilApi.obtenerPrestador(idPrestador)
      .then((resultado) => { if (vigente) setPerfil(resultado); })
      .catch((e) => { if (vigente) setError(e.message || 'No se pudo cargar el perfil.'); });
    return () => { vigente = false; };
  }, [idPrestador]);

  useEffect(() => {
    const alPresionarEscape = (event) => {
      if (event.key === 'Escape') onVolver();
    };
    window.addEventListener('keydown', alPresionarEscape);
    return () => window.removeEventListener('keydown', alPresionarEscape);
  }, [onVolver]);

  const fecha = fechaMiembro(perfil?.usuario?.fecha_registro);

  return (
    <article className="perfil-publico-pagina">
      <header className="perfil-publico-nav">
        <button type="button" onClick={onVolver}>
          <ArrowLeft size={16} /> Volver
        </button>
        <span>Perfil del prestador</span>
      </header>

      {error ? (
        <p className="perfil-publico-error" role="alert">{error}</p>
      ) : !perfil ? (
        <p className="perfil-publico-cargando" aria-busy="true">Cargando perfil…</p>
      ) : (
        <>
          <div className="perfil-publico-portada" />
          <div className="perfil-publico-avatar-wrap">
            <div className="perfil-publico-avatar">
              {perfil.usuario.foto_perfil
                ? <img src={perfil.usuario.foto_perfil} alt="" />
                : iniciales(perfil.usuario.nombre, perfil.usuario.apellido)}
            </div>
          </div>

          <div className="perfil-publico-contenido">
            <h1 id="perfil-publico-titulo">
              {perfil.usuario.nombre} {perfil.usuario.apellido}
            </h1>
            <p className="perfil-publico-oficio">{perfil.categoria}</p>
            <div className="perfil-publico-rating">
              <Estrellas valor={perfil.rating?.promedio} />
              <b>{Number(perfil.rating?.promedio || 0).toFixed(1).replace('.', ',')}</b>
              <span>({perfil.rating?.total ?? 0} calificaciones)</span>
            </div>
            {fecha && <p className="perfil-publico-meta">En UberOficios desde {fecha}</p>}
            {perfil.prestador.zona && (
              <p className="perfil-publico-meta"><MapPin size={14} /> Ofrece servicios en {perfil.prestador.zona}</p>
            )}
            {perfil.prestador.matricula && <p className="perfil-publico-meta">Cuenta con matrícula profesional</p>}
            <p className="perfil-publico-bio">
              {perfil.prestador.biografia || 'Todavía no agregó una descripción.'}
            </p>

            <section className="perfil-publico-seccion">
              <h2>Fotos de trabajos</h2>
              {perfil.fotos?.length ? (
                <div className="perfil-publico-fotos">
                  {perfil.fotos.map((foto) => (
                    <figure key={foto.id_foto}>
                      <img src={foto.url_imagen} alt={foto.descripcion || 'Trabajo realizado'} />
                      {foto.descripcion && <figcaption>{foto.descripcion}</figcaption>}
                    </figure>
                  ))}
                </div>
              ) : (
                <p className="perfil-publico-vacio">Todavía no agregó fotos de trabajos.</p>
              )}
            </section>

            <section className="perfil-publico-seccion">
              <h2>Opiniones de clientes</h2>
              {perfil.calificaciones?.length ? (
                <ul className="perfil-publico-opiniones">
                  {perfil.calificaciones.map((calificacion) => (
                    <li key={calificacion.id_calificacion}>
                      <div>
                        <b>{calificacion.cliente.nombre} {calificacion.cliente.apellido}</b>
                        <Estrellas valor={calificacion.puntuacion} />
                      </div>
                      {calificacion.comentario && <p>{calificacion.comentario}</p>}
                      {calificacion.url_comprobante && (
                        <a
                          className="perfil-publico-comprobante"
                          href={calificacion.url_comprobante}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <img src={calificacion.url_comprobante} alt="Foto comprobante del trabajo" />
                          <span>Ver foto comprobante</span>
                        </a>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="perfil-publico-vacio">Todavía no recibió calificaciones.</p>
              )}
            </section>
          </div>
        </>
      )}
    </article>
  );
}
