import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth import get_user_id_from_token
from app.database import Base
from app.models.Cliente import Cliente
from app.models.PrestadorServicio import PrestadorServicio
from app.models.creditos import BilleteraCredito, TransaccionCredito
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.routes.auth import register
from app.schemas.auth import RegisterRequest


class AuthRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(
            self.engine,
            tables=[
                Rol.__table__,
                Usuario.__table__,
                Cliente.__table__,
                PrestadorServicio.__table__,
                BilleteraCredito.__table__,
                TransaccionCredito.__table__,
            ],
        )
        self.db = Session(self.engine)
        self.db.add(Rol(nombre="CLIENTE"))
        self.db.add(Rol(nombre="PRESTADOR"))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_registro_devuelve_sesion_activa(self):
        resultado = register(
            RegisterRequest(
                nombre="Ana",
                apellido="Prueba",
                email="ana@example.com",
                contrasena="ClaveSegura123",
                rol="CLIENTE",
            ),
            self.db,
        )

        self.assertEqual(resultado["rol"], "CLIENTE")
        self.assertEqual(resultado["token_type"], "bearer")
        self.assertEqual(
            get_user_id_from_token(resultado["access_token"]),
            resultado["id_usuario"],
        )
        self.assertIsNotNone(
            self.db.query(Cliente)
            .filter(Cliente.id_usuario == resultado["id_usuario"])
            .one_or_none()
        )


if __name__ == "__main__":
    unittest.main()
