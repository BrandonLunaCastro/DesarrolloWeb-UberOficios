import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { avisosApi } from '../../services/avisosService';
import AvisoCard from './AvisoCard';
import './feed.css';

export default function FeedPage({ onIrAPerfil, onPostular }) {
  const [avisos, setAvisos] = useState(null); // null = cargando
  const [saldo, setSaldo] = useState(null);
  const [error, setError] = useState(null);
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vivo = true;
    avisosApi.listarPorZona().then((d) => vivo && setAvisos(d)).catch((e) => vivo && setError(e));
    avisosApi.saldo().then((s) => vivo && setSaldo(s)).catch(() => {}); // si falla, el banner muestra "—"
    return () => { vivo = false; };
  }, [intento]);

  const reintentar = () => { setAvisos(null); setError(null); setIntento((n) => n + 1); };
  const sinZona = error?.status === 400;

  return (
    <section className="feed">
      <div className="feed-saldo">
        <div>
          <p>Tu Saldo Disponible</p>
          <div className="feed-num"><b>{saldo ?? '—'}</b><span>CRÉDITOS</span></div>
        </div>
        <button className="feed-recargar"><Plus size={16} /> Recargar</button>
      </div>

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
          {avisos.map((a) => <AvisoCard key={a.id_aviso} aviso={a} saldo={saldo} onPostular={onPostular} />)}
        </div>
      )}
    </section>
  );
}
