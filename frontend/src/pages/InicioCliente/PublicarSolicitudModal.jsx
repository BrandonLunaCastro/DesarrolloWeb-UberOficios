import { useEffect, useState } from 'react';
import { CheckCircle2, X } from 'lucide-react';
import { avisosApi } from '../../services/avisosService';
import { OFICIOS, ZONAS } from '../../constants/catalogos';
import './inicioCliente.css';

const MAX_DESC = 500;

/**
 * Modal "Publicar Solicitud" (US-CL-01). Conectado a POST /avisos.
 * Props:
 *  - oficioInicial?, descripcionInicial?: string (vienen del buscador y de "Servicios rápidos")
 *  - telefono?: string          (precarga el teléfono del cliente; es opcional)
 *  - onClose: () => void
 *  - onSuccess?: (aviso) => void
 *  - onUnauthorized?: () => void (401: token vencido)
 */
export default function PublicarSolicitudModal({ telefono = '', oficioInicial = '', descripcionInicial = '', onClose, onSuccess, onUnauthorized }) {
  const [form, setForm] = useState({ oficio: oficioInicial, zona: '', descripcion: descripcionInicial, telefono: telefono ?? '' });
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);
  const [errorGeneral, setErrorGeneral] = useState('');
  const [creado, setCreado] = useState(null);

  useEffect(() => {
    const esc = (e) => e.key === 'Escape' && !enviando && onClose();
    document.addEventListener('keydown', esc);
    return () => document.removeEventListener('keydown', esc);
  }, [onClose, enviando]);

  const set = (campo) => (e) => {
    setForm((f) => ({ ...f, [campo]: e.target.value }));
    setErrores((x) => ({ ...x, [campo]: undefined }));
  };

  // Solo validación de formato; las reglas de negocio las valida el backend.
  const validar = () => {
    const x = {};
    if (!form.oficio) x.oficio = 'Elegí una categoría.';
    if (!form.zona) x.zona = 'Elegí tu zona.';
    if (!form.descripcion.trim()) x.descripcion = 'Contanos qué necesitás.';
    else if (form.descripcion.trim().length < 10) x.descripcion = 'Agregá un poco más de detalle (mín. 10 caracteres).';
    if (form.telefono.trim() && !/^[\d\s()+-]{6,20}$/.test(form.telefono.trim())) x.telefono = 'Ingresá un teléfono válido.';
    return x;
  };

  const enviar = async (e) => {
    e.preventDefault();
    if (enviando) return;
    const x = validar();
    setErrores(x);
    if (Object.keys(x).length) return;

    setEnviando(true);
    setErrorGeneral('');
    try {
      const aviso = await avisosApi.crear({
        oficio: form.oficio,
        descripcion: form.descripcion.trim(),
        zona: form.zona,
        telefono: form.telefono.trim() || null,
      });
      setCreado(aviso);
      onSuccess?.(aviso);
    } catch (err) {
      if (err.status === 401) {
        localStorage.removeItem('jwt');
        onUnauthorized?.();
        return;
      }
      setErrorGeneral(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="feed-modal-bg" role="dialog" aria-modal="true" aria-labelledby="ps-title" onClick={() => !enviando && onClose()}>
      <div className="feed-modal ps-modal" onClick={(e) => e.stopPropagation()}>
        <header>
          <h3 id="ps-title">Publicar Solicitud</h3>
          <button className="feed-x" aria-label="Cerrar" onClick={onClose} disabled={enviando}><X size={18} /></button>
        </header>

        {creado ? (
          <div className="ps-ok" role="status">
            <CheckCircle2 size={40} />
            <h4>¡Solicitud publicada!</h4>
            <p>Avisamos a los prestadores de <b>{creado.zona}</b>. Publicar es gratis: no se usó ningún crédito.</p>
            <button className="feed-btn" onClick={onClose}>Listo</button>
          </div>
        ) : (
          <form className="ps-form" onSubmit={enviar} noValidate>
            <p className="ps-hint">Es gratis. Los prestadores de tu zona te van a enviar sus presupuestos.</p>

            <div className="ps-field">
              <label htmlFor="ps-oficio">Categoría / Oficio</label>
              <select id="ps-oficio" value={form.oficio} onChange={set('oficio')} disabled={enviando} aria-invalid={!!errores.oficio}>
                <option value="">Elegí un oficio…</option>
                {OFICIOS.map((o) => <option key={o}>{o}</option>)}
              </select>
              {errores.oficio && <span className="ps-err">{errores.oficio}</span>}
            </div>

            <div className="ps-field">
              <label htmlFor="ps-zona">Zona aproximada</label>
              <select id="ps-zona" value={form.zona} onChange={set('zona')} disabled={enviando} aria-invalid={!!errores.zona}>
                <option value="">Elegí tu zona…</option>
                {ZONAS.map((z) => <option key={z}>{z}</option>)}
              </select>
              {errores.zona && <span className="ps-err">{errores.zona}</span>}
            </div>

            <div className="ps-field">
              <label htmlFor="ps-desc">Descripción del trabajo</label>
              <textarea id="ps-desc" rows={4} maxLength={MAX_DESC} value={form.descripcion} onChange={set('descripcion')}
                placeholder="Ej: Pierde agua debajo de la bacha de la cocina…" disabled={enviando} aria-invalid={!!errores.descripcion} />
              <div className="ps-row">
                {errores.descripcion ? <span className="ps-err">{errores.descripcion}</span> : <span />}
                <small>{form.descripcion.length}/{MAX_DESC}</small>
              </div>
            </div>

            <div className="ps-field">
              <label htmlFor="ps-tel">Teléfono de contacto <small>(opcional)</small></label>
              <input id="ps-tel" type="tel" inputMode="tel" value={form.telefono} onChange={set('telefono')}
                placeholder="261 555 0000" disabled={enviando} autoComplete="tel" aria-invalid={!!errores.telefono} />
              {errores.telefono && <span className="ps-err">{errores.telefono}</span>}
            </div>

            {errorGeneral && <p className="ps-err ps-err-box" role="alert">{errorGeneral}</p>}

            <div className="ps-actions">
              <button type="button" className="ps-cancel" onClick={onClose} disabled={enviando}>Cancelar</button>
              <button type="submit" className="feed-btn" disabled={enviando}>{enviando ? 'Publicando…' : 'Publicar'}</button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
