import { useEffect } from 'react';
import { MapPin, X } from 'lucide-react';
import PostulacionForm from './PostulacionForm';

const formatearPrecio = (valor) => `$ ${Number(valor).toLocaleString('es-AR')}`;

export default function PostulacionModal({ aviso, onClose, onSuccess, onUnauthorized }) {
  useEffect(() => {
    const esc = (e) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', esc);
    return () => document.removeEventListener('keydown', esc);
  }, [onClose]);

  return (
    <div className="feed-modal-bg" role="dialog" aria-modal="true" aria-labelledby="pm-title" onClick={onClose}>
      <div className="feed-modal" onClick={(e) => e.stopPropagation()}>
        <header>
          <h3 id="pm-title">Postularme</h3>
          <button className="feed-x" aria-label="Cerrar" onClick={onClose}><X size={18} /></button>
        </header>
        <div className="feed-resumen">
          <b>{aviso.titulo ?? aviso.oficio}</b>
          <span><MapPin size={12} /> {aviso.zona}</span>
          <p>{aviso.descripcion}</p>
          {aviso.presupuesto_minimo != null && aviso.presupuesto_maximo != null && (
            <p className="feed-resumen-rango">
              Presupuestos recibidos: <b>{formatearPrecio(aviso.presupuesto_minimo)}</b> mín. · <b>{formatearPrecio(aviso.presupuesto_maximo)}</b> máx.
            </p>
          )}
        </div>
        <PostulacionForm idAviso={aviso.id_aviso} onSuccess={onSuccess} onUnauthorized={onUnauthorized} />
      </div>
    </div>
  );
}
