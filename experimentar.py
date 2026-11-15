"""Entrena ambas redes y compara políticas con episodios emparejados por semilla."""

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from statistics import mean, stdev

import numpy as np

from ecosistema import (
    ACCIONES, CONFIGURACIONES, ESCENARIOS, ESPECIES, Mundo, cargar_modelos, guardar_modelos,
    politica_neuronal, redes, regla,
)

RAIZ = Path(__file__).resolve().parent
SEMILLA_RED = 77
SEMILLAS_ENTRENAMIENTO = tuple(range(100, 110))
SEMILLAS_EVALUACION = tuple(range(1000, 1010))


def generar_ejemplos():
    datos = {especie: ([], []) for especie in ESPECIES}
    for escenario in ESCENARIOS.values():
        for semilla in SEMILLAS_ENTRENAMIENTO:
            mundo = Mundo(escenario, semilla)
            exploracion = np.random.default_rng(semilla + 5000)

            def etiquetar(especie, x):
                accion, _ = regla(especie, x)
                entradas, etiquetas = datos[especie]
                entradas.append(x)
                etiquetas.append(accion)
                # Muestrea estados fuera de las trayectorias puras del profesor.
                if exploracion.random() < 0.20:
                    accion = int(exploracion.choice(np.flatnonzero(x[7:12])))
                return accion, None

            while not mundo.terminado:
                mundo.avanzar(etiquetar)
    return {especie: (np.asarray(x), np.asarray(y)) for especie, (x, y) in datos.items()}


def evaluar(nombre, politica):
    filas = []
    for etiqueta, escenario in ESCENARIOS.items():
        for semilla in SEMILLAS_EVALUACION:
            mundo = Mundo(escenario, semilla)
            while not mundo.terminado:
                mundo.avanzar(politica)
            filas.append({"escenario": etiqueta, "politica": nombre, "semilla": semilla,
                          **mundo.metricas()})
    return filas


def escribir_csv(ruta, filas):
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def resumir(filas):
    grupos = {}
    for fila in filas:
        grupos.setdefault((fila["escenario"], fila["politica"]), []).append(fila)
    salida = []
    for (escenario, politica), grupo in grupos.items():
        for metrica in tuple(grupo[0])[3:]:
            cifras = [fila[metrica] for fila in grupo if fila[metrica] is not None]
            salida.append({
                "escenario": escenario, "politica": politica, "metrica": metrica,
                "n": len(cifras), "media": mean(cifras) if cifras else None,
                "desviacion_muestral": stdev(cifras) if len(cifras) > 1 else None,
            })
    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epocas", type=int, default=25)
    parser.add_argument("--salida", type=Path, default=RAIZ / "resultados")
    args = parser.parse_args()
    if args.epocas < 1:
        parser.error("--epocas debe ser positivo")
    args.salida.mkdir(parents=True, exist_ok=True)
    datos = generar_ejemplos()
    print("Evaluando la referencia por reglas...", flush=True)
    filas = evaluar("reglas", regla)
    entrenamiento = {}
    for configuracion in CONFIGURACIONES:
        print(f"Entrenando y evaluando: {configuracion}...", flush=True)
        modelos = redes(configuracion, SEMILLA_RED)
        politica = politica_neuronal(modelos)
        filas.extend(evaluar(f"{configuracion}_inicial", politica))
        guardar_modelos(args.salida / f"{configuracion}_inicial.npz", modelos)
        entrenamiento[configuracion] = {}
        for especie, modelo in modelos.items():
            iniciales = [w.copy() for w in modelo.pesos]
            x, y = datos[especie]
            perdida = modelo.entrenar(x, y, args.epocas)
            cambio = np.sqrt(sum(np.square(w - i).sum()
                                 for w, i in zip(modelo.pesos, iniciales)))
            entrenamiento[configuracion][especie] = {
                "muestras": len(y), "perdida_por_epoca": perdida,
                "norma_cambio_pesos": float(cambio),
            }
        guardar_modelos(args.salida / f"{configuracion}_entrenada.npz", modelos)
        filas.extend(evaluar(f"{configuracion}_entrenada", politica))

    amplia = politica_neuronal(cargar_modelos(args.salida / "amplia_entrenada.npz", "amplia"))

    def presa_neuronal(especie, x):
        return amplia(especie, x) if especie == "presa" else regla(especie, x)

    def depredador_neuronal(especie, x):
        return amplia(especie, x) if especie == "depredador" else regla(especie, x)

    filas.extend(evaluar("amplia_solo_presa", presa_neuronal))
    filas.extend(evaluar("amplia_solo_depredador", depredador_neuronal))
    escribir_csv(args.salida / "episodios.csv", filas)
    escribir_csv(args.salida / "resumen.csv", resumir(filas))
    metadata = {
        "escenarios": {nombre: asdict(e) for nombre, e in ESCENARIOS.items()},
        "semillas_entrenamiento": SEMILLAS_ENTRENAMIENTO,
        "semillas_evaluacion": SEMILLAS_EVALUACION,
        "semilla_red_presa": SEMILLA_RED, "semilla_red_depredador": SEMILLA_RED + 1,
        "arquitecturas_ocultas": CONFIGURACIONES, "acciones": ACCIONES,
        "epocas": args.epocas, "lote": 128, "tasa": 0.08,
        "exploracion_entrenamiento": 0.20, "entrenamiento": entrenamiento,
    }
    (args.salida / "configuracion.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"{len(filas)} episodios. Resultados en {args.salida}")


if __name__ == "__main__":
    main()

