import { useEffect, useMemo, useRef, useState } from 'react';
import { ImagePlus, X } from 'lucide-react';
import { perfilApi } from '../../services/perfilService';

const TIPOS = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_MB = 5;
const MAX_POR_SUBIDA = 12;

export default function PortfolioUploader({ onClose, onUploaded }) {
  const [files, setFiles] = useState([]);
  const [errores, setErrores] = useState([]);
  const [subiendo, setSubiendo] = useState(false);
  const input = useRef(null);
  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files]);
  useEffect(() => () => previews.forEach(URL.revokeObjectURL), [previews]);

  function agregar(lista) {
    if (!lista) return;
    const errs = []; const ok = [];
    for (const f of Array.from(lista)) {
      if (!TIPOS.includes(f.type)) errs.push(`${f.name}: solo JPG, PNG o WebP.`);
      else if (f.size > MAX_MB * 1024 * 1024) errs.push(`${f.name}: supera los ${MAX_MB} MB.`);
      else ok.push(f);
    }
    const total = [...files, ...ok];
    if (total.length > MAX_POR_SUBIDA) errs.push(`Máximo ${MAX_POR_SUBIDA} fotos por vez.`);
    setFiles(total.slice(0, MAX_POR_SUBIDA)); setErrores(errs);
    if (input.current) input.current.value = '';
  }

  async function subir() {
    setSubiendo(true); setErrores([]);
    try { onUploaded(await perfilApi.subirFotos(files)); onClose(); }
    catch (e) { setErrores([e instanceof Error ? e.message : 'No se pudieron subir las fotos.']); setSubiendo(false); }
  }

  return (
    <div className="modal-bg" role="dialog" aria-modal="true" aria-labelledby="up-title" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <header><h2 id="up-title">Agregar al portafolio</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Cerrar"><X size={18} /></button></header>

        <div className="drop" onClick={() => input.current?.click()} onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); agregar(e.dataTransfer.files); }}>
          <ImagePlus size={28} /><p>Arrastrá tus fotos o <u>elegilas</u></p>
          <small>JPG, PNG o WebP · hasta {MAX_MB} MB cada una</small>
          <input ref={input} type="file" accept={TIPOS.join(',')} multiple hidden onChange={(e) => agregar(e.target.files)} />
        </div>

        {errores.map((m) => <p key={m} className="err" role="alert">{m}</p>)}
        {files.length > 0 && (
          <ul className="previews">
            {files.map((f, i) => (
              <li key={f.name + i}><img src={previews[i]} alt={f.name} />
                <button className="icon-btn" aria-label={`Quitar ${f.name}`}
                  onClick={() => setFiles(files.filter((_, j) => j !== i))}><X size={14} /></button></li>
            ))}
          </ul>
        )}
        <footer>
          <button className="btn" onClick={onClose}>Cancelar</button>
          <button className="btn primary" disabled={!files.length || subiendo} onClick={subir}>
            {subiendo ? 'Subiendo…' : `Subir ${files.length || ''} foto${files.length === 1 ? '' : 's'}`}</button>
        </footer>
      </div>
    </div>
  );
}
