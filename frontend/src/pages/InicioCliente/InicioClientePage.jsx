import { useEffect, useState } from 'react';
import { MapPin } from 'lucide-react';
import { avisosApi } from '../../services/avisosService';
import { notificacionesApi } from '../../services/notificacionesService';
import { presupuestosApi } from '../../services/presupuestosService';
import { SERVICIOS_RAPIDOS } from '../../constants/catalogos';
import CalificacionModal from '../Calificacion/CalificacionModal';
import PublicarSolicitudModal from './PublicarSolicitudModal';
import '../Calificacion/calificacion.css';
import './inicioCliente.css';

// Pantalla "Cliente - Inicio" del Figma: buscador + PUBLICAR GRATIS, servicios rápidos y seguimiento de avisos.
export default function InicioClientePage({ usuario, onUnauthorized }) {
  const [texto, setTexto] = useState('');
  const [modal, setModal] = useState(null); // null | { oficio, descripcion }
  const [publicados, setPublicados] = useState(null);
  const [errorAvisos, setErrorAvisos] = useState('');
  const [pendientes, setPendientes] = useState(null);
  const [errorPendientes, setErrorPendientes] = useState('');
  const [calificando, setCalificando] = useState(null);
  const [enviandoCalificacion, setEnviandoCalificacion] = useState(false);
  const [errorCalificacion, setErrorCalificacion] = useState('');

  useEffect(() => {
    let vivo = true;
    avisosApi.listarMios()
      .then((avisos) => vivo && setPublicados(avisos))
      .catch((error) => {
        if (!vivo) return;
        if (error.status === 401) {
          onUnauthorized?.();
          return;
        }
        setErrorAvisos(error.message);
      });
    return () => { vivo = false; };
  }, [onUnauthorized]);

  useEffect(() => {
    let vivo = true;
    const cargarPendientes = () => {
      presupuestosApi.listarCalificacionesPendientes()
        .then((items) => {
          if (!vivo) return;
          setPendientes(items);
          setErrorPendientes('');
        })
        .catch((error) => {
          if (!vivo) return;
          if (error.status === 401) {
            onUnauthorized?.();
            return;
          }
          setErrorPendientes(error.message);
        });
    };

    cargarPendientes();
    const cancelarRealtime = notificacionesApi.suscribir((evento) => {
      if (
        evento.type === 'calificacion_pendiente_nueva'
        || evento.type === 'calificacion_completada'
        || evento.type === 'conectado'
      ) {
        cargarPendientes();
      }
    });
    return () => {
      vivo = false;
      cancelarRealtime();
    };
  }, [onUnauthorized]);

  const abrir = (datos = {}) => setModal({ oficio: '', descripcion: '', ...datos });

  const enviarCalificacion = async ({ puntuacion, comentario, fotoComprobante }) => {
    setEnviandoCalificacion(true);
    setErrorCalificacion('');
    try {
      await presupuestosApi.calificar(calificando.id_postulacion, {
        puntuacion,
        comentario,
        fotoComprobante,
      });
      setPendientes((items) => items.filter(
        (item) => item.id_postulacion !== calificando.id_postulacion,
      ));
      setCalificando(null);
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized?.();
        return;
      }
      setErrorCalificacion(error.message);
    } finally {
      setEnviandoCalificacion(false);
    }
  };

  return (
    <section className="ic">
      <form className="ic-hero" onSubmit={(e) => { e.preventDefault(); abrir({ descripcion: texto.trim() }); }}>
        <h2>{`¿Qué necesitás solucionar${usuario?.nombre ? `, ${usuario.nombre}` : ''}?`}</h2>
        <p>Publicá tu problema y recibí presupuestos de profesionales de tu zona.</p>
        <div className="ic-bar">
          <input value={texto} onChange={(e) => setTexto(e.target.value)} aria-label="Qué necesitás"
            placeholder="Escribí acá lo que necesitás (ej. Fuga de agua)..." />
          <button type="submit">PUBLICAR</button>
        </div>
      </form>

      <h3 className="ic-sub">SERVICIOS RÁPIDOS</h3>
      <div className="ic-rapidos">
        {SERVICIOS_RAPIDOS.map((s) => (
          <button key={s.oficio} onClick={() => abrir({ oficio: s.oficio })}><span aria-hidden>{s.emoji}</span>{s.oficio}</button>
        ))}
      </div>

      <section className="ic-pendientes" aria-labelledby="ic-pendientes-titulo">
        <h3 className="ic-sub" id="ic-pendientes-titulo">CALIFICACIONES PENDIENTES</h3>
        {errorPendientes ? (
          <p className="feed-msg" role="alert">{errorPendientes}</p>
        ) : pendientes === null ? (
          <p className="feed-msg" aria-busy="true">Revisando trabajos para calificar…</p>
        ) : pendientes.length === 0 ? (
          <p className="feed-msg">No tenés trabajos pendientes de calificación.</p>
        ) : (
          <div className="ic-pendientes-lista">
            {pendientes.map((pendiente) => (
              <article className="ic-pendiente" key={pendiente.id_postulacion}>
                <div>
                  <strong>{pendiente.titulo}</strong>
                  <p>Trabajo realizado por {pendiente.nombre_prestador}</p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setErrorCalificacion('');
                    setCalificando(pendiente);
                  }}
                >
                  Calificar trabajo
                </button>
              </article>
            ))}
          </div>
        )}
      </section>

      <h3 className="ic-sub">SEGUIMIENTO DE AVISOS</h3>
      {errorAvisos ? (
        <p className="feed-msg" role="alert">{errorAvisos}</p>
      ) : publicados === null ? (
        <p className="feed-msg" aria-busy="true">Cargando tus avisos…</p>
      ) : publicados.length === 0 ? (
        <p className="feed-msg">Todavía no publicaste ninguna solicitud.</p>
      ) : (
        <div className="feed-list">
          {publicados.map((a) => (
            <article key={a.id_aviso} className="ic-card">
              <div className="ic-top">
                <span className="ic-tag">{a.oficio}</span>
                <span className={`ic-activa${a.estado === 'abierto' ? '' : ' cerrada'}`}>
                  ● {({
                    abierto: 'Activa',
                    en_proceso: 'En proceso',
                    finalizado: 'Completado',
                    expirado: 'Expirado',
                    cancelado: 'Cancelado',
                  })[a.estado] || a.estado}
                </span>
              </div>
              <b>{a.descripcion.length > 60 ? `${a.descripcion.slice(0, 60)}…` : a.descripcion}</b>
              <p>{a.descripcion}</p>
              <small><MapPin size={12} /> {a.zona} · Publicado hace un momento</small>
            </article>
          ))}
        </div>
      )}

      {modal && (
        <PublicarSolicitudModal
          telefono={usuario?.telefono ?? ''}
          oficioInicial={modal.oficio}
          descripcionInicial={modal.descripcion}
          onClose={() => setModal(null)}
          onSuccess={(a) => {
            setErrorAvisos('');
            setPublicados((p) => [a, ...(p ?? [])]);
          }}
          onUnauthorized={onUnauthorized}
        />
      )}
      {calificando && (
        <CalificacionModal
          aviso={{ titulo: calificando.titulo }}
          propuesta={{ nombre: calificando.nombre_prestador }}
          enviando={enviandoCalificacion}
          error={errorCalificacion}
          onEnviar={enviarCalificacion}
          onCerrar={() => setCalificando(null)}
        />
      )}
    </section>
  );
}
