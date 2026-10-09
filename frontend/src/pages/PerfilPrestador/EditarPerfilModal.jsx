import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { perfilApi } from '../../services/perfilService';

const MAX_BIO = 500;

export default function EditarPerfilModal({ perfil, onClose, onSaved }) {
  const [bio, setBio] = useState(perfil.prestador.biografia ?? '');
  const [sel, setSel] = useState(perfil.zonas.map((z) => z.id_zona));
  const [zonas, setZonas] = useState([]);
  const [estado, setEstado] = useState('idle');
  const [error, setError] = useState('');

  useEffect(() => { perfilApi.zonas().then(setZonas).catch(() => setError('No se pudieron cargar las zonas.')); }, []);

  const toggle = (id) => setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  const bioError = bio.trim().length < 20 ? 'Contá un poco más: mínimo 20 caracteres.' : '';
  const zonaError = sel.length === 0 ? 'Elegí al menos una zona.' : '';

  async function submit(e) {
    e.preventDefault();
    if (bioError || zonaError) return;
    setEstado('saving'); setError('');
    try { onSaved(await perfilApi.actualizar({ biografia: bio.trim(), zonas_ids: sel })); onClose(); }
    catch (err) { setEstado('error'); setError(err instanceof Error ? err.message : 'No se pudo guardar.'); }
  }

  return (
    <div className="modal-bg" role="dialog" aria-modal="true" aria-labelledby="ep-title" onClick={onClose}>
      <form className="modal" onSubmit={submit} onClick={(e) => e.stopPropagation()}>
        <header><h2 id="ep-title">Editar perfil</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Cerrar"><X size={18} /></button></header>

        <label htmlFor="bio">Descripción</label>
        <textarea id="bio" rows={5} maxLength={MAX_BIO} value={bio} onChange={(e) => setBio(e.target.value)} />
        <div className="hint"><span className="err">{bioError}</span><span>{bio.length}/{MAX_BIO}</span></div>

        <fieldset><legend>Zonas donde ofrecés servicios</legend>
          <div className="chips">
            {zonas.map((z) => (
              <button type="button" key={z.id_zona} aria-pressed={sel.includes(z.id_zona)}
                className={`chip ${sel.includes(z.id_zona) ? 'on' : ''}`} onClick={() => toggle(z.id_zona)}>{z.nombre}</button>
            ))}
          </div>
          <span className="err">{zonaError}</span>
        </fieldset>

        {error && <p className="err" role="alert">{error}</p>}
        <footer>
          <button type="button" className="btn" onClick={onClose}>Cancelar</button>
          <button className="btn primary" disabled={estado === 'saving' || !!bioError || !!zonaError}>
            {estado === 'saving' ? 'Guardando…' : 'Guardar cambios'}</button>
        </footer>
      </form>
    </div>
  );
}
