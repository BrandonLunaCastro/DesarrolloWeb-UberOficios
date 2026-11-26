import asyncio
from decimal import Decimal
import unittest

from app.routes.avisos import (
    _normalizar_categoria,
    _oficio_coincide_con_categoria,
)
from app.services.postulaciones import _rangos_presupuesto_por_aviso


class ResultadoSimulado:
    def all(self):
        return [
            (1, Decimal("12000.00"), Decimal("18000.00")),
            (2, Decimal("7500.00"), Decimal("7500.00")),
        ]


class SesionSimulada:
    def __init__(self):
        self.consultas = 0

    async def execute(self, _consulta):
        self.consultas += 1
        return ResultadoSimulado()


class CatalogoAvisosTests(unittest.TestCase):
    def test_normaliza_oficios_separados(self):
        self.assertEqual(_normalizar_categoria("Plomería"), "plomeria")
        self.assertEqual(_normalizar_categoria("Gasista"), "gas")
        self.assertEqual(_normalizar_categoria("Mecánica"), "mecanica")

    def test_feed_coincide_oficio_y_categoria_y_no_mezcla_servicios(self):
        self.assertTrue(_oficio_coincide_con_categoria("Plomería", "Plomería"))
        self.assertTrue(_oficio_coincide_con_categoria("Mecánica", "Mecánica"))
        self.assertFalse(_oficio_coincide_con_categoria("Plomería", "Electricidad"))
        self.assertFalse(_oficio_coincide_con_categoria("Mecánica", "Cerrajería"))

    def test_categoria_legacy_plomeria_y_gas_coincide_con_ambos_oficios(self):
        self.assertTrue(_oficio_coincide_con_categoria("Plomería", "Plomería y Gas"))
        self.assertTrue(_oficio_coincide_con_categoria("Gas", "Plomería y Gas"))
        self.assertFalse(_oficio_coincide_con_categoria("Electricidad", "Plomería y Gas"))


class RangoPresupuestosTests(unittest.TestCase):
    def test_devuelve_minimo_y_maximo_por_aviso(self):
        db = SesionSimulada()

        resultado = asyncio.run(_rangos_presupuesto_por_aviso(db, {1, 2}))

        self.assertEqual(
            resultado,
            {
                1: (Decimal("12000.00"), Decimal("18000.00")),
                2: (Decimal("7500.00"), Decimal("7500.00")),
            },
        )
        self.assertEqual(db.consultas, 1)

    def test_no_consulta_si_no_hay_avisos(self):
        db = SesionSimulada()

        self.assertEqual(asyncio.run(_rangos_presupuesto_por_aviso(db, set())), {})
        self.assertEqual(db.consultas, 0)


if __name__ == "__main__":
    unittest.main()
