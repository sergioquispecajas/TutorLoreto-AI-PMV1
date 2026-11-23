-- TutorLoreto AI: ampliación incremental para PMV2 y PMV3.
-- Ejecutar en MySQL Workbench sobre la base tutorloreto.
-- No elimina ni modifica las tablas de PMV1. Se puede volver a ejecutar.

USE tutorloreto;

CREATE TABLE IF NOT EXISTS perfiles_estudiante (
    id INT AUTO_INCREMENT PRIMARY KEY,
    identificador VARCHAR(64) NOT NULL UNIQUE,
    grado TINYINT UNSIGNED NOT NULL,
    nivel_academico VARCHAR(20) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_perfil_grado CHECK (grado BETWEEN 1 AND 5),
    CONSTRAINT chk_perfil_nivel CHECK (nivel_academico IN ('basico','intermedio','avanzado'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sesiones_practica (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    estudiante_id INT NOT NULL,
    asignatura_id INT NOT NULL,
    tema VARCHAR(160) NOT NULL,
    dificultad VARCHAR(20) NOT NULL,
    origen VARCHAR(30) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    total_ejercicios TINYINT UNSIGNED NOT NULL,
    aciertos TINYINT UNSIGNED NOT NULL DEFAULT 0,
    duracion_segundos INT UNSIGNED NOT NULL DEFAULT 0,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizada_en TIMESTAMP NULL DEFAULT NULL,
    INDEX idx_sesiones_estudiante_fecha (estudiante_id, creado_en),
    INDEX idx_sesiones_tema (estudiante_id, asignatura_id, tema),
    CONSTRAINT fk_sesion_estudiante FOREIGN KEY (estudiante_id)
        REFERENCES perfiles_estudiante(id),
    CONSTRAINT fk_sesion_asignatura FOREIGN KEY (asignatura_id)
        REFERENCES asignaturas(id),
    CONSTRAINT chk_sesion_dificultad CHECK (dificultad IN ('inicial','intermedia','avanzada')),
    CONSTRAINT chk_sesion_estado CHECK (estado IN ('PENDIENTE','COMPLETADA'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ejercicios_practica (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sesion_id BIGINT NOT NULL,
    numero TINYINT UNSIGNED NOT NULL,
    enunciado TEXT NOT NULL,
    opciones_json JSON NOT NULL,
    respuesta_correcta CHAR(1) NOT NULL,
    explicacion TEXT NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ejercicio_numero (sesion_id, numero),
    CONSTRAINT fk_ejercicio_sesion FOREIGN KEY (sesion_id)
        REFERENCES sesiones_practica(id),
    CONSTRAINT chk_ejercicio_correcta CHECK (respuesta_correcta IN ('A','B','C','D'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS respuestas_practica (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sesion_id BIGINT NOT NULL,
    ejercicio_id BIGINT NOT NULL,
    respuesta CHAR(1) NOT NULL,
    es_correcta BOOLEAN NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_respuesta_ejercicio (sesion_id, ejercicio_id),
    CONSTRAINT fk_respuesta_sesion FOREIGN KEY (sesion_id)
        REFERENCES sesiones_practica(id),
    CONSTRAINT fk_respuesta_ejercicio FOREIGN KEY (ejercicio_id)
        REFERENCES ejercicios_practica(id),
    CONSTRAINT chk_respuesta_opcion CHECK (respuesta IN ('A','B','C','D'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Comprobaciones posteriores:
SHOW TABLES LIKE '%practica%';
SHOW TABLES LIKE 'perfiles_estudiante';
