import { useEffect, useMemo, useState } from 'react';
import { Clock3, MapPin, UserRound, X } from 'lucide-react';
import { avisosApi } from '../../services/avisosService';
import { presupuestosApi } from '../../services/presupuestosService';
import { perfilApi } from '../../services/perfilService';
import './presupuestosPrestador.css';

const filtros = [
  { id: 'todos', label: 'Todos' },
  { id: 'pendiente', label: 'Pendientes' },
  { id: 'aceptado', label: 'Aceptados' },
];

const formatearPrecio = (valor) => `$ ${Number(valor).toLocaleString('es-AR')}`;

function fechaLegible(fecha) {
  const parsed = new Date(fecha);
  if (!fecha || Number.isNaN(parsed.getTime())) return 'Fecha no disponible';
  return parsed.toLocaleString('es-AR', { dateStyle: 'medium', timeStyle: 'short' });
}

function normalizarEstado(estado = '') {
  const valor = estado.trim().toUpperCase();
  if (valor.startsWith('PENDIENT')) return 'pendiente';
  if (valor.startsWith('ACEPTAD')) return 'aceptado';
  if (['RECHAZADO', 'NO_SELECCIONADO', 'DESCARTADO'].includes(valor)) return 'no-seleccionado';
  return 'otro';
}

function transformarPostulacion(postulacion) {
  const cliente = [postulacion.nombre_cliente, postulacion.apellido_cliente]
    .filter(Boolean)
    .join(' ') || 'Cliente';

  return {
    id: postulacion.id_postulacion,
    oficio: postulacion.oficio_prestador || 'Servicio',
    titulo: postulacion.titulo_aviso || 'Aviso',
    cliente,
    zona: postulacion.zona_aviso || '',
    descripcion: postulacion.descripcion_aviso || '',
    comentario: postulacion.comentario || '',
    presupuesto: Number(postulacion.presupuesto),
    estado: normalizarEstado(postulacion.estado),
    estadoOriginal: postulacion.estado,
    enviado: fechaLegible(postulacion.fecha_postulacion),
  };
}

function PresupuestoModal({ presupuesto, onCerrar }) {
  return (
    <div className="pp-modal-fondo" onMouseDown={(event) => event.target === event.currentTarget && onCerrar()}>
      <section className="pp-modal" role="dialog" aria-modal="true" aria-labelledby="pp-modal-titulo">
        <button type="button" className="pp-cerrar" aria-label="Cerrar" onClick={onCerrar}><X size={18} /></button>
        <span className="pp-kicker">{presupuesto.oficio}</span>
        <h2 id="pp-modal-titulo">{presupuesto.titulo}</h2>
        <p className="pp-modal-cliente">
          <UserRound size={14} /> {presupuesto.cliente}
          {presupuesto.zona && <> · <MapPin size={14} /> {presupuesto.zona}</>}
        </p>
        <strong className="pp-modal-precio">{formatearPrecio(presupuesto.presupuesto)}</strong>
        <p className="pp-modal-descripcion">{presupuesto.descripcion}</p>
        <h3>Tu mensaje al cliente</h3>
        <p className="pp-modal-comentario">{presupuesto.comentario || 'No agregaste un comentario.'}</p>
        <p className="pp-modal-fecha"><Clock3 size={14} /> Enviado {presupuesto.enviado}</p>
        <div className="pp-modal-acciones">
          <button type="button" className="pp-btn-primario" onClick={onCerrar}>Cerrar</button>
        </div>
      </section>
    </div>
  );
}

function EstadoPresupuesto({ estado, estadoOriginal }) {
  const labels = {
    pendiente: 'Pendiente de respuesta',
    aceptado: 'Aceptado',
    'no-seleccionado': 'No seleccionado',
    otro: estadoOriginal || 'Estado desconocido',
  };
  return <span className={`pp-estado ${estado}`}>{labels[estado]}</span>;
}

function PresupuestoCard({ presupuesto, onVer }) {
  return (
    <article className={`pp-card ${presupuesto.estado === 'aceptado' ? 'aceptado' : ''}`}>
      <div className="pp-card-cabecera">
        <div className="pp-card-titulo">
          <span className="pp-kicker">{presupuesto.oficio}</span>
          <h3>{presupuesto.titulo}</h3>
        </div>
        <div className="pp-card-precio">
          <EstadoPresupuesto estado={presupuesto.estado} estadoOriginal={presupuesto.estadoOriginal} />
          <strong>{formatearPrecio(presupuesto.presupuesto)}</strong>
        </div>
      </div>

      <div className="pp-meta">
        <span><UserRound size={13} />{presupuesto.cliente}</span>
        {presupuesto.zona && <span><MapPin size={13} />{presupuesto.zona}</span>}
      </div>
      <p className="pp-descripcion">{presupuesto.descripcion}</p>
      <div className="pp-card-pie">
        <div className="pp-fechas"><span>Enviado {presupuesto.enviado}</span></div>
        <div className="pp-acciones">
          <button type="button" className="pp-btn-secundario" onClick={() => onVer(presupuesto)}>
            Ver presupuesto
          </button>
        </div>
      </div>
    </article>
  );
}

