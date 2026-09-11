# UberOficios

Aplicación web para consultar y encontrar prestadores de servicios locales, como mecánicos, plomeros, electricistas, técnicos, etc.

El proyecto está dividido en:

* **Backend:** Python + FastAPI + SQLAlchemy + PostgreSQL
* **Base de datos:** PostgreSQL mediante Supabase
* **Frontend:** HTML + CSS + JavaScript
* **Autenticación:** Passlib + bcrypt + JWT

---

# 1. Estructura del proyecto

```text
UberOficios/
│
├── backend/
│   └── app/
│       ├── models/
│       ├── routes/
│       ├── schemas/
│       ├── auth.py
│       ├── database.py
│       └── main.py
│
├── frontend/
│
├── alembic/
│
├── .env
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

> El archivo `.env` no debe subirse a GitHub porque contiene información sensible de conexión.

---

# 2. Requisitos

Antes de comenzar, instalar:

* Python 3
* Git
* Visual Studio Code

Se recomienda tener Python agregado al PATH.

Para comprobar Python:

```powershell
python --version
```

Para comprobar Git:

```powershell
git --version
```

---

# 3. Clonar el repositorio

Abrir PowerShell o una terminal y ejecutar:

```powershell
git clone URL_DEL_REPOSITORIO
```

Luego entrar al proyecto:

```powershell
cd UberOficios
```

---

# 4. Crear el entorno virtual

Cada integrante del equipo debe crear su propio entorno virtual.

Desde la raíz del proyecto:

```powershell
python -m venv venv
```

No se debe copiar el `venv` de otro integrante.

---

# 5. Activar el entorno virtual

En Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Si se activó correctamente, la terminal debería mostrar:

```text
(venv)
```

Por ejemplo:

```text
(venv) PS E:\UberOficios>
```

---

# 6. Instalar las dependencias

Con el entorno virtual activado:

```powershell
pip install -r requirements.txt
```

Esto instala las librerías necesarias para ejecutar el backend.

Entre ellas se encuentran las utilizadas por:

* FastAPI
* Uvicorn
* SQLAlchemy
* PostgreSQL
* Passlib
* bcrypt
* JWT

## Importante sobre bcrypt

El proyecto utiliza:

```text
bcrypt==4.0.1
```

Esta versión debe mantenerse porque estamos utilizando Passlib para el hash de contraseñas.

No actualizar bcrypt manualmente a una versión 5.x sin comprobar la compatibilidad con Passlib.

---

# 7. Crear el archivo `.env`

El archivo `.env` no se encuentra en el repositorio por seguridad.

Cada integrante debe crear su propio archivo:

```text
.env
```

en la raíz del proyecto.

La configuración debe ser proporcionada por el equipo.

Ejemplo de estructura:

```env
DATABASE_URL=URL_DE_LA_BASE_DE_DATOS
```

> No subir el archivo `.env` a GitHub.

El `.gitignore` debe contener:

```gitignore
venv/
__pycache__/
*.pyc
.env
```

---

# 8. Ejecutar el backend

Importante: el backend se ejecuta desde la carpeta `backend`.

Primero:

```powershell
cd backend
```

Luego:

```powershell
uvicorn app.main:app --reload
```

Si todo funciona correctamente aparecerá algo similar a:

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

---

# 9. Abrir Swagger

FastAPI genera automáticamente una interfaz para probar los endpoints.

Abrir en el navegador:

```text
http://127.0.0.1:8000/docs
```

Desde ahí se pueden probar los endpoints del backend.

---

# 10. Comprobar el Health Check

El proyecto tiene un endpoint para comprobar que el servidor está funcionando:

```text
GET /health
```

Desde Swagger se puede ejecutar.

La respuesta esperada es:

```json
{
  "status": "ok"
}
```

---

# 11. Autenticación

Actualmente el backend contiene endpoints relacionados con autenticación.

## Registrar usuario

Endpoint:

```text
POST /auth/register
```

Datos necesarios:

```json
{
  "nombre_apellido": "Nombre Apellido",
  "correo": "correo@email.com",
  "contrasena": "123456"
}
```

El proceso es:

```text
Datos recibidos
      ↓
Pydantic valida los datos
      ↓
Se comprueba si el correo ya existe
      ↓
Se hashea la contraseña con Passlib + bcrypt
      ↓
Se crea el Usuario
      ↓
