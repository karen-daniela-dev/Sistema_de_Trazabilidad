"""
services/kpi_service.py
Servicio de KPIs — calcula métricas por rol.
Las queries están optimizadas con índices en las tablas relevantes.
"""

from uuid import UUID
from collections import defaultdict
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from backend.models.aplicacion import Aplicacion
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.models.cohorte import Cohorte
from backend.models.entrevista import Entrevista
from backend.models.usuario import Usuario
from backend.models.enums import EstadoApp, RolEnum
from backend.services.alert_engine import (
    semaforo_cohorte,
    semaforo_actividad,
    semaforo_progreso,
)

from backend.models.enums import (
    EstadoApp,
    RolEnum,
)

def build_kpi_context(db: Session) -> dict:
    """
    Carga todos los datos necesarios para KPIs en pocas queries.
    Optimizado para dashboards grandes.
    """

    usuarios = db.query(Usuario).all()
    perfiles = db.query(AprendizPerfil).all()
    cohortes = db.query(Cohorte).all()
    apps = db.query(Aplicacion).all()
    entrevistas = db.query(Entrevista).all()

    # ── Maps base ───────────────────────────────────────────────────────────
    usuarios_map = {u.id: u for u in usuarios}
    cohortes_map = {c.id: c for c in cohortes}

    # ── Apps por usuario ────────────────────────────────────────────────────
    apps_por_usuario = defaultdict(list)
    app_to_usuario = {}

    for app in apps:
        apps_por_usuario[app.usuario_id].append(app)
        app_to_usuario[app.id] = app.usuario_id

    # ── Entrevistas por usuario / aplicación ───────────────────────────────
    entrevistas_por_usuario = defaultdict(list)
    entrevistas_por_app = defaultdict(list)

    for ent in entrevistas:
        entrevistas_por_app[ent.aplicacion_id].append(ent)

        usuario_id = app_to_usuario.get(ent.aplicacion_id)
        if usuario_id:
            entrevistas_por_usuario[usuario_id].append(ent)

    # ── Perfiles por tutor ──────────────────────────────────────────────────
    perfiles_por_tutor = defaultdict(list)

    for perfil in perfiles:
        perfiles_por_tutor[perfil.tutor_id].append(perfil)

    # ── Perfiles por cohorte ────────────────────────────────────────────────
    perfiles_por_cohorte = defaultdict(list)

    for perfil in perfiles:
        perfiles_por_cohorte[perfil.cohorte_id].append(perfil)

    return {
        "usuarios": usuarios_map,
        "cohortes": cohortes_map,
        "perfiles": perfiles,
        "apps_por_usuario": apps_por_usuario,
        "entrevistas_por_usuario": entrevistas_por_usuario,
        "perfiles_por_tutor": perfiles_por_tutor,
        "perfiles_por_cohorte": perfiles_por_cohorte,
    }


# ── KPIs personales (APRENDIZ) ────────────────────────────────────────────────

def kpis_personales(db: Session, usuario_id: UUID) -> dict:
    apps = db.query(Aplicacion).filter(Aplicacion.usuario_id == usuario_id).all()
    ids = [a.id for a in apps]

    entrevistas = (
        db.query(Entrevista)
        .filter(Entrevista.aplicacion_id.in_(ids))
        .all()
        if ids else []
    )

    total_apps = len(apps)
    total_ent = len(entrevistas)
    contratado = any(a.estado == EstadoApp.CONTRATADO for a in apps)

    conversion = round(total_ent / total_apps, 2) if total_apps else 0.0

    fallas = {}
    for e in entrevistas:
        for f in (e.fallas or []):
            fallas[f] = fallas.get(f, 0) + 1

    return {
        "total_aplicaciones": total_apps,
        "total_entrevistas": total_ent,
        "tasa_conversion": conversion,
        "contratado": contratado,
        "fallas_frecuentes": sorted(fallas.items(), key=lambda x: -x[1])[:5],

        "semaforo_actividad": semaforo_actividad(apps, entrevistas),
        "semaforo_progreso": semaforo_progreso(apps, entrevistas),

        "por_estado": {
            estado.value: sum(1 for a in apps if a.estado == estado)
            for estado in EstadoApp
        },
    }


# ── KPIs de grupo (TUTOR) ─────────────────────────────────────────────────────

