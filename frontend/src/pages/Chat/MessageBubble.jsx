import { formatoHora } from './utils';

export default function MessageBubble({ mensaje, propio, onReintentar }) {
  const { texto, fecha, estado } = mensaje;
  return (
    <div className={`msg ${propio ? 'msg-propio' : 'msg-otro'}`}>
      <div className="msg-burbuja">{texto}</div>
      <span className={`msg-meta ${estado === 'error' ? 'msg-err' : ''}`}>
        {estado === 'enviando' ? 'Enviando…'
          : estado === 'error' ? <>No se pudo enviar. <button type="button" onClick={onReintentar}>Reintentar</button></>
          : formatoHora(fecha)}
      </span>
    </div>
  );
}
