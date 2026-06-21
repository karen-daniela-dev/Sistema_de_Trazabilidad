# 🎓 Sistema de Empleabilidad — Full Stack Java Bootcamp

Sistema completo de seguimiento de empleabilidad para bootcamp.  
**Stack:** FastAPI · Streamlit · PostgreSQL · JWT

---

## 📁 Estructura del proyecto

```
empleabilidad/
├── backend/                  # API REST FastAPI
│   ├── main.py               # Entry point, CORS, middlewares
│   ├── config.py             # Settings desde .env
│   ├── database.py           # Engine SQLAlchemy + SessionLocal
│   ├── models/               # ORM SQLAlchemy (7 tablas)
│   ├── schemas/              # Pydantic — validación entrada/salida
│   ├── routers/              # Endpoints por dominio
│   ├── services/             # Lógica de negocio pura
│   ├── dependencies/         # Auth JWT + RBAC
│   ├── middleware/           # Audit logs
│   ├── utils/                # Security (JWT, bcrypt) + Pagination
│   └── tests/                # Unit · Integration · Security
├── frontend/                 # UI Streamlit
│   ├── app.py                # Entry point + router por rol
│   ├── api_client.py         # HTTP wrapper centralizado
│   ├── components/ui.py      # KPI cards, semáforos, gráficos
│   └── pages/                # Dashboard por rol
├── scripts/
│   └── seed_dev_data.py      # Datos de prueba para desarrollo
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── Makefile
├── requirements.txt
└── .env.example
```

---

## ⚡ Arranque rápido (desarrollo)

### 1. Prerequisitos
- Python 3.12+
- PostgreSQL 15+ en localhost:5432
- (Opcional) Docker + Docker Compose

### 2. Setup inicial

```bash
# Clonar y entrar al directorio
cd empleabilidad

# Copiar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de BD y JWT secret

# Instalar dependencias
pip install -r requirements.txt

# Crear bases de datos PostgreSQL
psql -U postgres -c "CREATE USER empleabilidad_user WITH PASSWORD 'secret';"
psql -U postgres -c "CREATE DATABASE empleabilidad_db OWNER empleabilidad_user;"
psql -U postgres -c "CREATE DATABASE empleabilidad_test OWNER empleabilidad_user;"
```

### 3. Iniciar servicios

```bash
# Terminal 1 — Backend FastAPI (auto-crea tablas)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend Streamlit
streamlit run frontend/app.py --server.port 8501

# (Opcional) Cargar datos de prueba
python -m scripts.seed_dev_data
```

### 4. Acceder

| Servicio | URL |
|---|---|
| Frontend (Streamlit) | http://localhost:8501 |
| API REST | http://localhost:8000 |
| Documentación API | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

---

## 🐳 Docker Compose

```bash
# Levantar todo (BD + backend + frontend)
docker compose up --build -d

# Solo la BD para desarrollo local
docker compose up db -d

# BD de test
docker compose --profile test up db_test -d

# Detener todo
docker compose down
```

---

## 👤 Credenciales de prueba (después del seed)

| Rol | Email | Password |
|---|---|---|
| Coordinador | coord@bootcamp.com | `Coord@1234` |
| Tutor 1 | tutor1@bootcamp.com | `Tutor@1234` |
| Tutor 2 | tutor2@bootcamp.com | `Tutor@1234` |
| Aprendiz | ana@gmail.com | `Aprend@1234` |
| Aprendiz (contratado) | carlos@gmail.com | `Aprend@1234` |

---

## 🧪 Tests

```bash
# Tests unitarios (sin BD requerida — lógica pura)
python -m pytest backend/tests/unit/ -v

# Tests de integración (requiere BD de test)
python -m pytest backend/tests/integration/ -v

# Tests de seguridad
python -m pytest backend/tests/security/ -v

# Todos los tests con reporte de cobertura
python -m pytest backend/tests/ --cov=backend --cov-report=html

# Cobertura mínima requerida: 75%
```

### Cobertura por módulo