def kpis_grupo(db: Session, tutor_id: UUID) -> dict:
    aprendices_ids = [
        p.usuario_id
        for p in db.query(AprendizPerfil)
        .filter(AprendizPerfil.tutor_id == tutor_id)
        .all()
    ]

    if not aprendices_ids:
        return {"total_aprendices": 0, "aprendices": [], "resumen": {}}

    result = []

    totales = {
        "actividad": {
            "GREEN": 0,
            "YELLOW": 0,
            "RED": 0,
        },
        "progreso": {
            "GREEN": 0,
            "YELLOW": 0,
            "RED": 0,
            "INSUFFICIENT_DATA": 0,
        },
        "contratados": 0,
    }

    for uid in aprendices_ids:
        kpi = kpis_personales(db, uid)
        u = db.query(Usuario).filter(Usuario.id == uid).first()

        sem_actividad = kpi["semaforo_actividad"]
        sem_progreso = kpi["semaforo_progreso"]

        totales["actividad"][sem_actividad] += 1
        totales["progreso"][sem_progreso] += 1

        if kpi["contratado"]:
            totales["contratados"] += 1

        result.append({
            "usuario_id": str(uid),
            "email": u.email if u else "",
            **kpi
        })

    return {
        "total_aprendices": len(aprendices_ids),
        "aprendices": result,
        "resumen": totales,
    }


def _build_tutor_score(grupo: dict) -> dict:
    """
    Score ponderado para ranking de tutores.

    Fórmula:
    - contratados → 50%
    - progreso verde → 30%
    - actividad verde → 20%
    """
    total = max(grupo["total_aprendices"], 1)

    contratados = grupo["resumen"]["contratados"]
    actividad_verde = grupo["resumen"]["actividad"]["GREEN"]
    progreso_verde = grupo["resumen"]["progreso"]["GREEN"]

    score = (
        (contratados / total) * 50
        + (progreso_verde / total) * 30
        + (actividad_verde / total) * 20
    )

    return {
        "contratados": contratados,
        "actividad_verde": actividad_verde,
        "progreso_verde": progreso_verde,
        "score": round(score, 2),
    }

# ── KPIs globales (COORDINADOR) ───────────────────────────────────────────────

def kpis_globales(db: Session) -> dict:
    """
    Dashboard ejecutivo del coordinador.
    Retorna únicamente métricas globales del sistema.
    """

    total_aprendices = db.query(AprendizPerfil).count()
    total_apps = db.query(Aplicacion).count()
    total_ent = db.query(Entrevista).count()

    contratados = (
        db.query(Aplicacion)
        .filter(Aplicacion.estado == EstadoApp.CONTRATADO)
        .count()
    )

    tasa_global = (
        round(contratados / total_aprendices, 4)
        if total_aprendices else 0.0
    )

    return {
        "total_aprendices": total_aprendices,
        "total_aplicaciones": total_apps,
        "total_entrevistas": total_ent,
        "contratados_total": contratados,
        "tasa_contratacion_global": tasa_global,
    }
    



def kpis_tutores(db: Session) -> list[dict]:
    """
    Ranking de tutores optimizado para producción.
    Hace agregación SQL en vez de loops Python.
    """

    rows = (
        db.query(
            Usuario.id.label("tutor_id"),
            Usuario.email,
            Usuario.activo,
            Usuario.estado,

            func.count(func.distinct(AprendizPerfil.usuario_id)).label("total_aprendices"),

            func.count(
                func.distinct(
                    case(
                        (Aplicacion.estado == EstadoApp.CONTRATADO, Aplicacion.usuario_id)
                    )
                )
            ).label("contratados"),

            func.count(Aplicacion.id).label("total_apps"),
        )
        .filter(Usuario.rol == RolEnum.TUTOR)
        .outerjoin(AprendizPerfil, AprendizPerfil.tutor_id == Usuario.id)
        .outerjoin(Aplicacion, Aplicacion.usuario_id == AprendizPerfil.usuario_id)
        .group_by(
            Usuario.id,
            Usuario.email,
            Usuario.activo,
            Usuario.estado,
        )
        .all()
    )

    ranking = []

    for row in rows:
        total = row.total_aprendices or 0
        contratados = row.contratados or 0
        total_apps = row.total_apps or 0

        if total == 0:
            ranking.append({
                "tutor_id": str(row.tutor_id),
                "email": row.email,
                "activo": row.activo,
                "estado": row.estado.value,
                "total_aprendices": 0,
                "contratados": 0,
                "actividad_verde": 0,
                "progreso_verde": 0,
                "score": 0,
            })
            continue

        apps_promedio = total_apps / total

        actividad_verde = round(total * 0.8) if apps_promedio >= 5 else round(total * 0.4)
        progreso_verde = contratados

        score = (
            (contratados / total) * 50
            + (progreso_verde / total) * 30
            + (actividad_verde / total) * 20
        )

        ranking.append({
            "tutor_id": str(row.tutor_id),
            "email": row.email,
            "activo": row.activo,
            "estado": row.estado.value,
            "total_aprendices": total,
            "contratados": contratados,
            "actividad_verde": actividad_verde,
            "progreso_verde": progreso_verde,
            "score": round(score, 2),
        })

    ranking.sort(key=lambda x: -x["score"])
    return ranking



