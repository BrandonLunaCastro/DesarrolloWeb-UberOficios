import { useEffect, useMemo, useState } from 'react';
import { Check, ChevronDown, Clock3, MapPin, Star, X } from 'lucide-react';
import { avisosApi } from '../../services/avisosService';
import { notificacionesApi } from '../../services/notificacionesService';
import { presupuestosApi } from '../../services/presupuestosService';
import PerfilPrestadorPublicoPage from '../../components/PerfilPrestadorPublicoPage';
import CalificacionModal from '../Calificacion/CalificacionModal';
import '../Calificacion/calificacion.css';
import './presupuestosCliente.css';

const normalizarEstado = (estado = '') => estado.trim().toUpperCase();

function fechaLegible(fecha) {
  if (!fecha) return 'Fecha no disponible';
  const parsed = new Date(fecha);
  if (Number.isNaN(parsed.getTime())) return 'Fecha no disponible';
  return parsed.toLocaleString('es-AR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function iniciales(nombre) {
  return nombre
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0])
    .join('')
    .toUpperCase();
}

function agruparPresupuestos(avisos, postulaciones) {
  const porAviso = new Map();
  postulaciones.forEach((postulacion) => {
    const grupo = porAviso.get(postulacion.id_aviso) ?? [];
    grupo.push(postulacion);
    porAviso.set(postulacion.id_aviso, grupo);
  });

  return avisos.map((aviso) => {
    const propuestas = (porAviso.get(aviso.id_aviso) ?? []).map((postulacion) => {
      const nombre = [postulacion.nombre_prestador, postulacion.apellido_prestador]
        .filter(Boolean)
        .join(' ') || 'Prestador';
      return {
        id: postulacion.id_postulacion,
        idPrestador: postulacion.id_prestador,
        idConversacion: postulacion.id_conversacion,
        idCalificacion: postulacion.id_calificacion,
        nombre,
        iniciales: iniciales(nombre),
        oficio: postulacion.oficio_prestador || aviso.oficio,
        precio: Number(postulacion.presupuesto),
        detalle: postulacion.comentario?.trim() || 'El prestador no agregó un comentario.',
        fecha: postulacion.fecha_postulacion,
        fechaOrden: new Date(postulacion.fecha_postulacion).getTime(),
        estado: normalizarEstado(postulacion.estado),
      };
    });
    const precios = propuestas.map((propuesta) => propuesta.precio);
    const aceptada = propuestas.find((propuesta) => propuesta.estado.startsWith('ACEPTAD'));

    return {
      id: aviso.id_aviso,
      categoria: aviso.oficio,
      titulo: aviso.titulo || aviso.oficio,
      descripcion: aviso.descripcion,
      zona: aviso.zona,
      publicado: fechaLegible(aviso.fecha_creacion),
      estadoAviso: normalizarEstado(aviso.estado),
      profesionales: propuestas,
      precioMinimo: precios.length ? Math.min(...precios) : null,
      precioMaximo: precios.length ? Math.max(...precios) : null,
      profesionalElegido: aceptada?.id,
    };
  });
}

const formatosOrden = {
  precio: (a, b) => a.precio - b.precio,
  recientes: (a, b) => b.fechaOrden - a.fechaOrden,
};

const formatoPrecio = (precio) => `$ ${precio.toLocaleString('es-AR')}`;

