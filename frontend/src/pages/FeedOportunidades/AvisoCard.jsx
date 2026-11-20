import { MapPin, Users } from 'lucide-react';
import { COSTO_POSTULACION } from '../../services/postulacionService';

const URGENCIA = { baja: 'Urgencia baja', media: 'Urgencia media', alta: 'Urgencia alta' };

export default function AvisoCard({ aviso, saldo, onPostular }) {
  const {
    titulo,
    oficio,
    descripcion,
    zona,
    urgencia,
    postulados,
    ya_postulado: yaPostulado,
    costo_creditos = COSTO_POSTULACION,
  } = aviso;
  const sinSaldo = saldo != null && saldo < costo_creditos;

  return (
    <article className={`aviso aviso-${urgencia ?? 'sin'}`}>
      <div className="aviso-top">
        {urgencia && <span className="aviso-badge">{URGENCIA[urgencia] ?? urgencia}</span>}
        <span className="aviso-zona"><MapPin size={13} /> {zona}</span>
      </div>
      <h3>{titulo ?? oficio}</h3>
      <p>{descripcion}</p>
      <footer>
        {postulados != null
          ? <span className="aviso-post"><Users size={16} /> <b>{postulados}</b> {postulados === 1 ? 'postulado' : 'postulados'}</span>
          : <span />}
        {yaPostulado ? (
          <span className="aviso-ya-postulado" role="status">Ya te postulaste</span>
        ) : (
          <button className="aviso-btn" disabled={sinSaldo} title={sinSaldo ? 'No tenés créditos suficientes' : ''} onClick={() => onPostular?.(aviso)}>
            Postularme <span className="aviso-costo">{costo_creditos}<i /></span>
          </button>
        )}
      </footer>
    </article>
  );
}
