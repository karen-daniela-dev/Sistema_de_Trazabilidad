"""
constants/interview_catalog.py

Catálogo oficial de fallas y subfallas utilizadas
en las entrevistas de empleabilidad.

Este archivo representa la única fuente de verdad
para todo el sistema.

Es utilizado por:

- Backend (Dashboard Tutor)
- Backend (validaciones)
- Frontend Angular (mediante endpoint futuro)
"""

from __future__ import annotations

# =============================================================================
# FALLAS
# =============================================================================

FALLAS = {
    "TECNICA": "💻 Técnica",
    "COMUNICACION": "🗣️ Comunicación",
    "BLANDAS": "🤝 Habilidades blandas",
    "REGULACION_EMOCIONAL": "🧘 Regulación emocional",
}

# =============================================================================
# SUBFALLAS
# =============================================================================

SUBFALLAS = {

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

# =============================================================================
# MAPA INVERSO
# =============================================================================

SUBFALLA_TO_FALLA: dict[str, str] = {}

for falla, subfallas in SUBFALLAS.items():

    for subfalla in subfallas:

        SUBFALLA_TO_FALLA[subfalla] = falla
# =============================================================================
# TEMAS TÉCNICOS
# =============================================================================

TEMAS_TECNICOS = [
    "JAVA",
    "SPRING_BOOT",
    "APIS",
    "SQL",
    "ALGORITMOS",
    "OTRO",
]

def get_falla_from_subfalla(subfalla: str) -> str | None:
    """
    Retorna la categoría (falla) a la que pertenece
    una subfalla.

    Parameters
    ----------
    subfalla:
        Nombre de la subfalla.

    Returns
    -------
    str | None
        Clave de la falla o None si no existe.
    """
    return SUBFALLA_TO_FALLA.get(subfalla)