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

    def obtener_respuesta(self, identificador: int) -> dict | None:
        with get_engine().connect() as conexion:
            fila = conexion.execute(
                text('''SELECT id, consulta_id, contenido, origen, creado_en
                        FROM respuestas WHERE consulta_id = :id
                        ORDER BY id DESC LIMIT 1'''),
                {'id': identificador},
            ).mappings().first()
            if fila is None:
                return None
            return {
                'id': fila['id'], 'consulta_id': fila['consulta_id'],
                'contenido': fila['contenido'], 'origen': fila['origen'],
                'estado': 'RESPONDIDA',
                'creado_en': fila['creado_en'].isoformat(),
            }

    def guardar_respuesta(self, identificador: int, contenido: str, origen: str) -> dict:
        """Guarda la explicación y actualiza el estado en una única transacción."""
        with get_engine().begin() as conexion:
            # Bloqueo por consulta para evitar dos respuestas simultáneas a un mismo ID.
            consulta = conexion.execute(
                text('SELECT id FROM consultas WHERE id = :id FOR UPDATE'),
                {'id': identificador},
            ).first()
            if consulta is None:
                raise ValueError('La consulta ya no existe.')
            previa = conexion.execute(
                text('''SELECT id, consulta_id, contenido, origen, creado_en
                        FROM respuestas WHERE consulta_id = :id
                        ORDER BY id DESC LIMIT 1'''),
                {'id': identificador},
            ).mappings().first()
            if previa is not None:
                return {
                    'id': previa['id'], 'consulta_id': previa['consulta_id'],
                    'contenido': previa['contenido'], 'origen': previa['origen'],
                    'estado': 'RESPONDIDA', 'creado_en': previa['creado_en'].isoformat(),
                }
            resultado = conexion.execute(
                text('''INSERT INTO respuestas(consulta_id, contenido, origen)
                        VALUES (:id, :contenido, :origen)'''),
                {'id': identificador, 'contenido': contenido, 'origen': origen},
            )
            conexion.execute(
                text("UPDATE consultas SET estado = 'RESPONDIDA' WHERE id = :id"),
                {'id': identificador},
            )
            return {
                'id': int(resultado.lastrowid), 'consulta_id': identificador,
                'contenido': contenido, 'origen': origen, 'estado': 'RESPONDIDA',
            }
