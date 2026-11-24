import { useEffect, useState } from 'react';
import {
  iniciarCompraCreditos,
  listarPaquetesCreditos,
  simularPagoCreditos,
} from '../../services/creditosService';

const estados = {
  pendiente: 'Compra de prueba pendiente. No se realizó ningún cobro.',
  aprobada: 'Pago simulado aprobado. Los créditos ya fueron acreditados.',
  rechazada: 'Pago simulado rechazado. No se acreditaron créditos.',
  cancelada: 'Compra de prueba cancelada. No se acreditaron créditos.',
};

function mostrarPrecio(precio, moneda) {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: moneda,
    maximumFractionDigits: 0,
  }).format(precio);
}

export default function CompraCreditos() {
  const [paquetes, setPaquetes] = useState([]);
  const [seleccionado, setSeleccionado] = useState(null);
  const [compra, setCompra] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState('');

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
    return () => { activo = false; };
  }, []);

  async function iniciarCompra() {
    if (!seleccionado) return;
    setProcesando(true);
    setError('');
    try {
      const resultado = await iniciarCompraCreditos(seleccionado);
      setCompra(resultado);
    } catch (e) {
      setError(e.message);
    } finally {
      setProcesando(false);
    }
  }

  async function simularPago(resultado) {
    if (!compra) return;
    setProcesando(true);
    setError('');
    try {
      const compraActualizada = await simularPagoCreditos(compra.id, resultado);
      setCompra(compraActualizada);
    } catch (e) {
      setError(e.message);
    } finally {
      setProcesando(false);
    }
  }

  return (
    <section className="compra-creditos" aria-labelledby="titulo-compra-creditos">
      <h2 id="titulo-compra-creditos">Comprar créditos</h2>
      <p>Elegí un paquete para registrar una compra simulada. No se realizará ningún cobro real.</p>
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
                <span>{paquete.creditos} créditos</span>
                <strong>{mostrarPrecio(paquete.precio, paquete.moneda)}</strong>
              </button>
            ))}
          </div>
          <button
            type="button"
            className="btn primary"
            onClick={iniciarCompra}
            disabled={!seleccionado || procesando}
          >
            {procesando ? 'Registrando…' : 'Crear compra de prueba'}
          </button>
        </>
      )}
      {!cargando && paquetes.length === 0 && !error && <p>No hay paquetes disponibles.</p>}
      {compra && (
        <div className="estado-compra" role="status">
          <b>Compra #{compra.id} — {compra.estado}</b>
          <span>{estados[compra.estado]}</span>
          {compra.estado === 'pendiente' && (
            <div className="acciones-pago-simulado" role="group" aria-label="Resultado de pago de prueba">
              <button type="button" className="btn primary" onClick={() => simularPago('APROBADA')} disabled={procesando}>Aprobar pago de prueba</button>
              <button type="button" className="btn" onClick={() => simularPago('RECHAZADA')} disabled={procesando}>Rechazar</button>
              <button type="button" className="btn" onClick={() => simularPago('CANCELADA')} disabled={procesando}>Cancelar</button>
            </div>
          )}
        </div>
      )}
      {error && <p className="err" role="alert">{error}</p>}
    </section>
  );
}
