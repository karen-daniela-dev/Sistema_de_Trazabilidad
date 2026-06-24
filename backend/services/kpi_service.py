"""
Servicio de KPIs — calcula métricas por rol.
Las queries están optimizadas con índices en las tablas relevantes.
"""
from datetime import date
from uuid import UUID

from sqlalchemy import func, case, select
from sqlalchemy.orm import Session

from backend.models.aplicacion import Aplicacion
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.models.cohorte import Cohorte
from backend.models.entrevista import Entrevista
from backend.models.usuario import Usuario
from backend.models.enums import EstadoApp, RolEnum
from backend.services.alert_engine import semaforo_aprendiz, semaforo_cohorte, semaforo_actividad, semaforo_progreso


# ── KPIs personales (APRENDIZ) ────────────────────────────────────────────────

def kpis_personales(db: Session, usuario_id: UUID) -> dict:
    apps = db.query(Aplicacion).filter(Aplicacion.usuario_id == usuario_id).all()
    ids = [a.id for a in apps]
    entrevistas = (
        db.query(Entrevista).filter(Entrevista.aplicacion_id.in_(ids)).all()
        if ids else []
    )

    total_apps = len(apps)
    total_ent = len(entrevistas)
    contratado = any(a.estado == EstadoApp.CONTRATADO for a in apps)

    conversion = round(total_ent / total_apps, 2) if total_apps else 0.0

    fallas: dict[str, int] = {}
    for e in entrevistas:
        for f in (e.fallas or []):
            fallas[f] = fallas.get(f, 0) + 1

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first() #eliminar

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
        for p in db.query(AprendizPerfil).filter(AprendizPerfil.tutor_id == tutor_id).all()
    ]

    if not aprendices_ids:
        return {"total_aprendices": 0, "aprendices": [], "resumen": {}}

    result = []
    totales = {"GREEN": 0, "YELLOW": 0, "RED": 0, "contratados": 0}

    for uid in aprendices_ids:
        kpi = kpis_personales(db, uid)
        u = db.query(Usuario).filter(Usuario.id == uid).first()
        semaforo = kpi["semaforo"]
        totales[semaforo] = totales.get(semaforo, 0) + 1
        if kpi["contratado"]:
            totales["contratados"] += 1
        result.append({"usuario_id": str(uid), "email": u.email if u else "", **kpi})

    return {
        "total_aprendices": len(aprendices_ids),
        "aprendices": result,
        "resumen": totales,
    }


# ── KPIs globales (COORDINADOR) ───────────────────────────────────────────────

def kpis_globales(db: Session) -> dict:
    cohortes = db.query(Cohorte).all()
    total_aprendices = db.query(AprendizPerfil).count()
    total_apps = db.query(Aplicacion).count()
    total_ent = db.query(Entrevista).count()
    contratados = (
        db.query(Aplicacion).filter(Aplicacion.estado == EstadoApp.CONTRATADO).count()
    )

    tasa_global = round(contratados / total_aprendices, 4) if total_aprendices else 0.0

    cohortes_detalle = []
    for c in cohortes:
        aprendices_ids = [
            p.usuario_id
            for p in db.query(AprendizPerfil).filter(AprendizPerfil.cohorte_id == c.id).all()
        ]
        c_contratados = (
            db.query(Aplicacion)
            .filter(
                Aplicacion.usuario_id.in_(aprendices_ids),
                Aplicacion.estado == EstadoApp.CONTRATADO,
            )
            .count()
            if aprendices_ids else 0
        )
        cohortes_detalle.append({
            "id": str(c.id),
            "nombre": c.nombre,
            "estado": c.estado.value,
            "total_aprendices": len(aprendices_ids),
            "contratados": c_contratados,
            "meta": c.meta_contratacion,
            "pct_meta": round(c_contratados / c.meta_contratacion, 2) if c.meta_contratacion else 0,
            "semaforo": semaforo_cohorte(c, c_contratados),
        })

    # Ranking de tutores
    tutores = db.query(Usuario).filter(Usuario.rol == RolEnum.TUTOR).all()
    ranking = []
    for t in tutores:
        g = kpis_grupo(db, t.id)
        ranking.append({
            "tutor_id": str(t.id),
            "email": t.email,
            "total_aprendices": g["total_aprendices"],
            "contratados": g["resumen"].get("contratados", 0),
            "semaforo_verde": g["resumen"].get("GREEN", 0),
        })
    ranking.sort(key=lambda x: -x["contratados"])

    return {
        "total_aprendices": total_aprendices,
        "total_aplicaciones": total_apps,
        "total_entrevistas": total_ent,
        "contratados_total": contratados,
        "tasa_contratacion_global": tasa_global,
        "cohortes": cohortes_detalle,
        "ranking_tutores": ranking,
    }
