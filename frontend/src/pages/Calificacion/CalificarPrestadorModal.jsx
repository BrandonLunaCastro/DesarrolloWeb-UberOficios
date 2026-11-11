import { useEffect, useState } from 'react';
import { Check, Star, X } from 'lucide-react';
import { calificacionApi } from '../../services/calificacionService';
import './calificacion.css';

const ETIQUETAS = ['Muy malo', 'Malo', 'Regular', 'Bueno', 'Excelente'];
const MAX_COMENTARIO = 500;

/**
 * Props:
 *  - idAviso: number             (solicitud / trabajo que se califica)
 *  - nombrePrestador: string
 *  - detalle?: string            (por ejemplo, el oficio o el título del aviso)
 *  - onClose: () => void
 *  - onSuccess?: (calificacion) => void   (para marcar el trabajo como calificado / refrescar la lista)
 *  - onUnauthorized?: () => void
 */
export default function CalificarPrestadorModal({ idAviso, nombrePrestador, detalle, onClose, onSuccess, onUnauthorized }) {
  const [puntuacion, setPuntuacion] = useState(0);
  const [hover, setHover] = useState(0);
  const [comentario, setComentario] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [enviada, setEnviada] = useState(false);

  useEffect(() => {
    const esc = (e) => e.key === 'Escape' && !enviando && onClose();
    document.addEventListener('keydown', esc);
    return () => document.removeEventListener('keydown', esc);
  }, [enviando, onClose]);

  const mostrada = hover || puntuacion;

  async function enviar(e) {
    e.preventDefault();
    if (!puntuacion || enviando) return;
    setEnviando(true);
    setError('');
    try {
      const r = await calificacionApi.calificar(idAviso, { puntuacion, comentario });
      setEnviada(true);
      onSuccess?.(r);
    } catch (err) {
      if (err.status === 401) onUnauthorized?.();
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="cal-bg" role="dialog" aria-modal="true" aria-labelledby="cal-t" onClick={() => !enviando && onClose()}>
      <div className="cal" onClick={(e) => e.stopPropagation()}>
        <header>
          <h3 id="cal-t">{enviada ? 'Calificación enviada' : `Calificar a ${nombrePrestador}`}</h3>
          <button className="cal-x" onClick={onClose} disabled={enviando} aria-label="Cerrar"><X size={18} /></button>
        </header>

        {enviada ? (
          <div className="cal-ok" role="status">
            <span className="cal-check"><Check size={26} /></span>
            <p><b>¡Gracias por tu calificación!</b></p>
            <div className="cal-fija" aria-label={`${puntuacion} de 5 estrellas`}>
              {[1, 2, 3, 4, 5].map((n) => <Star key={n} size={22} fill={n <= puntuacion ? '#f59e0b' : 'none'} stroke={n <= puntuacion ? '#f59e0b' : '#cbd5e1'} />)}
            </div>
            <p className="cal-sub">Tu opinión ayuda a otros clientes a elegir y queda en el perfil de {nombrePrestador}.</p>
            <button className="cal-btn" onClick={onClose}>Cerrar</button>
          </div>
        ) : (
          <form onSubmit={enviar} noValidate>
            {detalle && <p className="cal-sub">{detalle}</p>}

            <fieldset className="cal-grupo" onMouseLeave={() => setHover(0)}>
              <legend>¿Cómo fue el servicio?</legend>
              <div className="cal-estrellas">
                {[1, 2, 3, 4, 5].map((n) => (
                  <label key={n} className="cal-estrella" onMouseEnter={() => setHover(n)}>
                    <input type="radio" name="puntuacion" value={n} checked={puntuacion === n} onChange={() => setPuntuacion(n)} disabled={enviando} />
                    <Star size={34} fill={n <= mostrada ? '#f59e0b' : 'none'} stroke={n <= mostrada ? '#f59e0b' : '#cbd5e1'} />
                    <span className="cal-solo-lector">{n} {n === 1 ? 'estrella' : 'estrellas'}</span>
                  </label>
                ))}
              </div>
              <p className="cal-etiqueta" aria-live="polite">{mostrada ? `${mostrada} de 5 · ${ETIQUETAS[mostrada - 1]}` : 'Elegí una puntuación de 1 a 5'}</p>
            </fieldset>

            <label htmlFor="cal-com" className="cal-lbl">Comentario (opcional)</label>
            <textarea id="cal-com" rows={4} maxLength={MAX_COMENTARIO} value={comentario} onChange={(e) => setComentario(e.target.value)}
              placeholder="Contanos cómo fue el trabajo: puntualidad, trato, prolijidad…" disabled={enviando} />
            <div className="cal-cont">{comentario.length}/{MAX_COMENTARIO}</div>

            {error && <p className="cal-err" role="alert">{error}</p>}
            <div className="cal-acc">
              <button type="button" className="cal-sec" onClick={onClose} disabled={enviando}>Cancelar</button>
              <button className="cal-btn" disabled={!puntuacion || enviando}>{enviando ? 'Enviando…' : 'Enviar calificación'}</button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
