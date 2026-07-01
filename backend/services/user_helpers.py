"""
Helpers relacionados con usuarios.

Centraliza lógica reutilizable que no pertenece
a un dashboard específico.
"""

from backend.models.usuario import Usuario


def display_name(obj) -> str:
    """
    Nombre mostrado en la interfaz.

    Temporalmente utiliza el email.

    Cuando el modelo Usuario implemente
    nombres y apellidos, únicamente será
    necesario modificar este helper.
    """

    return obj.email.split("@")[0]