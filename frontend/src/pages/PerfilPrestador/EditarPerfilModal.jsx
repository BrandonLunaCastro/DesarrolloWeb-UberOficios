import { useState } from 'react';
import { X } from 'lucide-react';
import { perfilApi } from '../../services/perfilService';
import { OFICIOS, ZONAS } from '../../constants/catalogos';

const MAX_BIO = 500;

export default function EditarPerfilModal({ perfil, onClose, onSaved }) {
  const [bio, setBio] = useState(perfil.prestador.biografia ?? '');
  const [zona, setZona] = useState(perfil.prestador.zona ?? '');
  const [oficio, setOficio] = useState(perfil.prestador.oficio ?? '');
  const [estado, setEstado] = useState('idle');
  const [error, setError] = useState('');

  async function submit(e) {
    e.preventDefault();
    setEstado('saving'); setError('');
    try {
      onSaved(await perfilApi.actualizar({
        biografia: bio.trim() || null,
        zona: zona.trim() || null,
        oficio: oficio.trim() || null,
      }));
      onClose();
    }
    catch (err) { setEstado('error'); setError(err instanceof Error ? err.message : 'No se pudo guardar.'); }
  }

  return (
    <div className="modal-bg" role="dialog" aria-modal="true" aria-labelledby="ep-title" onClick={onClose}>
      <form className="modal" onSubmit={submit} onClick={(e) => e.stopPropagation()}>
        <header><h2 id="ep-title">Editar perfil</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Cerrar"><X size={18} /></button></header>

        <label htmlFor="bio">Descripción</label>
        <textarea id="bio" rows={5} maxLength={MAX_BIO} value={bio} onChange={(e) => setBio(e.target.value)} />
        <div className="hint"><span /><span>{bio.length}/{MAX_BIO}</span></div>

        <label htmlFor="oficio">Oficio</label>
        <select id="oficio" value={oficio} onChange={(e) => setOficio(e.target.value)}>
          <option value="">Elegí un oficio…</option>
          {oficio && !OFICIOS.includes(oficio) && <option value={oficio}>{oficio} (actual)</option>}
          {OFICIOS.map((opcion) => <option key={opcion} value={opcion}>{opcion}</option>)}
        </select>

        <label htmlFor="zona">Zona donde ofrecés servicios</label>
        <select id="zona" value={zona} onChange={(e) => setZona(e.target.value)}>
          <option value="">Elegí una zona…</option>
          {zona && !ZONAS.includes(zona) && <option value={zona}>{zona} (actual)</option>}
          {ZONAS.map((opcion) => <option key={opcion} value={opcion}>{opcion}</option>)}
        </select>

        {error && <p className="err" role="alert">{error}</p>}
        <footer>
          <button type="button" className="btn" onClick={onClose}>Cancelar</button>
          <button className="btn primary" disabled={estado === 'saving'}>
            {estado === 'saving' ? 'Guardando…' : 'Guardar cambios'}</button>
        </footer>
      </form>
    </div>
  );
}
