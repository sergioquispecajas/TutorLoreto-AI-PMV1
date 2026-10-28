-- OPCIONAL: ejecutar UNA VEZ en MySQL Workbench para completar el catálogo
-- No elimina ni modifica registros anteriores. La lista debe revisarse contra el plan escolar.
USE tutorloreto;
INSERT IGNORE INTO asignaturas (nombre) VALUES
('Matemática'),
('Comunicación'),
('Ciencia y Tecnología'),
('Ciencias Sociales'),
('Desarrollo Personal, Ciudadanía y Cívica'),
('Educación para el Trabajo'),
('Inglés'),
('Arte y Cultura'),
('Educación Física'),
('Educación Religiosa'),
('Castellano como Segunda Lengua');
SELECT id,nombre FROM asignaturas ORDER BY nombre;
