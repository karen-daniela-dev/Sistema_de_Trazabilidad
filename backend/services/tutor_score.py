from __future__ import annotations


def build_tutor_score(
    total_aprendices: int,
    total_aplicaciones: int,
    contratados: int,
) -> dict:
    """
    Calcula el score de desempeño de un tutor.

    Fórmula actual:

    - Contratados: 50%
    - Progreso: 30%
    - Actividad: 20%

    Centralizar este cálculo evita duplicación
    entre dashboards y facilita futuros cambios.
    """

    if total_aprendices <= 0:
        return {
            "actividad_verde": 0,
            "progreso_verde": 0,
            "score": 0.0,
        }

    apps_promedio = (
        total_aplicaciones / total_aprendices
    )

    actividad_verde = (
        round(total_aprendices * 0.8)
        if apps_promedio >= 5
        else round(total_aprendices * 0.4)
    )

    progreso_verde = contratados

    score = (
        (contratados / total_aprendices) * 50
        + (progreso_verde / total_aprendices) * 30
        + (actividad_verde / total_aprendices) * 20
    )

    return {
        "actividad_verde": actividad_verde,
        "progreso_verde": progreso_verde,
        "score": round(score, 2),
    }