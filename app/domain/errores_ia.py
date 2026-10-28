"""Errores del módulo local de generación de explicaciones."""


class IANoDisponible(Exception):
    """El servicio o modelo local no está disponible."""


class IATiempoAgotado(Exception):
    """El servicio local tardó demasiado en responder."""


class IARespuestaInvalida(Exception):
    """El servicio devolvió una respuesta vacía o incorrecta."""


class ConsultaNoEncontrada(Exception):
    """No se encontró la consulta a explicar."""
