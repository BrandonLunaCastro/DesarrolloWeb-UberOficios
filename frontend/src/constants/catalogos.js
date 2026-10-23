// El backend guarda `oficio` y `zona` como texto libre (no hay endpoints /oficios ni /zonas).
// Mantenemos las listas acá para que cliente y prestador escriban EXACTAMENTE lo mismo:
// GET /avisos/zona compara la zona del prestador con la del aviso (sin mayúsculas ni espacios).
// TODO: cuando el back exponga catálogos, reemplazar por una llamada a la API.
export const ZONAS = ['Capital', 'Godoy Cruz', 'Guaymallén', 'Las Heras', 'Luján de Cuyo', 'Maipú'];

// Los 4 primeros son los "Servicios rápidos" del Figma.
export const OFICIOS = [
  'Electricidad',
  'Plomería',
  'Gasista',
  'Albañilería',
  'Pintura',
  'Carpintería',
  'Cerrajería',
  'Aire acondicionado',
  'Otro',
];
export const SERVICIOS_RAPIDOS = [
  { oficio: 'Electricidad', emoji: '⚡' },
  { oficio: 'Plomería', emoji: '💧' },
  { oficio: 'Gasista', emoji: '🔥' },
  { oficio: 'Albañilería', emoji: '🧱' },
];