export default function PresupuestosPrestadorPage({ onUnauthorized }) {
  const [presupuestos, setPresupuestos] = useState(null);
  const [saldo, setSaldo] = useState(null);
  const [filtro, setFiltro] = useState('todos');
  const [detalle, setDetalle] = useState(null);
  const [errorPresupuestos, setErrorPresupuestos] = useState('');
  const [errorSaldo, setErrorSaldo] = useState('');
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vivo = true;

    perfilApi.obtener()
      .then((perfil) => {
        const idPrestador = perfil?.prestador?.id_prestador;
        if (!idPrestador) {
          throw new Error('No encontramos el perfil de prestador asociado a esta cuenta.');
        }
        return presupuestosApi.listarParaPrestador(idPrestador);
      })
      .then((items) => {
        if (vivo) setPresupuestos(items.map(transformarPostulacion));
      })
      .catch((error) => {
        if (!vivo) return;
        if (error.status === 401) {
          onUnauthorized?.();
          return;
        }
        setErrorPresupuestos(error.message);
      });

    avisosApi.saldo()
      .then((valor) => vivo && setSaldo(valor))
      .catch((error) => {
        if (!vivo) return;
        if (error.status === 401) {
          onUnauthorized?.();
          return;
        }
        setErrorSaldo(error.message);
      });

    return () => { vivo = false; };
  }, [onUnauthorized, intento]);

  const conteos = {
    todos: presupuestos?.length ?? 0,
    pendiente: presupuestos?.filter((item) => item.estado === 'pendiente').length ?? 0,
    aceptado: presupuestos?.filter((item) => item.estado === 'aceptado').length ?? 0,
  };
  const visibles = useMemo(
    () => (presupuestos ?? []).filter((item) => filtro === 'todos' || item.estado === filtro),
    [filtro, presupuestos],
  );

  const reintentar = () => {
    setPresupuestos(null);
    setSaldo(null);
    setErrorPresupuestos('');
    setErrorSaldo('');
    setIntento((actual) => actual + 1);
  };

  return (
    <section className="pp">
      <header className="pp-titulo">
        <span className="pp-kicker">COMO PRESTADOR</span>
        <h2>Mis Presupuestos</h2>
        <p>Seguí tus propuestas y coordiná los trabajos que te aceptaron.</p>
      </header>

      <section className="pp-saldo" aria-label="Saldo disponible">
        <div>
          <span>Tu Saldo Disponible</span>
          <div className="pp-saldo-valor"><strong>{saldo ?? '—'}</strong><span>CRÉDITOS</span></div>
          {errorSaldo && (
            <p className="pp-saldo-error" role="alert">
              No pudimos cargar el saldo. {errorSaldo}{' '}
              <button type="button" onClick={reintentar}>Reintentar</button>
            </p>
          )}
        </div>
        <button type="button" className="pp-recargar" disabled title="La recarga todavía no está disponible">
          + Recargar
        </button>
      </section>

      <div className="pp-filtros" role="tablist" aria-label="Filtrar presupuestos">
        {filtros.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={filtro === id}
            className={filtro === id ? 'activo' : ''}
            onClick={() => setFiltro(id)}
          >
            {label} ({conteos[id]})
          </button>
        ))}
      </div>

      {errorPresupuestos ? (
        <div className="pp-error-carga" role="alert">
          <p>No pudimos cargar tus presupuestos. {errorPresupuestos}</p>
          <button type="button" className="pp-btn-secundario" onClick={reintentar}>Reintentar</button>
        </div>
      ) : presupuestos === null ? (
        <p className="pp-vacio" aria-busy="true">Cargando tus presupuestos…</p>
      ) : (
        <div className="pp-lista">
          {visibles.length ? visibles.map((presupuesto) => (
            <PresupuestoCard
              key={presupuesto.id}
              presupuesto={presupuesto}
              onVer={setDetalle}
            />
          )) : (
            <p className="pp-vacio">
              {presupuestos.length === 0
                ? 'Todavía no enviaste presupuestos.'
                : 'No tenés presupuestos en esta categoría.'}
            </p>
          )}
        </div>
      )}

      {detalle && <PresupuestoModal presupuesto={detalle} onCerrar={() => setDetalle(null)} />}
    </section>
  );
}
