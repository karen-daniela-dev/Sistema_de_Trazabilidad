"""
Seed masivo con fallas, subfallas y reflexiones detalladas.
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
    FallaEnum, PercepcionGrupal, RespuestaEmpresa
)
from backend.utils.security import hash_password
from backend.services.cohort_engine import fecha_fin_desde_inicio
from backend.services.state_engine import aplicar_estado
import uuid

random.seed(42)

EMPRESAS = [
    "Bancolombia", "Rappi", "Platzi", "Mercado Libre", "Grupo Éxito",
    "Avianca", "Claro Colombia", "EPM", "Davivienda", "Nutresa",
    "Pragma", "PSL", "Globant", "Endava", "Softtek",
    "IBM Colombia", "Accenture", "Deloitte", "EY Colombia", "PwC",
]
VACANTES = [
    "Desarrollador Backend Java", "Ingeniero Spring Boot", "Full Stack Developer",
    "Desarrollador de Software Jr", "Programador Java", "Backend Developer",
    "Desarrollador API REST", "Ingeniero de Software", "Java Developer Jr",
    "Desarrollador Web Backend",
]
CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Pereira"]

# Subfallas reales por falla
SUBFALLAS_POR_FALLA = {
    "TECNICA": [
        "No conocía el tema",
        "Error lógico",
        "Falta de profundidad",
    ],
    "COMUNICACION": [
        "No supe explicar",
        "Falta de claridad",
        "Desorden al hablar",
    ],
    "BLANDAS": [
        "No estructuré respuestas",
        "No comuniqué experiencia",
    ],
    "REGULACION_EMOCIONAL": [
        "Me bloqueé",
        "Perdí el hilo",
        "Nervios altos",
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
]

ORIGENES = [o.value for o in OrigenApp]
MODALIDADES_APP = [m.value for m in ModalidadApp]
TIPOS_ENT = [t.value for t in TipoEntrevista]
MODALIDADES_ENT = [m.value for m in ModalidadEntrevista]
TEMAS_TECNICOS = ["JAVA", "SPRING_BOOT", "APIS", "SQL", "ALGORITMOS", "OTRO"]

PWD = hash_password("Test@1234")


def rand_fecha(dias_min=1, dias_max=150):
    return date.today() - timedelta(days=random.randint(dias_min, dias_max))


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
    db.add(u); db.flush(); return u


def hacer_entrevista(app_id, tipo, dias, fallas_keys, grupal=False):
    """Crea una entrevista con fallas y subfallas realistas."""
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


def seed():
    create_all_tables()
    db = SessionLocal()
    print("🌱 Generando datos masivos con fallas detalladas...\n")

    try:
        # ── Coordinador ───────────────────────────────────────────
        coord = crear_usuario(db, "coord@bootcamp.com", RolEnum.COORDINADOR)
        print("✅ Coordinador")

        # ── 4 Tutores ─────────────────────────────────────────────
        tutores = [crear_usuario(db, f"tutor{i}@bootcamp.com", RolEnum.TUTOR) for i in range(1, 5)]
        print(f"✅ {len(tutores)} tutores")

        # ── 3 Cohortes ────────────────────────────────────────────
        cohortes_data = [
            ("Full Stack Java 2023-II", date.today() - timedelta(days=240), EstadoCohorte.FINALIZADA, 15),
            ("Full Stack Java 2024-I",  date.today() - timedelta(days=120), EstadoCohorte.ACTIVA,     20),
            ("Full Stack Java 2024-II", date.today() - timedelta(days=30),  EstadoCohorte.ACTIVA,     18),
        ]
        cohortes = []
        for nombre, inicio, estado_c, meta in cohortes_data:
            c = db.query(Cohorte).filter(Cohorte.nombre == nombre).first()
            if not c:
                c = Cohorte(
                    nombre=nombre, fecha_inicio=inicio,
                    fecha_fin=fecha_fin_desde_inicio(inicio),
                    estado=estado_c, meta_contratacion=meta,
                    permitir_extension=(estado_c == EstadoCohorte.FINALIZADA),
                )
                db.add(c); db.flush()
            cohortes.append(c)
        print(f"✅ {len(cohortes)} cohortes")

        # ── Aprendices ────────────────────────────────────────────
        nombres = [
            "ana","carlos","sofia","daniel","maria","juan","laura","pedro",
            "valeria","miguel","camila","andres","isabella","sebastian","valentina",
            "felipe","natalia","julian","paula","david","sara","jorge","diana",
            "alejandro","monica","ricardo","paola","luis","adriana","gabriel",
            "catalina","mario","andrea","nicolas","claudia","roberto","patricia",
            "sergio","liliana","fernando","carolina","henry","marcela","ivan","gloria",
        ]

        aprendiz_idx = 1
        for ci, cohorte in enumerate(cohortes):
            tutor_pool = tutores[:2] if ci == 0 else tutores[1:3] if ci == 1 else tutores[2:]

            for _ in range(15):
                nombre = nombres[aprendiz_idx % len(nombres)]
                email  = f"{nombre}{aprendiz_idx}@gmail.com"
                aprendiz_idx += 1

                ap = crear_usuario(db, email, RolEnum.APRENDIZ,
                                   dias_login=random.choice([1,2,3,7,10,15,20,25]))
                tutor = random.choice(tutor_pool)

                if not db.query(AprendizPerfil).filter(AprendizPerfil.usuario_id == ap.id).first():
                    db.add(AprendizPerfil(
                        usuario_id=ap.id, cohorte_id=cohorte.id,
                        tutor_id=tutor.id, ciudad=random.choice(CIUDADES),
                        telefono=f"30{random.randint(10000000,99999999)}",
                    )); db.flush()

                # ── Aplicaciones ──────────────────────────────────
                for _ in range(random.randint(3, 8)):
                    app = Aplicacion(
                        usuario_id=ap.id,
                        empresa=random.choice(EMPRESAS),
                        vacante=random.choice(VACANTES),
                        modalidad=random.choice(MODALIDADES_APP),
                        origen=random.choice(ORIGENES),
                        fecha_aplicacion=rand_fecha(5, 100),
                    )
                    db.add(app); db.flush()

                    perfil_tipo = random.choices(
                        ["contratado","avanzando","rechazado","en_espera","aplicado"],
                        weights=[10, 28, 22, 25, 15],
                    )[0]

                    todas_fallas = list(SUBFALLAS_POR_FALLA.keys())

                    if perfil_tipo == "contratado":
                        # 3-5 entrevistas, sin fallas o pocas
                        for k in range(random.randint(3, 5)):
                            fallas = random.sample(todas_fallas, random.randint(0, 1))
                            e = hacer_entrevista(app.id, TIPOS_ENT[min(k, 2)],
                                                 random.randint(1,5) + k*7, fallas,
                                                 grupal=random.random() > 0.7)
                            e.autoevaluacion = random.randint(3, 5)
                            db.add(e); db.flush()
                        todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
                        aplicar_estado(app, todas)
                        app.estado = EstadoApp.CONTRATADO

                    elif perfil_tipo == "avanzando":
                        for k in range(random.randint(2, 4)):
                            fallas = random.sample(todas_fallas, random.randint(1, 2))
                            e = hacer_entrevista(app.id, random.choice(TIPOS_ENT),
                                                 random.randint(1, 7), fallas)
                            e.autoevaluacion = random.randint(2, 4)
                            db.add(e); db.flush()
                        todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
                        aplicar_estado(app, todas)

                    elif perfil_tipo == "rechazado":
                        for k in range(random.randint(2, 3)):
                            fallas = random.sample(todas_fallas, random.randint(2, 3))
                            e = hacer_entrevista(app.id, random.choice(TIPOS_ENT),
                                                 random.randint(11, 14), fallas)
                            e.autoevaluacion = random.randint(1, 3)
                            db.add(e); db.flush()
                        todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
                        aplicar_estado(app, todas)

                    elif perfil_tipo == "en_espera":
                        fallas = random.sample(todas_fallas, random.randint(0, 2))
                        e = hacer_entrevista(app.id, TipoEntrevista.RRHH.value,
                                             random.randint(2, 9), fallas)
                        db.add(e); db.flush()
                        todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
                        aplicar_estado(app, todas)
                    # aplicado: sin entrevistas

        db.commit()

        total_ap   = db.query(Usuario).filter(Usuario.rol == RolEnum.APRENDIZ).count()
        total_apps = db.query(Aplicacion).count()
        total_ent  = db.query(Entrevista).count()
        contrat    = db.query(Aplicacion).filter(Aplicacion.estado == EstadoApp.CONTRATADO).count()

        print(f"\n🎉 Seed completado!")
        print(f"{'─'*50}")
        print(f"  Aprendices  : {total_ap}")
        print(f"  Aplicaciones: {total_apps}")
        print(f"  Entrevistas : {total_ent}")
        print(f"  Contratados : {contrat}")
        print(f"{'─'*50}")
        print(f"  Coordinador : coord@bootcamp.com  / Test@1234")
        print(f"  Tutores     : tutor1-4@bootcamp.com / Test@1234")
        print(f"  Aprendices  : ana1@gmail.com ...   / Test@1234")
        print(f"{'─'*50}\n")

    except Exception as ex:
        db.rollback()
        print(f"❌ Error: {ex}")
        import traceback; traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()