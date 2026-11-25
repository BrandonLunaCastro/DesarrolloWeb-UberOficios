# Guía técnica del backend de OficiosYa

Guía de estudio para entender cómo se conectan la API, PostgreSQL, la
autenticación, los perfiles, los créditos y Mercado Pago. Está escrita según el
código actual del repositorio y prioriza explicar el flujo, no el frontend.

Para ver las tablas y relaciones en un diagrama, consulta el
[modelo entidad-relación](./MODELO_MER.md).

## 1. Vista general

El backend está construido con:

- **FastAPI** para exponer endpoints HTTP y WebSocket.
- **Pydantic** para validar cuerpos de solicitud y estructurar respuestas.
- **SQLAlchemy** para consultar y modificar PostgreSQL.
- **Alembic** para versionar cambios de la base de datos.
- **Passlib + bcrypt** para almacenar contraseñas como hashes.
- **python-jose + JWT** para autenticar solicitudes.
- **Mercado Pago Checkout Pro** para vender paquetes de créditos.

El punto de entrada es `app/main.py`. Allí se crea la aplicación FastAPI, se
registran los routers y se configura CORS. FastAPI publica la documentación
interactiva en `/docs` y el esquema OpenAPI en `/openapi.json`. El endpoint
`GET /health` sirve para comprobar que el proceso está respondiendo.

## 2. Cómo llega una solicitud a la base

### Conexión síncrona

`app/database.py`:

1. Carga las variables de entorno con `load_dotenv()`.
2. Lee `DATABASE_URL` y los parámetros `DB_POOL_SIZE`,
   `DB_MAX_OVERFLOW` y `DB_POOL_TIMEOUT`.
3. Crea un `engine` de SQLAlchemy usando el driver PostgreSQL síncrono
   `psycopg2`.
4. Crea `SessionLocal`, que fabrica sesiones.
5. Expone `get_db()`, una dependencia de FastAPI que abre una sesión, la
   entrega al endpoint y la cierra al terminar.

Los endpoints síncronos reciben la sesión así:

```python
db: Session = Depends(get_db)
```

`get_db()` **no confirma automáticamente** los cambios. Cada operación que
modifica datos debe llamar a `db.commit()`; si ocurre un error transaccional,
normalmente se llama a `db.rollback()`.

### Conexión asíncrona

`app/async_database.py` crea un segundo engine con `asyncpg`. Normaliza URLs
como `postgres://` o `postgresql://` al formato
`postgresql+asyncpg://` y expone `get_async_db()`.

Los endpoints asíncronos reciben:

```python
db: AsyncSession = Depends(get_async_db)
```

En esos endpoints se usan operaciones con `await`, por ejemplo
`await db.execute(...)`, `await db.commit()` y `await db.refresh(...)`.

El proyecto tiene un pool síncrono y otro asíncrono. Por defecto cada uno
permite 3 conexiones normales y 1 adicional temporal; el máximo combinado es
8 conexiones por proceso. Los valores se ajustan mediante las variables de
pool, sin cambiar las consultas.

**Idea importante:** una sesión pertenece a una operación/solicitud; no se
comparte globalmente entre usuarios.

## 3. Modelos y relaciones principales

Los modelos declarativos viven en `app/models/` y usan el `Base` de
`app/database.py`.

- **`Usuario`** guarda identidad, email, hash de contraseña y `id_rol`.
- **`Rol`** contiene roles como `CLIENTE` y `PRESTADOR`.
- **`Cliente`** guarda el perfil de cliente relacionado con un usuario.
- **`PrestadorServicio`** guarda el perfil de prestador y sus datos de
  servicio.
- **`BilleteraCredito`** guarda el saldo de créditos del prestador.
- **`TransaccionCredito`** registra cada movimiento de la billetera.
- **`PaqueteCredito`** define paquetes activos, cantidad, precio en centavos y
  moneda.
