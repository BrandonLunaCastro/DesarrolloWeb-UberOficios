# Guía de instalación y ejecución de UberOficios

Esta guía explica cómo preparar el proyecto en Windows para ejecutarlo en una
computadora nueva. El sistema tiene un backend con FastAPI, un frontend con
React y una base de datos PostgreSQL.

## Estructura del proyecto

```text
DesarrolloWeb-UberOficios/
├── backend/
│   ├── app/
│   │   ├── models/       # Modelos de datos
│   │   ├── routes/       # Rutas y endpoints de la API
│   │   ├── schemas/      # Esquemas de validación
│   │   ├── scripts/      # Tareas ejecutables del backend
│   │   ├── services/     # Lógica de servicios e integraciones
│   │   ├── main.py       # Inicialización de FastAPI
│   │   ├── auth.py       # Funciones de autenticación
│   │   └── database.py   # Conexión a PostgreSQL
│   ├── alembic/          # Migraciones de la base de datos
│   ├── tests/            # Pruebas automatizadas del backend
│   ├── requirements.txt  # Dependencias de Python
│   └── alembic.ini       # Configuración de Alembic
├── frontend/
│   ├── public/           # Recursos estáticos
│   ├── src/
│   │   ├── assets/       # Imágenes y otros recursos
│   │   ├── components/   # Componentes reutilizables
│   │   ├── constants/    # Constantes del frontend
│   │   ├── pages/        # Páginas de la aplicación
│   │   ├── services/     # Comunicación con la API
│   │   ├── App.jsx       # Componente principal
│   │   └── main.jsx      # Punto de entrada de React
│   ├── package.json      # Dependencias y comandos npm
│   └── package-lock.json # Versiones exactas de dependencias
├── GUIA_INSTALACION.md
└── README.md
```

El backend y el frontend se instalan y ejecutan por separado. El archivo
`backend\requirements.txt` contiene las dependencias de Python; `frontend\package.json`
y `frontend\package-lock.json` contienen las del cliente web. El entorno virtual
`venv` y el archivo `.env` se crean localmente y no forman parte del código que
se descarga.

## 1. Requisitos

Instalar previamente:

- Git.
- Python 3.
- Node.js LTS (incluye npm).
- Un editor de código, por ejemplo Visual Studio Code.
- Acceso a una base de datos PostgreSQL y su URL de conexión.

Comprobar que Git, Python, Node.js y npm estén disponibles en PowerShell:

```powershell
git --version
python --version
node --version
npm --version
```

## 2. Descargar el proyecto

Abrir PowerShell en la carpeta donde se guardará el proyecto y ejecutar:

```powershell
git clone https://github.com/BrandonLunaCastro/DesarrolloWeb-UberOficios.git
cd DesarrolloWeb-UberOficios
```

## 3. Instalar las dependencias del backend

Desde la carpeta raíz del proyecto, crear y activar un entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Si PowerShell impide activar el entorno, permitir scripts solo durante la
sesión actual y volver a activarlo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Instalar los paquetes requeridos por el backend:

```powershell
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

El entorno virtual debe permanecer activado en la terminal donde se ejecutará
el backend.

## 4. Configurar la conexión a PostgreSQL

Crear un archivo llamado `.env` en la carpeta raíz del proyecto. Solicitar al
responsable del proyecto los datos de conexión; no usar credenciales reales de
otra persona ni compartir este archivo. Como mínimo, definir:

```env
DATABASE_URL=postgresql://USUARIO:CONTRASENA@HOST:5432/NOMBRE_BASE
FRONTEND_URL=http://localhost:5173
```

Reemplazar los valores de ejemplo por los datos entregados. Si la contraseña
tiene caracteres especiales, la URL debe codificarlos correctamente.

El equipo debe proporcionar una base PostgreSQL accesible. Puede ser una base
local o una instancia compartida (por ejemplo, Supabase). No se incluyen
credenciales de base de datos en el repositorio. Antes de continuar, confirmar
que el usuario tenga permiso para crear o modificar las tablas de la base
seleccionada.

Las siguientes variables son opcionales para iniciar la aplicación, pero se
necesitan para utilizar las funciones correspondientes:

```env
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
MERCADOPAGO_ENVIRONMENT=test
MERCADOPAGO_ACCESS_TOKEN=
MERCADOPAGO_WEBHOOK_SECRET=
MERCADOPAGO_WEBHOOK_URL=
```

Cloudinary habilita el almacenamiento de imágenes. Mercado Pago habilita el
flujo de compra de créditos y requiere credenciales de prueba para probar pagos.
No se deben completar con valores inventados ni subir secretos a Git.

## 5. Preparar el esquema de la base

En la terminal con el entorno virtual activo, entrar a `backend` y ejecutar las
migraciones:

```powershell
cd backend
alembic upgrade head
```

Este comando aplica a la base configurada en `DATABASE_URL` las migraciones
incluidas en el proyecto. Si falla, revisar la URL, el acceso a PostgreSQL y los
permisos antes de iniciar el servidor.

## 6. Iniciar el backend

Desde `backend`, en la misma terminal:

```powershell
uvicorn app.main:app --reload
```

Dejar esta terminal abierta. El backend quedará disponible en
`http://127.0.0.1:8000`. Se puede comprobar su estado visitando
`http://127.0.0.1:8000/health`; debe responder:

```json
{"status":"ok"}
```

La documentación interactiva de la API está en `http://127.0.0.1:8000/docs`.

## 7. Instalar e iniciar el frontend

Abrir una segunda terminal y, desde la raíz del proyecto, ejecutar:

```powershell
cd frontend
npm ci
npm run dev
```

Vite indicará la dirección local del frontend, normalmente
`http://localhost:5173`. El frontend usa por defecto el backend local en
`http://127.0.0.1:8000`; no hace falta definir `VITE_API_URL` para esta
configuración.

## 8. Uso diario

Una vez instalado, para trabajar localmente:

1. Abrir PowerShell en la raíz del proyecto y ejecutar:

   ```powershell
   .\venv\Scripts\Activate.ps1
   cd backend
   uvicorn app.main:app --reload
   ```

2. Abrir otra terminal en la raíz del proyecto y ejecutar:

   ```powershell
   cd frontend
   npm run dev
   ```

3. Abrir en el navegador la dirección que muestre Vite.

Para detener cada servidor, volver a su terminal y presionar `Ctrl+C`.

## 9 Prueba a traves del servicio Render

1. Link Front End: 
2. Link Backend: 

## Problemas frecuentes

- **`python`, `node` o `npm` no se reconoce:** instalar la herramienta y
  reiniciar PowerShell para actualizar el PATH.
- **Error de conexión a la base:** verificar `DATABASE_URL`, conectividad,
  permisos y que PostgreSQL esté disponible.
- **No se encuentra `alembic` o `uvicorn`:** activar el entorno virtual y
  confirmar que se instalaron los paquetes de `backend\requirements.txt`.
- **El frontend no conecta con la API:** comprobar que ambos servidores estén
  activos y que el backend responda en `/health`.
- **Falla una función de pagos o imágenes:** comprobar que el responsable haya
  proporcionado las credenciales de prueba correspondientes en `.env`.