Se guarda en PostgreSQL
```

La contraseña **no se guarda en texto plano**.

Por ejemplo, si el usuario escribe:

```text
123456
```

en la base de datos se almacena un hash similar a:

```text
$2b$12$................................
```

---

# 12. Importante: no modificar las contraseñas almacenadas

Las contraseñas están almacenadas mediante hash.

No se deben guardar contraseñas directamente como:

```text
123456
password
admin123
```

El backend utiliza:

```python
pwd_context.hash(contrasena)
```

para generar el hash.

Para comprobar una contraseña se utiliza:

```python
pwd_context.verify(
    contrasena,
    contrasena_hash
)
```

---

# 13. Trabajar con Git

Antes de comenzar a trabajar, siempre actualizar el repositorio:

```powershell
git pull
```

Después de realizar cambios:

```powershell
git status
```

Agregar los archivos modificados:

```powershell
git add .
```

Crear el commit:

```powershell
git commit -m "descripcion del cambio"
```

Finalmente:

```powershell
git push
```

---

# 14. Antes de empezar a programar

Siempre hacer:

```powershell
git pull
```

Esto permite obtener los últimos cambios realizados por los demás integrantes.

Ejemplo:

```text
GitHub
   ↓
git pull
   ↓
Tu computadora
   ↓
Realizás cambios
   ↓
git add
   ↓
git commit
   ↓
git push
   ↓
GitHub
```

---

# 15. Trabajo entre compañeros

El proyecto está separado en backend y frontend:

```text
UberOficios/
│
├── backend/
│
└── frontend/
```

Esto permite que los integrantes puedan trabajar principalmente en su respectiva parte del proyecto.

### Backend

Ubicación:

```text
backend/
```

Tecnologías:

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* JWT
* Passlib

### Frontend

Ubicación:

```text
frontend/
```

Tecnologías:

* HTML
* CSS
* JavaScript

---

# 16. Regla importante antes de hacer cambios

Antes de comenzar:

```powershell
git pull
```

Después de terminar una tarea:

```powershell
git status
git add .
git commit -m "descripcion"
git push
```

Evitar trabajar durante mucho tiempo sin actualizar el repositorio.

---

# 17. Si Git muestra conflictos

Si aparece un mensaje indicando que existen conflictos, **no borrar archivos ni hacer `git push --force`**.

Primero avisar al equipo para resolver el conflicto correctamente.

---

# 18. Flujo recomendado para una tarea

Ejemplo: implementar un nuevo endpoint.

### 1. Actualizar código

```powershell
git pull
```

### 2. Crear/modificar código

Trabajar dentro de:

```text
backend/app/
```

### 3. Probar

Ejecutar:

```powershell
cd backend
uvicorn app.main:app --reload
```

Y comprobar mediante:

```text
http://127.0.0.1:8000/docs
```

### 4. Guardar cambios

Desde la raíz:

```powershell
git add .
```

### 5. Crear commit

```powershell
git commit -m "feat: agregar nuevo endpoint"
```

### 6. Subir

```powershell
git push
```

---

# 19. Estado actual del proyecto

Actualmente el backend tiene:

* Estructura organizada dentro de `backend/app`
* Conexión con PostgreSQL
* Modelos SQLAlchemy
* FastAPI funcionando
* Swagger funcionando
* Health Check
* Sistema de registro de usuarios
* Validación mediante Pydantic
* Hash de contraseñas mediante Passlib + bcrypt
* Primer endpoint de autenticación:

```text
POST /auth/register
```

---

# 20. Objetivo del desarrollo

El proyecto se desarrollará progresivamente.

No es necesario implementar todas las entidades y funcionalidades de una sola vez.

La idea es:

```text
Base de datos
      ↓
Modelos
      ↓
Schemas
      ↓
Endpoints
      ↓
Autenticación
      ↓
Lógica de negocio
      ↓
Frontend
      ↓
Integración
      ↓
Pruebas
```

Cada funcionalidad debe probarse antes de continuar con la siguiente.

---

# 21. Comando rápido para empezar a trabajar

Después de haber clonado y configurado el proyecto, el flujo habitual será:

```powershell
cd UberOficios
git pull

.\venv\Scripts\Activate.ps1

cd backend
uvicorn app.main:app --reload
```

Luego abrir:

```text
http://127.0.0.1:8000/docs
```

¡Listo para trabajar!

