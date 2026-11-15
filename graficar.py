"""Genera gráficas a partir del CSV de resultados, sin alterar los experimentos."""

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ecosistema import ESCENARIOS


METRICAS = {
    "supervivencia_presas": ("Presas vivas al cierre (%)", 100),
    "alimento": ("Plantas consumidas", 1),
    "capturas": ("Capturas por episodio", 1),
}
ETIQUETAS = {
    "reglas": "Reglas",
    "compacta_inicial": "Compacta inicial",
    "compacta_entrenada": "Compacta entrenada",
    "amplia_inicial": "Amplia inicial",
    "amplia_entrenada": "Amplia entrenada",
    "amplia_solo_presa": "Solo presa neuronal",
    "amplia_solo_depredador": "Solo depredador neuronal",
}
COLORES = ("#627487", "#5ea6a1", "#257774", "#919dc4", "#3b4e8b", "#a85f17", "#a14e65")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resultados", type=Path, default=Path(__file__).parent / "resultados")
    ruta = parser.parse_args().resultados
    with (ruta / "resumen.csv").open(encoding="utf-8", newline="") as archivo:
        datos = {(fila["escenario"], fila["politica"], fila["metrica"]): fila
                 for fila in csv.DictReader(archivo)}
    salida = ruta / "graficas"
    salida.mkdir(exist_ok=True)
    escenarios = list(ESCENARIOS)
    posiciones = np.arange(len(escenarios))
    ancho = 0.11
    for metrica, (titulo, escala) in METRICAS.items():
        fig, eje = plt.subplots(figsize=(11, 5), layout="constrained")
        for i, (politica, etiqueta) in enumerate(ETIQUETAS.items()):
            filas = [datos[(escenario, politica, metrica)] for escenario in escenarios]
            medias = [float(fila["media"]) * escala for fila in filas]
            desv = [float(fila["desviacion_muestral"]) * escala for fila in filas]
            eje.bar(posiciones + (i - 3) * ancho, medias, ancho, label=etiqueta,
                    color=COLORES[i], yerr=desv, capsize=2, error_kw={"elinewidth": 0.8})
        eje.set_title(titulo)
        eje.set_ylabel("Media ± desviación estándar muestral")
        eje.set_xticks(posiciones, ["Abundante", "Escasez", "Presión"])
        eje.grid(axis="y", alpha=0.22)
        eje.set_axisbelow(True)
        eje.legend(loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=3, frameon=False)
        for extension in ("png", "svg"):
            fig.savefig(salida / f"{metrica}.{extension}", dpi=150)
        plt.close(fig)


if __name__ == "__main__":
    main()