| Módulo | Tests | Cobertura objetivo |
|---|---|---|
| `services/state_engine.py` | 13 unit | 100% |
| `services/alert_engine.py` | 10 unit | 95% |
| `services/cohort_engine.py` | 5 unit | 100% |
| `utils/security.py` | 13 unit | 100% |
| `routers/auth.py` | 8 integration | 90% |
| `routers/aplicaciones.py` | 9 integration | 85% |
| `routers/entrevistas.py` | 8 integration | 85% |
| Seguridad (RBAC, JWT) | 16 security | 100% |

---

## 🔐 Seguridad

### Autenticación
- JWT HS256, expiración configurable (default: 480 min)
- Payload: `{ sub: uuid, rol: enum, exp: timestamp }`
- Rate limiting en login: 10 req/minuto por IP

### Control de acceso por rol

| Endpoint | COORDINADOR | TUTOR | APRENDIZ |
|---|---|---|---|
| `POST /cohortes/` | ✅ | ❌ | ❌ |
| `POST /usuarios/tutor` | ✅ | ❌ | ❌ |
| `GET /kpis/global` | ✅ | ❌ | ❌ |
| `GET /kpis/grupo` | ✅ | ✅ | ❌ |
| `GET /kpis/personal` | ✅ | ✅ | ✅ |
| `POST /aplicaciones/` | ❌ | ❌ | ✅* |
| `POST /entrevistas/` | ❌ | ❌ | ✅* |

*Solo si la cohorte está ACTIVA

### Headers de seguridad (automáticos)
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000 (solo producción)
```

### Política de contraseñas
- Mínimo 8 caracteres
- Al menos: 1 mayúscula, 1 minúscula, 1 número, 1 carácter especial (`@$!%*?&-_`)
- Almacenadas con bcrypt (salt único por hash)

---

## 🔄 Motor de estados de aplicación

```
APLICADO (0 entrevistas)
    ↓ crea entrevista 1
EN_ESPERA (1 entrevista)
    ↓ crea entrevista 2+
AVANZANDO (≥2 entrevistas, última < 10 días)
    ↓ sin entrevistas 10-15 días
RECHAZADO
    ↓ crea nueva entrevista
AVANZANDO
    ↓ aprendiz marca contratado (terminal)
CONTRATADO ✅
```

**Reglas clave:**
- Estado calculado por el sistema — nunca definido por el usuario
- `CONTRATADO` es estado terminal irreversible
- Recálculo automático en cada nueva entrevista

---

## 📊 KPIs por rol

### Coordinador
- Tasa de contratación global y por cohorte
- Comparativo entre cohortes (contratados vs meta)
- Ranking de tutores por efectividad
- Semáforos (🟢🟡🔴) por cohorte y aprendiz

### Tutor
- Estado del grupo (verde/amarillo/rojo)
- Aplicaciones y entrevistas por aprendiz
- Fallas más frecuentes del grupo
- Alertas de inactividad

### Aprendiz
- Historial de aplicaciones con estados
- Tasa de conversión aplicación→entrevista
- Fallas identificadas en entrevistas
- Semáforo personal

---

## 🚨 Motor de alertas

| Alerta | Trigger | Destinatario |
|---|---|---|
| `INACTIVIDAD` | > 14 días sin actividad | Aprendiz + Tutor |
| `BAJA_CONVERSION` | ≥5 apps sin entrevista | Aprendiz + Tutor |
| `MULTIPLES_RECHAZOS` | ≥3 aplicaciones rechazadas | Aprendiz + Tutor |
| `COHORTE_YELLOW` | 70%+ tiempo, meta incompleta | Coordinador |
| `COHORTE_RED` | 70%+ tiempo, <50% meta | Coordinador |

---

## 🚀 Deploy a producción

### Variables de entorno críticas para producción

```bash
ENVIRONMENT=production
SECRET_KEY=<openssl rand -hex 32>    # NUNCA el default
DATABASE_URL=postgresql://...
DEBUG=false
ALLOWED_ORIGINS=https://tudominio.com
```

### Con Docker

```bash
# Build y push
docker build -f Dockerfile.backend -t empleabilidad-api:latest .
docker build -f Dockerfile.frontend -t empleabilidad-ui:latest .