- **`CompraCredito`** guarda una compra, su precio y créditos al momento de
  comprar, su estado y las referencias de Mercado Pago.
- Otros modelos cubren avisos, postulaciones, conversaciones, mensajes,
  notificaciones, calificaciones y fotos.

`Usuario.id_rol` representa **el rol activo**. Los perfiles de cliente y
prestador son registros separados; el cambio de rol conserva los perfiles que
ya existían y crea el perfil faltante. No se agrega una tabla o columna para
alternar roles.

## 4. Registro, contraseñas y login

### Registro: `POST /auth/register`

El cuerpo se valida con `RegisterRequest`. El campo `rol` solo admite
`CLIENTE` o `PRESTADOR`.

El proceso es:

1. Se comprueba que el email no esté registrado.
2. Se busca el registro del rol solicitado en la tabla `rol`.
3. Se calcula un hash con `hashear_contrasena()`, configurado mediante
   Passlib para usar **bcrypt**.
4. Se crea `Usuario` con `password_hash`; la contraseña original no se guarda.
5. Si es cliente, se crea su fila en `cliente`.
6. Si es prestador, se crea su perfil, billetera y una transacción de
   bonificación inicial de 5 créditos.
7. Se confirma la transacción de la base de datos.

Si se viola una restricción de integridad —por ejemplo, un email duplicado
registrado en paralelo— se hace `rollback`. La base también protege la
unicidad del email; la comprobación previa del endpoint no reemplaza esa
restricción.

Un **hash no se puede descifrar** para recuperar la contraseña. En el login se
compara la contraseña ingresada contra el hash guardado mediante
`verificar_contrasena()`.

### Login: `POST /auth/login`

El backend busca el usuario por email, carga su rol y compara la contraseña.
Si coincide, crea un JWT firmado y responde con `access_token` y
`token_type: "bearer"`. Si el email o la contraseña no coinciden, responde
`401`.

### JWT y endpoints protegidos

El frontend envía el token en el encabezado:

```http
Authorization: Bearer <token>
```

`HTTPBearer` extrae el bearer token. `get_user_id_from_token()` lo verifica
con `python-jose`, el algoritmo `HS256` y `SECRET_KEY`. El claim `sub` contiene
el ID del usuario. `get_current_user_id()` entrega ese ID a los endpoints;
`get_current_user()` además consulta al usuario y su rol actual en la base.

Por eso, las operaciones con permisos no deberían confiar únicamente en datos
que envía el cliente: consultan la identidad y, cuando corresponde, el rol o la
propiedad del recurso en el backend. Los errores habituales son `401` para
sesión inválida, `403` para falta de permiso, `404` para recurso inexistente
y `409` para un conflicto con el estado del recurso.

**Limitaciones importantes del código actual:**

- `SECRET_KEY` está definida directamente en `app/auth.py`; para producción
  debería provenir de una variable secreta de entorno y ser aleatoria y
  privada.
- `crear_token()` no incluye un claim de expiración (`exp`). Por eso no hay
  vencimiento automático del JWT en la implementación actual.
- El JWT incluye el rol al momento del login, pero el cambio de rol actualiza
  la base de datos y no emite otro token. La autorización del backend consulta
  el rol actual desde la base, no debe tratar el claim `rol` del token como
  estado actualizado.

## 5. Cambio entre cliente y prestador

`PUT /auth/me/rol` requiere JWT y recibe:

```json
{ "rol": "PRESTADOR" }
```

El endpoint bloquea la fila del usuario durante la operación, busca el rol y:

- Al cambiar a `PRESTADOR`, crea el perfil y la billetera si faltan. La
  bonificación inicial se registra una sola vez, al crear ese perfil.
- Al cambiar a `CLIENTE`, crea el perfil de cliente si falta.
- Actualiza el rol activo del usuario y confirma los cambios en una
  transacción.

