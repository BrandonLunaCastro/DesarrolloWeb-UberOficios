import { useEffect, useState } from 'react';
import {
  COSTO_POSTULACION,
  obtenerSaldo,
  postularseAAviso,
} from '../../services/postulacionService';
import './PostulacionForm.css';

/**
 * Props:
 *  - idAviso: number
 *  - onUnauthorized: () => void   (token vencido: limpiar sesión y volver al login)
 *  - onSuccess?: (postulacion) => void
 */
export default function PostulacionForm({ idAviso, onUnauthorized, onSuccess }) {
  const [saldo, setSaldo] = useState(null); // null = todavía sin dato (no es lo mismo que 0)
  const [saldoError, setSaldoError] = useState('');
  const [presupuesto, setPresupuesto] = useState('');
  const [comentario, setComentario] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [postulado, setPostulado] = useState(false);
  const [mensaje, setMensaje] = useState(null); // { tipo: 'ok' | 'error', texto }

  const manejarError = (err) => {
    if (err.status === 401) {
      localStorage.removeItem('jwt');
      onUnauthorized?.();
      return;
    }
    return err.message;
  };

  const cargarSaldo = async () => {
    setSaldoError('');
    try {
      setSaldo(await obtenerSaldo());
    } catch (err) {
      const texto = manejarError(err);
      if (texto) setSaldoError(texto);
    }
  };

  useEffect(() => {
    cargarSaldo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const saldoInsuficiente = saldo !== null && saldo < COSTO_POSTULACION;
  const bloqueado = enviando || postulado || saldoInsuficiente;

  // Validación previa solo de formato; las reglas de negocio las valida el backend.
  const validarPresupuesto = () => {
    const valor = Number(presupuesto);
    if (!presupuesto || Number.isNaN(valor) || valor <= 0) {
      return 'Ingresá un presupuesto mayor a 0.';
    }
    if (!/^\d+(\.\d{1,2})?$/.test(String(presupuesto))) {
      return 'El presupuesto admite hasta 2 decimales.';
    }
    return '';
  };

  const manejarSubmit = async (e) => {
    e.preventDefault();
    if (bloqueado) return;

    const errorLocal = validarPresupuesto();
    if (errorLocal) {
      setMensaje({ tipo: 'error', texto: errorLocal });
      return;
    }

    setEnviando(true);
    setMensaje(null);
    try {
      const postulacion = await postularseAAviso(idAviso, { presupuesto, comentario });
      setPostulado(true);
      setMensaje({ tipo: 'ok', texto: 'Te postulaste correctamente.' });
      onSuccess?.(postulacion);
      cargarSaldo(); // refleja el crédito descontado
    } catch (err) {
      const texto = manejarError(err);
      if (texto) setMensaje({ tipo: 'error', texto }); // mensaje real del backend
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form className="postulacion" onSubmit={manejarSubmit} noValidate>
      <div className="postulacion__creditos">
        <p>
          Costo de postularte: <strong>{COSTO_POSTULACION}</strong>{' '}
          {COSTO_POSTULACION === 1 ? 'crédito' : 'créditos'}
        </p>
        {saldoError ? (
          <p className="postulacion__error">
            No pudimos cargar tu saldo. {saldoError}{' '}
            <button type="button" onClick={cargarSaldo}>Reintentar</button>
          </p>
        ) : (
          <p>
            Tu saldo: <strong>{saldo === null ? 'Cargando…' : saldo}</strong>
          </p>
        )}
        {saldoInsuficiente && (
          <p className="postulacion__error">
            No tenés créditos suficientes para postularte a este aviso.
          </p>
        )}
      </div>

      <label htmlFor={`presupuesto-${idAviso}`}>Tu presupuesto</label>
      <input
        id={`presupuesto-${idAviso}`}
        type="number"
        inputMode="decimal"
        min="0.01"
        step="0.01"
        value={presupuesto}
        onChange={(e) => setPresupuesto(e.target.value)}
        disabled={bloqueado}
        required
      />

      <label htmlFor={`comentario-${idAviso}`}>Comentario (opcional)</label>
      <textarea
        id={`comentario-${idAviso}`}
        rows={3}
        maxLength={2000}
        value={comentario}
        onChange={(e) => setComentario(e.target.value)}
        disabled={bloqueado}
      />

      <button type="submit" disabled={bloqueado}>
        {enviando
          ? 'Enviando…'
          : postulado
            ? 'Postulación enviada'
            : `Confirmar postulación (${COSTO_POSTULACION} ${COSTO_POSTULACION === 1 ? 'crédito' : 'créditos'})`}
      </button>

      {mensaje && (
        <p
          role={mensaje.tipo === 'error' ? 'alert' : 'status'}
          className={mensaje.tipo === 'error' ? 'postulacion__error' : 'postulacion__ok'}
        >
          {mensaje.texto}
        </p>
      )}
    </form>
  );
}