# En producción: cambiar 'command' en docker-compose.yml
# backend: quitar --reload
# Agregar reverse proxy (nginx) con SSL
```

### Lista de verificación pre-deploy

- [ ] `SECRET_KEY` cambiada (mínimo 32 bytes aleatorios)
- [ ] `DEBUG=false`
- [ ] `ENVIRONMENT=production`
- [ ] `ALLOWED_ORIGINS` con dominios reales
- [ ] PostgreSQL con backups configurados
- [ ] SMTP configurado para emails de activación
- [ ] Reverse proxy con SSL/TLS
- [ ] `/docs` y `/redoc` desactivados (automático en producción)

---

## 🛠️ Comandos útiles (Makefile)

```bash
make setup-dev          # Setup inicial completo
make dev-backend        # Arrancar backend
make dev-frontend       # Arrancar frontend
make test               # Todos los tests
make test-unit          # Solo unitarios
make test-security      # Solo seguridad
make coverage           # Reporte HTML de cobertura
make lint               # Análisis de código (ruff)
make format             # Formatear (black)
make db-up              # Levantar BD con Docker
make seed               # Cargar datos de prueba
make migrate            # Aplicar migraciones Alembic
```

---

## 📝 Validaciones del sistema

### Entrevistas — Campos condicionales
| Condición | Campo habilitado |
|---|---|
| `grupal = true` | `percepcion_grupal` (requerido) |
| `TECNICA` en `fallas` | `temas_tecnicos` |
| Cualquier falla | `subfallas` (validadas contra la falla) |
| Siempre | `autoevaluacion` (1-5), `reflexion_bien`, `reflexion_mejorar` |

### Subfallas válidas por falla
| Falla | Subfallas |
|---|---|
| TECNICA | JAVA_BASICO, SPRING_BOOT, SQL_QUERIES, ALGORITMOS, APIS_REST, ARQUITECTURA |
| COMUNICACION | CLARIDAD, ESCUCHA, ARGUMENTACION |
| BLANDAS | TRABAJO_EQUIPO, PUNTUALIDAD, ACTITUD |
| REGULACION_EMOCIONAL | ANSIEDAD, BLOQUEO_MENTAL, FRUSTACION |

---

## 🔌 API — Endpoints principales

### Auth
```
POST /auth/register     Registro de aprendiz
POST /auth/login        Login (JWT)
POST /auth/activate     Activar cuenta tutor
GET  /auth/me           Usuario actual
```

### Cohortes
```
GET    /cohortes/           Listar cohortes
POST   /cohortes/           Crear cohorte (COORDINADOR)
PATCH  /cohortes/{id}       Actualizar cohorte (COORDINADOR)
POST   /cohortes/sincronizar-estados   Forzar sincronización
```

### Usuarios
```
GET    /usuarios/tutores    Listar tutores
POST   /usuarios/tutor      Crear tutor + email activación (COORDINADOR)
POST   /usuarios/perfil     Crear perfil aprendiz
GET    /usuarios/perfil/me  Mi perfil
PATCH  /usuarios/perfil/me  Actualizar perfil (solo campos permitidos)
```

### Aplicaciones
```
GET    /aplicaciones/                   Listar (filtrado por rol)
POST   /aplicaciones/                   Crear (APRENDIZ, cohorte ACTIVA)
GET    /aplicaciones/{id}               Detalle
POST   /aplicaciones/marcar-contratado  Marcar CONTRATADO (APRENDIZ)
DELETE /aplicaciones/{id}               Eliminar (APRENDIZ, solo las propias)
```

### Entrevistas
```
POST   /entrevistas/                          Crear + recalcula estado app
GET    /entrevistas/por-aplicacion/{app_id}   Listar por aplicación
GET    /entrevistas/{id}                      Detalle
```

### KPIs
```
GET    /kpis/personal    KPIs del aprendiz autenticado
GET    /kpis/grupo       KPIs del grupo (TUTOR/COORDINADOR)
GET    /kpis/global      KPIs globales (COORDINADOR)
GET    /kpis/alertas     Alertas del usuario actual
PATCH  /kpis/alertas/{id}/leer   Marcar alerta leída
```

---

*Documentación generada para v1.0.0 — Sistema de Empleabilidad Full Stack Java*
