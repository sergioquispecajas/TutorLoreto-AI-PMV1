"""Adaptador de persistencia: único módulo que usa consultas SQL reales."""
from sqlalchemy import text
from app.infrastructure.database import get_engine
from app.domain.consulta import Consulta


class MySQLConsultaRepository:
    def asignaturas(self) -> list[dict]:
        with get_engine().connect() as conexion:
            consulta = conexion.execute(text('SELECT id, nombre FROM asignaturas ORDER BY id'))
            return [dict(fila) for fila in consulta.mappings()]

    def registrar(self, consulta: Consulta) -> dict:
        # Usamos una transacción para no confirmar registros incompletos.
        with get_engine().begin() as conexion:
            encontrada = conexion.execute(
                text('SELECT id FROM asignaturas WHERE id = :id'),
                {'id': consulta.asignatura_id},
            ).first()
            if encontrada is None:
                raise ValueError('La asignatura indicada no existe.')
            resultado = conexion.execute(
                text("""INSERT INTO consultas(asignatura_id, pregunta, estado)
                        VALUES (:asignatura_id, :pregunta, 'PENDIENTE')"""),
                {'asignatura_id': consulta.asignatura_id, 'pregunta': consulta.pregunta},
            )
            return {
                'id': int(resultado.lastrowid),
                'asignatura_id': consulta.asignatura_id,
                'pregunta': consulta.pregunta,
                'estado': 'PENDIENTE',
            }

    def obtener(self, identificador: int) -> dict | None:
        with get_engine().connect() as conexion:
            fila = conexion.execute(
                text('SELECT id, asignatura_id, pregunta, estado, creado_en FROM consultas WHERE id = :id'),
                {'id': identificador},
            ).mappings().first()
            if fila is None:
                return None
            return {**dict(fila), 'creado_en': fila['creado_en'].isoformat()}
