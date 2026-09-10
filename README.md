UberOficios
Aplicación web para consultar y encontrar prestadores de servicios locales, como mecánicos, plomeros, electricistas, técnicos, etc.
El proyecto está dividido en:
Backend: Python + FastAPI + SQLAlchemy + PostgreSQL
Base de datos: PostgreSQL mediante Supabase
Frontend: HTML + CSS + JavaScript
Autenticación: Passlib + bcrypt + JWT
Control de versiones: Git + GitHub
1. Estructura del proyecto
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

El archivo .env no debe subirse a GitHub porque contiene información sensible de conexión.
2. Requisitos
Antes de comenzar, instalar:
Python 3
Git
Visual Studio Code
Comprobar Python:
python --version

Comprobar Git:
git --version

3. Clonar el repositorio
Cada integrante debe clonar el repositorio una sola vez.
git clone URL_DEL_REPOSITORIO

Entrar al proyecto:
cd UberOficios

4. Crear el entorno virtual
Cada integrante debe crear su propio entorno virtual.
python -m venv venv

No se debe copiar el venv de otro integrante ni subirlo a GitHub.
5. Activar el entorno virtual
En Windows PowerShell:
.\venv\Scripts\Activate.ps1

Si se activó correctamente, aparecerá:
(venv)

al principio de la terminal.
6. Instalar las dependencias
Con el entorno virtual activado:
pip install -r requirements.txt

Esto instala las librerías necesarias para ejecutar el backend.
Entre ellas:
FastAPI
Uvicorn
SQLAlchemy
PostgreSQL
Passlib
bcrypt
JWT
Importante: bcrypt
El proyecto utiliza:
bcrypt==4.0.1

Esta versión debe mantenerse debido a la compatibilidad con Passlib.
No actualizar bcrypt manualmente a una versión 5.x sin comprobar la compatibilidad.
7. Configurar el archivo .env
El archivo .env no debe estar en el repositorio.
Cada integrante debe crear su propio:
.env

en la raíz del proyecto.
Ejemplo:
DATABASE_URL=URL_DE_LA_BASE_DE_DATOS

La información real de conexión debe ser proporcionada por el equipo.
Nunca subir contraseñas, claves privadas ni credenciales a GitHub.
El .gitignore debe contener:
venv/
__pycache__/
*.pyc
.env

8. Ejecutar el backend
El backend se ejecuta desde la carpeta backend.
cd backend

Luego:
uvicorn app.main:app --reload

Si funciona correctamente:
Uvicorn running on http://127.0.0.1:8000
Application startup complete.

9. Swagger
FastAPI proporciona automáticamente una interfaz para probar los endpoints.
Abrir:
http://127.0.0.1:8000/docs

Desde Swagger se pueden ejecutar y probar los endpoints del backend.
10. Health Check
El proyecto tiene un endpoint para comprobar que el servidor está funcionando:
GET /health

Respuesta esperada:
{
  "status": "ok"
}

11. Autenticación
Actualmente el backend contiene funcionalidades relacionadas con autenticación.
Registro de usuarios
Endpoint:
POST /auth/register

Datos:
{
  "nombre_apellido": "Nombre Apellido",
  "correo": "correo@email.com",
  "contrasena": "123456"
}

El proceso es:
Datos recibidos
      ↓
Pydantic valida los datos
      ↓
Se comprueba si el correo ya existe
      ↓
Se hashea la contraseña
      ↓
Se crea el Usuario
      ↓
Se guarda en PostgreSQL

La contraseña no se almacena en texto plano.
Por ejemplo:
123456

se convierte en un hash similar a:
$2b$12$................................

12. Trabajo con Git y Branches
Para evitar que un cambio de un integrante rompa el código estable, no se debe trabajar directamente sobre main.
La rama main representa el código estable del proyecto.
Cada nueva funcionalidad debe desarrollarse en una rama independiente.
La estructura será:
main
│
├── feature/register
├── feature/login
├── feature/prestadores
├── feature/clientes
├── feature/calificaciones
└── feature/busqueda

13. ¿Qué es main?
main es la rama principal y estable.
Debe contener código que:
Funcione.
Haya sido probado.
Esté listo para integrarse con el resto del proyecto.
Regla
No desarrollar funcionalidades directamente en main.
14. Crear una branch para una funcionalidad
Antes de comenzar una tarea, actualizar main:
git switch main
git pull

Después crear una nueva branch:
git switch -c feature/nombre-de-la-funcionalidad

Ejemplo:
git switch -c feature/prestadores

Ahora estamos trabajando en:
feature/prestadores

y no directamente en main.
15. Trabajar dentro de la branch
Ahora se puede modificar el código normalmente.
Por ejemplo:
backend/app/models/
backend/app/routes/
backend/app/schemas/

Después probar el funcionamiento:
cd backend
uvicorn app.main:app --reload

Y utilizar:
http://127.0.0.1:8000/docs

para probar los endpoints.
16. Guardar los cambios
Cuando la funcionalidad esté funcionando:
Volver a la raíz del proyecto:
cd ..

Comprobar cambios:
git status

Agregar los archivos:
git add .

Crear el commit:
git commit -m "feat: agregar funcionalidad de prestadores"

17. Subir la branch a GitHub
Después del commit:
git push -u origin feature/prestadores

Esto crea/sube la branch a GitHub.
18. Pull Request
Una vez subida la branch, se debe crear un Pull Request (PR) en GitHub.
El flujo es:
feature/prestadores
        ↓
      GitHub
        ↓
 Pull Request
        ↓
