from datetime import datetime, timedelta, timezone
import unittest

from app.services.vencimiento_avisos import DURACION_AVISO, aviso_vencido


class AvisoVencidoTests(unittest.TestCase):
    def test_expira_al_cumplir_las_72_horas(self):
        ahora = datetime(2025, 1, 4, tzinfo=timezone.utc)
        fecha_publicacion = ahora - DURACION_AVISO

        self.assertTrue(aviso_vencido(fecha_publicacion, ahora))

    def test_sigue_abierto_antes_de_las_72_horas(self):
        ahora = datetime(2025, 1, 4, tzinfo=timezone.utc)
        fecha_publicacion = ahora - DURACION_AVISO + timedelta(microseconds=1)

        self.assertFalse(aviso_vencido(fecha_publicacion, ahora))

    def test_trata_fecha_sin_zona_como_utc(self):
        ahora = datetime(2025, 1, 4, tzinfo=timezone.utc)
        fecha_publicacion = (ahora - DURACION_AVISO).replace(tzinfo=None)

        self.assertTrue(aviso_vencido(fecha_publicacion, ahora))


if __name__ == "__main__":
    unittest.main()
