# -*- coding: utf-8 -*-
r"""TutorLoreto AI - Reentrenamiento local de la PoC de Google Colab (S9).

Reproduce la generacion sintetica, particion, comparacion y seleccion del
notebook original, pero serializa con la version de scikit-learn instalada
localmente. NO utiliza registros reales de alumnos.

Uso desde PMV1_codigo:
    .\.venv\Scripts\python.exe .\modelos\entrenar_refuerzo_local.py
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

SEED = 42
VARIABLES = [
    "grado",
    "porcentaje_aciertos",
    "respuestas_incorrectas",
    "tiempo_promedio_segundos",
    "temas_con_error",
    "intentos_previos",
]


def generar_dataset_sintetico(n=1200, seed=SEED):
    # Misma regla y semilla de la PoC facilitada por el equipo.
    rng = np.random.default_rng(seed)
    grado = rng.integers(1, 6, n)
    aciertos = np.clip(rng.normal(72, 18, n), 0, 100)
    incorrectas = np.clip(rng.poisson(np.maximum(0.4, (100 - aciertos) / 20)), 0, 8)
    tiempo = np.clip(rng.lognormal(mean=np.log(45), sigma=0.42, size=n), 10, 180)
    temas_error = np.clip(rng.poisson(np.maximum(0.15, (100 - aciertos) / 28)), 0, 6)
    intentos = np.clip(rng.poisson(1.2 + temas_error * 0.35), 0, 8)
    z = (
        -2.1 + 0.035 * (70 - aciertos) + 0.42 * incorrectas
        + 0.43 * temas_error + 0.009 * (tiempo - 45) + 0.10 * intentos
    )
    prob = 1 / (1 + np.exp(-z))
    etiqueta = rng.binomial(1, prob)
    return pd.DataFrame({
        "grado": grado.astype(int),
        "porcentaje_aciertos": aciertos.round(1),
        "respuestas_incorrectas": incorrectas.astype(int),
        "tiempo_promedio_segundos": tiempo.round(1),
        "temas_con_error": temas_error.astype(int),
        "intentos_previos": intentos.astype(int),
        "necesita_refuerzo": etiqueta.astype(int),
    })


def main():
    df = generar_dataset_sintetico()
    X = df[VARIABLES]
    y = df["necesita_refuerzo"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=SEED, stratify=y
    )
    modelos = {
        "Árbol de Decisión": DecisionTreeClassifier(
            max_depth=5, min_samples_leaf=10, random_state=SEED
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=7, min_samples_leaf=5,
            class_weight="balanced", random_state=SEED
        ),
        "Regresión Logística": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED),
        ),
    }
    modelos_entrenados = {}
    resultados = []
    for nombre, modelo in modelos.items():
        modelo.fit(X_train, y_train)
        pred = modelo.predict(X_test)
        modelos_entrenados[nombre] = modelo
        fila = {
            "Modelo": nombre,
            "Accuracy": accuracy_score(y_test, pred),
            "Precision": precision_score(y_test, pred, zero_division=0),
            "Recall": recall_score(y_test, pred, zero_division=0),
            "F1-Score": f1_score(y_test, pred, zero_division=0),
        }
        fila["Promedio métricas"] = np.mean([
            fila["Accuracy"], fila["Precision"], fila["Recall"], fila["F1-Score"]
        ])
        resultados.append(fila)

    comparacion = pd.DataFrame(resultados).sort_values(
        "Promedio métricas", ascending=False
    ).reset_index(drop=True)
    nombre_final = str(comparacion.loc[0, "Modelo"])
    modelo_final = modelos_entrenados[nombre_final]
    pred_final = modelo_final.predict(X_test)

    ejemplo = pd.DataFrame([{
        "grado": 3,
        "porcentaje_aciertos": 55.0,
        "respuestas_incorrectas": 3,
        "tiempo_promedio_segundos": 65.0,
        "temas_con_error": 2,
        "intentos_previos": 2,
    }])[VARIABLES]
    clase = int(modelo_final.predict(ejemplo)[0])
    prob_estimada = float(modelo_final.predict_proba(ejemplo)[0, 1])

    salida = Path(__file__).resolve().parent / "modelo_refuerzo_local.joblib"
    if salida.exists():
        raise FileExistsError(
            f"Ya existe {salida.name}. No se ha sobrescrito. "
            "Conserva el archivo anterior y revisa antes de reentrenar."
        )
    paquete = {
        "modelo": modelo_final,
        "variables": VARIABLES,
        "nombre_modelo": nombre_final,
        "version_sklearn": sklearn.__version__,
        "origen": "PoC S9, 1200 datos sintéticos, reentrenado localmente",
    }
    joblib.dump(paquete, salida)

    print("\n=== POC TUTORLORETO AI - REENTRENAMIENTO LOCAL ===")
    print(f"Python/sklearn: {sklearn.__version__} (scikit-learn)")
    print(f"Dataset: {df.shape[0]} registros sintéticos; train={len(X_train)}; test={len(X_test)}")
    print("\nComparación de algoritmos:\n", comparacion.round(3).to_string(index=False))
    print("\nModelo seleccionado:", nombre_final)
    print("Matriz de confusión:", confusion_matrix(y_test, pred_final, labels=[0, 1]).tolist())
    print("Caso sintético:", "REQUIERE REFUERZO" if clase else "PUEDE CONTINUAR")
    print(f"Probabilidad no calibrada, solo demostrativa: {prob_estimada:.1%}")
    print("Archivo generado:", salida)
    print("AVISO: la precisión con datos sintéticos no valida el uso con estudiantes reales.")


if __name__ == "__main__":
    main()
