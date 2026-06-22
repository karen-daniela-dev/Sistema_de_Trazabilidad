"""
Seed masivo para desarrollo — genera datos realistas y variados.
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
    "Heinsohn", "Arus", "Cadena", "Indra", "Stefanini",
]
VACANTES = [
    "Desarrollador Backend Java", "Ingeniero Spring Boot", "Full Stack Developer",
    "Desarrollador de Software Jr", "Programador Java", "Backend Developer",
    "Desarrollador API REST", "Ingeniero de Software", "Java Developer Jr",
    "Desarrollador Web Backend", "Software Engineer", "Programador Jr",
]
CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Pereira", "Manizales"]
FALLAS = [f.value for f in FallaEnum]
ORIGENES = [o.value for o in OrigenApp]
MODALIDADES_APP = [m.value for m in ModalidadApp]
TIPOS_ENT = [t.value for t in TipoEntrevista]
MODALIDADES_ENT = [m.value for m in ModalidadEntrevista]

PWD = hash_password("Test@1234")

def rand_fecha(dias_min=1, dias_max=150):
    return date.today() - timedelta(days=random.randint(dias_min, dias_max))

def rand_datetime(dias_min=1, dias_max=150):
    return datetime.now(timezone.utc) - timedelta(
        days=random.randint(dias_min, dias_max),
        hours=random.randint(0, 8)
    )

def crear_usuario(db, email, rol, estado=EstadoUsuario.ACTIVO, dias_login=1):
    if db.query(Usuario).filter(Usuario.email == email).first():
        return db.query(Usuario).filter(Usuario.email == email).first()
    u = Usuario(
        email=email, password_hash=PWD, rol=rol,
        estado=estado, activo=True,
        last_login=datetime.now(timezone.utc) - timedelta(days=dias_login),
    )
    db.add(u); db.flush(); return u

def seed():
    create_all_tables()
    db = SessionLocal()
    print("🌱 Generando datos masivos...\n")

    try:
        # ── Coordinador ───────────────────────────────────────────
        coord = crear_usuario(db, "coord@bootcamp.com", RolEnum.COORDINADOR)
        print("✅ Coordinador creado")

        # ── 4 Tutores ─────────────────────────────────────────────
        tutores = []
        for i in range(1, 5):
            t = crear_usuario(db, f"tutor{i}@bootcamp.com", RolEnum.TUTOR)
            tutores.append(t)
        print(f"✅ {len(tutores)} tutores creados")

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
        print(f"✅ {len(cohortes)} cohortes creadas")

        # ── 45 Aprendices ─────────────────────────────────────────
        aprendices_creados = 0
        aprendiz_idx = 1

        nombres = [
            "ana","carlos","sofia","daniel","maria","juan","laura","pedro",
            "valeria","miguel","camila","andres","isabella","sebastian","valentina",
            "felipe","natalia","julian","paula","david","sara","jorge","diana",
            "alejandro","monica","ricardo","paola","luis","adriana","gabriel",
            "catalina","mario","andrea","nicolas","claudia","roberto","patricia",
            "sergio","liliana","fernando","carolina","henry","marcela","ivan","gloria"
        ]

        for cohorte in cohortes:
            # 15 aprendices por cohorte
            tutor_pool = tutores[:2] if cohorte == cohortes[0] else tutores[1:3] if cohorte == cohortes[1] else tutores[2:]
            n_aprendices = 15

            for i in range(n_aprendices):
                nombre = nombres[aprendiz_idx % len(nombres)]
                email = f"{nombre}{aprendiz_idx}@gmail.com"
                aprendiz_idx += 1

                # Variedad de inactividad
                dias_login = random.choice([1, 2, 3, 7, 10, 15, 20, 25])
                ap = crear_usuario(db, email, RolEnum.APRENDIZ, dias_login=dias_login)

                tutor = random.choice(tutor_pool)
                if not db.query(AprendizPerfil).filter(AprendizPerfil.usuario_id == ap.id).first():
                    perfil = AprendizPerfil(
                        usuario_id=ap.id, cohorte_id=cohorte.id,
                        tutor_id=tutor.id, ciudad=random.choice(CIUDADES),
                        telefono=f"30{random.randint(10000000,99999999)}",
                    )
                    db.add(perfil); db.flush()

                # ── Aplicaciones por aprendiz ──────────────────────
                n_apps = random.randint(2, 8)
                for j in range(n_apps):
                    empresa = random.choice(EMPRESAS)
                    app = Aplicacion(
                        usuario_id=ap.id,
                        empresa=empresa,
                        vacante=random.choice(VACANTES),
                        modalidad=random.choice(MODALIDADES_APP),
                        origen=random.choice(ORIGENES),
                        fecha_aplicacion=rand_fecha(5, 100),
                    )
                    db.add(app); db.flush()

                    # ── Entrevistas por aplicación ─────────────────
                    # Distribución realista de estados
                    perfil_tipo = random.choices(
                        ["contratado", "avanzando", "rechazado", "en_espera", "aplicado"],
                        weights=[10, 25, 20, 25, 20]
                    )[0]

                    entrevistas = []

                    if perfil_tipo == "contratado":
                        n_ent = random.randint(3, 5)
                        for k in range(n_ent):
                            dias = random.randint(1, 5) + k * 7
                            e = Entrevista(
                                aplicacion_id=app.id,
                                tipo=TIPOS_ENT[min(k, len(TIPOS_ENT)-1)],
                                modalidad=random.choice(MODALIDADES_ENT),
                                fecha=rand_datetime(dias, dias+2),
                                grupal=random.choice([True, False]),
                                percepcion_grupal=random.choice([p.value for p in PercepcionGrupal]) if random.random() > 0.5 else None,
                                fallas=random.sample(FALLAS, random.randint(0, 2)),
                                autoevaluacion=random.randint(3, 5),
                                reflexion_bien="Buena comunicación y preparación técnica",
                                reflexion_mejorar="Mejorar velocidad en algoritmos",
                                respuesta_empresa=RespuestaEmpresa.AVANZO.value,
                            )
                            if e.grupal and not e.percepcion_grupal:
                                e.percepcion_grupal = PercepcionGrupal.MEJOR.value
                            db.add(e); db.flush()
                            entrevistas.append(e)
                        todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
                        aplicar_estado(app, todas)
                        app.estado = EstadoApp.CONTRATADO

                    elif perfil_tipo == "avanzando":
                        n_ent = random.randint(2, 4)
                        for k in range(n_ent):
                            e = Entrevista(
                                aplicacion_id=app.id,
                                tipo=random.choice(TIPOS_ENT),
                                modalidad=random.choice(MODALIDADES_ENT),
                                fecha=rand_datetime(1, 8),
                                grupal=False,
                                fallas=random.sample(FALLAS, random.randint(0, 2)),
                                autoevaluacion=random.randint(2, 4),
                                reflexion_bien="Me expresé bien",
                                reflexion_mejorar="Debo practicar más SQL",
                            )
                            db.add(e); db.flush()
                            entrevistas.append(e)
                        todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
                        aplicar_estado(app, todas)

                    elif perfil_tipo == "rechazado":
                        n_ent = random.randint(2, 3)
                        for k in range(n_ent):
                            e = Entrevista(
                                aplicacion_id=app.id,
                                tipo=random.choice(TIPOS_ENT),
                                modalidad=random.choice(MODALIDADES_ENT),
                                fecha=rand_datetime(11, 14),
                                grupal=False,
                                fallas=random.sample(FALLAS, random.randint(1, 3)),
                                autoevaluacion=random.randint(1, 3),
                                reflexion_bien="Llegué a tiempo",
                                reflexion_mejorar="Necesito mejorar mucho en Java y Spring",
                                respuesta_empresa=RespuestaEmpresa.RECHAZADO.value,
                            )
                            db.add(e); db.flush()
                            entrevistas.append(e)
                        todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
                        aplicar_estado(app, todas)

                    elif perfil_tipo == "en_espera":
                        e = Entrevista(
                            aplicacion_id=app.id,
                            tipo=TipoEntrevista.RRHH.value,
                            modalidad=random.choice(MODALIDADES_ENT),
                            fecha=rand_datetime(2, 9),
                            grupal=False,
                            fallas=random.sample(FALLAS, random.randint(0, 1)),
                            autoevaluacion=random.randint(2, 4),
                            reflexion_bien="Buena actitud",
                            reflexion_mejorar="Mejorar inglés",
                        )
                        db.add(e); db.flush()
                        todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
                        aplicar_estado(app, todas)
                    # else: APLICADO — sin entrevistas

                aprendices_creados += 1

        db.commit()

        # Stats finales
        total_apps = db.query(Aplicacion).count()
        total_ent = db.query(Entrevista).count()
        total_ap = db.query(Usuario).filter(Usuario.rol == RolEnum.APRENDIZ).count()
        contratados = db.query(Aplicacion).filter(Aplicacion.estado == EstadoApp.CONTRATADO).count()

        print(f"\n🎉 Seed masivo completado!")
        print(f"{'─'*50}")
        print(f"  Aprendices  : {total_ap}")
        print(f"  Aplicaciones: {total_apps}")
        print(f"  Entrevistas : {total_ent}")
        print(f"  Contratados : {contratados}")
        print(f"{'─'*50}")
        print(f"\n  Coordinador : coord@bootcamp.com   / Coord@1234")
        print(f"  Tutores     : tutor1-4@bootcamp.com / Test@1234")
        print(f"  Aprendices  : ana1@gmail.com ... / Test@1234")
        print(f"{'─'*50}\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()