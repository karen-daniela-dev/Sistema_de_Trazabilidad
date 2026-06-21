"""
Script de seed para desarrollo — crea datos de prueba realistas.
NUNCA ejecutar en producción.
"""
import sys, os
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
    OrigenApp, EstadoApp, TipoEntrevista, ModalidadEntrevista
)
from backend.utils.security import hash_password
from backend.services.cohort_engine import fecha_fin_desde_inicio
from backend.services.state_engine import aplicar_estado
import uuid


def seed():
    create_all_tables()
    db = SessionLocal()

    print("🌱 Iniciando seed de datos de desarrollo...")

    try:
        # ── Coordinador ───────────────────────────────────────────────────────
        coord = db.query(Usuario).filter(Usuario.email == "coord@bootcamp.com").first()
        if not coord:
            coord = Usuario(
                email="coord@bootcamp.com",
                password_hash=hash_password("Coord@1234"),
                rol=RolEnum.COORDINADOR,
                estado=EstadoUsuario.ACTIVO,
                activo=True,
                last_login=datetime.now(timezone.utc),
            )
            db.add(coord)
            print("  ✅ Coordinador: coord@bootcamp.com / Coord@1234")

        # ── Tutores ───────────────────────────────────────────────────────────
        tutor1 = db.query(Usuario).filter(Usuario.email == "tutor1@bootcamp.com").first()
        if not tutor1:
            tutor1 = Usuario(
                email="tutor1@bootcamp.com",
                password_hash=hash_password("Tutor@1234"),
                rol=RolEnum.TUTOR,
                estado=EstadoUsuario.ACTIVO,
                activo=True,
                last_login=datetime.now(timezone.utc),
            )
            db.add(tutor1)

        tutor2 = db.query(Usuario).filter(Usuario.email == "tutor2@bootcamp.com").first()
        if not tutor2:
            tutor2 = Usuario(
                email="tutor2@bootcamp.com",
                password_hash=hash_password("Tutor@1234"),
                rol=RolEnum.TUTOR,
                estado=EstadoUsuario.ACTIVO,
                activo=True,
                last_login=datetime.now(timezone.utc),
            )
            db.add(tutor2)

        db.flush()
        print("  ✅ Tutores: tutor1@bootcamp.com / tutor2@bootcamp.com (pwd: Tutor@1234)")

        # ── Cohorte ───────────────────────────────────────────────────────────
        inicio = date.today() - timedelta(days=60)
        cohorte = db.query(Cohorte).filter(Cohorte.nombre == "Full Stack Java 2024-I").first()
        if not cohorte:
            cohorte = Cohorte(
                nombre="Full Stack Java 2024-I",
                fecha_inicio=inicio,
                fecha_fin=fecha_fin_desde_inicio(inicio),
                estado=EstadoCohorte.ACTIVA,
                meta_contratacion=8,
                permitir_extension=False,
            )
            db.add(cohorte)
            db.flush()
            print(f"  ✅ Cohorte: {cohorte.nombre} (activa hasta {cohorte.fecha_fin})")

        # ── Aprendices con diferentes estados ─────────────────────────────────
        aprendices_data = [
            ("ana@gmail.com", tutor1, "Bogotá", True),     # activa, en proceso
            ("carlos@gmail.com", tutor1, "Medellín", True), # contratado
            ("sofia@gmail.com", tutor2, "Cali", True),      # con rechazos
            ("daniel@gmail.com", tutor2, "Bogotá", False),  # inactivo
            ("maria@gmail.com", tutor1, "Barranquilla", True),
        ]

        for email, tutor, ciudad, activo in aprendices_data:
            if db.query(Usuario).filter(Usuario.email == email).first():
                continue

            ap = Usuario(
                email=email,
                password_hash=hash_password("Aprend@1234"),
                rol=RolEnum.APRENDIZ,
                estado=EstadoUsuario.ACTIVO,
                activo=True,
                last_login=datetime.now(timezone.utc) - timedelta(days=(0 if activo else 20)),
            )
            db.add(ap)
            db.flush()

            perfil = AprendizPerfil(
                usuario_id=ap.id,
                cohorte_id=cohorte.id,
                tutor_id=tutor.id,
                ciudad=ciudad,
                telefono="3001234567",
            )
            db.add(perfil)
            db.flush()

            # Crear algunas aplicaciones y entrevistas por aprendiz
            empresas = [
                ("Bancolombia", "Backend Java"),
                ("Rappi", "Desarrollador Spring"),
                ("Platzi", "Full Stack Dev"),
            ]
            for empresa, vacante in empresas[:2]:
                app = Aplicacion(
                    usuario_id=ap.id,
                    empresa=empresa,
                    vacante=vacante,
                    modalidad=ModalidadApp.HIBRIDO,
                    origen=OrigenApp.PROPIA,
                )
                db.add(app)
                db.flush()

                # Agregar entrevistas según el aprendiz
                if email == "carlos@gmail.com":
                    for i in range(3):
                        e = Entrevista(
                            aplicacion_id=app.id,
                            tipo=TipoEntrevista.RRHH if i == 0 else TipoEntrevista.TECNICA,
                            modalidad=ModalidadEntrevista.VIRTUAL,
                            fecha=datetime.now(timezone.utc) - timedelta(days=i * 5),
                            grupal=False,
                            autoevaluacion=4,
                        )
                        db.add(e)
                    db.flush()
                    todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
                    aplicar_estado(app, todas)
                    app.estado = EstadoApp.CONTRATADO

                elif email == "ana@gmail.com":
                    e = Entrevista(
                        aplicacion_id=app.id,
                        tipo=TipoEntrevista.RRHH,
                        modalidad=ModalidadEntrevista.VIRTUAL,
                        fecha=datetime.now(timezone.utc) - timedelta(days=2),
                        grupal=False,
                        fallas=["COMUNICACION"],
                        autoevaluacion=3,
                    )
                    db.add(e)
                    e2 = Entrevista(
                        aplicacion_id=app.id,
                        tipo=TipoEntrevista.TECNICA,
                        modalidad=ModalidadEntrevista.VIRTUAL,
                        fecha=datetime.now(timezone.utc) - timedelta(days=1),
                        grupal=False,
                        fallas=["TECNICA"],
                        temas_tecnicos=["SPRING_BOOT"],
                        autoevaluacion=4,
                    )
                    db.add(e2)
                    db.flush()
                    todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
                    aplicar_estado(app, todas)

        db.commit()
        print("\n🎉 Seed completado exitosamente!")
        print("\n─── Credenciales de acceso ───────────────────────────────")
        print("Coordinador : coord@bootcamp.com    / Coord@1234")
        print("Tutor 1     : tutor1@bootcamp.com   / Tutor@1234")
        print("Tutor 2     : tutor2@bootcamp.com   / Tutor@1234")
        print("Aprendices  : ana@gmail.com          / Aprend@1234")
        print("              carlos@gmail.com        (CONTRATADO)")
        print("              sofia@gmail.com")
        print("──────────────────────────────────────────────────────────\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error en seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
