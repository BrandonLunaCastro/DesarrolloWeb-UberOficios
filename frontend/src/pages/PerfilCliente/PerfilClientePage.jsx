import { useEffect, useState } from 'react';
import { Calendar, Camera, CheckCircle2, Pencil, Phone, User } from 'lucide-react';
import { clienteApi } from '../../services/clienteService';
import PublicarSolicitudModal from '../InicioCliente/PublicarSolicitudModal';
import './perfilCliente.css';

const iniciales = (n = '', a = '') => `${n[0] ?? ''}${a[0] ?? ''}`.toUpperCase();
const mesAnio = (iso) => {
  if (!iso) return '';
  const t = new Date(iso).toLocaleDateString('es-AR', { month: 'long', year: 'numeric' });
  return t.charAt(0).toUpperCase() + t.slice(1);
};

/**
 * Pantalla "Cliente - perfil" (Figma).
 *  - Vista: portada, avatar, nombre, datos personales y "¿Qué necesitás hoy?".
 *  - Se pueden editar nombre, apellido y teléfono. El correo no: es el dato con el que se inicia sesión.
 *  - La zona se elige al publicar cada solicitud.
 *  - onActualizado?.({ nombre, apellido }) permite que el layout refresque el nombre del menú.
 *  - abrirEdicion: abre la pantalla directamente en modo edición (lápiz del menú del avatar).
 */
