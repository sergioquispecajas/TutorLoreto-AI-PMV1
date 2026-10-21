import pytest
from app.application.registrar_consulta import registrar_consulta

class RepoFalso:
    def __init__(self): self.datos=[]
    def registrar(self,consulta):
        self.datos.append(consulta)
        return {"id":1,"estado":"PENDIENTE","pregunta":consulta.pregunta}

def test_registro_valido():
    repo=RepoFalso()
    salida=registrar_consulta(repo,1,"  ¿Qué es una fracción? ")
    assert salida["id"]==1
    assert repo.datos[0].pregunta=="¿Qué es una fracción?"

@pytest.mark.parametrize("pregunta",[""," ","  \n"])
def test_rechaza_vacio(pregunta):
    with pytest.raises(ValueError,match="obligatoria"):
        registrar_consulta(RepoFalso(),1,pregunta)

def test_rechaza_asignatura_invalida():
    with pytest.raises(ValueError):
        registrar_consulta(RepoFalso(),0,"Pregunta válida")