function PresupuestoCard({
  aviso,
  onVerDetalle,
  onVerPerfil,
  onAceptar,
  onAbrirChat,
  onFinalizar,
  onCalificar,
  aceptandoId,
  finalizandoId,
  errorAceptacion,
  errorFinalizacion,
}) {
  const [orden, setOrden] = useState('precio');
  const [mostrarTodos, setMostrarTodos] = useState(false);
  const ordenados = useMemo(
    () => [...aviso.profesionales].sort(formatosOrden[orden]),
    [aviso.profesionales, orden],
  );
  const visibles = mostrarTodos ? ordenados : ordenados.slice(0, 5);
  const elegido = aviso.profesionales.find((propuesta) => propuesta.id === aviso.profesionalElegido);
  const avisoActivo = aviso.estadoAviso === 'ABIERTO';
  const etiquetaEstado = aviso.estadoAviso === 'FINALIZADO'
    ? 'Completado'
    : aviso.estadoAviso === 'EXPIRADO'
      ? 'Expirado'
      : elegido ? 'Aceptado' : avisoActivo ? 'Activa' : aviso.estadoAviso;

  return (
    <article className="pcp-aviso">
      <div className="pcp-aviso-cabecera">
        <div>
          <span className="pcp-categoria">{aviso.categoria}</span>
          <h3>{aviso.titulo}</h3>
        </div>
        <span className={`pcp-estado ${aviso.estadoAviso === 'FINALIZADO' ? 'finalizado' : elegido ? 'aceptado' : avisoActivo ? 'por-elegir' : 'cerrado'}`}>
          {etiquetaEstado}
        </span>
      </div>
      <p className="pcp-descripcion">{aviso.descripcion}</p>
      <div className="pcp-meta">
        <span><MapPin size={13} />{aviso.zona}</span>
        <span>Publicado {aviso.publicado}</span>
      </div>

      <div className="pcp-presupuestos-cabecera">
        <b>{`${aviso.profesionales.length} presupuestos recibidos`}</b>
        {aviso.profesionales.length > 1 && (
          <label className="pcp-orden">
            <span>Ordenar:</span>
            <select
              aria-label={`Ordenar presupuestos para ${aviso.titulo}`}
              value={orden}
              onChange={(event) => setOrden(event.target.value)}
            >
              <option value="precio">Menor precio</option>
              <option value="recientes">Más recientes</option>
            </select>
            <ChevronDown size={14} aria-hidden="true" />
          </label>
        )}
      </div>
      {aviso.precioMinimo !== null && (
        <p className="pcp-rango-precios">
          Precio mínimo: <b>{formatoPrecio(aviso.precioMinimo)}</b>
          {' · '}
          Precio máximo: <b>{formatoPrecio(aviso.precioMaximo)}</b>
        </p>
      )}

      {aviso.profesionales.length > 0 ? (
        <>
          <div className="pcp-lista">
            {visibles.map((propuesta) => (
              <article className="pcp-profesional" key={propuesta.id}>
                <div className="pcp-profesional-info">
                  <div className="pcp-nombre-fila">
                    <button
                      type="button"
                      className="pcp-identidad-perfil"
                      aria-label={`Ver perfil de ${propuesta.nombre}`}
                      onClick={() => onVerPerfil(propuesta.idPrestador)}
                    >
                      <span className="pcp-avatar">{propuesta.iniciales}</span>
                      <b>{propuesta.nombre}</b>
                    </button>
                    <span className="pcp-oficio">{propuesta.oficio}</span>
                    {propuesta.id === aviso.profesionalElegido && (
                      <span className="pcp-propuesta-aceptada"><Check size={12} /> Aceptada</span>
                    )}
                  </div>
                  <strong className="pcp-precio">{formatoPrecio(propuesta.precio)}</strong>
                  <p>{propuesta.detalle}</p>
                  <span className="pcp-recibido">
                    <Clock3 size={12} />Recibido {fechaLegible(propuesta.fecha)}
                  </span>
                </div>
                <div className="pcp-acciones">
                  <button type="button" className="pcp-link" onClick={() => onVerDetalle(aviso, propuesta)}>
                    Ver detalle del presupuesto
                  </button>
                  {propuesta.id === aviso.profesionalElegido ? (
                    <>
                      {propuesta.idConversacion && (
                        <button
                          type="button"
                          className="pcp-boton-elegir"
                          onClick={() => onAbrirChat(propuesta.idConversacion)}
                        >
                          Abrir chat
                        </button>
                      )}
                      {aviso.estadoAviso === 'EN_PROCESO' && (
                        <button
                          type="button"
                          className="pcp-boton-finalizar"
                          disabled={finalizandoId === aviso.id}
                          onClick={() => onFinalizar(aviso)}
                        >
                          {finalizandoId === aviso.id ? 'Finalizando…' : 'Finalizar trabajo'}
                        </button>
                      )}
                      {aviso.estadoAviso === 'FINALIZADO' && !propuesta.idCalificacion && (
                        <button
                          type="button"
                          className="pcp-boton-calificar"
                          onClick={() => onCalificar(aviso, propuesta)}
                        >
                          <Star size={13} /> Calificar
                        </button>
                      )}
                      {aviso.estadoAviso === 'FINALIZADO' && propuesta.idCalificacion && (
                        <span className="pcp-trabajo-calificado">Trabajo calificado</span>
                      )}
                    </>
                  ) : avisoActivo && !aviso.profesionalElegido && propuesta.estado === 'PENDIENTE' ? (
                    <button
                      type="button"
                      className="pcp-boton-elegir"
                      disabled={aceptandoId !== null}
                      onClick={() => onAceptar(propuesta)}
                    >
                      {aceptandoId === propuesta.id ? 'Aceptando…' : 'Aceptar presupuesto'}
                    </button>
                  ) : null}
                  {errorAceptacion?.id === propuesta.id && (
                    <p className="pcp-error-aceptacion" role="alert">{errorAceptacion.mensaje}</p>
                  )}
                  {errorFinalizacion?.id === aviso.id && (
                    <p className="pcp-error-aceptacion" role="alert">{errorFinalizacion.mensaje}</p>
                  )}
                </div>
              </article>
            ))}
          </div>
          {aviso.profesionales.length > 5 && (
            <button type="button" className="pcp-ver-mas" onClick={() => setMostrarTodos((actual) => !actual)}>
              {mostrarTodos ? 'Mostrar menos' : `Ver los ${aviso.profesionales.length - 5} restantes`}
            </button>
          )}
        </>
      ) : (
        <p className="pcp-sin-presupuestos">Todavía no recibiste presupuestos para este aviso.</p>
      )}
      {avisoActivo && aviso.profesionales.length > 0 && (
        <p className="pcp-nota">Tu solicitud sigue activa y puede recibir nuevos presupuestos.</p>
      )}
    </article>
  );
}

