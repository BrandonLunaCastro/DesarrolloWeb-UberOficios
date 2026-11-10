import { useEffect, useState } from 'react';
import { ArrowUpRight, Gift, RotateCcw, ShoppingCart } from 'lucide-react';
import { creditosApi } from '../../services/creditosService';
import './creditos.css';

const peso = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 });
const fechaHora = new Intl.DateTimeFormat('es-AR', { dateStyle: 'medium', timeStyle: 'short' });
const fmt = (iso) => { const d = new Date(iso); return Number.isNaN(d.getTime()) ? '' : fechaHora.format(d); };
const TIPOS = {
  adquirido: { label: 'Adquiridos', Icono: ShoppingCart },
  gratuito: { label: 'Gratuitos', Icono: Gift },
  consumido: { label: 'Consumidos', Icono: ArrowUpRight },
  devuelto: { label: 'Devueltos', Icono: RotateCcw }, // solo se muestra si hay devoluciones
};
const ESTADOS = { aprobada: 'Aprobada', pendiente: 'Pendiente', rechazada: 'Rechazada', cancelada: 'Cancelada' };
const RESULTADO = {
  aprobado: ['ok', 'Recibimos tu pago. Estamos acreditando tus créditos: el saldo se actualiza en instantes.'],
  pendiente: ['pend', 'Tu pago está pendiente. Los créditos se acreditan cuando se confirme.'],
  rechazado: ['err', 'El pago fue rechazado. Podés intentar de nuevo.'],
};

