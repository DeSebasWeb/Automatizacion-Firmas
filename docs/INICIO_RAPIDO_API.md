# 🚀 Inicio Rápido - API de Autenticación

Esta guía te ayudará a iniciar el servidor API correctamente.

## ⚠️ CORRECCIÓN DE ERRORES ENCONTRADOS

Se corrigieron imports incorrectos en:
- ✅ `src/infrastructure/database/repositories/user_repository_impl.py`
- ✅ `src/infrastructure/database/mappers/user_mapper.py`

**Problema:** Algunos archivos usaban `from domain.` en lugar de `from src.domain.`

---

## 📋 PASOS PARA INICIAR EL SERVIDOR

### 1️⃣ Instalar Dependencias de la API

```bash
# Asegúrate de estar en el directorio raíz y con el venv activado
pip install fastapi uvicorn[standard] PyJWT pydantic-settings python-multipart
```

### 2️⃣ Verificar que PostgreSQL esté corriendo

```bash
# Windows: Abrir "Servicios" y verificar que PostgreSQL esté iniciado
# O desde PowerShell:
Get-Service postgresql*

# Linux/Mac:
sudo systemctl status postgresql
```

### 3️⃣ Crear base de datos (si no existe)

```bash
# Conectarse a PostgreSQL
psql -U postgres

# Crear base de datos
CREATE DATABASE verifyid_core;

# Salir
\q
```

### 4️⃣ Ejecutar migraciones

```bash
# Desde el directorio raíz
alembic upgrade head
```

### 5️⃣ Iniciar el servidor

**Opción 1: Con uvicorn directamente (RECOMENDADO)**

```bash
uvicorn src.infrastructure.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Opción 2: Con uvicorn en modo producción**

```bash
uvicorn src.infrastructure.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6️⃣ Verificar que funciona

Abre tu navegador y visita:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 🔍 RESPUESTA A TUS PREGUNTAS

### ¿No es mejor un script como en Java/Spring Boot?

**Respuesta:** En Python/FastAPI hay varias formas de iniciar:

#### ✅ **Forma 1: Uvicorn directo (la más común)**
```bash
uvicorn src.infrastructure.api.main:app --reload
```

**Ventajas:**
- Es el estándar de FastAPI
- Más control sobre parámetros (workers, host, port)
- Hot-reload automático en desarrollo

#### ✅ **Forma 2: Script Python dedicado** (si prefieres)
Puedes crear `run_api.py` en la raíz:

```python
"""API Server launcher."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.infrastructure.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info"
    )
```

Luego iniciar con:
```bash
python run_api.py
```

#### ✅ **Forma 3: Makefile** (muy común en proyectos Python)
Crear `Makefile` en la raíz:

```makefile
.PHONY: run-api
run-api:
	uvicorn src.infrastructure.api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: run-api-prod
run-api-prod:
	uvicorn src.infrastructure.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Luego:
```bash
make run-api
```

**Comparación con Java/Spring:**

| Aspecto | Spring Boot | FastAPI/Python |
|---------|-------------|----------------|
| **Inicio** | `./mvnw spring-boot:run` o botón IDE | `uvicorn main:app --reload` |
| **Hot-reload** | DevTools | `--reload` flag |
| **Configuración** | `application.properties` | `.env` + `settings.py` |
| **Empaquetado** | JAR/WAR | Docker image |

---

## 📦 DEPENDENCIAS NECESARIAS

### requirements-api.txt (crear este archivo)

```txt
# FastAPI Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Security
PyJWT==2.8.0
bcrypt==4.1.2
python-multipart==0.0.6

# Database
SQLAlchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1

# Logging
structlog==24.1.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0  # Para testing de FastAPI
```

**Instalar todo:**
```bash
pip install -r requirements-api.txt
```

---

## 🐛 TROUBLESHOOTING

### Error: "ModuleNotFoundError: No module named 'fastapi'"

**Solución:**
```bash
pip install fastapi uvicorn[standard]
```

### Error: "ModuleNotFoundError: No module named 'domain'"

**Causa:** Imports incorrectos (ya corregidos en este sprint)

**Verificar que todos los imports usen:**
```python
from src.domain.  # ✅ Correcto
from domain.      # ❌ Incorrecto
```

### Error: "relation 'users' does not exist"

**Solución:**
```bash
alembic upgrade head
```

### Error: Puerto 8000 ya en uso

**Solución Windows:**
```bash
# Ver qué proceso usa el puerto
netstat -ano | findstr :8000

# Matar el proceso (reemplaza PID con el número que viste)
taskkill /PID <PID> /F
```

**Solución Linux/Mac:**
```bash
# Ver qué proceso usa el puerto
lsof -i :8000

# Matar el proceso
kill -9 <PID>

# O usar otro puerto
uvicorn src.infrastructure.api.main:app --reload --port 8001
```

### El servidor inicia pero sale error 500 al hacer requests

**Causas posibles:**
1. Base de datos no está corriendo
2. Migraciones no ejecutadas
3. Variables de entorno incorrectas

**Verificar logs:**
```bash
# Los logs mostrarán el error exacto
# Buscar líneas con "ERROR" o "Traceback"
```

---

## ✅ CHECKLIST DE VERIFICACIÓN

Antes de probar la API, verifica:

- [ ] ✅ PostgreSQL está corriendo
- [ ] ✅ Base de datos `verifyid_core` existe
- [ ] ✅ Migraciones ejecutadas (`alembic upgrade head`)
- [ ] ✅ Dependencias instaladas (`pip install fastapi uvicorn PyJWT`)
- [ ] ✅ Archivo `.env` existe (opcional, usa defaults si no existe)
- [ ] ✅ Virtual environment activado (`venv/Scripts/activate`)

---

## 🎯 COMANDOS RÁPIDOS DE DESARROLLO

```bash
# 1. Activar virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 2. Instalar dependencias
pip install fastapi uvicorn[standard] PyJWT pydantic-settings

# 3. Ejecutar migraciones
alembic upgrade head

# 4. Iniciar servidor
uvicorn src.infrastructure.api.main:app --reload

# 5. Ver documentación
# http://localhost:8000/docs
```

---

## 📊 ESTRUCTURA DE INICIO

```
Inicio del Servidor
    ↓
1. Uvicorn carga src.infrastructure.api.main:app
    ↓
2. FastAPI ejecuta lifespan (startup)
    ↓
3. init_db() inicializa pool de conexiones
    ↓
4. FastAPI registra routers (health, auth)
    ↓
5. Servidor listo en http://localhost:8000
```

---

## 🔄 PROCESO DE DESARROLLO TÍPICO

1. **Cambias código** → Uvicorn detecta cambio (con `--reload`)
2. **Auto-reload** → Servidor se reinicia automáticamente
3. **Pruebas en Swagger** → http://localhost:8000/docs
4. **Verificas logs** → En la terminal donde corre uvicorn

---

## 🎉 ¡LISTO!

Una vez que el servidor inicie sin errores, verás:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Ahora puedes probar con Postman siguiendo la guía: [POSTMAN_TESTING_GUIDE.md](./POSTMAN_TESTING_GUIDE.md)
