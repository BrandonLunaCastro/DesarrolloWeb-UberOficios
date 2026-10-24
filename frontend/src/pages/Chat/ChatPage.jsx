import { useEffect, useState } from 'react';
import { chatApi } from '../../services/chatService';
import ConversationList from './ConversationList';
import ChatWindow from './ChatWindow';
import './chat.css';

export default function ChatPage({ conversacionInicial = null, onUnauthorized }) {
  const [yo, setYo] = useState(null);
  const [convs, setConvs] = useState(null); // null = cargando
  const [error, setError] = useState(null);
  const [abierta, setAbierta] = useState(conversacionInicial);
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vivo = true;
    Promise.all([chatApi.obtenerYo(), chatApi.listarConversaciones()])
      .then(([u, l]) => { if (vivo) { setYo(u); setConvs(l); } })
      .catch((e) => { if (!vivo) return; if (e.status === 401) onUnauthorized?.(); setError(e); });
    return () => { vivo = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intento]);

  const reintentar = () => { setConvs(null); setError(null); setIntento((n) => n + 1); };

  // Cuando llega o se envía un mensaje, la conversación sube al principio con su último mensaje
  const actividad = (idConv, msg) =>
    setConvs((prev) => {
      const c = prev.find((x) => x.id === idConv);
      if (!c) return prev;
      return [{ ...c, ultimo: { texto: msg.texto, fecha: msg.fecha } }, ...prev.filter((x) => x.id !== idConv)];
    });

  const eliminada = (idConv) => { setConvs((prev) => prev.filter((c) => c.id !== idConv)); setAbierta(null); };

  const conv = convs?.find((c) => c.id === abierta);

  return (
    <section className={`chat ${conv ? 'chat--abierta' : ''}`}>
      <ConversationList convs={convs} error={error} activa={abierta} onAbrir={setAbierta} onReintentar={reintentar} />
      {conv && yo ? (
        <ChatWindow key={conv.id} conversacion={conv} yoId={yo.id} onVolver={() => setAbierta(null)} onActividad={actividad} onEliminada={eliminada} onUnauthorized={onUnauthorized} />
      ) : (
        <div className="chat-panel chat-sinsel"><p>Elegí una conversación para ver los mensajes.</p></div>
      )}
    </section>
  );
}
