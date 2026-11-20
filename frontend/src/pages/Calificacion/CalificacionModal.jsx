import { useEffect, useMemo, useState } from 'react';
import { Star, X } from 'lucide-react';

const TIPOS_IMAGEN_PERMITIDOS = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_BYTES = 5 * 1024 * 1024;

export default function CalificacionModal({
  aviso,
  propuesta,
  enviando,
  error,
  onEnviar,
  onCerrar,
}) {
  const [puntuacion, setPuntuacion] = useState(0);
  const [comentario, setComentario] = useState('');
  const [foto, setFoto] = useState(null);
  const [errorFoto, setErrorFoto] = useState('');
  const vistaPrevia = useMemo(
    () => (foto ? URL.createObjectURL(foto) : null),
    [foto],
  );

  useEffect(() => () => {
    if (vistaPrevia) URL.revokeObjectURL(vistaPrevia);
  }, [vistaPrevia]);

  const seleccionarFoto = (event) => {
    const archivo = event.target.files?.[0] ?? null;
    setErrorFoto('');
    if (archivo && !TIPOS_IMAGEN_PERMITIDOS.includes(archivo.type)) {
      setFoto(null);
      setErrorFoto('Seleccioná una imagen JPG, PNG o WebP.');
    } else if (archivo && archivo.size > MAX_BYTES) {
      setFoto(null);
      setErrorFoto('La foto no puede superar los 5 MB.');
    } else {
      setFoto(archivo);
    }
    event.target.value = '';
  };

  const enviar = (event) => {
    event.preventDefault();
    onEnviar({
      puntuacion,
      comentario: comentario.trim(),
      fotoComprobante: foto,
    });
  };

  return (
    <div className="cal-bg" onMouseDown={(event) => event.target === event.currentTarget && onCerrar()}>
      <section className="cal" role="dialog" aria-modal="true" aria-labelledby="cal-t">
        <header>
          <h3 id="cal-t">Calificar a {propuesta.nombre}</h3>
          <button type="button" className="cal-x" aria-label="Cerrar calificación" onClick={onCerrar}>
            <X size={18} />
          </button>
        </header>
        <p className="cal-sub">{aviso.titulo}</p>
        <form onSubmit={enviar} noValidate>
          <fieldset className="cal-grupo">
            <legend>Tu calificación</legend>
            <div className="cal-estrellas">
              {[1, 2, 3, 4, 5].map((valor) => (
                <button
                  key={valor}
                  type="button"
                  className={`cal-estrella${puntuacion >= valor ? ' seleccionada' : ''}`}
                  aria-label={`${valor} ${valor === 1 ? 'estrella' : 'estrellas'}`}
                  aria-pressed={puntuacion === valor}
                  onClick={() => setPuntuacion(valor)}
                >
                  <Star size={30} fill={puntuacion >= valor ? 'currentColor' : 'none'} />
                </button>
              ))}
            </div>
            <p className="cal-etiqueta">Elegí una puntuación de 1 a 5</p>
          </fieldset>
          <label htmlFor="cal-comentario" className="cal-lbl">Comentario (opcional)</label>
          <textarea
            id="cal-comentario"
            rows={4}
            maxLength={2000}
            value={comentario}
            onChange={(event) => setComentario(event.target.value)}
          />
          <div className="cal-cont">{comentario.length}/2000</div>
          <label htmlFor="cal-foto" className="cal-lbl">Foto comprobante (opcional)</label>
          <input
            id="cal-foto"
            className="cal-foto-input"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={seleccionarFoto}
            disabled={enviando}
          />
          {foto && (
            <div className="cal-foto-preview">
              <img src={vistaPrevia} alt="Vista previa del comprobante" />
              <button
                type="button"
                className="cal-sec"
                onClick={() => setFoto(null)}
                disabled={enviando}
              >
                Quitar foto
              </button>
            </div>
          )}
          {errorFoto && <p className="cal-err" role="alert">{errorFoto}</p>}
          {error && <p className="cal-err" role="alert">{error}</p>}
          <div className="cal-acc">
            <button type="button" className="cal-sec" onClick={onCerrar}>Cancelar</button>
            <button className="cal-btn" disabled={!puntuacion || enviando}>
              {enviando ? 'Enviando…' : 'Enviar calificación'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