export default function PerfilClientePage({ onUnauthorized, onActualizado, abrirEdicion = false }) {
  const [perfil, setPerfil] = useState(null);   // GET /auth/me
  const [form, setForm] = useState({ nombre: '', apellido: '', telefono: '' });
  const [inicial, setInicial] = useState({ nombre: '', apellido: '', telefono: '' }); // último valor guardado
  const [editando, setEditando] = useState(abrirEdicion); // true si se llegó desde el lápiz del menú
  const [errorCarga, setErrorCarga] = useState('');
  const [errores, setErrores] = useState({});
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState(null); // { tipo: 'ok' | 'error', texto }
  const [intento, setIntento] = useState(0);
  const [texto, setTexto] = useState('');
  const [modal, setModal] = useState(null);     // null | { descripcion }

  useEffect(() => {
    let vivo = true;
    clienteApi.obtener()
      .then((p) => {
        if (!vivo) return;
        setPerfil(p);
        const v = { nombre: p.nombre ?? '', apellido: p.apellido ?? '', telefono: p.telefono ?? '' };
        setForm(v); setInicial(v); setErrorCarga('');
      })
      .catch((e) => {
        if (!vivo) return;
        if (e.status === 401) { localStorage.removeItem('jwt'); onUnauthorized?.(); return; }
        setErrorCarga(e.message);
      });
    return () => { vivo = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intento]);

  const set = (campo) => (e) => {
    setForm((f) => ({ ...f, [campo]: e.target.value }));
    setErrores((x) => ({ ...x, [campo]: undefined }));
    setMensaje(null);
  };

  const hayCambios = form.nombre.trim() !== inicial.nombre
    || form.apellido.trim() !== inicial.apellido
    || form.telefono !== inicial.telefono;

  const cancelar = () => { setForm(inicial); setErrores({}); setMensaje(null); setEditando(false); };

  const guardar = async (e) => {
    e.preventDefault();
    if (guardando || !hayCambios) return;
    const x = {};
    if (!form.nombre.trim()) x.nombre = 'Ingresá tu nombre.';
    if (!form.apellido.trim()) x.apellido = 'Ingresá tu apellido.';
    if (form.telefono.trim() && !/^[\d\s()+-]{6,20}$/.test(form.telefono.trim())) x.telefono = 'Ingresá un teléfono válido.';
    setErrores(x);
    if (Object.keys(x).length) return;

    const body = {}; // el back actualiza únicamente los campos que recibe
    if (form.nombre.trim() !== inicial.nombre) body.nombre = form.nombre.trim();
    if (form.apellido.trim() !== inicial.apellido) body.apellido = form.apellido.trim();
    if (form.telefono !== inicial.telefono) body.telefono = form.telefono.trim() || null;

    setGuardando(true);
    setMensaje(null);
    try {
      const r = await clienteApi.actualizar(body);
      const c = r?.cliente ?? r?.prestador ?? {};
      // Nombre y apellido: se muestra lo que el back realmente guardó. Si la respuesta no trae `usuario`,
      // se vuelve a pedir el perfil para no mostrar un cambio que el back ignoró.
      let u = r?.usuario ?? null;
      if (!u && ('nombre' in body || 'apellido' in body)) {
        try { u = await clienteApi.obtener(); } catch { u = null; }
      }
      const v = {
        nombre: u?.nombre ?? perfil.nombre ?? '',
        apellido: u?.apellido ?? perfil.apellido ?? '',
        telefono: c.telefono ?? form.telefono.trim(),
      };
      setPerfil((p) => ({ ...p, nombre: v.nombre, apellido: v.apellido, telefono: v.telefono }));
      setForm(v); setInicial(v);
      setEditando(false);
      setMensaje({ tipo: 'ok', texto: 'Cambios guardados correctamente.' });
      onActualizado?.({ nombre: v.nombre, apellido: v.apellido });
    } catch (err) {
      if (err.status === 401) { localStorage.removeItem('jwt'); onUnauthorized?.(); return; }
      setMensaje({ tipo: 'error', texto: err.message });
    } finally {
      setGuardando(false);
    }
  };

  if (errorCarga) {
    return (
      <section className="pc">
        <div className="feed-msg" role="alert">
          <p>{errorCarga}</p>
          <button className="feed-btn" onClick={() => { setErrorCarga(''); setIntento((n) => n + 1); }}>Reintentar</button>
        </div>
      </section>
    );
  }
  if (!perfil) return <section className="pc"><div className="feed-skel" aria-busy="true" /><div className="feed-skel" /></section>;

  const nombreCompleto = `${perfil.nombre ?? ''} ${perfil.apellido ?? ''}`.trim();
  const ini = iniciales(perfil.nombre, perfil.apellido) || '·';

  return (
    <section className="pc">
      {/* Portada + avatar + nombre */}
      <div className="pc-top">
        <div className="pc-cover">
          {/* La portada y la foto todavía no se pueden subir: el backend no tiene endpoint para imágenes. */}
          <button type="button" className="pc-cover-btn" disabled title="Próximamente"><Camera size={12} /> Editar portada</button>
        </div>
        <div className="pc-id">
          <span className="pc-av" aria-hidden>{ini}</span>
          <button type="button" className="pc-edit" onClick={() => (editando ? cancelar() : setEditando(true))} aria-pressed={editando}>
            <Pencil size={12} /> Editar perfil
          </button>
        </div>
        <h2>{nombreCompleto}</h2>
        <span className="pc-rol">Perfil de cliente</span>
      </div>

      {mensaje && (
        <p className={mensaje.tipo === 'ok' ? 'pc-ok' : 'pc-err pc-err-box'} role={mensaje.tipo === 'ok' ? 'status' : 'alert'}>
          {mensaje.tipo === 'ok' && <CheckCircle2 size={15} />} {mensaje.texto}
        </p>
      )}

      {editando ? (
        <form onSubmit={guardar} noValidate>
          <div className="pc-card">
            <h3><User size={15} /> Información Personal</h3>
            <div className="pc-grid">
              <div className="pc-field">
                <label htmlFor="pc-nombre">Nombre</label>
                <input id="pc-nombre" value={form.nombre} onChange={set('nombre')} maxLength={100} autoComplete="given-name"
                  disabled={guardando} aria-invalid={!!errores.nombre} autoFocus />
                {errores.nombre && <span className="pc-err">{errores.nombre}</span>}
              </div>
              <div className="pc-field">
                <label htmlFor="pc-apellido">Apellido</label>
                <input id="pc-apellido" value={form.apellido} onChange={set('apellido')} maxLength={100} autoComplete="family-name"
                  disabled={guardando} aria-invalid={!!errores.apellido} />
                {errores.apellido && <span className="pc-err">{errores.apellido}</span>}
              </div>
              <div className="pc-field pc-full"><label htmlFor="pc-email">Correo electrónico</label><input id="pc-email" value={perfil.email ?? ''} readOnly /></div>
              <div className="pc-field pc-full">
                <label htmlFor="pc-tel">Teléfono</label>
                <input id="pc-tel" type="tel" inputMode="tel" value={form.telefono} onChange={set('telefono')} placeholder="261 555 0000"
                  autoComplete="tel" disabled={guardando} aria-invalid={!!errores.telefono} />
                {errores.telefono && <span className="pc-err">{errores.telefono}</span>}
              </div>
            </div>
            <p className="pc-nota">El correo electrónico no se puede modificar desde acá.</p>
          </div>

          <div className="pc-actions">
            <button type="button" className="ps-cancel" onClick={cancelar} disabled={guardando}>Cancelar</button>
            <button type="submit" className="feed-btn" disabled={!hayCambios || guardando}>{guardando ? 'Guardando…' : 'Guardar cambios'}</button>
          </div>
        </form>
      ) : (
        <div className="pc-duo">
          <div className="pc-card">
            <div className="pc-card-h">
              <h3>Datos Personales</h3>
              <button type="button" className="pc-icon" aria-label="Editar datos personales" onClick={() => setEditando(true)}><Pencil size={13} /></button>
            </div>
            <ul className="pc-list">
              {perfil.fecha_registro && <li><Calendar size={14} /> {`Se unió en ${mesAnio(perfil.fecha_registro)}`}</li>}
              <li>La zona se indica al publicar cada solicitud.</li>
              {inicial.telefono && <li><Phone size={14} /> {inicial.telefono}</li>}
            </ul>
          </div>

          <form className="pc-card pc-post" onSubmit={(e) => { e.preventDefault(); setModal({ descripcion: texto.trim() }); }}>
            <div className="pc-post-row">
              <span className="pc-av sm" aria-hidden>{ini}</span>
              <input value={texto} onChange={(e) => setTexto(e.target.value)} aria-label="Qué necesitás hoy"
                placeholder={`¿Qué necesitás hoy, ${perfil.nombre ?? ''}?`} />
            </div>
            <button type="submit" className="feed-btn pc-post-btn">Publicar</button>
          </form>
        </div>
      )}

      {modal && (
        <PublicarSolicitudModal
          telefono={inicial.telefono}
          descripcionInicial={modal.descripcion}
          onClose={() => setModal(null)}
          onSuccess={() => setTexto('')}
          onUnauthorized={onUnauthorized}
        />
      )}
    </section>
  );
}