Esta operación usa las tablas existentes. Si falta la fila de un rol en la
tabla `rol`, devuelve un error de configuración (`503`).

## 6. Créditos y consistencia del saldo

`app/services/creditos.py` contiene la lógica común de movimientos.

- `TipoTransaccionEnum` distingue recargas, consumos, devoluciones y
  bonificaciones.
- `registrar_transaccion()` valida que el monto tenga el signo esperado,
  bloquea al prestador y a su billetera con `FOR UPDATE`, calcula el nuevo
  saldo y registra el movimiento.
- El saldo se mantiene tanto en `BilleteraCredito.saldo_actual` como en
  `PrestadorServicio.saldo_creditos`; el servicio actualiza ambos juntos.
- Si el saldo resultante sería negativo, se hace rollback y la operación se
  rechaza.

El bono mensual se calcula a partir de la fecha de inicio del ciclo y de los
meses ya acreditados. El comando
`python -m app.scripts.acreditar_creditos_mensuales` procesa los bonos
vencidos y confirma la transacción. Se programa periódicamente en el hosting.

Los precios de los paquetes se guardan en **centavos** para evitar errores de
punto flotante. Por ejemplo, `300000` centavos equivalen a `ARS 3000`.

## 7. Mercado Pago: flujo de principio a fin

La integración es **Checkout Pro** y usa la API REST de Mercado Pago
directamente con `urllib`; el backend no tiene instalado el SDK oficial. El
access token corresponde a la cuenta vendedora de la empresa. El prestador es
el comprador de créditos; el flujo no divide el pago entre prestadores.

### Configuración

En desarrollo se usan variables locales ignoradas por Git; en Render se
configuran en el entorno del servicio backend:

| Variable | Propósito |
|---|---|
| `MERCADOPAGO_ENVIRONMENT` | `test` para checkout de prueba o `production` para cobros reales. |
| `MERCADOPAGO_ACCESS_TOKEN` | Token privado de la cuenta vendedora; solo backend. |
| `MERCADOPAGO_WEBHOOK_SECRET` | Clave de firma configurada para el webhook. |
| `MERCADOPAGO_WEBHOOK_URL` | URL pública HTTPS del endpoint de notificaciones. |
| `FRONTEND_URL` | Origen al que Checkout Pro devuelve al comprador y que también se agrega a CORS. |

El entorno se selecciona explícitamente con `MERCADOPAGO_ENVIRONMENT`; no se
deduce del prefijo del token. En `test` se usa `sandbox_init_point`; en
`production`, `init_point`.

La Public Key no se usa en este flujo porque el backend crea la preferencia y
el comprador paga en la página alojada por Mercado Pago. El backend tampoco
recibe ni guarda números de tarjeta.

### Crear una compra

1. El prestador autenticado llama `POST /creditos/compras` con
   `{"paquete_id": ...}`.
2. El backend comprueba que Mercado Pago esté configurado y que el usuario
   tenga perfil de prestador.
3. Busca un paquete activo y copia cantidad, precio y moneda a
   `CompraCredito`. Así, un cambio futuro del precio del paquete no modifica
   una compra ya iniciada.
4. Guarda la compra como `PENDIENTE`.
5. `crear_preferencia()` llama `POST /checkout/preferences` en Mercado Pago.
   Convierte centavos a unidades de moneda y envía el ID de compra como
   `external_reference`, además de las URL de retorno y notificación.
6. La clave `X-Idempotency-Key` se genera de forma determinista para esa
   compra, evitando crear preferencias duplicadas al reintentar la misma
   operación.
7. El backend guarda el ID de preferencia y la URL de checkout y la devuelve
   al cliente.

El retorno del navegador a `FRONTEND_URL` **no confirma el pago**. Solo sirve
para que la persona vuelva al sitio y consulte el estado.

### Confirmar el pago con el webhook

