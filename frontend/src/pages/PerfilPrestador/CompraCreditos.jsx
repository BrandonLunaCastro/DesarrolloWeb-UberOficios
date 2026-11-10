import { useEffect, useState } from 'react';
import {
  consultarCompraCreditos,
  iniciarCompraCreditos,
  listarPaquetesCreditos,
  reintentarCheckoutCreditos,
} from '../../services/creditosService';

const estados = {
  PENDIENTE: 'Pago pendiente. Los créditos se acreditarán al confirmarse el pago.',
  APROBADA: 'Pago aprobado. Los créditos ya fueron acreditados.',
  RECHAZADA: 'El pago fue rechazado. No se acreditaron créditos.',
  CANCELADA: 'La compra fue cancelada. No se acreditaron créditos.',
};

function mostrarPrecio(centavos, moneda) {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: moneda,
    maximumFractionDigits: 0,
  }).format(centavos / 100);
}

export default function CompraCreditos() {
  const [paquetes, setPaquetes] = useState([]);
  const [seleccionado, setSeleccionado] = useState(null);
  const [compra, setCompra] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState('');
  const compraId = compra?.id;
  const compraEstado = compra?.estado;

  useEffect(() => {
    let activo = true;
    listarPaquetesCreditos()
      .then((resultado) => {
        if (!activo) return;
        setPaquetes(resultado);
        if (resultado.length) setSeleccionado(resultado[0].id);
      })
      .catch((e) => {
        if (activo) setError(e.message);
      })
      .finally(() => {
        if (activo) setCargando(false);
      });
    const compraId = new URLSearchParams(window.location.search).get('compra_id');
    if (compraId && /^\d+$/.test(compraId)) {
      consultarCompraCreditos(compraId)
        .then((resultado) => {
          if (activo) setCompra(resultado);
        })
        .catch((e) => {
          if (activo) setError(e.message);
        });
    }
    return () => { activo = false; };
  }, []);

  useEffect(() => {
    if (!compraId || compraEstado !== 'PENDIENTE') return undefined;
    let activo = true;
    const intervalo = window.setInterval(() => {
      consultarCompraCreditos(compraId)
        .then((resultado) => {
          if (activo) setCompra(resultado);
        })
        .catch((e) => {
          if (activo) setError(e.message);
        });
    }, 3000);
    return () => {
      activo = false;
      window.clearInterval(intervalo);
    };
  }, [compraId, compraEstado]);

  async function iniciarCompra() {
    if (!seleccionado) return;
    setProcesando(true);
    setError('');
    try {
      const resultado = await iniciarCompraCreditos(seleccionado);
      setCompra(resultado);
      if (resultado.url_pago) window.location.assign(resultado.url_pago);
    } catch (e) {
      setError(e.message);
      if (e.compraId) {
        consultarCompraCreditos(e.compraId)
          .then(setCompra)
          .catch((consultaError) => setError(consultaError.message));
      }
    } finally {
      setProcesando(false);
    }
  }

  async function reintentarPago() {
    if (!compra) return;
    setProcesando(true);
    setError('');
    try {
      const resultado = await reintentarCheckoutCreditos(compra.id);
      setCompra(resultado);
      if (resultado.url_pago) window.location.assign(resultado.url_pago);
    } catch (e) {
      setError(e.message);
    } finally {
      setProcesando(false);
    }
  }

  return (
    <section className="compra-creditos" aria-labelledby="titulo-compra-creditos">
      <h2 id="titulo-compra-creditos">Comprar créditos</h2>
      <p>Elegí un paquete. Los créditos se suman a tu saldo únicamente cuando Mercado Pago confirma el pago.</p>
      {cargando && <p aria-busy="true">Cargando paquetes…</p>}
      {!cargando && paquetes.length > 0 && (
        <>
          <div className="paquetes-creditos">
            {paquetes.map((paquete) => (
              <button
                type="button"
                key={paquete.id}
                className={`paquete-credito ${seleccionado === paquete.id ? 'seleccionado' : ''}`}
                aria-pressed={seleccionado === paquete.id}
                onClick={() => setSeleccionado(paquete.id)}
                disabled={procesando}
              >
                <b>{paquete.nombre}</b>
                <span>{paquete.cantidad_creditos} créditos</span>
                <strong>{mostrarPrecio(paquete.precio_centavos, paquete.moneda)}</strong>
              </button>
            ))}
          </div>
          <button
            type="button"
            className="btn primary"
            onClick={iniciarCompra}
            disabled={!seleccionado || procesando}
          >
            {procesando ? 'Preparando pago…' : 'Continuar al pago'}
          </button>
        </>
      )}
      {!cargando && paquetes.length === 0 && !error && <p>No hay paquetes disponibles.</p>}
      {compra && (
        <div className="estado-compra" role="status">
          <b>Compra #{compra.id} — {compra.estado}</b>
          <span>{estados[compra.estado]}</span>
          {compra.estado === 'PENDIENTE' && compra.url_pago && (
            <a href={compra.url_pago}>Continuar con el pago</a>
          )}
          {compra.estado === 'PENDIENTE' && !compra.url_pago && (
            <button type="button" className="btn" onClick={reintentarPago} disabled={procesando}>
              Reintentar pago
            </button>
          )}
        </div>
      )}
      {error && <p className="err" role="alert">{error}</p>}
    </section>
  );
}
