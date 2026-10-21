-- Ejecutar en MySQL Workbench como script completo.
CREATE DATABASE IF NOT EXISTS tutorloreto CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tutorloreto;

CREATE TABLE IF NOT EXISTS asignaturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS consultas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asignatura_id INT NOT NULL,
    pregunta TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_consultas_asignaturas
      FOREIGN KEY (asignatura_id) REFERENCES asignaturas(id)
);

-- Preparada para implementar HU04; no se llena en esta entrega.
CREATE TABLE IF NOT EXISTS respuestas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    consulta_id INT NOT NULL,
    contenido TEXT NOT NULL,
    origen VARCHAR(30) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_respuestas_consultas
      FOREIGN KEY (consulta_id) REFERENCES consultas(id)
);

INSERT IGNORE INTO asignaturas (nombre) VALUES
('Matemática'), ('Comunicación'), ('Ciencia y Tecnología');

SELECT * FROM asignaturas;
