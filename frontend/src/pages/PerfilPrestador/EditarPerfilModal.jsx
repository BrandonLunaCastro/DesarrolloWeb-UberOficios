import { useState } from 'react';
import { X } from 'lucide-react';
import { perfilApi } from '../../services/perfilService';

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
        <input id="oficio" maxLength={100} value={oficio} onChange={(e) => setOficio(e.target.value)} />

        <label htmlFor="zona">Zona donde ofrecés servicios</label>
        <input id="zona" maxLength={150} value={zona} onChange={(e) => setZona(e.target.value)} />

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
