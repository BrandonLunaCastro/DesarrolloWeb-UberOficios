import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { avisosApi, COSTO_POSTULACION } from '../../services/avisosService';
import AvisoCard from './AvisoCard';
import './feed.css';

export default function FeedPage({ onIrAPerfil, onIrAAdquirirCreditos, onPostular }) {
  const [avisos, setAvisos] = useState(null); // null = cargando
  const [saldo, setSaldo] = useState(null);
  const [error, setError] = useState(null);
  const [mensajeSaldo, setMensajeSaldo] = useState('');
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vivo = true;
    avisosApi.listarPorZona().then((d) => vivo && setAvisos(d)).catch((e) => vivo && setError(e));
    avisosApi.saldo().then((s) => vivo && setSaldo(s)).catch(() => {}); // si falla, el banner muestra "—"
    return () => { vivo = false; };
  }, [intento]);

  const reintentar = () => { setAvisos(null); setError(null); setIntento((n) => n + 1); };
  const sinZona = error?.status === 400;
  const handlePostular = (aviso) => {
    const costo = aviso.costo_creditos ?? COSTO_POSTULACION;
    if (saldo != null && saldo < costo) {
      setMensajeSaldo('No tenés créditos suficientes para postularte. Tu saldo permanece intacto.');
      return;
    }

    setMensajeSaldo('');
    onPostular?.(aviso);
  };

  return (
    <section className="feed">
      <div className="feed-saldo">
        <div>
          <p>Tu Saldo Disponible</p>
          <div className="feed-num"><b>{saldo ?? '—'}</b><span>CRÉDITOS</span></div>
        </div>
        {onIrAAdquirirCreditos && (
          <button className="feed-recargar" onClick={onIrAAdquirirCreditos}>
            <Plus size={16} /> Adquirir créditos
          </button>
        )}
      </div>

      {mensajeSaldo && (
        <div className="feed-msg feed-creditos-alerta" role="alert">
          <p>{mensajeSaldo}</p>
          {onIrAAdquirirCreditos && (
            <button className="feed-btn" onClick={onIrAAdquirirCreditos}>
              Adquirir créditos
            </button>
          )}
        </div>
      )}

      <h2>Oportunidades cerca tuyo</h2>

      {error ? (
        <div className="feed-msg" role="alert">
          <p>{error.message}</p>
          {sinZona && onIrAPerfil
            ? <button className="feed-btn" onClick={onIrAPerfil}>Ir a mi perfil</button>
            : <button className="feed-btn" onClick={reintentar}>Reintentar</button>}
        </div>
      ) : avisos === null ? (
        <div aria-busy="true"><div className="feed-skel" /><div className="feed-skel" /></div>
      ) : avisos.length === 0 ? (
        <p className="feed-msg">No hay oportunidades en tu zona por ahora. Volvé a mirar más tarde.</p>
      ) : (
        <div className="feed-list">
          {avisos.map((a) => <AvisoCard key={a.id_aviso} aviso={a} onPostular={handlePostular} />)}
        </div>
      )}
    </section>
  );
}