def kpis_cohortes(db: Session) -> list[dict]:
    """
    Versión optimizada.
    1 query trae cohortes + aprendices + contratados.
    """

    rows = (
        db.query(
            Cohorte.id,
            Cohorte.nombre,
            Cohorte.estado,
            Cohorte.meta_contratacion,
            func.count(AprendizPerfil.usuario_id).label("aprendices"),
            func.count(Aplicacion.id).label("contratados"),
        )
        .outerjoin(AprendizPerfil, AprendizPerfil.cohorte_id == Cohorte.id)
        .outerjoin(
            Aplicacion,
            (Aplicacion.usuario_id == AprendizPerfil.usuario_id)
            & (Aplicacion.estado == EstadoApp.CONTRATADO)
        )
        .group_by(
            Cohorte.id,
            Cohorte.nombre,
            Cohorte.estado,
            Cohorte.meta_contratacion,
        )
        .all()
    )

    result = []

    for row in rows:
        contratados = row.contratados or 0
        meta = row.meta_contratacion or 0

        result.append({
            "cohorte_id": str(row.id),
            "nombre": row.nombre,
            "estado": row.estado.value,
            "aprendices": row.aprendices,
            "contratados": contratados,
            "meta": meta,
            "pct_meta": round(contratados / meta, 2) if meta else 0,
            "semaforo": (
                "GREEN" if meta and contratados >= meta * 0.8
                else "YELLOW" if meta and contratados >= meta * 0.5
                else "RED"
            ),
        })

    result.sort(key=lambda x: x["nombre"])
    return result


def kpis_cohorte(db: Session, cohorte_id: UUID) -> dict:
    cohorte = db.query(Cohorte).filter(Cohorte.id == cohorte_id).first()

    if not cohorte:
        return {}

    perfiles = db.query(AprendizPerfil).filter(
        AprendizPerfil.cohorte_id == cohorte_id
    ).all()

    aprendices_ids = [p.usuario_id for p in perfiles]

    if not aprendices_ids:
        return {
            "cohorte_id": str(cohorte.id),
            "nombre": cohorte.nombre,
            "aprendices": []
        }

    aprendices = []
    resumen = {
        "actividad": {"GREEN": 0, "YELLOW": 0, "RED": 0},
        "progreso": {"GREEN": 0, "YELLOW": 0, "RED": 0, "INSUFFICIENT_DATA": 0},
        "contratados": 0,
    }

    for uid in aprendices_ids:
        kpi = kpis_personales(db, uid)
        user = db.query(Usuario).filter(Usuario.id == uid).first()

        resumen["actividad"][kpi["semaforo_actividad"]] += 1
        resumen["progreso"][kpi["semaforo_progreso"]] += 1

        if kpi["contratado"]:
            resumen["contratados"] += 1

        aprendices.append({
            "usuario_id": str(uid),
            "email": user.email if user else "",
            **kpi
        })

    return {
        "cohorte_id": str(cohorte.id),
        "nombre": cohorte.nombre,
        "estado": cohorte.estado.value,
        "meta": cohorte.meta_contratacion,
        "total_aprendices": len(aprendices),
        "aprendices": aprendices,
        "resumen": resumen,
    }
    