Mercado Pago notifica a `POST /creditos/pagos/webhook`. Este endpoint no usa
JWT de usuario: valida la firma `x-signature` con
`MERCADOPAGO_WEBHOOK_SECRET` mediante HMAC-SHA256 y comparación de tiempo
constante.

Después:

1. Extrae el ID del pago de la notificación.
2. Consulta ese pago a la API de Mercado Pago usando el Access Token privado.
3. Comprueba que coincidan el ID, la `external_reference` de la compra, el
   importe y la moneda.
4. Bloquea la compra en la base para evitar procesarla simultáneamente más de
   una vez.
5. Si el pago está `approved`, registra una transacción positiva, actualiza la
   billetera y marca la compra como `APROBADA`.
6. Si está `rejected` o `cancelled`, guarda el estado correspondiente sin
   acreditar créditos. Otros estados permanecen pendientes.

El estado de la compra y las restricciones únicas sobre la referencia de pago
y la transacción ayudan a que una notificación repetida no acredite créditos
dos veces. La confirmación siempre depende del webhook validado, no de la
respuesta del navegador.

## 8. Endpoints principales

Salvo `/health` y el webhook de Mercado Pago, los endpoints siguientes
requieren autenticación cuando así se indica. En `/docs` se puede consultar el
contrato completo, los parámetros y los esquemas Pydantic.

### Autenticación y cuenta

| Método | Ruta | Uso |
|---|---|---|
| `POST` | `/auth/register` | Crear usuario y perfil inicial. Público. |
| `POST` | `/auth/login` | Verificar credenciales y obtener JWT. Público. |
| `GET` | `/auth/me` | Consultar usuario y rol activo. JWT. |
| `PUT` | `/auth/me/rol` | Cambiar el rol activo y asegurar su perfil. JWT. |
| `GET` | `/auth/me/saldo` | Consultar saldo del prestador. JWT. |
| `GET`, `PUT` | `/usuarios/perfil` | Consultar o actualizar el perfil. JWT. |

### Avisos, postulaciones y presupuestos

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/avisos/zona` | Avisos abiertos en la zona del prestador. |
| `GET` | `/avisos/mios` | Avisos del cliente autenticado. |
| `POST` | `/avisos` | Publicar un aviso. |
| `POST` | `/avisos/{id_aviso}/postulaciones` | Postularse como prestador. |
| `POST` | `/avisos/{id_aviso}/finalizar` | Finalizar un trabajo como cliente. |
| `PUT` | `/presupuestos/{id_postulacion}/presupuesto` | Actualizar un presupuesto como prestador. |
| `POST` | `/presupuestos/{id_postulacion}/aceptar` | Aceptar un presupuesto como cliente. |
| `GET` | `/prestadores/{id_prestador}/presupuestos` | Consultar presupuestos enviados por el prestador autenticado. |
| `GET` | `/clientes/{id_cliente}/presupuestos` | Consultar presupuestos recibidos por el cliente autenticado. |

Estos endpoints aplican validaciones de rol, propiedad y estado. Por ejemplo,
un cliente no puede postularse como prestador y solo se puede finalizar un
trabajo que esté en proceso y pertenezca a ese cliente.

### Créditos y Mercado Pago

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/creditos/paquetes` | Listar paquetes activos. JWT. |
| `POST` | `/creditos/compras` | Crear compra pendiente y preferencia de Checkout Pro. JWT de prestador. |
| `GET` | `/creditos/compras` | Historial de compras del prestador. |
| `GET` | `/creditos/compras/{compra_id}` | Consultar el estado de una compra propia. |
| `POST` | `/creditos/compras/{compra_id}/checkout` | Reintentar la creación del checkout pendiente. |
| `POST` | `/creditos/pagos/webhook` | Confirmación servidor a servidor enviada por Mercado Pago. Firma, sin JWT de usuario. |
| `GET` | `/creditos/movimientos` | Historial de movimientos de la billetera. JWT. |

