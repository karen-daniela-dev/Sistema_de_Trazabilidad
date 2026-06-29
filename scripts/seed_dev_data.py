"""
Seed masivo con fallas, subfallas y reflexiones detalladas.

Estructura:
  - 1  coordinador
  - 30 tutores (rotan por época, cada uno en UNA cohorte a la vez)
  - 20 cohortes escalonadas en el tiempo
       · 5  FINALIZADAS   (completaron 6 meses)
       · 5  DESHABILITADAS (completaron 6 meses + cierre administrativo)
       · 5  ACTIVAS consolidadas
       · 5  ACTIVAS recientes
  - 6 tutores asignados por cohorte (sin solapamiento temporal)
  - 40-55 aprendices por cohorte
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("ENVIRONMENT", "development")

from datetime import date, datetime, timedelta, timezone
from backend.database import SessionLocal, create_all_tables
from backend.models.usuario import Usuario
from backend.models.cohorte import Cohorte
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.models.aplicacion import Aplicacion
from backend.models.entrevista import Entrevista
from backend.models.enums import (
    RolEnum, EstadoUsuario, EstadoCohorte, ModalidadApp,
    OrigenApp, EstadoApp, TipoEntrevista, ModalidadEntrevista,
    PercepcionGrupal, RespuestaEmpresa,
)
from backend.utils.security import hash_password
from backend.services.cohort_engine import fecha_fin_desde_inicio
from backend.services.state_engine import aplicar_estado

random.seed(42)

# ── Datos de referencia ────────────────────────────────────────────────────────

EMPRESAS = [
    "Bancolombia", "Rappi", "Platzi", "Mercado Libre", "Grupo Éxito",
    "Avianca", "Claro Colombia", "EPM", "Davivienda", "Nutresa",
    "Pragma", "PSL", "Globant", "Endava", "Softtek",
    "IBM Colombia", "Accenture", "Deloitte", "EY Colombia", "PwC",
    "Tata Consultancy", "Infosys", "Cognizant", "Ceiba", "MercadoPago",
    "Nequi", "Addi", "Habi", "Frubana", "Sysco",
]
VACANTES = [
    "Desarrollador Backend Java", "Ingeniero Spring Boot", "Full Stack Developer",
    "Desarrollador de Software Jr", "Programador Java", "Backend Developer",
    "Desarrollador API REST", "Ingeniero de Software", "Java Developer Jr",
    "Desarrollador Web Backend", "Desarrollador Microservicios", "QA Automation Jr",
    "DevOps Jr", "Analista de Sistemas", "Desarrollador Cloud AWS",
]
CIUDADES = [
    "Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga",
    "Pereira", "Cartagena", "Manizales", "Ibagué", "Cúcuta",
]
SUBFALLAS_POR_FALLA = {
    "TECNICA": [
        "No conocía el tema", "Error lógico", "Falta de profundidad",
        "No supo resolver el reto técnico", "Confundió conceptos de OOP",
    ],
    "COMUNICACION": [
        "No supe explicar", "Falta de claridad", "Desorden al hablar",
        "Respuestas muy cortas", "No escuchó bien las preguntas",
    ],
    "BLANDAS": [
        "No estructuré respuestas", "No comuniqué experiencia",
        "Falta de proactividad en el diálogo", "No mostró trabajo en equipo",
    ],
    "REGULACION_EMOCIONAL": [
        "Me bloqueé", "Perdí el hilo", "Nervios altos",
        "Silencios prolongados", "Voz insegura",
    ],
}
REFLEXIONES_BIEN = [
    "Expliqué bien mis proyectos anteriores",
    "Respondí con seguridad las preguntas de RRHH",
    "Llegué puntual y bien presentado",
    "Demostré conocimiento en Spring Boot",
    "Mantuve buena comunicación durante toda la entrevista",
    "Resolví correctamente el ejercicio de SQL",
    "Pregunté dudas relevantes al final",
    "Expresé claramente mi motivación por la empresa",
    "Conecté mi historia personal con el rol",
    "Usé ejemplos concretos de mis proyectos del bootcamp",
    "Mantuve contacto visual y lenguaje corporal positivo",
    "Demostré curiosidad por el equipo y la cultura",
]
REFLEXIONES_MEJORAR = [
    "Necesito practicar más algoritmos de ordenamiento",
    "Debo mejorar la explicación de conceptos de Java OOP",
    "Estudiar más sobre arquitectura de microservicios",
    "Practicar SQL joins complejos",
    "Mejorar la claridad al explicar proyectos",
    "Reducir los nervios al hablar en público",
    "Estructurar mejor las respuestas STAR",
    "Profundizar en Spring Security",
    "Practicar más ejercicios en vivo de código",
    "Mejorar el inglés técnico",
    "Investigar más sobre la empresa antes de la entrevista",
    "Trabajar la narrativa de mi perfil profesional",
    "Practicar el pitch personal de 2 minutos",
    "Mejorar la gestión del tiempo en retos de código",
]
NOMBRES_BASE = [
    "ana","carlos","sofia","daniel","maria","juan","laura","pedro",
    "valeria","miguel","camila","andres","isabella","sebastian","valentina",
    "felipe","natalia","julian","paula","david","sara","jorge","diana",
    "alejandro","monica","ricardo","paola","luis","adriana","gabriel",
    "catalina","mario","andrea","nicolas","claudia","roberto","patricia",
    "sergio","liliana","fernando","carolina","henry","marcela","ivan","gloria",
    "oscar","beatriz","hugo","rosa","jaime","teresa","ernesto","pilar",
    "rafael","nora","alfredo","sandra","enrique","marta","victor","luz",
    "gonzalo","elena","hernan","nancy","ignacio","hilda","rodrigo","lina",
    "esteban","viviana","samuel","manuela","tomas","alejandra","mateo","xiomara",
    "simon","leidy","santiago","yuli","fabian","alba","javier","jessica",
]

ORIGENES       = [o.value for o in OrigenApp]
MODALIDADES_APP= [m.value for m in ModalidadApp]
TIPOS_ENT      = [t.value for t in TipoEntrevista]
MODALIDADES_ENT= [m.value for m in ModalidadEntrevista]
TEMAS_TECNICOS = ["JAVA", "SPRING_BOOT", "APIS", "SQL", "ALGORITMOS", "OTRO"]
TODAS_FALLAS   = list(SUBFALLAS_POR_FALLA.keys())

PWD = hash_password("Test@1234")
HOY = date.today()


# ── Helpers ────────────────────────────────────────────────────────────────────

def rand_fecha(dias_min=1, dias_max=150):
    return HOY - timedelta(days=random.randint(dias_min, dias_max))


def rand_datetime(dias_min=1, dias_max=150):
    return datetime.now(timezone.utc) - timedelta(
        days=random.randint(dias_min, dias_max),
        hours=random.randint(0, 8),
    )


def crear_usuario(db, email, rol, estado=EstadoUsuario.ACTIVO, dias_login=1):
    u = db.query(Usuario).filter(Usuario.email == email).first()
    if u:
        return u
    u = Usuario(
        email=email, password_hash=PWD, rol=rol,
        estado=estado, activo=True,
        last_login=datetime.now(timezone.utc) - timedelta(days=dias_login),
    )
    db.add(u); db.flush()
    return u


def hacer_entrevista(app_id, tipo, dias, fallas_keys, grupal=False):
    """Construye una Entrevista con subfallas y temas coherentes."""
    subfallas = []
    for fk in fallas_keys:
        subs = SUBFALLAS_POR_FALLA.get(fk, [])
        if subs:
            n = random.randint(1, min(2, len(subs)))
            subfallas.extend(random.sample(subs, n))

    temas = []
    if "TECNICA" in fallas_keys:
        temas = random.sample(TEMAS_TECNICOS, random.randint(1, 3))

    percepcion = None
    if grupal:
        percepcion = random.choice([p.value for p in PercepcionGrupal])

    return Entrevista(
        aplicacion_id=app_id,
        tipo=tipo,
        modalidad=random.choice(MODALIDADES_ENT),
        fecha=rand_datetime(dias, dias + 2),
        grupal=grupal,
        percepcion_grupal=percepcion,
        fallas=fallas_keys,
        subfallas=subfallas,
        temas_tecnicos=temas,
        autoevaluacion=random.randint(1, 5),
        reflexion_bien=random.choice(REFLEXIONES_BIEN),
        reflexion_mejorar=random.choice(REFLEXIONES_MEJORAR),
        respuesta_empresa=random.choice([r.value for r in RespuestaEmpresa] + [None]),
    )


def seed_aplicaciones(db, ap_id, estado_cohorte, dias_inicio_cohorte):
    """
    Genera entre 0 y 9 aplicaciones para un aprendiz,
    ajustando el perfil según el estado y antigüedad de su cohorte.
    """
    # Cohortes recientes (<45 días): poca actividad todavía
    if dias_inicio_cohorte < 45:
        n_apps = random.randint(0, 2)
    # Deshabilitadas: completaron el ciclo pero con cierre; actividad variable
    elif estado_cohorte == EstadoCohorte.INACTIVA:
        n_apps = random.randint(2, 7)
    else:
        n_apps = random.randint(3, 9)

    for _ in range(n_apps):
        app = Aplicacion(
            usuario_id=ap_id,
            empresa=random.choice(EMPRESAS),
            vacante=random.choice(VACANTES),
            modalidad=random.choice(MODALIDADES_APP),
            origen=random.choice(ORIGENES),
            fecha_aplicacion=rand_fecha(5, min(180, dias_inicio_cohorte + 10)),
        )
        db.add(app); db.flush()

        # Pesos de escenario según tipo de cohorte
        if estado_cohorte == EstadoCohorte.FINALIZADA:
            # Histórica: más contratados y rechazados definitivos
            pesos = [18, 22, 30, 15, 15]
        elif estado_cohorte == EstadoCohorte.INACTIVA:
            # Cerrada administrativamente: mezcla de todos los estados
            pesos = [12, 20, 28, 22, 18]
        elif dias_inicio_cohorte < 45:
            # Reciente: mayoría solo aplicados o en espera inicial
            pesos = [2, 8, 12, 33, 45]
        else:
            # Activa consolidada: distribución equilibrada
            pesos = [10, 28, 22, 25, 15]

        perfil = random.choices(
            ["contratado", "avanzando", "rechazado", "en_espera", "aplicado"],
            weights=pesos,
        )[0]

        if perfil == "contratado":
            for k in range(random.randint(3, 6)):
                fallas = random.sample(TODAS_FALLAS, random.randint(0, 1))
                e = hacer_entrevista(
                    app.id, TIPOS_ENT[min(k, len(TIPOS_ENT) - 1)],
                    random.randint(1, 5) + k * 7, fallas,
                    grupal=random.random() > 0.75,
                )
                e.autoevaluacion = random.randint(3, 5)
                db.add(e); db.flush()
            todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
            aplicar_estado(app, todas)
            app.estado = EstadoApp.CONTRATADO

        elif perfil == "avanzando":
            for k in range(random.randint(2, 4)):
                fallas = random.sample(TODAS_FALLAS, random.randint(1, 2))
                e = hacer_entrevista(
                    app.id, random.choice(TIPOS_ENT),
                    random.randint(1, 7), fallas,
                    grupal=random.random() > 0.88,
                )
                e.autoevaluacion = random.randint(2, 4)
                db.add(e); db.flush()
            todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
            aplicar_estado(app, todas)

        elif perfil == "rechazado":
            for k in range(random.randint(1, 3)):
                fallas = random.sample(TODAS_FALLAS, random.randint(2, 4))
                e = hacer_entrevista(
                    app.id, random.choice(TIPOS_ENT),
                    random.randint(11, 20), fallas,
                    grupal=random.random() > 0.9,
                )
                e.autoevaluacion = random.randint(1, 3)
                db.add(e); db.flush()
            todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
            aplicar_estado(app, todas)

        elif perfil == "en_espera":
            for k in range(random.randint(1, 2)):
                fallas = random.sample(TODAS_FALLAS, random.randint(0, 2))
                tipo_e = TipoEntrevista.RRHH.value if k == 0 else random.choice(TIPOS_ENT)
                e = hacer_entrevista(app.id, tipo_e, random.randint(2, 9), fallas)
                db.add(e); db.flush()
            todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
            aplicar_estado(app, todas)

        # perfil "aplicado": la app ya está creada sin entrevistas


# ── Definición de cohortes ─────────────────────────────────────────────────────
#
# 20 cohortes escalonadas en 4 épocas de 5 cohortes cada una.
# Cada época ocupa ~6 meses, sin solapamiento entre épocas consecutivas,
# lo que permite reutilizar los 30 tutores en épocas alternadas.
#
#  Época A (tutores  1-30): cohortes  1-5   (hace ~24-30 meses)
#  Época B (tutores  1-30): cohortes  6-10  (hace ~18-24 meses) ← reutilizados
#  Época C (tutores  1-30): cohortes 11-15  (hace ~12-18 meses) ← reutilizados
#  Época D (tutores  1-30): cohortes 16-20  (hace  0-12 meses)  ← reutilizados
#
# Todos los tutores forman un pool único de 30; en cada época los 30 están
# disponibles (ya terminaron la época anterior) y se distribuyen 6 por cohorte.
#
COHORTES_DEF = [
    # ── INACTIVAS (3) — completaron ciclo, cierre administrativo ──────
    # nombre                           inicio_dias  estado                meta  ext
    ("Full Stack Java 2022-I",          900, EstadoCohorte.INACTIVA,      20, False),
    ("Backend Cloud 2022",              840, EstadoCohorte.INACTIVA,      15, False),
    ("Java Enterprise 2022-I",          780, EstadoCohorte.INACTIVA,      20, False),

    # ── FINALIZADAS (5) — históricas con datos completos ──────────────
    ("Full Stack Java 2022-II",         720, EstadoCohorte.FINALIZADA,    18, True ),
    ("Full Stack Java 2023-I",          660, EstadoCohorte.FINALIZADA,    22, True ),
    ("Backend Avanzado 2023-I",         600, EstadoCohorte.FINALIZADA,    18, False),
    ("Full Stack Java 2023-II",         540, EstadoCohorte.FINALIZADA,    20, True ),
    ("Java Enterprise 2023-I",          480, EstadoCohorte.FINALIZADA,    22, False),

    # ── ACTIVAS consolidadas (8) — llevan varios meses en curso ───────
    ("Full Stack Java 2023-III",        420, EstadoCohorte.ACTIVA,        25, False),
    ("Backend Cloud 2023",              380, EstadoCohorte.ACTIVA,        20, False),
    ("Java + DevOps 2023",              340, EstadoCohorte.ACTIVA,        22, False),
    ("Full Stack Java 2024-I",          300, EstadoCohorte.ACTIVA,        25, False),
    ("Backend Avanzado 2024-I",         260, EstadoCohorte.ACTIVA,        20, False),
    ("Java Enterprise 2024-I",          220, EstadoCohorte.ACTIVA,        22, False),
    ("Full Stack Java 2024-II",         180, EstadoCohorte.ACTIVA,        28, False),
    ("Backend Cloud 2024",              140, EstadoCohorte.ACTIVA,        20, False),

    # ── ACTIVAS recientes (4) — recién iniciadas ───────────────────────
    ("Java Enterprise 2024-II",          90, EstadoCohorte.ACTIVA,        22, False),
    ("Full Stack Java 2024-III",         60, EstadoCohorte.ACTIVA,        30, False),
    ("Backend Avanzado 2024-II",         30, EstadoCohorte.ACTIVA,        25, False),
    ("Full Stack Java 2025-I",           10, EstadoCohorte.ACTIVA,        35, False),
]


def seed():
    create_all_tables()
    db = SessionLocal()
    print("🌱 Generando datos masivos...\n")

    try:
        # ── Coordinador ───────────────────────────────────────────────────────
        crear_usuario(db, "coord@bootcamp.com", RolEnum.COORDINADOR)
        print("✅ Coordinador")

        # ── 30 tutores ────────────────────────────────────────────────────────
        # Se crean todos; la asignación a UNA cohorte la controla AprendizPerfil.
        tutores = [
            crear_usuario(db, f"tutor{i}@bootcamp.com", RolEnum.TUTOR,
                          dias_login=random.randint(1, 10))
            for i in range(1, 31)
        ]
        print(f"✅ {len(tutores)} tutores")

        # ── Cohortes ──────────────────────────────────────────────────────────
        cohortes = []
        for nombre, inicio_dias, estado_c, meta, ext in COHORTES_DEF:
            fecha_inicio = HOY - timedelta(days=inicio_dias)
            c = db.query(Cohorte).filter(Cohorte.nombre == nombre).first()
            if not c:
                c = Cohorte(
                    nombre=nombre,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin_desde_inicio(fecha_inicio),
                    estado=estado_c,
                    meta_contratacion=meta,
                    permitir_extension=ext,
                )
                db.add(c); db.flush()
            cohortes.append((c, inicio_dias, estado_c))
        print(f"✅ {len(cohortes)} cohortes")

        # ── Distribución de tutores por cohorte ───────────────────────────────
        # 20 cohortes × 6 tutores = 120 slots.
        # Pool de 30 tutores se reparte en bloques de 6 y se rota
        # por los 20 slots (30 tutores * 4 rondas = 120 asignaciones).
        # Cada tutor queda asignado a exactamente 4 cohortes pero
        # NUNCA en dos cohortes que se solapen en el tiempo (épocas distintas).
        #
        # Orden de asignación: shuffle por época para que no siempre
        # los mismos 6 tutores vayan juntos.
        random.shuffle(tutores)  # mezcla inicial
        tutores_pool = tutores * 4  # 30 × 4 = 120 slots en orden
        tutor_idx = 0

        aprendiz_idx = 1

        for c, inicio_dias, estado_c in cohortes:
            # Tomar 6 tutores consecutivos del pool rotado
            tutores_cohorte = tutores_pool[tutor_idx: tutor_idx + 6]
            tutor_idx += 6

            # Número de aprendices: 40-55 en todos los estados
            n_aprendices = random.randint(40, 55)

            for _ in range(n_aprendices):
                nombre = NOMBRES_BASE[aprendiz_idx % len(NOMBRES_BASE)]
                email  = f"{nombre}{aprendiz_idx}@gmail.com"
                aprendiz_idx += 1

                ap = crear_usuario(
                    db, email, RolEnum.APRENDIZ,
                    dias_login=random.choice([1,2,3,7,10,15,20,25,30]),
                )
                tutor = random.choice(tutores_cohorte)

                if not db.query(AprendizPerfil).filter(
                    AprendizPerfil.usuario_id == ap.id
                ).first():
                    db.add(AprendizPerfil(
                        usuario_id=ap.id,
                        cohorte_id=c.id,
                        tutor_id=tutor.id,
                        ciudad=random.choice(CIUDADES),
                        telefono=f"30{random.randint(10_000_000, 99_999_999)}",
                    )); db.flush()

                seed_aplicaciones(db, ap.id, estado_c, inicio_dias)

        db.commit()

        # ── Resumen ───────────────────────────────────────────────────────────
        total_ap   = db.query(Usuario).filter(Usuario.rol == RolEnum.APRENDIZ).count()
        total_apps = db.query(Aplicacion).count()
        total_ent  = db.query(Entrevista).count()
        contrat    = db.query(Aplicacion).filter(Aplicacion.estado == EstadoApp.CONTRATADO).count()

        n_fin = db.query(Cohorte).filter(Cohorte.estado == EstadoCohorte.FINALIZADA).count()
        n_dsh = db.query(Cohorte).filter(Cohorte.estado == EstadoCohorte.INACTIVA).count()
        n_act = db.query(Cohorte).filter(Cohorte.estado == EstadoCohorte.ACTIVA).count()

        print(f"\n🎉 Seed completado!")
        print(f"{'─'*55}")
        print(f"  Cohortes totales   : {n_fin + n_dsh + n_act}")
        print(f"    · Finalizadas    : {n_fin}")
        print(f"    · Inactivas      : {n_dsh}")
        print(f"    · Activas        : {n_act}")
        print(f"  Tutores            : 30  (6 por cohorte, sin solapamiento)")
        print(f"  Aprendices         : {total_ap}")
        print(f"  Aplicaciones       : {total_apps}")
        print(f"  Entrevistas        : {total_ent}")
        print(f"  Contratados        : {contrat}")
        print(f"{'─'*55}")
        print(f"  Coordinador : coord@bootcamp.com  / Test@1234")
        print(f"  Tutores     : tutor1-30@bootcamp.com / Test@1234")
        print(f"  Aprendices  : ana1@gmail.com ...   / Test@1234")
        print(f"{'─'*55}\n")

    except Exception as ex:
        db.rollback()
        print(f"❌ Error: {ex}")
        import traceback; traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
