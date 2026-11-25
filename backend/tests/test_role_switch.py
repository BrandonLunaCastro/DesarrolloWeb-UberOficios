import unittest

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from app.database import Base
from app.models.Cliente import Cliente
from app.models.PrestadorServicio import PrestadorServicio
from app.models.creditos import BilleteraCredito, TransaccionCredito
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.routes.auth import cambiar_rol_usuario
from app.schemas.auth import CambiarRolRequest


class CambiarRolTests(unittest.TestCase):
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
        rol_cliente = Rol(nombre="CLIENTE")
        self.db.add(rol_cliente)
        self.db.add(Rol(nombre="PRESTADOR"))
        self.db.flush()
        usuario = Usuario(
            nombre="Ana",
            apellido="Prueba",
            email="ana@example.com",
            password_hash="hash",
            rol=rol_cliente,
        )
        self.db.add(usuario)
        self.db.flush()
        self.id_usuario = usuario.id_usuario
        self.db.add(Cliente(id_usuario=self.id_usuario))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_crea_perfiles_y_bono_una_sola_vez_al_alternar_roles(self):
        prestador = cambiar_rol_usuario(
            CambiarRolRequest(rol="PRESTADOR"),
            self.db,
            self.id_usuario,
        )

        self.assertEqual(prestador["rol"], "PRESTADOR")
        perfil_prestador = (
            self.db.query(PrestadorServicio)
            .filter(PrestadorServicio.id_usuario == self.id_usuario)
            .one()
        )
        billetera = (
            self.db.query(BilleteraCredito)
            .filter(BilleteraCredito.prestador_id == perfil_prestador.id_prestador)
            .one()
        )
        self.assertEqual(perfil_prestador.saldo_creditos, 5)
        self.assertEqual(billetera.saldo_actual, 5)

        cliente = cambiar_rol_usuario(
            CambiarRolRequest(rol="CLIENTE"),
            self.db,
            self.id_usuario,
        )
        self.assertEqual(cliente["rol"], "CLIENTE")
        self.assertIsNotNone(
            self.db.query(Cliente)
            .filter(Cliente.id_usuario == self.id_usuario)
            .one_or_none()
        )

        cambiar_rol_usuario(
            CambiarRolRequest(rol="PRESTADOR"),
            self.db,
            self.id_usuario,
        )
        cantidad_bonos = (
            self.db.query(func.count(TransaccionCredito.id))
            .filter(
                TransaccionCredito.billetera_id == billetera.id,
                TransaccionCredito.referencia_tipo == "bonificacion_inicial",
            )
            .scalar()
        )
        self.assertEqual(cantidad_bonos, 1)


if __name__ == "__main__":
    unittest.main()