Otros grupos registrados en `app/main.py` incluyen conversaciones y mensajes,
notificaciones, calificaciones y fotos de portafolio. El chat y las
notificaciones exponen también WebSockets autenticados. Su lista detallada está
en `/docs`.

## 9. Validación de datos y respuestas

Los esquemas de `app/schemas/` son modelos Pydantic. FastAPI los usa para
validar cuerpos, parámetros y respuestas. Ejemplos:

- `RegisterRequest` solo admite roles conocidos.
- `IniciarCompraRequest` recibe el ID del paquete, no el precio enviado por
  el navegador.
- `CompraCreditoResponse` define qué datos de una compra salen por la API.

El servidor decide el precio consultando el paquete en la base. No se debe
confiar en un importe calculado por el cliente. FastAPI suele responder `422`
cuando el cuerpo no cumple el esquema.

## 10. Migraciones de base de datos

Las migraciones están en `backend/alembic/versions/`. Alembic versiona el
esquema y registra la revisión aplicada en `alembic_version`; no se crean
tablas automáticamente al iniciar FastAPI.

`backend/alembic/env.py` carga el `.env`, toma `DATABASE_URL` e importa los
modelos para construir `Base.metadata`.

Para actualizar la base desde la carpeta `backend`:

```powershell
python -m alembic upgrade head
```

En Render debe ejecutarse contra la base de datos de Render, no contra una
base local distinta. La migración
`71e4c8a9d2f0_quitar_campos_de_pasarela_externa.py` se conserva porque una
versión previa pudo haberla registrado en la base. La migración posterior
`a3c6d9e2f410_restaurar_campos_pasarela_creditos.py` restaura los campos que
necesita la integración real. No elimines esa cadena sin comprobar primero
la revisión `alembic_version` de cada entorno.

## 11. Pruebas y ejecución local

Desde `backend`, las pruebas se pueden ejecutar con:

```powershell
python -m unittest discover -s tests
```

Para iniciar la API local:

```powershell
python -m uvicorn app.main:app --reload
```

Luego se puede abrir `http://127.0.0.1:8000/docs`. Para hacer pruebas reales
de webhook, Mercado Pago necesita una URL pública HTTPS; `localhost` no es
accesible desde sus servidores.

## 12. Preguntas que podrían hacerte

**¿Por qué guardan un hash y no la contraseña?**  
Porque bcrypt transforma la contraseña en un hash no reversible. En el login
se verifica la entrada contra el hash; no se recupera la contraseña original.

**¿Qué diferencia hay entre `get_db` y `get_async_db`?**  
`get_db` entrega una `Session` síncrona con el driver `psycopg2`.
`get_async_db` entrega una `AsyncSession` con `asyncpg`; sus consultas y
confirmaciones usan `await`.

**¿Cómo evita el sistema acreditar dos veces una compra?**  
Bloquea la fila de compra durante la confirmación, no vuelve a procesar una
compra que ya salió de `PENDIENTE` y usa restricciones únicas en la base.

**¿Por qué no se acreditan créditos al volver del checkout?**  
La persona puede cerrar la pestaña o alterar una URL de retorno. El webhook
firmado se valida en el backend y el pago se consulta directamente a Mercado
Pago.

**¿Quién recibe el dinero de la compra?**  
La cuenta vendedora cuya credencial está en `MERCADOPAGO_ACCESS_TOKEN`; en
este diseño la empresa vende créditos y el prestador los compra.

**¿Para qué sirve `external_reference`?**  
Relaciona el pago consultado en Mercado Pago con el ID de
`CompraCredito` guardado por el backend.

**¿Qué confirma que un webhook es legítimo?**  
La firma HMAC recibida, verificada con el secreto del webhook. Además, el
backend obtiene el pago desde la API oficial y comprueba referencia, importe
y moneda.

**¿Qué hace Alembic que no hace SQLAlchemy?**  
SQLAlchemy mapea objetos y ejecuta consultas; Alembic aplica cambios
versionados al esquema de la base.

