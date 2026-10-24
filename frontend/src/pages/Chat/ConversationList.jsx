import { MessageSquare } from 'lucide-react';
import { horaOFecha, iniciales } from './utils';

export default function ConversationList({ convs, error, activa, onAbrir, onReintentar }) {
  return (
    <aside className="chat-lista" aria-label="Conversaciones">
      <h2>Mensajes</h2>
      {error ? (
        <div className="chat-aviso" role="alert">
          <p>{error.message}</p>
          <button className="chat-btn" onClick={onReintentar}>Reintentar</button>
        </div>
      ) : convs === null ? (
        <div aria-busy="true">{[0, 1, 2].map((i) => <div key={i} className="chat-skel" />)}</div>
      ) : convs.length === 0 ? (
        <div className="chat-aviso">
          <MessageSquare size={28} />
          <p><b>Todavía no tenés conversaciones</b></p>
          <p>Se habilitan cuando el cliente acepta un presupuesto de un aviso.</p>
        </div>
      ) : (
        <ul>
          {convs.map((c) => (
            <li key={c.id}>
              <button className={`chat-fila ${activa === c.id ? 'activa' : ''}`} aria-current={activa === c.id} onClick={() => onAbrir(c.id)}>
                <span className="chat-av">{iniciales(c.otro.nombre)}</span>
                <span className="chat-fila-txt">
                  <span className="chat-fila-top"><b>{c.otro.nombre}</b>{c.ultimo && <small>{horaOFecha(c.ultimo.fecha)}</small>}</span>
                  <span className="chat-fila-aviso">{c.oficio}</span>
                  <span className="chat-fila-ult">{c.ultimo?.texto ?? 'Sin mensajes todavía'}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
