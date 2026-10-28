
"""Adaptador local para el modelo predictivo de la PoC S9."""

from pathlib import Path

import joblib
import pandas as pd


class ModeloRefuerzoLocal:
    def __init__(self):
        ruta = (
            Path(__file__).resolve().parents[3]
            / "modelos"
            / "modelo_refuerzo_local.joblib"
        )

        paquete = joblib.load(ruta)

        self.modelo = paquete["modelo"]
        self.variables = paquete["variables"]

    def predecir(self, datos: dict) -> dict:
        fila = pd.DataFrame(
            [{variable: datos[variable] for variable in self.variables}],
            columns=self.variables,
        )

        clase = int(self.modelo.predict(fila)[0])
        probabilidad = float(self.modelo.predict_proba(fila)[0, 1])

        return {
            "necesita_refuerzo": bool(clase),
            "resultado": (
                "REQUIERE REFUERZO"
                if clase == 1
                else "PUEDE CONTINUAR"
            ),
            "probabilidad_demostrativa": round(probabilidad, 4),
            "advertencia": "Estimación basada en datos sintéticos.",
        }