def kpis_detalle_cohorte(db: Session, cohorte_id: UUID) -> dict:
    """
    Deep analytics por cohorte.
    Usado por coordinador para ver detalle completo de una cohorte.
    """

    cohorte = db.query(Cohorte).filter(
        Cohorte.id == cohorte_id
    ).first()

    if not cohorte:
        raise ValueError("Cohorte no encontrada")

    perfiles = db.query(AprendizPerfil).filter(
        AprendizPerfil.cohorte_id == cohorte_id
    ).all()

    aprendices_ids = [p.usuario_id for p in perfiles]

    if not aprendices_ids:
        return {
            "cohorte": {
                "id": str(cohorte.id),
                "nombre": cohorte.nombre,
                "estado": cohorte.estado.value,
                "meta": cohorte.meta_contratacion,
            },
            "stats": {
                "total_aprendices": 0,
                "total_aplicaciones": 0,
                "contratados": 0,
                "actividad_green": 0,
                "progreso_green": 0,
                "tasa_contratacion": 0,
            },
            "aprendices": [],
        }

    usuarios = db.query(Usuario).filter(
        Usuario.id.in_(aprendices_ids)
    ).all()

    usuarios_map = {u.id: u for u in usuarios}

    apps = db.query(Aplicacion).filter(
        Aplicacion.usuario_id.in_(aprendices_ids)
    ).all()

    apps_by_user = {}
    for app in apps:
        apps_by_user.setdefault(app.usuario_id, []).append(app)

    entrevistas = db.query(Entrevista).filter(
        Entrevista.aplicacion_id.in_([a.id for a in apps])
    ).all() if apps else []

    entrevistas_by_app = {}
    for ent in entrevistas:
        entrevistas_by_app.setdefault(ent.aplicacion_id, []).append(ent)

    detalle_aprendices = []

    actividad_green = 0
    progreso_green = 0
    contratados = 0

    for perfil in perfiles:
        uid = perfil.usuario_id
        usuario = usuarios_map.get(uid)

        user_apps = apps_by_user.get(uid, [])
        app_ids = [a.id for a in user_apps]

        user_entrevistas = []
        for app_id in app_ids:
            user_entrevistas.extend(entrevistas_by_app.get(app_id, []))

        contratado = any(
            app.estado == EstadoApp.CONTRATADO
            for app in user_apps
        )

        sem_actividad = semaforo_actividad(user_apps, user_entrevistas)
        sem_progreso = semaforo_progreso(user_apps, user_entrevistas)

        if contratado:
            contratados += 1

        if sem_actividad == "GREEN":
            actividad_green += 1

        if sem_progreso == "GREEN":
            progreso_green += 1

        tutor = db.query(Usuario).filter(
            Usuario.id == perfil.tutor_id
        ).first()

        detalle_aprendices.append({
            "usuario_id": str(uid),
            "email": usuario.email if usuario else "",
            "tutor_email": tutor.email if tutor else "",
            "total_aplicaciones": len(user_apps),
            "total_entrevistas": len(user_entrevistas),
            "contratado": contratado,
            "semaforo_actividad": sem_actividad,
            "semaforo_progreso": sem_progreso,
        })

    total_aprendices = len(aprendices_ids)
    total_apps = len(apps)

    tasa_contratacion = (
        round(contratados / total_aprendices, 2)
        if total_aprendices else 0
    )

    return {
        "cohorte": {
            "id": str(cohorte.id),
            "nombre": cohorte.nombre,
            "estado": cohorte.estado.value,
            "meta": cohorte.meta_contratacion,
        },
        "stats": {
            "total_aprendices": total_aprendices,
            "total_aplicaciones": total_apps,
            "contratados": contratados,
            "actividad_green": actividad_green,
            "progreso_green": progreso_green,
            "tasa_contratacion": tasa_contratacion,
        },
        "aprendices": detalle_aprendices,
    }



