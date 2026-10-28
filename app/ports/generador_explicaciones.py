"""Puerto de salida: abstracción del generador de explicaciones académicas."""
from typing import Protocol


class GeneradorExplicaciones(Protocol):
    def generar(self, *, pregunta: str, asignatura: str) -> str:
        """Retorna una explicación pedagógica generada localmente."""
        ...