**¿Qué conviene mejorar antes de producción?**  
Mover `SECRET_KEY` a una variable secreta, agregar vencimiento y renovación
segura a los JWT, validar las URLs y secretos por entorno, y probar el flujo
completo con credenciales y usuarios de prueba antes de activar pagos reales.

## 13. Tecnologías y servicios: qué son y cómo los usamos

No todo lo que se suele llamar “servicio” es un proveedor externo. FastAPI,
Passlib y SQLAlchemy son bibliotecas del backend; JWT es un estándar de
tokens. Supabase, Mercado Pago, Cloudinary y Render sí son servicios
externos/plataformas que el sistema consume o donde se ejecuta.

### API y servidor

**FastAPI — framework de la API.**  
Permite declarar rutas HTTP, métodos (`GET`, `POST`, `PUT`, etc.), dependencias
con `Depends()` y respuestas. En este proyecto organiza los routers de
autenticación, avisos, créditos, chat y demás módulos. También genera `/docs`
y `/openapi.json`. FastAPI coordina la solicitud; la lógica de negocio está
en los endpoints, servicios y modelos del proyecto.

**Uvicorn — servidor ASGI.**  
Es el proceso que recibe conexiones HTTP/WebSocket y ejecuta la aplicación
FastAPI. En desarrollo se inicia con
`python -m uvicorn app.main:app --reload`; en Render se ejecuta el comando
configurado para el servicio. FastAPI define la aplicación y Uvicorn la sirve.

**Pydantic — validación de datos.**  
Los esquemas en `app/schemas/` declaran qué datos acepta y devuelve cada
operación. FastAPI los usa para validar JSON, parámetros y archivos/formularios
antes de ejecutar la lógica. Un dato mal formado normalmente produce una
respuesta `422`.

**Starlette y WebSockets.**  
FastAPI se apoya en Starlette para componentes ASGI, middleware y conexiones
WebSocket. La aplicación usa WebSockets para chat y notificaciones en tiempo
real. No hay un proveedor de WebSocket aparte: las conexiones las atiende la
misma API.

### Base de datos

**PostgreSQL — motor relacional.**  
Guarda usuarios, roles, perfiles, avisos, postulaciones, compras, créditos,
mensajes y demás información estructurada.

**Supabase — servicio administrado de PostgreSQL.**  
La base PostgreSQL del proyecto está alojada en Supabase. El backend se conecta
usando `DATABASE_URL`; en esta integración Supabase funciona como proveedor de
base de datos. La autenticación de la aplicación es propia (JWT del backend),
no la autenticación de Supabase.

**SQLAlchemy — ORM y acceso a datos.**  
Mapea clases Python a tablas y permite crear consultas usando modelos, en vez
de concatenar SQL manualmente. También maneja sesiones y transacciones. El
proyecto tiene sesiones síncronas (`psycopg2`) y asíncronas (`asyncpg`).

**Alembic — migraciones.**  
Versiona modificaciones del esquema de PostgreSQL. Se usa para aplicar
cambios de columnas, tablas y restricciones de forma ordenada entre desarrollo
y producción; no es el ORM ni el servidor de base.

### Autenticación y seguridad

**Passlib — interfaz para hash de contraseñas.**  
Se usa en `app/auth.py` para generar y verificar hashes. Evita implementar
manualmente el manejo criptográfico de contraseñas y permite configurar el
esquema usado.

**bcrypt — algoritmo de hash de contraseñas.**  
Passlib está configurado con `bcrypt`. En el registro se guarda el resultado
de `pwd_context.hash()` en `password_hash`; en el login se usa
`pwd_context.verify()`. No se guarda ni se puede recuperar la contraseña
original desde ese hash.