Revisión del equipo
        ↓
      main

El Pull Request permite revisar los cambios antes de incorporarlos a main.
19. ¿Por qué usamos Pull Requests?
Porque queremos evitar:
Compañero
    ↓
modifica código
    ↓
push directo a main
    ↓
💥 main deja de funcionar

En cambio:
Compañero
    ↓
feature/prestadores
    ↓
commit
    ↓
push
    ↓
Pull Request
    ↓
revisión
    ↓
merge
    ↓
main

Esto permite detectar errores antes de modificar la rama estable.
20. Proteger la rama main
En GitHub se recomienda configurar main como Protected Branch.
La idea es impedir que los integrantes hagan push directamente a main.
El flujo recomendado será:
Branch de trabajo
       ↓
Pull Request
       ↓
Revisión
       ↓
Merge
       ↓
main

De esta manera, main queda protegida.
21. Ejemplo de trabajo entre dos compañeros
Supongamos que:
Brandon
Trabaja en:
feature/login

Compañero
Trabaja en:
feature/prestadores

El repositorio queda:
                    main
                     │
            ┌────────┴────────┐
            ↓                 ↓
     feature/login     feature/prestadores
          Brandon             compañero

Cada uno puede trabajar independientemente.
Cuando una funcionalidad termina:
feature/login
      ↓
Pull Request
      ↓
revisión
      ↓
main

Después la otra:
feature/prestadores
      ↓
Pull Request
      ↓
revisión
      ↓
main

22. Antes de comenzar una nueva tarea
Siempre actualizar main:
git switch main
git pull

Después crear la branch:
git switch -c feature/nueva-funcionalidad

Ejemplo:
git switch -c feature/calificaciones

23. Si otro compañero ya actualizó main
Si estás trabajando en una branch y otro integrante incorporó cambios a main, primero hay que actualizarse antes de continuar o integrar la funcionalidad.
Una forma sencilla:
git switch main
git pull

Luego volver a tu branch:
git switch feature/nueva-funcionalidad

Si aparecen conflictos al integrar cambios, no borrar archivos ni utilizar:
git push --force

sin consultar al equipo.
24. Flujo completo de trabajo
Este será el flujo habitual del equipo:
1. git switch main
        ↓
2. git pull
        ↓
3. git switch -c feature/nueva-funcionalidad
        ↓
4. Programar
        ↓
5. Probar
        ↓
6. git status
        ↓
7. git add .
        ↓
8. git commit -m "feat: descripción"
        ↓
9. git push -u origin feature/nueva-funcionalidad
        ↓
10. Crear Pull Request
        ↓
11. Revisar
        ↓
12. Merge a main

25. Después de hacer Merge
Una vez que el Pull Request fue aceptado y fusionado:
git switch main
git pull

La funcionalidad ya estará disponible en la rama principal.
La branch utilizada para esa funcionalidad puede eliminarse si el equipo considera que ya no es necesaria.
26. Convención para nombres de branches
Utilizar:
feature/nombre

para nuevas funcionalidades.
Ejemplos:
feature/register
feature/login
feature/prestadores
feature/clientes
feature/calificaciones
feature/busqueda

Para correcciones:
fix/nombre-del-error

Ejemplo:
fix/error-login

27. Convención para commits
Utilizar mensajes claros.
Ejemplos:
feat: agregar registro de usuarios

feat: agregar endpoints de prestadores

fix: corregir validacion de correo

chore: actualizar dependencias

La idea es que mirando el historial de Git se pueda entender qué se modificó.
28. Reglas importantes del equipo
No trabajar directamente en main
❌ main → programar

Utilizar:
✅ feature/... → programar

No subir .env
❌ git add .env

No subir venv
❌ git add venv/

No hacer push --force sobre main
❌ git push --force

Siempre probar antes de crear el Pull Request
Código
 ↓
Prueba
 ↓
Commit
 ↓
Push
 ↓
Pull Request

29. Estado actual del proyecto
Actualmente el backend cuenta con:
Estructura organizada dentro de backend/app
FastAPI funcionando
Swagger funcionando
Health Check
PostgreSQL
SQLAlchemy
Modelos de usuarios
Schemas con Pydantic
Registro de usuarios
Validación de datos
Hash de contraseñas con Passlib + bcrypt
POST /auth/register
30. Objetivo del desarrollo
El proyecto se desarrollará progresivamente.
La idea es trabajar por funcionalidades:
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

Cada funcionalidad debe probarse antes de integrarse a main.
31. Comandos rápidos
Actualizar proyecto
git switch main
git pull

Crear branch
git switch -c feature/nueva-funcionalidad

Ver branch actual
git branch

Ver cambios
git status

Guardar cambios
git add .
git commit -m "feat: descripcion"

Subir branch
git push -u origin nombre-de-la-branch

Volver a main
git switch main

32. Inicio rápido para un nuevo integrante
Después de clonar y configurar el proyecto:
cd UberOficios

python -m venv venv

.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

git switch main

git pull

cd backend

uvicorn app.main:app --reload

Abrir:
http://127.0.0.1:8000/docs

Cuando vaya a comenzar una tarea:
git switch main
git pull
git switch -c feature/nombre-de-la-tarea

A partir de ese momento puede trabajar en su branch sin modificar directamente main.
33. Regla principal del proyecto
main debe mantenerse estable. Cada funcionalidad nueva se desarrolla en una branch, se prueba y luego se incorpora mediante Pull Request.
