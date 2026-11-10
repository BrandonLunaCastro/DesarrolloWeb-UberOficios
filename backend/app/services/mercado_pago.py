import hashlib
import hmac
import json
import os
import re
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import NAMESPACE_URL, uuid5

from app.models.creditos import CompraCredito


class MercadoPagoError(Exception):
    pass


def configuracion_mercado_pago_disponible() -> bool:
    return all(
        os.getenv(variable)
        for variable in (
            "MERCADOPAGO_ACCESS_TOKEN",
            "MERCADOPAGO_WEBHOOK_SECRET",
            "MERCADOPAGO_WEBHOOK_URL",
        )
    )


def _solicitud_mercado_pago(
    metodo: str,
    ruta: str,
    *,
    payload: dict | None = None,
    idempotency_key: str | None = None,
) -> dict:
    token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    if not token:
        raise MercadoPagoError("La pasarela de pago no está configurada")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key

    request = Request(
        f"https://api.mercadopago.com{ruta}",
        data=data,
        headers=headers,
        method=metodo,
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read())
    except HTTPError as error:
        raise MercadoPagoError(
            f"Mercado Pago rechazó la solicitud (HTTP {error.code})"
        ) from error
    except (URLError, TimeoutError) as error:
        raise MercadoPagoError("No se pudo conectar con Mercado Pago") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MercadoPagoError("Mercado Pago devolvió una respuesta inválida") from error

    if not isinstance(result, dict):
        raise MercadoPagoError("Mercado Pago devolvió una respuesta inválida")
    return result


def crear_preferencia(compra: CompraCredito) -> dict:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    return_url = f"{frontend_url}/?compra_id={compra.id}"
    respuesta = _solicitud_mercado_pago(
        "POST",
        "/checkout/preferences",
        idempotency_key=str(uuid5(NAMESPACE_URL, f"oficiosya:compra-credito:{compra.id}")),
        payload={
            "items": [
                {
                    "id": str(compra.paquete_id),
                    "title": f"Créditos para OficiosYa ({compra.cantidad_creditos})",
                    "quantity": 1,
                    "currency_id": compra.moneda,
                    "unit_price": float(Decimal(compra.precio_centavos) / 100),
                }
            ],
            "external_reference": str(compra.id),
            "notification_url": os.environ["MERCADOPAGO_WEBHOOK_URL"],
            "back_urls": {
                "success": return_url,
                "pending": return_url,
                "failure": return_url,
            },
            "auto_return": "approved",
        },
    )
    preference_id = respuesta.get("id")
    token = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
    payment_url = (
        respuesta.get("sandbox_init_point")
        if token.startswith("TEST-")
        else respuesta.get("init_point")
    )
    if not preference_id or not payment_url:
        raise MercadoPagoError("Mercado Pago no devolvió un enlace de pago válido")
    return {"id": str(preference_id), "url": payment_url}


def obtener_pago(payment_id: str) -> dict:
    if not re.fullmatch(r"\d{1,30}", payment_id):
        raise MercadoPagoError("Identificador de pago inválido")
    return _solicitud_mercado_pago("GET", f"/v1/payments/{payment_id}")


def firma_webhook_valida(
    *,
    payment_id: str,
    request_id: str | None,
    signature: str | None,
) -> bool:
    secret = os.getenv("MERCADOPAGO_WEBHOOK_SECRET")
    if not secret or not request_id or not signature:
        return False

    valores = {}
    for componente in signature.split(","):
        clave, separador, valor = componente.strip().partition("=")
        if separador:
            valores[clave] = valor
    timestamp = valores.get("ts")
    firma_recibida = valores.get("v1")
    if not timestamp or not firma_recibida:
        return False

    manifiesto = f"id:{payment_id};request-id:{request_id};ts:{timestamp};"
    firma_esperada = hmac.new(
        secret.encode("utf-8"),
        manifiesto.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(firma_esperada, firma_recibida)


def importe_pago_valido(pago: dict, compra: CompraCredito) -> bool:
    try:
        importe_centavos = Decimal(str(pago["transaction_amount"])) * 100
        return (
            importe_centavos == Decimal(compra.precio_centavos)
            and pago.get("currency_id") == compra.moneda
        )
    except (KeyError, ArithmeticError, ValueError):
        return False