**JWT — estándar para transportar identidad autenticada.**  
El servidor firma un token con claims como el identificador `sub`. El cliente
lo envía como `Authorization: Bearer ...`; el backend verifica la firma antes
de aceptar una ruta protegida. Un JWT firmado **no está cifrado**: su payload
puede leerse, así que no deben incluirse contraseñas, claves ni información
secreta. En este proyecto se usa el algoritmo HS256 y la clave configurada en
`app/auth.py`.

**python-jose — biblioteca que implementa JWT en Python.**  
`jwt.encode()` crea el token y `jwt.decode()` verifica su firma en
`get_user_id_from_token()`. JWT es el formato/estándar; python-jose es la
biblioteca que usamos para trabajar con él.

### Pagos y archivos

**Mercado Pago — proveedor de pagos.**  
Checkout Pro aloja el checkout para que el prestador pague el paquete. El
backend crea la preferencia por REST, recibe el webhook firmado, consulta el
pago en la API de Mercado Pago y recién entonces acredita los créditos. La
integración usa `urllib` de Python; no usa el SDK oficial. Sus credenciales
privadas solo deben estar en variables de entorno del backend.

**Cloudinary — almacenamiento de imágenes.**  
Se usa para las fotos de portafolio y comprobantes. El backend valida el
archivo, lo sube a Cloudinary y guarda en PostgreSQL su URL segura y su
`public_id`. El `public_id` permite eliminar después el archivo del proveedor.
Las credenciales se leen de `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` y
`CLOUDINARY_API_SECRET`.

**python-multipart — recepción de archivos/formularios.**  
Permite que FastAPI procese solicitudes `multipart/form-data` para endpoints
que reciben imágenes. No almacena los archivos: el almacenamiento persistente
lo hace Cloudinary.

### Configuración y despliegue

**python-dotenv — configuración local.**  
Carga las variables definidas en un `.env` local, como `DATABASE_URL`. El
archivo no debe subirse al repositorio. En Render, las variables se cargan
desde la configuración del servicio y no dependen del `.env` de la
computadora del desarrollador.

**Render — plataforma de despliegue.**  
Ejecuta el backend y publica la API en una URL HTTPS. También permite definir
variables de entorno para producción. No reemplaza FastAPI: Render hospeda el
proceso que ejecuta Uvicorn y la aplicación.

### Cómo se conectan (resumen para presentar)

```text
Usuario / frontend
        │ HTTP con Bearer JWT
        ▼
Render ejecuta Uvicorn
        │
        ▼
FastAPI valida solicitud y esquema Pydantic
        │
        ├── Passlib/bcrypt verifica contraseñas
        ├── python-jose verifica JWT
        ├── SQLAlchemy consulta PostgreSQL en Supabase
        ├── Mercado Pago procesa compras y envía webhooks
        └── Cloudinary recibe y almacena imágenes
```

### Explicación oral breve

> “El backend está hecho con FastAPI y corre con Uvicorn. FastAPI recibe las
> solicitudes, valida los datos con Pydantic y deriva cada operación a su
> endpoint o servicio. SQLAlchemy conecta la lógica con PostgreSQL, que está
> alojado en Supabase, y Alembic mantiene versionado el esquema. Las
> contraseñas se guardan como hashes bcrypt usando Passlib. Para las sesiones
> usamos JWT firmado con HS256, que el backend valida en cada ruta protegida.
> Para vender créditos integramos Checkout Pro de Mercado Pago: la acreditación
> se hace solo después de validar el webhook y consultar el pago. Cloudinary
> almacena las imágenes; en la base guardamos sus URLs e identificadores.
> Render aloja el backend y sus variables de entorno.”

**Aclaración de seguridad para la exposición:** la implementación actual debe
mejorarse antes de producción: la clave de firma JWT está hardcodeada y el
token no incluye expiración. Es correcto describir cómo funciona hoy y agregar
que la solución recomendada es guardar una clave aleatoria en el entorno,
establecer vencimiento y diseñar renovación/revocación de tokens.
