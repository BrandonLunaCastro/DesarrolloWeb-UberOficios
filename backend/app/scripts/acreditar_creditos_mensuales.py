import logging

from app.database import SessionLocal
from app.services.creditos import acreditar_bonos_mensuales


def main() -> None:
    db = SessionLocal()
    try:
        prestadores, creditos = acreditar_bonos_mensuales(db)
        db.commit()
    finally:
        db.close()

    logging.info(
        "Bono mensual acreditado: %s prestadores, %s créditos",
        prestadores,
        creditos,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
