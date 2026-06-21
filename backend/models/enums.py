"""
Enums del dominio — fuente única de verdad.
Se importan en modelos y schemas.
"""
import enum


class RolEnum(str, enum.Enum):
    COORDINADOR = "COORDINADOR"
    TUTOR = "TUTOR"
    APRENDIZ = "APRENDIZ"


class EstadoUsuario(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


class EstadoCohorte(str, enum.Enum):
    ACTIVA = "ACTIVA"
    FINALIZADA = "FINALIZADA"
    INACTIVA = "INACTIVA"


class ModalidadApp(str, enum.Enum):
    HIBRIDO = "HIBRIDO"
    REMOTO = "REMOTO"
    PRESENCIAL = "PRESENCIAL"


class OrigenApp(str, enum.Enum):
    PROPIA = "PROPIA"
    TUTOR = "TUTOR"
    EMPLEABILIDAD = "EMPLEABILIDAD"


class EstadoApp(str, enum.Enum):
    APLICADO = "APLICADO"
    EN_ESPERA = "EN_ESPERA"
    AVANZANDO = "AVANZANDO"
    RECHAZADO = "RECHAZADO"
    CONTRATADO = "CONTRATADO"


class TipoEntrevista(str, enum.Enum):
    RRHH = "RRHH"
    TECNICA = "TECNICA"
    PRUEBA_TECNICA = "PRUEBA_TECNICA"


class ModalidadEntrevista(str, enum.Enum):
    VIRTUAL = "VIRTUAL"
    PRESENCIAL = "PRESENCIAL"


class PercepcionGrupal(str, enum.Enum):
    MEJOR = "MEJOR"
    IGUAL = "IGUAL"
    POR_MEJORAR = "POR_MEJORAR"


class FallaEnum(str, enum.Enum):
    TECNICA = "TECNICA"
    COMUNICACION = "COMUNICACION"
    BLANDAS = "BLANDAS"
    REGULACION_EMOCIONAL = "REGULACION_EMOCIONAL"


class SubfallaTecnica(str, enum.Enum):
    JAVA_BASICO = "JAVA_BASICO"
    SPRING_BOOT = "SPRING_BOOT"
    SQL_QUERIES = "SQL_QUERIES"
    ALGORITMOS = "ALGORITMOS"
    APIS_REST = "APIS_REST"
    ARQUITECTURA = "ARQUITECTURA"


class SubfallaComunicacion(str, enum.Enum):
    CLARIDAD = "CLARIDAD"
    ESCUCHA = "ESCUCHA"
    ARGUMENTACION = "ARGUMENTACION"


class SubfallaBlandas(str, enum.Enum):
    TRABAJO_EQUIPO = "TRABAJO_EQUIPO"
    PUNTUALIDAD = "PUNTUALIDAD"
    ACTITUD = "ACTITUD"


class SubfallaEmocional(str, enum.Enum):
    ANSIEDAD = "ANSIEDAD"
    BLOQUEO_MENTAL = "BLOQUEO_MENTAL"
    FRUSTACION = "FRUSTACION"


class TemaTecnico(str, enum.Enum):
    JAVA = "JAVA"
    SPRING_BOOT = "SPRING_BOOT"
    APIS = "APIS"
    SQL = "SQL"
    ALGORITMOS = "ALGORITMOS"
    OTRO = "OTRO"


class RespuestaEmpresa(str, enum.Enum):
    AVANZO = "AVANZO"
    RECHAZADO = "RECHAZADO"
    SIN_RESPUESTA = "SIN_RESPUESTA"


# Mapeo falla → subfallas permitidas (para validación)
SUBFALLAS_POR_FALLA: dict[FallaEnum, type[enum.Enum]] = {
    FallaEnum.TECNICA: SubfallaTecnica,
    FallaEnum.COMUNICACION: SubfallaComunicacion,
    FallaEnum.BLANDAS: SubfallaBlandas,
    FallaEnum.REGULACION_EMOCIONAL: SubfallaEmocional,
}