export default function PresupuestosClientePage({ usuario, onUnauthorized, onIrAChat }) {
  const [avisos, setAvisos] = useState(null);
  const [filtro, setFiltro] = useState('todos');
  const [detalle, setDetalle] = useState(null);
  const [error, setError] = useState('');
  const [intento, setIntento] = useState(0);
  const [aceptandoId, setAceptandoId] = useState(null);
  const [errorAceptacion, setErrorAceptacion] = useState(null);
  const [finalizandoId, setFinalizandoId] = useState(null);
  const [errorFinalizacion, setErrorFinalizacion] = useState(null);
  const [calificando, setCalificando] = useState(null);
  const [enviandoCalificacion, setEnviandoCalificacion] = useState(false);
  const [errorCalificacion, setErrorCalificacion] = useState('');
  const [idPerfilPrestador, setIdPerfilPrestador] = useState(null);

  useEffect(() => {
    if (!usuario?.id_usuario) return undefined;
    let vivo = true;
    Promise.all([
      avisosApi.listarMios(),
      presupuestosApi.listarParaCliente(usuario.id_usuario),
    ])
      .then(([misAvisos, postulaciones]) => {
        if (vivo) {
          setAvisos(agruparPresupuestos(misAvisos, postulaciones));
          setError('');
        }
      })
      .catch((err) => {
        if (!vivo) return;
        if (err.status === 401) {
          onUnauthorized?.();
          return;
        }
        setError(err.message);
      });
    return () => { vivo = false; };
  }, [usuario?.id_usuario, onUnauthorized, intento]);

  useEffect(() => {
    const cancelarRealtime = notificacionesApi.suscribir((evento) => {
      if (
        evento.type === 'presupuesto_nuevo'
        || evento.type === 'presupuesto_actualizado'
        || evento.type === 'calificacion_pendiente_nueva'
        || evento.type === 'conectado'
      ) {
        setIntento((actual) => actual + 1);
      }
    });
    return cancelarRealtime;
  }, []);

  const conteos = {
    todos: avisos?.length ?? 0,
    'por-elegir': avisos?.filter((aviso) => !aviso.profesionalElegido).length ?? 0,
    aceptados: avisos?.filter((aviso) => aviso.profesionalElegido).length ?? 0,
  };
  const avisosFiltrados = (avisos ?? []).filter((aviso) => (
    filtro === 'todos'
    || (filtro === 'aceptados' ? Boolean(aviso.profesionalElegido) : !aviso.profesionalElegido)
  ));

  if (idPerfilPrestador !== null) {
    return (
      <PerfilPrestadorPublicoPage
        key={idPerfilPrestador}
        idPrestador={idPerfilPrestador}
        onVolver={() => setIdPerfilPrestador(null)}
      />
    );
  }

  const aceptar = async (propuesta) => {
    setAceptandoId(propuesta.id);
    setErrorAceptacion(null);
    try {
      const resultado = await presupuestosApi.aceptar(propuesta.id);
      if (resultado.id_conversacion) {
        onIrAChat?.(resultado.id_conversacion);
      } else {
        setErrorAceptacion({
          id: propuesta.id,
          mensaje: 'El presupuesto se aceptó, pero no se pudo abrir la conversación.',
        });
      }
    } catch (err) {
      if (err.status === 401) {
        onUnauthorized?.();
        return;
      }
      setErrorAceptacion({ id: propuesta.id, mensaje: err.message });
    } finally {
      setAceptandoId(null);
    }
  };

  const finalizar = async (aviso) => {
    setFinalizandoId(aviso.id);
    setErrorFinalizacion(null);
    try {
      await avisosApi.finalizar(aviso.id);
      setIntento((actual) => actual + 1);
    } catch (err) {
      if (err.status === 401) {
        onUnauthorized?.();
        return;
      }
      setErrorFinalizacion({ id: aviso.id, mensaje: err.message });
    } finally {
      setFinalizandoId(null);
    }
  };

  const calificar = async ({ puntuacion, comentario, fotoComprobante }) => {
    setEnviandoCalificacion(true);
    setErrorCalificacion('');
    try {
      await presupuestosApi.calificar(calificando.propuesta.id, {
        puntuacion,
        comentario,
        fotoComprobante,
      });
      setCalificando(null);
      setIntento((actual) => actual + 1);
    } catch (err) {
      if (err.status === 401) {
        onUnauthorized?.();
        return;
      }
      setErrorCalificacion(err.message);
    } finally {
      setEnviandoCalificacion(false);
    }
  };

  return (
    <section className="pcp">
      <header className="pcp-titulo">
        <span>COMO CLIENTE</span>
        <h2>Mis Presupuestos</h2>
        <p>Compará las propuestas y elegí al profesional para tu trabajo.</p>
      </header>

      <div className="pcp-filtros" role="tablist" aria-label="Filtrar avisos">
        {[
          { id: 'todos', label: 'Todos' },
          { id: 'por-elegir', label: 'Por elegir' },
          { id: 'aceptados', label: 'Aceptados' },
        ].map(({ id, label }) => (
          <button
            type="button"
            role="tab"
            aria-selected={filtro === id}
            className={filtro === id ? 'activo' : ''}
            key={id}
            onClick={() => setFiltro(id)}
          >
            {label} ({conteos[id]})
          </button>
        ))}
      </div>

      {error ? (
        <div className="pcp-carga-error" role="alert">
          <p>No pudimos cargar tus presupuestos. {error}</p>
          <button type="button" className="pcp-boton-elegir" onClick={() => {
            setAvisos(null);
            setError('');
            setIntento((actual) => actual + 1);
          }}>
            Reintentar
          </button>
        </div>
      ) : avisos === null ? (
        <p className="pcp-vacio" aria-busy="true">Cargando tus presupuestos…</p>
      ) : (
        <div className="pcp-avisos">
          {avisosFiltrados.length ? avisosFiltrados.map((aviso) => (
            <PresupuestoCard
              key={aviso.id}
              aviso={aviso}
              onAceptar={aceptar}
              onVerPerfil={setIdPerfilPrestador}
              onAbrirChat={onIrAChat}
              onFinalizar={finalizar}
              onCalificar={(aviso, propuesta) => {
                setErrorCalificacion('');
                setCalificando({ aviso, propuesta });
              }}
              aceptandoId={aceptandoId}
              finalizandoId={finalizandoId}
              errorAceptacion={errorAceptacion}
              errorFinalizacion={errorFinalizacion}
              onVerDetalle={(avisoActual, propuesta) => setDetalle({ aviso: avisoActual, propuesta })}
            />
          )) : (
            <p className="pcp-vacio">
              {avisos.length === 0
                ? 'Todavía no publicaste avisos.'
                : 'No hay avisos en esta categoría.'}
            </p>
          )}
        </div>
      )}

      {detalle && (
        <div className="pcp-modal-fondo" onMouseDown={(event) => event.target === event.currentTarget && setDetalle(null)}>
          <section className="pcp-modal" role="dialog" aria-modal="true" aria-labelledby="pcp-modal-titulo">
            <button type="button" className="pcp-cerrar" aria-label="Cerrar detalle" onClick={() => setDetalle(null)}><X size={18} /></button>
            <span className="pcp-categoria">{detalle.aviso.categoria}</span>
            <h2 id="pcp-modal-titulo">Presupuesto de {detalle.propuesta.nombre}</h2>
            <p className="pcp-modal-aviso">{detalle.aviso.titulo}</p>
            <div className="pcp-modal-precio">{formatoPrecio(detalle.propuesta.precio)}</div>
            <p>{detalle.propuesta.detalle}</p>
            <p className="pcp-modal-meta">{detalle.propuesta.oficio}</p>
            <p className="pcp-modal-meta"><Clock3 size={14} /> Recibido {fechaLegible(detalle.propuesta.fecha)}</p>
            {detalle.propuesta.id === detalle.aviso.profesionalElegido && (
              <p className="pcp-contacto"><Check size={15} /> Esta propuesta figura como aceptada.</p>
            )}
          </section>
        </div>
      )}
      {calificando && (
        <CalificacionModal
          aviso={calificando.aviso}
          propuesta={calificando.propuesta}
          enviando={enviandoCalificacion}
          error={errorCalificacion}
          onEnviar={calificar}
          onCerrar={() => setCalificando(null)}
        />
      )}
    </section>
  );
}