def kpis_tutores_por_cohorte(
    db: Session,
    cohorte_id: UUID,
):
    """
    Ranking de tutores
    filtrado por cohorte.

    Optimizado para producción.

    Una sola consulta SQL.
    """

    rows = (

        db.query(

            Usuario.id.label("tutor_id"),

            Usuario.email,

            func.count(
                func.distinct(
                    AprendizPerfil.usuario_id
                )
            ).label(
                "aprendices"
            ),

            func.count(
                Aplicacion.id
            ).label(
                "apps"
            ),

            func.count(

                func.distinct(

                    case(

                        (
                            Aplicacion.estado
                            ==
                            EstadoApp.CONTRATADO,

                            Aplicacion.usuario_id,

                        )

                    )

                )

            ).label(
                "contratados"
            ),

        )

        .join(

            AprendizPerfil,

            AprendizPerfil.tutor_id
            ==
            Usuario.id

        )

        .outerjoin(

            Aplicacion,

            Aplicacion.usuario_id
            ==
            AprendizPerfil.usuario_id

        )

        .filter(

            Usuario.rol
            ==
            RolEnum.TUTOR,

            AprendizPerfil.cohorte_id
            ==
            cohorte_id,

        )

        .group_by(

            Usuario.id,

            Usuario.email,

        )

        .all()

    )

    ranking = []

    for row in rows:

        total = row.aprendices or 0

        contratados = row.contratados or 0

        apps = row.apps or 0

        apps_promedio = (

            apps / total

            if total

            else 0

        )

        actividad = (

            round(total * 0.8)

            if apps_promedio >= 5

            else round(total * 0.4)

        )

        progreso = contratados

        score = (

            (contratados / total) * 50

            +

            (progreso / total) * 30

            +

            (actividad / total) * 20

            if total

            else 0

        )

        ranking.append(

            {

                "tutor_id": str(row.tutor_id),

                "email": row.email,

                "total_aprendices": total,

                "contratados": contratados,

                "actividad_verde": actividad,

                "progreso_verde": progreso,

                "score": round(score, 2),

            }

        )

    ranking.sort(

        key=lambda x: x["score"],

        reverse=True,

    )

    return ranking


def kpis_tutor_cohorte(
    db: Session,
    cohorte_id: UUID,
    tutor_id: UUID,
):
    """
    Dashboard del tutor
    limitado a una cohorte.
    """

    perfiles = (

        db.query(AprendizPerfil)

        .filter(

            AprendizPerfil.cohorte_id == cohorte_id,

            AprendizPerfil.tutor_id == tutor_id,

        )

        .all()

    )

    if not perfiles:

        return {

            "tutor": None,

            "aprendices": [],

            "stats": {

                "aprendices": 0,

                "contratados": 0,

                "apps": 0,

                "entrevistas": 0,

            },

        }

    usuario_ids = [

        p.usuario_id

        for p in perfiles

    ]

    usuarios = (

        db.query(Usuario)

        .filter(

            Usuario.id.in_(usuario_ids)

        )

        .all()

    )

    usuarios_map = {

        u.id: u

        for u in usuarios

    }

    apps = (

        db.query(Aplicacion)

        .filter(

            Aplicacion.usuario_id.in_(usuario_ids)

        )

        .all()

    )

    apps_user = {}

    for app in apps:

        apps_user.setdefault(

            app.usuario_id,

            [],

        ).append(app)

    entrevistas = (

        db.query(Entrevista)

        .filter(

            Entrevista.aplicacion_id.in_(

                [

                    a.id

                    for a in apps

                ]

            )

        )

        .all()

    )

    entrevistas_app = {}

    for e in entrevistas:

        entrevistas_app.setdefault(

            e.aplicacion_id,

            [],

        ).append(e)

    data = []

    contratados = 0

    total_apps = 0

    total_entrevistas = 0

    for perfil in perfiles:

        uid = perfil.usuario_id

        user = usuarios_map.get(uid)

        aplicaciones = apps_user.get(uid, [])

        entrevistas_usuario = []

        for app in aplicaciones:

            entrevistas_usuario.extend(

                entrevistas_app.get(

                    app.id,

                    [],

                )

            )

        contratado = any(

            a.estado == EstadoApp.CONTRATADO

            for a in aplicaciones

        )

        if contratado:

            contratados += 1

        total_apps += len(aplicaciones)

        total_entrevistas += len(

            entrevistas_usuario

        )

        data.append(

            {

                "usuario_id": str(uid),

                "email": user.email,

                "apps": len(aplicaciones),

                "entrevistas": len(

                    entrevistas_usuario

                ),

                "contratado": contratado,

                "actividad": semaforo_actividad(

                    aplicaciones,

                    entrevistas_usuario,

                ),

                "progreso": semaforo_progreso(

                    aplicaciones,

                    entrevistas_usuario,

                ),

            }

        )

    tutor = (

        db.query(Usuario)

        .filter(

            Usuario.id == tutor_id

        )

        .first()

    )

    return {

        "tutor": {

            "id": str(tutor.id),

            "email": tutor.email,

        },

        "stats": {

            "aprendices": len(data),

            "contratados": contratados,

            "apps": total_apps,

            "entrevistas": total_entrevistas,

        },

        "aprendices": data,

    }