import { Fragment, useEffect, useRef, useState } from 'react';
import { ArrowLeft, Info, Send, Trash2 } from 'lucide-react';
import { chatApi } from '../../services/chatService';
import MessageBubble from './MessageBubble';
import { etiquetaDia, iniciales } from './utils';

export default function ChatWindow({ conversacion, yoId, onVolver, onActividad, onEliminada, onUnauthorized }) {
  const id = conversacion.id;
  const [mensajes, setMensajes] = useState(null); // null = cargando
  const [error, setError] = useState(null);
  const [conexion, setConexion] = useState('conectado'); // 'conectado' | 'reconectando' | 'desconectado'
  const [texto, setTexto] = useState('');
  const [intento, setIntento] = useState(0);
  const lista = useRef(null);
  const [confirmando, setConfirmando] = useState(false);
  const [eliminando, setEliminando] = useState(false);
  const [errorEliminar, setErrorEliminar] = useState('');

  useEffect(() => {
    let vivo = true;
    chatApi.obtenerMensajes(id)
      .then((m) => vivo && setMensajes(m))
      .catch((e) => { if (!vivo) return; if (e.status === 401) onUnauthorized?.(); setError(e); });
    const baja = chatApi.suscribir(id, {
      // Se descartan duplicados por id (mismo mensaje por POST y por tiempo real, o al reconectar)
      onMensaje: (m) => {
        if (!vivo) return;
        setMensajes((prev) => (prev && !prev.some((x) => x.id === m.id) ? [...prev, m] : prev));
        onActividad?.(id, m);
      },
      onEstado: (e) => vivo && setConexion(e),
    });
    return () => { vivo = false; baja(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, intento]);

  useEffect(() => { if (lista.current) lista.current.scrollTop = lista.current.scrollHeight; }, [mensajes]);

  const reintentarCarga = () => { setMensajes(null); setError(null); setIntento((n) => n + 1); };

  async function enviar(contenido, tmpId) {
    const tmp = tmpId ?? `tmp-${Date.now()}`;
    const optimista = { id: tmp, idConversacion: id, idRemitente: yoId, texto: contenido, fecha: new Date().toISOString(), estado: 'enviando' };
    setMensajes((prev) => (tmpId ? prev.map((m) => (m.id === tmp ? { ...m, estado: 'enviando' } : m)) : [...prev, optimista]));
    try {
      const real = await chatApi.enviarMensaje(id, contenido);
      setMensajes((prev) => { const resto = prev.filter((m) => m.id !== tmp); return resto.some((m) => m.id === real.id) ? resto : [...resto, real]; });
      onActividad?.(id, real);
    } catch (e) {
      if (e.status === 401) onUnauthorized?.();
      setMensajes((prev) => prev.map((m) => (m.id === tmp ? { ...m, estado: 'error' } : m)));
    }
  }

  async function eliminar() {
    setEliminando(true);
    setErrorEliminar('');
    try {
      await chatApi.eliminarConversacion(id);
      onEliminada?.(id);
    } catch (e) {
      if (e.status === 401) onUnauthorized?.();
      setErrorEliminar(e.message);
      setEliminando(false);
    }
  }

  const submit = (e) => {
    e.preventDefault();
    const t = texto.trim();
    if (!t || !mensajes) return;
    setTexto('');
    enviar(t);
  };
  const teclas = (e) => { if (e.key === 'Enter' && !e.shiftKey) submit(e); };

  let diaPrev = '';
  return (
    <section className="chat-panel chat-ventana" aria-label={`Conversación con ${conversacion.otro.nombre}`}>
      <header className="chat-cab">
        <button className="chat-volver" onClick={onVolver} aria-label="Volver a las conversaciones"><ArrowLeft size={18} /></button>
        <span className="chat-av">{iniciales(conversacion.otro.nombre)}</span>
        <div className="chat-cab-txt">
          <b>{conversacion.otro.nombre}</b>
          <small>{conversacion.oficio}</small>
        </div>
        {conversacion.estado === 'en_proceso' && <span className="chat-badge">En proceso</span>}
        <button className="chat-icono" onClick={() => { setErrorEliminar(''); setConfirmando(true); }} aria-label="Eliminar conversación"><Trash2 size={16} /></button>
      </header>
      <p className="chat-nota"><Info size={13} /> Acordá el precio y los detalles por acá. El pago no se realiza por este medio.</p>

      {conexion !== 'conectado' && (
        <div className="chat-conexion" role="status">
          {conexion === 'reconectando' ? 'Reconectando…' : 'Sin conexión: no vas a recibir mensajes nuevos hasta que vuelva.'}
          {conexion === 'desconectado' && <button onClick={() => setIntento((n) => n + 1)}>Reintentar</button>}
        </div>
      )}

      <div className="chat-msgs" ref={lista} aria-live="polite">
        {error ? (
          <div className="chat-aviso" role="alert"><p>{error.message}</p><button className="chat-btn" onClick={reintentarCarga}>Reintentar</button></div>
        ) : mensajes === null ? (
          <div className="chat-aviso" aria-busy="true"><p>Cargando mensajes…</p></div>
        ) : mensajes.length === 0 ? (
          <div className="chat-aviso"><p><b>Todavía no hay mensajes</b></p><p>Coordiná los detalles del trabajo con {conversacion.otro.nombre}.</p></div>
        ) : (
          mensajes.map((m) => {
            const dia = new Date(m.fecha).toDateString();
            const nuevoDia = dia !== diaPrev;
            diaPrev = dia;
            return (
              <Fragment key={m.id}>
                {nuevoDia && <div className="chat-dia">{etiquetaDia(m.fecha)}</div>}
                <MessageBubble mensaje={m} propio={m.idRemitente === yoId} onReintentar={() => enviar(m.texto, m.id)} />
              </Fragment>
            );
          })
        )}
      </div>

      <form className="chat-form" onSubmit={submit}>
        <textarea rows={1} maxLength={2000} placeholder="Escribí un mensaje…" aria-label="Escribí un mensaje"
          value={texto} onChange={(e) => setTexto(e.target.value)} onKeyDown={teclas} disabled={mensajes === null} />
        <button className="chat-enviar" disabled={!texto.trim() || mensajes === null} aria-label="Enviar mensaje"><Send size={16} /></button>
      </form>

      {confirmando && (
        <div className="chat-confirm-bg" role="alertdialog" aria-modal="true" aria-labelledby="ce-t" onClick={() => !eliminando && setConfirmando(false)}>
          <div className="chat-confirm" onClick={(e) => e.stopPropagation()}>
            <h3 id="ce-t">¿Eliminar esta conversación?</h3>
            <p>Se va a borrar el chat con {conversacion.otro.nombre}. Esta acción no se puede deshacer.</p>
            {errorEliminar && <p className="chat-err" role="alert">{errorEliminar}</p>}
            <div className="chat-confirm-acc">
              <button className="chat-btn-sec" onClick={() => setConfirmando(false)} disabled={eliminando}>Cancelar</button>
              <button className="chat-btn chat-btn-peligro" onClick={eliminar} disabled={eliminando}>{eliminando ? 'Eliminando…' : 'Eliminar'}</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