// resultadoPago: 'aprobado' | 'pendiente' | 'rechazado' (cuando el checkout externo devuelve al usuario a la app)
export default function CreditosPage({ onUnauthorized, resultadoPago = null }) {
  const [datos, setDatos] = useState(null); // { saldo, paquetes, movimientos, compras }
  const [error, setError] = useState(null);
  const [intento, setIntento] = useState(0);
  const [tab, setTab] = useState('movimientos');
  const [filtro, setFiltro] = useState('todos');
  const [seleccion, setSeleccion] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [errorCompra, setErrorCompra] = useState('');
  const [aviso, setAviso] = useState('');

  const traer = () =>
    Promise.all([creditosApi.saldo(), creditosApi.paquetes(), creditosApi.movimientos(),
      // si el historial de compras falla (o todavía no existe en el back), el resto de la pantalla sigue funcionando
      creditosApi.compras().catch((e) => { if (e.status === 401) throw e; return null; })])
      .then(([saldo, paquetes, movimientos, compras]) => ({ saldo, paquetes, movimientos, compras }));

  useEffect(() => {
    let vivo = true;
    traer().then((d) => vivo && setDatos(d)).catch((e) => { if (!vivo) return; if (e.status === 401) onUnauthorized?.(); setError(e); });
    return () => { vivo = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intento]);

  // Mientras haya compras pendientes se consulta cada 3 s hasta que el back las confirme
  const hayPendientes = datos?.compras?.some((c) => c.estado === 'pendiente');
  useEffect(() => {
    if (!hayPendientes) return undefined;
    const t = setInterval(() => traer().then(setDatos).catch(() => {}), 3000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hayPendientes]);

  const reintentar = () => { setDatos(null); setError(null); setIntento((n) => n + 1); };

  async function confirmarCompra() {
    setEnviando(true);
    setErrorCompra('');
    try {
      const r = await creditosApi.comprar(seleccion.id);
      if (r?.url_pago) { window.location.assign(r.url_pago); return; } // checkout externo
      setSeleccion(null);
      setAviso('Compra iniciada. Tus créditos se acreditan cuando se confirme el pago.');
      setTab('compras');
      traer().then(setDatos).catch(() => {});
    } catch (e) {
      if (e.status === 401) onUnauthorized?.();
      setErrorCompra(e.message);
    } finally {
      setEnviando(false);
    }
  }

  if (error && !datos) {
    return <div className="cre-msg" role="alert"><p>{error.message}</p><button className="cre-btn" onClick={reintentar}>Reintentar</button></div>;
  }
  if (!datos) return <div aria-busy="true"><div className="cre-skel" /><div className="cre-skel" /></div>;

  const { saldo, paquetes, movimientos, compras } = datos;
  const totales = Object.keys(TIPOS).map((t) => [t, movimientos.filter((m) => m.tipo === t).reduce((s, m) => s + Math.abs(m.cantidad), 0)]).filter(([t, n]) => t !== 'devuelto' || n > 0);
  const visibles = movimientos.filter((m) => filtro === 'todos' || m.tipo === filtro);
  const res = RESULTADO[resultadoPago];
  // Ahorro frente al paquete con el crédito más caro (el más chico), como en el diseño de paquetes
  const base = paquetes.length ? Math.max(...paquetes.map((p) => p.precio / p.creditos)) : 0;
  const ahorroDe = (p) => (base ? Math.round((1 - p.precio / p.creditos / base) * 100) : 0);

  return (
    <section className="cre">
      <div className="cre-saldo">
        <div><p>Tu Saldo Disponible</p><div className="cre-num"><b>{saldo}</b><span>CRÉDITOS</span></div></div>
      </div>

      {res && <p className={`cre-aviso cre-${res[0]}`} role="status">{res[1]}</p>}
      {aviso && <p className="cre-aviso cre-ok" role="status">{aviso}</p>}

      <h2>Comprar créditos</h2>
      {paquetes.length === 0 ? (
        <p className="cre-msg">No hay paquetes disponibles por el momento.</p>
      ) : (
        <div className="cre-paquetes">
          {paquetes.map((p) => (
            <article key={p.id} className="cre-paquete">
              <h3>{p.nombre}</h3>
              <p className="cre-cant"><b>{p.creditos}</b> créditos</p>
              <p className="cre-precio">{peso.format(p.precio)}</p>
              <small>{peso.format(p.precio / p.creditos)} por crédito</small>
              {ahorroDe(p) > 0 && <span className="cre-ahorro">Ahorrás {ahorroDe(p)} %</span>}
              <span className="cre-relleno" />
              <button className="cre-btn" onClick={() => { setErrorCompra(''); setSeleccion(p); }}>Comprar</button>
            </article>
          ))}
        </div>
      )}

      <h2>Historial</h2>
      <div className="cre-tabs" role="tablist">
        {[['movimientos', 'Movimientos'], ['compras', 'Compras']].map(([id, label]) => (
          <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? 'on' : ''} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>

      {tab === 'movimientos' ? (
        <>
          <div className="cre-chips">
            <button className={filtro === 'todos' ? 'on' : ''} onClick={() => setFiltro('todos')}>Todos</button>
            {totales.map(([t, n]) => (
              <button key={t} className={filtro === t ? 'on' : ''} onClick={() => setFiltro(t)}>{TIPOS[t].label} · {n}</button>
            ))}
          </div>
          {visibles.length === 0 ? (
            <p className="cre-msg">{movimientos.length === 0 ? 'Todavía no tenés movimientos de créditos.' : 'No hay movimientos de este tipo.'}</p>
          ) : (
            <ul className="cre-lista">
              {visibles.map((m) => {
                const { label, Icono } = TIPOS[m.tipo];
                return (
                  <li key={m.id} className="cre-fila">
                    <span className={`cre-ic cre-t-${m.tipo}`}><Icono size={16} /></span>
                    <span className="cre-txt"><b>{m.descripcion}</b><small>{fmt(m.fecha)}</small></span>
                    <span className="cre-der">
                      <b className={`cre-cant-${m.tipo}`}>{m.cantidad > 0 ? '+' : '−'}{Math.abs(m.cantidad)}</b>
                      <small className={`cre-etq cre-t-${m.tipo}`}>{label}</small>
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </>
      ) : compras === null ? (
        <p className="cre-msg">No se pudo cargar el historial de compras.</p>
      ) : compras.length === 0 ? (
        <p className="cre-msg">Todavía no hiciste compras.</p>
      ) : (
        <ul className="cre-lista">
          {compras.map((c) => (
            <li key={c.id} className="cre-fila">
              <span className="cre-ic cre-t-adquirido"><ShoppingCart size={16} /></span>
              <span className="cre-txt"><b>{c.paquete} · {c.creditos} créditos</b><small>{fmt(c.fecha)}</small></span>
              <span className="cre-der">
                <b>{peso.format(c.monto)}</b>
                <small className={`cre-estado cre-e-${c.estado}`}>{ESTADOS[c.estado]}</small>
              </span>
            </li>
          ))}
        </ul>
      )}

      {seleccion && (
        <div className="cre-modal-bg" role="alertdialog" aria-modal="true" aria-labelledby="cm-t" onClick={() => !enviando && setSeleccion(null)}>
          <div className="cre-modal" onClick={(e) => e.stopPropagation()}>
            <h3 id="cm-t">Confirmar compra</h3>
            <p>Vas a comprar <b>{seleccion.creditos} créditos</b> ({seleccion.nombre}) por <b>{peso.format(seleccion.precio)}</b>.</p>
            <p className="cre-nota">El pago se completa en un sitio externo seguro. OficiosYa no guarda datos de tarjetas. Los créditos comprados no vencen ni se reembolsan, y se acreditan cuando se confirma el pago.</p>
            {errorCompra && <p className="cre-err" role="alert">{errorCompra}</p>}
            <div className="cre-acc">
              <button className="cre-btn-sec" onClick={() => setSeleccion(null)} disabled={enviando}>Cancelar</button>
              <button className="cre-btn" onClick={confirmarCompra} disabled={enviando}>{enviando ? 'Procesando…' : 'Continuar al pago'}</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
