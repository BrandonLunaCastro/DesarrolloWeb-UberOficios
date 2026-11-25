import os
import unittest
from unittest.mock import patch

from app.models.creditos import CompraCredito
from app.services.mercado_pago import (
    MercadoPagoError,
    configuracion_mercado_pago_disponible,
    crear_preferencia,
)


class MercadoPagoEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.compra = CompraCredito(
            id=123,
            paquete_id=1,
            cantidad_creditos=5,
            precio_centavos=300000,
            moneda="ARS",
        )
        self.entorno = {
            "MERCADOPAGO_ACCESS_TOKEN": "APP_USR_test_token",
            "MERCADOPAGO_WEBHOOK_SECRET": "webhook-secret",
            "MERCADOPAGO_WEBHOOK_URL": "https://api.example.com/creditos/pagos/webhook",
            "FRONTEND_URL": "https://app.example.com",
        }
        self.respuesta_preferencia = {
            "id": "preference-id",
            "sandbox_init_point": "https://sandbox.example.com/checkout",
            "init_point": "https://production.example.com/checkout",
        }

    @patch("app.services.mercado_pago._solicitud_mercado_pago")
    def test_entorno_test_usa_sandbox_aunque_el_token_empiece_con_app_usr(
        self,
        solicitar,
    ):
        solicitar.return_value = self.respuesta_preferencia
        with patch.dict(os.environ, self.entorno, clear=True):
            os.environ["MERCADOPAGO_ENVIRONMENT"] = "test"

            preferencia = crear_preferencia(self.compra)

        self.assertEqual(preferencia["url"], self.respuesta_preferencia["sandbox_init_point"])

    @patch("app.services.mercado_pago._solicitud_mercado_pago")
    def test_entorno_production_usa_init_point(self, solicitar):
        solicitar.return_value = self.respuesta_preferencia
        with patch.dict(os.environ, self.entorno, clear=True):
            os.environ["MERCADOPAGO_ENVIRONMENT"] = "production"

            preferencia = crear_preferencia(self.compra)

        self.assertEqual(preferencia["url"], self.respuesta_preferencia["init_point"])

    @patch("app.services.mercado_pago._solicitud_mercado_pago")
    def test_rechaza_entorno_no_configurado_sin_llamar_a_mercado_pago(
        self,
        solicitar,
    ):
        with patch.dict(os.environ, self.entorno, clear=True):
            with self.assertRaises(MercadoPagoError):
                crear_preferencia(self.compra)

        solicitar.assert_not_called()

    def test_pasarela_no_esta_disponible_sin_entorno_explicito(self):
        with patch.dict(os.environ, self.entorno, clear=True):
            self.assertFalse(configuracion_mercado_pago_disponible())
