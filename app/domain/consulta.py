from dataclasses import dataclass

@dataclass(frozen=True)
class Consulta:
    asignatura_id: int
    pregunta: str

    def validar(self):
        if self.asignatura_id < 1:
            raise ValueError("Selecciona una asignatura válida.")
        if not self.pregunta.strip():
            raise ValueError("La pregunta es obligatoria.")
        if len(self.pregunta.strip()) > 2000:
            raise ValueError("La pregunta no puede superar 2000 caracteres.")
