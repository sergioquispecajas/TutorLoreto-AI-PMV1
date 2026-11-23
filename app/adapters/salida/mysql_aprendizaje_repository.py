"""Adaptador MySQL para las funciones de aprendizaje del PMV2 y PMV3."""
import json
from sqlalchemy import text

from app.infrastructure.database import get_engine


def _fecha(valor):
    return valor.isoformat() if hasattr(valor, "isoformat") else valor


def _opciones(valor):
    if isinstance(valor, dict):
        return valor
    if isinstance(valor, str):
        try:
            return json.loads(valor)
        except json.JSONDecodeError:
            return {}
    return {}


class MySQLAprendizajeRepository:
    def guardar_perfil(self, identificador: str, grado: int, nivel_academico: str) -> dict:
        with get_engine().begin() as conexion:
            conexion.execute(text("""
                INSERT INTO perfiles_estudiante (identificador, grado, nivel_academico)
                VALUES (:identificador, :grado, :nivel)
                ON DUPLICATE KEY UPDATE
                    grado = VALUES(grado),
                    nivel_academico = VALUES(nivel_academico),
                    actualizado_en = CURRENT_TIMESTAMP
            """), {"identificador": identificador, "grado": grado, "nivel": nivel_academico})
        return self.obtener_perfil(identificador)

    def obtener_perfil(self, identificador: str) -> dict | None:
        with get_engine().connect() as conexion:
            fila = conexion.execute(text("""
                SELECT id, identificador, grado, nivel_academico, creado_en, actualizado_en
                FROM perfiles_estudiante WHERE identificador = :identificador
            """), {"identificador": identificador}).mappings().first()
        if fila is None:
            return None
        return {
            "id": int(fila["id"]),
            "identificador": fila["identificador"],
            "grado": int(fila["grado"]),
            "nivel_academico": fila["nivel_academico"],
            "creado_en": _fecha(fila["creado_en"]),
            "actualizado_en": _fecha(fila["actualizado_en"]),
        }

    def obtener_asignatura(self, asignatura_id: int) -> dict | None:
        with get_engine().connect() as conexion:
            fila = conexion.execute(text("""
                SELECT id, nombre FROM asignaturas WHERE id = :id
            """), {"id": asignatura_id}).mappings().first()
        return dict(fila) if fila else None

    def crear_practica(self, identificador: str, asignatura_id: int, tema: str,
                       dificultad: str, ejercicios: list[dict], origen: str) -> dict:
        with get_engine().begin() as conexion:
            perfil = conexion.execute(text("""
                SELECT id FROM perfiles_estudiante WHERE identificador = :identificador
            """), {"identificador": identificador}).first()
            if perfil is None:
                raise ValueError("Registra tu perfil antes de crear una práctica.")

            asignatura = conexion.execute(text("""
                SELECT id FROM asignaturas WHERE id = :id
            """), {"id": asignatura_id}).first()
            if asignatura is None:
                raise ValueError("La asignatura seleccionada no existe.")

            sesion = conexion.execute(text("""
                INSERT INTO sesiones_practica
                    (estudiante_id, asignatura_id, tema, dificultad, origen,
                     total_ejercicios, estado)
                VALUES
                    (:estudiante_id, :asignatura_id, :tema, :dificultad, :origen,
                     :total, 'PENDIENTE')
            """), {
                "estudiante_id": int(perfil[0]),
                "asignatura_id": asignatura_id,
                "tema": tema,
                "dificultad": dificultad,
                "origen": origen,
                "total": len(ejercicios),
            })
            practica_id = int(sesion.lastrowid)

            for indice, ejercicio in enumerate(ejercicios, start=1):
                conexion.execute(text("""
                    INSERT INTO ejercicios_practica
                        (sesion_id, numero, enunciado, opciones_json,
                         respuesta_correcta, explicacion)
                    VALUES
                        (:sesion_id, :numero, :enunciado, :opciones,
                         :correcta, :explicacion)
                """), {
                    "sesion_id": practica_id,
                    "numero": indice,
                    "enunciado": ejercicio["enunciado"],
                    "opciones": json.dumps(ejercicio["opciones"], ensure_ascii=False),
                    "correcta": ejercicio["respuesta_correcta"],
                    "explicacion": ejercicio["explicacion"],
                })

        return self.obtener_practica(practica_id, identificador)

    def obtener_practica(self, practica_id: int, identificador: str) -> dict | None:
        with get_engine().connect() as conexion:
            sesion = conexion.execute(text("""
                SELECT s.id, s.tema, s.dificultad, s.origen, s.estado,
                       s.total_ejercicios, s.aciertos, s.creado_en, s.finalizada_en,
                       a.nombre AS asignatura
                FROM sesiones_practica s
                JOIN perfiles_estudiante p ON p.id = s.estudiante_id
                JOIN asignaturas a ON a.id = s.asignatura_id
                WHERE s.id = :id AND p.identificador = :identificador
            """), {"id": practica_id, "identificador": identificador}).mappings().first()
            if sesion is None:
                return None

            filas = conexion.execute(text("""
                SELECT e.id, e.numero, e.enunciado, e.opciones_json,
                       e.respuesta_correcta, e.explicacion,
                       r.respuesta, r.es_correcta
                FROM ejercicios_practica e
                LEFT JOIN respuestas_practica r
                    ON r.sesion_id = e.sesion_id AND r.ejercicio_id = e.id
                WHERE e.sesion_id = :sesion_id
                ORDER BY e.numero
            """), {"sesion_id": practica_id}).mappings().all()

        completada = sesion["estado"] == "COMPLETADA"
        ejercicios = []
        for fila in filas:
            item = {
                "id": int(fila["id"]),
                "numero": int(fila["numero"]),
                "enunciado": fila["enunciado"],
                "opciones": _opciones(fila["opciones_json"]),
            }
            if completada:
                item.update({
                    "respuesta_correcta": fila["respuesta_correcta"],
                    "explicacion": fila["explicacion"],
                    "respuesta": fila["respuesta"],
                    "es_correcta": bool(fila["es_correcta"]),
                })
            ejercicios.append(item)

        total = int(sesion["total_ejercicios"])
        aciertos = int(sesion["aciertos"] or 0)
        return {
            "id": int(sesion["id"]),
            "asignatura": sesion["asignatura"],
            "tema": sesion["tema"],
            "dificultad": sesion["dificultad"],
            "origen": sesion["origen"],
            "estado": sesion["estado"],
            "total_ejercicios": total,
            "aciertos": aciertos,
            "porcentaje_aciertos": round(aciertos * 100 / total, 1) if total else 0,
            "creado_en": _fecha(sesion["creado_en"]),
            "finalizada_en": _fecha(sesion["finalizada_en"]),
            "ejercicios": ejercicios,
        }

    def evaluar_practica(self, practica_id: int, identificador: str,
                         respuestas: list[dict], duracion_segundos: int) -> dict | None:
        with get_engine().begin() as conexion:
            sesion = conexion.execute(text("""
                SELECT s.id, s.estado
                FROM sesiones_practica s
                JOIN perfiles_estudiante p ON p.id = s.estudiante_id
                WHERE s.id = :id AND p.identificador = :identificador
                FOR UPDATE
            """), {"id": practica_id, "identificador": identificador}).mappings().first()
            if sesion is None:
                return None

            if sesion["estado"] == "COMPLETADA":
                # Reenvíos de red son idempotentes: no duplican respuestas.
                pass
            else:
                ejercicios = conexion.execute(text("""
                    SELECT id, respuesta_correcta
                    FROM ejercicios_practica
                    WHERE sesion_id = :id ORDER BY numero
                    FOR UPDATE
                """), {"id": practica_id}).mappings().all()

                esperados = {int(e["id"]): e["respuesta_correcta"] for e in ejercicios}
                recibidos = {}
                for item in respuestas:
                    ejercicio_id = int(item["ejercicio_id"])
                    if ejercicio_id in recibidos:
                        raise ValueError("No envíes dos respuestas para el mismo ejercicio.")
                    recibidos[ejercicio_id] = str(item["respuesta"]).strip().upper()

                if set(recibidos) != set(esperados):
                    raise ValueError("Responde todos los ejercicios antes de finalizar.")
                if any(valor not in {"A", "B", "C", "D"} for valor in recibidos.values()):
                    raise ValueError("Selecciona una alternativa válida en cada ejercicio.")

                aciertos = 0
                for ejercicio_id, correcta in esperados.items():
                    seleccion = recibidos[ejercicio_id]
                    es_correcta = int(seleccion == correcta)
                    aciertos += es_correcta
                    conexion.execute(text("""
                        INSERT INTO respuestas_practica
                            (sesion_id, ejercicio_id, respuesta, es_correcta)
                        VALUES (:sesion_id, :ejercicio_id, :respuesta, :es_correcta)
                    """), {
                        "sesion_id": practica_id,
                        "ejercicio_id": ejercicio_id,
                        "respuesta": seleccion,
                        "es_correcta": es_correcta,
                    })

                conexion.execute(text("""
                    UPDATE sesiones_practica
                    SET estado = 'COMPLETADA',
                        aciertos = :aciertos,
                        duracion_segundos = :duracion,
                        finalizada_en = CURRENT_TIMESTAMP
                    WHERE id = :id
                """), {
                    "aciertos": aciertos,
                    "duracion": duracion_segundos,
                    "id": practica_id,
                })

        return self.obtener_practica(practica_id, identificador)

    def historial(self, identificador: str, limite: int = 50) -> list[dict]:
        with get_engine().connect() as conexion:
            filas = conexion.execute(text("""
                SELECT s.id, a.nombre AS asignatura, s.tema, s.dificultad,
                       s.estado, s.total_ejercicios, s.aciertos,
                       s.creado_en, s.finalizada_en
                FROM sesiones_practica s
                JOIN perfiles_estudiante p ON p.id = s.estudiante_id
                JOIN asignaturas a ON a.id = s.asignatura_id
                WHERE p.identificador = :identificador
                ORDER BY s.creado_en DESC
                LIMIT :limite
            """), {"identificador": identificador, "limite": limite}).mappings().all()

        resultado = []
        for fila in filas:
            total = int(fila["total_ejercicios"])
            aciertos = int(fila["aciertos"] or 0)
            resultado.append({
                "id": int(fila["id"]),
                "asignatura": fila["asignatura"],
                "tema": fila["tema"],
                "dificultad": fila["dificultad"],
                "estado": fila["estado"],
                "total_ejercicios": total,
                "aciertos": aciertos,
                "porcentaje_aciertos": round(aciertos * 100 / total, 1) if total and fila["estado"] == "COMPLETADA" else None,
                "creado_en": _fecha(fila["creado_en"]),
                "finalizada_en": _fecha(fila["finalizada_en"]),
            })
        return resultado

    def progreso(self, identificador: str) -> dict:
        with get_engine().connect() as conexion:
            filas = conexion.execute(text("""
                SELECT a.nombre AS asignatura, s.tema,
                       COUNT(DISTINCT s.id) AS sesiones,
                       COUNT(r.id) AS respuestas,
                       COALESCE(SUM(r.es_correcta), 0) AS aciertos,
                       MAX(s.finalizada_en) AS ultima_practica
                FROM sesiones_practica s
                JOIN perfiles_estudiante p ON p.id = s.estudiante_id
                JOIN asignaturas a ON a.id = s.asignatura_id
                JOIN ejercicios_practica e ON e.sesion_id = s.id
                LEFT JOIN respuestas_practica r
                    ON r.sesion_id = s.id AND r.ejercicio_id = e.id
                WHERE p.identificador = :identificador
                  AND s.estado = 'COMPLETADA'
                GROUP BY a.nombre, s.tema
                ORDER BY a.nombre, s.tema
            """), {"identificador": identificador}).mappings().all()

        temas = []
        por_asignatura = {}
        total_sesiones = 0
        total_respuestas = 0
        total_aciertos = 0
        for fila in filas:
            sesiones = int(fila["sesiones"])
            respuestas = int(fila["respuestas"])
            aciertos = int(fila["aciertos"])
            porcentaje = round(aciertos * 100 / respuestas, 1) if respuestas else 0
            tema = {
                "asignatura": fila["asignatura"],
                "tema": fila["tema"],
                "sesiones": sesiones,
                "respuestas": respuestas,
                "aciertos": aciertos,
                "porcentaje_aciertos": porcentaje,
                "ultima_practica": _fecha(fila["ultima_practica"]),
            }
            temas.append(tema)
            agregado = por_asignatura.setdefault(fila["asignatura"], {
                "asignatura": fila["asignatura"], "sesiones": 0,
                "respuestas": 0, "aciertos": 0,
            })
            agregado["sesiones"] += sesiones
            agregado["respuestas"] += respuestas
            agregado["aciertos"] += aciertos
            total_sesiones += sesiones
            total_respuestas += respuestas
            total_aciertos += aciertos

        asignaturas = []
        for agregado in por_asignatura.values():
            respuestas = agregado["respuestas"]
            agregado["porcentaje_aciertos"] = round(
                agregado["aciertos"] * 100 / respuestas, 1
            ) if respuestas else 0
            asignaturas.append(agregado)

        return {
            "total_practicas": total_sesiones,
            "total_preguntas": total_respuestas,
            "aciertos": total_aciertos,
            "porcentaje_global": round(total_aciertos * 100 / total_respuestas, 1) if total_respuestas else 0,
            "asignaturas": asignaturas,
            "temas": temas,
        }
