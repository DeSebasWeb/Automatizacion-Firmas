# 🧪 Guía de Testing con Postman - API de Autenticación

Esta guía te permitirá probar completamente el sistema de autenticación JWT implementado.

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Configuración del Entorno](#configuración-del-entorno)
3. [Colección de Endpoints](#colección-de-endpoints)
4. [Flujo de Testing Completo](#flujo-de-testing-completo)
5. [Variables de Postman](#variables-de-postman)
6. [Casos de Prueba](#casos-de-prueba)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 Requisitos Previos

### 1. Instalar Dependencias

```bash
pip install PyJWT
```

### 2. Iniciar la Base de Datos

Asegúrate de que PostgreSQL esté corriendo y la base de datos esté creada:

```bash
# Verificar que PostgreSQL esté corriendo
# Windows: Verificar en Servicios
# Linux/Mac: sudo systemctl status postgresql

# Crear base de datos si no existe
psql -U postgres -c "CREATE DATABASE verifyid_core;"
```

### 3. Ejecutar Migraciones

```bash
# Asegúrate de estar en el directorio raíz del proyecto
alembic upgrade head
```

### 4. Iniciar el Servidor

```bash
# Desde el directorio raíz
uvicorn src.infrastructure.api.main:app --reload

# O usando el script (si existe)
python -m src.infrastructure.api.main
```

Verifica que el servidor esté corriendo visitando: http://localhost:8000/docs

---

## ⚙️ Configuración del Entorno

### Crear un Entorno en Postman

1. Abre Postman
2. Click en "Environments" (icono de engranaje arriba a la derecha)
3. Click "Create Environment"
4. Nombre: `VerifyID - Development`

### Variables del Entorno

Agrega estas variables:

| Variable | Initial Value | Current Value |
|----------|--------------|---------------|
| `base_url` | `http://localhost:8000` | `http://localhost:8000` |
| `api_prefix` | `/api/v1` | `/api/v1` |
| `access_token` | *(vacío)* | *(vacío)* |
| `refresh_token` | *(vacío)* | *(vacío)* |
| `user_id` | *(vacío)* | *(vacío)* |
| `test_email` | `test@example.com` | `test@example.com` |
| `test_password` | `SecurePass123!` | `SecurePass123!` |

---

## 📡 Colección de Endpoints

### 1️⃣ Health Check

**Endpoint:** `GET {{base_url}}/health`

**Descripción:** Verifica que el servidor esté funcionando.

**Request:**
```
GET http://localhost:8000/health
```

**Expected Response:** `200 OK`
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "0.1.0"
}
```

---

### 2️⃣ Register User (Registrar Usuario)

**Endpoint:** `POST {{base_url}}{{api_prefix}}/auth/register`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "email": "{{test_email}}",
  "password": "{{test_password}}"
}
```

**Expected Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "test@example.com",
  "email_verified": false,
  "is_active": true,
  "created_at": "2024-01-20T10:30:00.000Z",
  "last_login_at": null
}
```

**Postman Test Script:**
```javascript
// Guardar user_id para usar en otros requests
if (pm.response.code === 201) {
    var jsonData = pm.response.json();
    pm.environment.set("user_id", jsonData.id);
    pm.test("User registered successfully", function () {
        pm.expect(jsonData.email).to.eql(pm.environment.get("test_email"));
        pm.expect(jsonData.email_verified).to.be.false;
        pm.expect(jsonData.is_active).to.be.true;
    });
}
```

**Casos de Error:**

| Caso | Status | Response |
|------|--------|----------|
| Email duplicado | `400 Bad Request` | `{"detail": "Email already registered: ..."}` |
| Email inválido | `400 Bad Request` | `{"detail": "Invalid email format: ..."}` |
| Password < 8 chars | `400 Bad Request` | `{"detail": "Password must be at least 8 characters..."}` |

---

### 3️⃣ Verify Email (DEV ONLY)

**⚠️ IMPORTANTE:** Este endpoint solo funciona en desarrollo. En producción, la verificación se haría por email.

**Endpoint:** `POST {{base_url}}{{api_prefix}}/auth/dev/verify-email/{{user_id}}`

**Headers:**
```
Content-Type: application/json
```

**No requiere body**

**Expected Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "test@example.com",
  "email_verified": true,
  "is_active": true,
  "created_at": "2024-01-20T10:30:00.000Z",
  "last_login_at": null
}
```

**Postman Test Script:**
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.test("Email verified successfully", function () {
        pm.expect(jsonData.email_verified).to.be.true;
    });
}
```

---

### 4️⃣ Login (Iniciar Sesión)

**Endpoint:** `POST {{base_url}}{{api_prefix}}/auth/login`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "email": "{{test_email}}",
  "password": "{{test_password}}"
}
```

**Expected Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Postman Test Script:**
```javascript
// Guardar tokens automáticamente
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("access_token", jsonData.access_token);
    pm.environment.set("refresh_token", jsonData.refresh_token);

    pm.test("Login successful", function () {
        pm.expect(jsonData.token_type).to.eql("bearer");
        pm.expect(jsonData.access_token).to.not.be.empty;
        pm.expect(jsonData.refresh_token).to.not.be.empty;
        pm.expect(jsonData.expires_in).to.eql(3600);
    });
}
```

**Casos de Error:**

| Caso | Status | Response |
|------|--------|----------|
| Email no existe | `401 Unauthorized` | `{"detail": "Invalid email or password"}` |
| Password incorrecto | `401 Unauthorized` | `{"detail": "Invalid email or password"}` |
| Email no verificado | `401 Unauthorized` | `{"detail": "Invalid email or password"}` |
| Usuario inactivo | `401 Unauthorized` | `{"detail": "Invalid email or password"}` |

**Nota de Seguridad:** Todos los errores de autenticación devuelven el mismo mensaje genérico para prevenir enumeración de usuarios.

---

### 5️⃣ Get Current User (Obtener Usuario Actual)

**Endpoint:** `GET {{base_url}}{{api_prefix}}/auth/me`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**No requiere body**

**Expected Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "test@example.com",
  "email_verified": true,
  "is_active": true,
  "created_at": "2024-01-20T10:30:00.000Z",
  "last_login_at": "2024-01-20T10:35:00.000Z"
}
```

**Postman Test Script:**
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.test("Current user retrieved", function () {
        pm.expect(jsonData.id).to.eql(pm.environment.get("user_id"));
        pm.expect(jsonData.email).to.eql(pm.environment.get("test_email"));
    });
}
```

**Casos de Error:**

| Caso | Status | Response |
|------|--------|----------|
| Token faltante | `403 Forbidden` | `{"detail": "Not authenticated"}` |
| Token inválido | `401 Unauthorized` | `{"detail": "Invalid token"}` |
| Token expirado | `401 Unauthorized` | `{"detail": "Token has expired"}` |
| Usuario no existe | `401 Unauthorized` | `{"detail": "User not found"}` |

---

## 🔄 Flujo de Testing Completo

### Escenario 1: Happy Path (Registro y Login Exitoso)

Ejecuta los requests en este orden:

1. **Health Check** → Verifica que el servidor esté funcionando
2. **Register User** → Crea un nuevo usuario
   - Guarda el `user_id` de la respuesta
3. **Verify Email (DEV)** → Verifica el email del usuario
   - Usa el `user_id` guardado
4. **Login** → Inicia sesión
   - Guarda `access_token` y `refresh_token`
5. **Get Current User** → Obtiene info del usuario autenticado
   - Usa el `access_token` en el header

### Escenario 2: Registro con Email Duplicado

1. **Register User** con `test@example.com` → `201 Created`
2. **Register User** nuevamente con el mismo email → `400 Bad Request`
   - Mensaje: "Email already registered"

### Escenario 3: Login sin Verificar Email

1. **Register User** con `unverified@example.com` → `201 Created`
2. **Login** con `unverified@example.com` → `401 Unauthorized`
   - Mensaje: "Invalid email or password"
   - Razón: email_verified = false

### Escenario 4: Token Expirado

1. **Login** → Guarda token
2. Espera 61 minutos (o modifica `ACCESS_TOKEN_EXPIRE_MINUTES` a 1 minuto en config)
3. **Get Current User** → `401 Unauthorized`
   - Mensaje: "Token has expired"

---

## 🔐 Variables de Postman Avanzadas

### Auto-guardar Tokens con Pre-request Script

Agrega este script en la pestaña "Pre-request Script" de la colección:

```javascript
// Función helper para login automático si el token expiró
function autoLogin() {
    const loginUrl = pm.environment.get("base_url") + pm.environment.get("api_prefix") + "/auth/login";
    const loginData = {
        email: pm.environment.get("test_email"),
        password: pm.environment.get("test_password")
    };

    pm.sendRequest({
        url: loginUrl,
        method: 'POST',
        header: {
            'Content-Type': 'application/json'
        },
        body: {
            mode: 'raw',
            raw: JSON.stringify(loginData)
        }
    }, function (err, res) {
        if (!err && res.code === 200) {
            var jsonData = res.json();
            pm.environment.set("access_token", jsonData.access_token);
            pm.environment.set("refresh_token", jsonData.refresh_token);
            console.log("Auto-login successful");
        }
    });
}
```

---

## 📝 Casos de Prueba Detallados

### Test Case 1: Validación de Email

**Request:** `POST /auth/register`

| Input Email | Expected Status | Expected Message |
|-------------|----------------|------------------|
| `valid@example.com` | 201 | Usuario creado |
| `invalid-email` | 400 | "Invalid email format" |
| `@example.com` | 400 | "Invalid email format" |
| `test@` | 400 | "Invalid email format" |
| `a@b.c` | 400 | "Email too short" |

### Test Case 2: Validación de Password

**Request:** `POST /auth/register`

| Input Password | Expected Status | Expected Message |
|---------------|----------------|------------------|
| `SecurePass123` | 201 | Usuario creado |
| `short` | 400 | "Password must be at least 8 characters" |
| `12345678` | 201 | Usuario creado (solo números ok) |
| `abcdefgh` | 201 | Usuario creado (solo letras ok) |

### Test Case 3: Autenticación

**Request:** `POST /auth/login`

| Scenario | Email Verified | Is Active | Expected Status |
|----------|---------------|-----------|----------------|
| Normal user | ✅ true | ✅ true | 200 OK |
| Unverified email | ❌ false | ✅ true | 401 Unauthorized |
| Inactive user | ✅ true | ❌ false | 401 Unauthorized |
| Both false | ❌ false | ❌ false | 401 Unauthorized |

---

## 🐛 Troubleshooting

### Error: "Connection refused" al hacer request

**Causa:** El servidor no está corriendo.

**Solución:**
```bash
uvicorn src.infrastructure.api.main:app --reload
```

---

### Error: "relation 'users' does not exist"

**Causa:** Las migraciones no se ejecutaron.

**Solución:**
```bash
alembic upgrade head
```

---

### Error: "Invalid token"

**Causas posibles:**
1. Token copiado incorrectamente (espacios extra)
2. Token expirado
3. SECRET_KEY cambió (invalida todos los tokens)

**Solución:**
1. Verifica que el header sea: `Authorization: Bearer {{access_token}}`
2. Haz login nuevamente
3. Reinicia el servidor si es necesario

---

### Error: "User cannot authenticate" en logs pero 401 genérico

**Causa:** Usuario tiene `email_verified=false` o `is_active=false`

**Solución:**
1. Usa el endpoint `POST /auth/dev/verify-email/{user_id}` (solo dev)
2. O actualiza manualmente en la base de datos:
```sql
UPDATE users SET email_verified = true WHERE email = 'test@example.com';
```

---

### Login exitoso pero "User not found" en /auth/me

**Causa:** El usuario fue eliminado después de hacer login.

**Solución:**
1. Verifica que el usuario exista: `SELECT * FROM users WHERE id = 'user_id';`
2. Haz login nuevamente

---

## 🎯 Endpoints de Swagger UI

Para testing interactivo, visita: **http://localhost:8000/docs**

Ventajas:
- Interfaz gráfica
- Documentación automática
- Test directo desde el navegador
- "Try it out" para cada endpoint

---

## 📊 Ejemplo de Colección Postman Completa

Puedes importar esta colección JSON en Postman:

```json
{
  "info": {
    "name": "VerifyID Authentication API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "1. Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "2. Register User",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "if (pm.response.code === 201) {",
              "    var jsonData = pm.response.json();",
              "    pm.environment.set('user_id', jsonData.id);",
              "}"
            ]
          }
        }
      ],
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"{{test_email}}\",\n  \"password\": \"{{test_password}}\"\n}"
        },
        "url": {
          "raw": "{{base_url}}{{api_prefix}}/auth/register",
          "host": ["{{base_url}}{{api_prefix}}"],
          "path": ["auth", "register"]
        }
      }
    },
    {
      "name": "3. Verify Email (DEV)",
      "request": {
        "method": "POST",
        "header": [],
        "url": {
          "raw": "{{base_url}}{{api_prefix}}/auth/dev/verify-email/{{user_id}}",
          "host": ["{{base_url}}{{api_prefix}}"],
          "path": ["auth", "dev", "verify-email", "{{user_id}}"]
        }
      }
    },
    {
      "name": "4. Login",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "if (pm.response.code === 200) {",
              "    var jsonData = pm.response.json();",
              "    pm.environment.set('access_token', jsonData.access_token);",
              "    pm.environment.set('refresh_token', jsonData.refresh_token);",
              "}"
            ]
          }
        }
      ],
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"{{test_email}}\",\n  \"password\": \"{{test_password}}\"\n}"
        },
        "url": {
          "raw": "{{base_url}}{{api_prefix}}/auth/login",
          "host": ["{{base_url}}{{api_prefix}}"],
          "path": ["auth", "login"]
        }
      }
    },
    {
      "name": "5. Get Current User",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "url": {
          "raw": "{{base_url}}{{api_prefix}}/auth/me",
          "host": ["{{base_url}}{{api_prefix}}"],
          "path": ["auth", "me"]
        }
      }
    }
  ]
}
```

---

## ✅ Checklist de Testing Completo

- [ ] Health check funciona
- [ ] Registro con email válido funciona
- [ ] Registro con email duplicado devuelve error 400
- [ ] Registro con password corto devuelve error 400
- [ ] Verificación de email (DEV) funciona
- [ ] Login con credenciales correctas funciona
- [ ] Login sin verificar email devuelve error 401
- [ ] Get current user con token válido funciona
- [ ] Get current user sin token devuelve error 403
- [ ] Get current user con token expirado devuelve error 401
- [ ] Tokens se guardan correctamente en variables de entorno

---

## 🎉 ¡Listo!

Si completaste todos los pasos, tu sistema de autenticación JWT está funcionando correctamente.

**Próximos pasos:**
- Implementar refresh token endpoint
- Implementar logout (blacklist de tokens)
- Implementar verificación de email real (envío de emails)
- Implementar reset de password
