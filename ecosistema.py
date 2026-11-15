"""Simulación discreta de depredadores y presas, independiente de Pygame."""

from dataclasses import dataclass

import numpy as np


DIRECCIONES = np.array([(0, -1), (0, 1), (-1, 0), (1, 0), (0, 0)])
ACCIONES = ("Arriba", "Abajo", "Izquierda", "Derecha", "Quieto")
ESPECIES = ("presa", "depredador")
ENTRADAS = 12
CONFIGURACIONES = {"compacta": (16, 8), "amplia": (32, 16)}


@dataclass(frozen=True)
class Escenario:
    plantas: int
    depredadores: int
    presas: int = 12
    lado: int = 20
    pasos: int = 120


ESCENARIOS = {
    "abundante": Escenario(22, 2),
    "escasez": Escenario(6, 2),
    "presion": Escenario(22, 5),
}


@dataclass
class Agente:
    especie: str
    posicion: np.ndarray
    energia: int = 65
    accion: int = 4
    observacion: np.ndarray | None = None
    probabilidades: np.ndarray | None = None


class Mundo:
    def __init__(self, escenario, semilla):
        self.escenario = escenario
        self.rng = np.random.default_rng(semilla)
        celdas = self.rng.permutation(escenario.lado**2)
        posiciones = np.column_stack((celdas % escenario.lado, celdas // escenario.lado))
        tipos = ["presa"] * escenario.presas + ["depredador"] * escenario.depredadores
        self.agentes = [Agente(tipo, pos) for tipo, pos in zip(tipos, posiciones)]
        self.plantas = set(map(tuple, posiciones[len(tipos):len(tipos) + escenario.plantas]))
        self.paso = 0
        self.alimento = 0
        self.tiempos_captura = []

    @property
    def terminado(self):
        return self.paso >= self.escenario.pasos or not any(
            a.especie == "presa" for a in self.agentes
        )

    def observar(self, agente):
        lado = self.escenario.lado
        x, y = agente.posicion
        plantas = sorted(self.plantas)
        presas = [a.posicion for a in self.agentes if a.especie == "presa"]
        rivales = [a.posicion for a in self.agentes if a.especie == "depredador"]
        clases = (plantas, rivales) if agente.especie == "presa" else ([], presas)
        vectores = []
        for objetivos in clases:
            if len(objetivos):
                delta = np.asarray(objetivos) - agente.posicion
                cercano = delta[np.abs(delta).sum(axis=1).argmin()]
                vectores.extend([*(cercano / (lado - 1)), 1])
            else:
                vectores.extend((0, 0, 0))
        libres = [y > 0, y < lado - 1, x > 0, x < lado - 1, True]
        return np.array([*vectores, agente.energia / 100, *libres], dtype=float)

    def avanzar(self, politica):
        if self.terminado:
            return
        origenes = {id(a): a.posicion for a in self.agentes}
        for agente in self.agentes:
            agente.observacion = self.observar(agente)
            agente.accion, agente.probabilidades = politica(agente.especie, agente.observacion)
        for agente in self.agentes:
            # Las presas pierden un turno de movimiento cada cuatro pasos.
            if agente.especie == "depredador" or self.paso % 4 != 3:
                agente.posicion = np.clip(
                    agente.posicion + DIRECCIONES[agente.accion], 0, self.escenario.lado - 1
                )
            agente.energia -= 2 if agente.especie == "depredador" else 1

        self.paso += 1
        capturadas = set()
        for depredador in (a for a in self.agentes if a.especie == "depredador"):
            for presa in (a for a in self.agentes if a.especie == "presa"):
                if id(presa) in capturadas:
                    continue
                coinciden = np.array_equal(depredador.posicion, presa.posicion)
                se_cruzan = (np.array_equal(depredador.posicion, origenes[id(presa)])
                             and np.array_equal(presa.posicion, origenes[id(depredador)]))
                if coinciden or se_cruzan:
                    capturadas.add(id(presa))
                    self.tiempos_captura.append(self.paso)
                    depredador.energia = min(100, depredador.energia + 35)
                    break

        for presa in (a for a in self.agentes if a.especie == "presa" and id(a) not in capturadas):
            celda = tuple(presa.posicion)
            if celda in self.plantas:
                self.plantas.remove(celda)
                self.alimento += 1
                presa.energia = min(100, presa.energia + 27)
        self.agentes = [a for a in self.agentes if id(a) not in capturadas and a.energia > 0]

        # Proponer una celda en cada turno mantiene la secuencia exógena por semilla.
        celda = tuple(self.rng.integers(0, self.escenario.lado, size=2))
        if self.paso % 3 == 0 and len(self.plantas) < self.escenario.plantas:
            if not any(tuple(a.posicion) == celda for a in self.agentes):
                self.plantas.add(celda)

    def metricas(self):
        presas = [a.energia for a in self.agentes if a.especie == "presa"]
        depredadores = [a.energia for a in self.agentes if a.especie == "depredador"]
        return {
            "pasos": self.paso,
            "supervivencia_presas": len(presas) / self.escenario.presas,
            "alimento": self.alimento,
            "capturas": len(self.tiempos_captura),
            "energia_presa_por_inicial": sum(presas) / self.escenario.presas,
            "energia_depredador_por_inicial": sum(depredadores) / self.escenario.depredadores,
            "tiempo_medio_captura": float(np.mean(self.tiempos_captura)) if self.tiempos_captura else None,
        }


def regla(especie, x):
    """Profesor y referencia con la misma información que recibe la red."""
    permitido = x[7:12].astype(bool)
    rival = x[3:5]
    distancia_actual = np.abs(rival).sum()
    if especie == "depredador":
        puntaje = -np.abs(rival - DIRECCIONES / 19).sum(axis=1)
    else:
        planta = x[:2]
        atraccion = -np.abs(planta - DIRECCIONES / 19).sum(axis=1) * x[2]
        peligro = np.abs(rival - DIRECCIONES / 19).sum(axis=1)
        puntaje = atraccion + peligro * (2.5 if x[5] and distancia_actual <= 4 / 19 else 0)
    return int(np.argmax(np.where(permitido, puntaje, -np.inf))), None


class Red:
    def __init__(self, ocultas, semilla):
        self.rng = np.random.default_rng(semilla)
        capas = (ENTRADAS, *ocultas, len(ACCIONES))
        self.pesos = [
            self.rng.normal(0, np.sqrt(2 / entrada), size=(entrada, salida))
            for entrada, salida in zip(capas, capas[1:])
        ]
        self.sesgos = [np.zeros(w.shape[1]) for w in self.pesos]

    def adelante(self, x):
        activaciones = [x]
        for w, b in zip(self.pesos[:-1], self.sesgos[:-1]):
            activaciones.append(np.maximum(0, activaciones[-1] @ w + b))
        logits = activaciones[-1] @ self.pesos[-1] + self.sesgos[-1]
        exponenciales = np.exp(logits - logits.max(axis=1, keepdims=True))
        activaciones.append(exponenciales / exponenciales.sum(axis=1, keepdims=True))
        return activaciones

    def entrenar(self, x, y, epocas):
        historial = []
        for _ in range(epocas):
            indices = self.rng.permutation(len(y))
            perdida = 0.0
            for inicio in range(0, len(y), 128):
                ids = indices[inicio:inicio + 128]
                activaciones = self.adelante(x[ids])
                filas = np.arange(len(ids))
                perdida -= np.log(np.maximum(activaciones[-1][filas, y[ids]], 1e-12)).sum()
                grad = activaciones[-1].copy()
                grad[filas, y[ids]] -= 1
                grad /= len(ids)
                for i in reversed(range(len(self.pesos))):
                    previo = (grad @ self.pesos[i].T) * (activaciones[i] > 0) if i else None
                    self.pesos[i] -= 0.08 * (activaciones[i].T @ grad)
                    self.sesgos[i] -= 0.08 * grad.sum(axis=0)
                    grad = previo
            historial.append(float(perdida / len(y)))
        return historial


def redes(configuracion, semilla):
    return {especie: Red(CONFIGURACIONES[configuracion], semilla + i)
            for i, especie in enumerate(ESPECIES)}


def politica_neuronal(modelos):
    def decidir(especie, x):
        probabilidades = modelos[especie].adelante(x[None])[-1][0]
        return int(np.argmax(np.where(x[7:12], probabilidades, -np.inf))), probabilidades
    return decidir


def guardar_modelos(ruta, modelos):
    matrices = {}
    for especie, red in modelos.items():
        for i, (w, b) in enumerate(zip(red.pesos, red.sesgos)):
            matrices[f"{especie}_w{i}"] = w
            matrices[f"{especie}_b{i}"] = b
    np.savez_compressed(ruta, **matrices)


def cargar_modelos(ruta, configuracion):
    modelos = redes(configuracion, 0)
    with np.load(ruta) as matrices:
        for especie, red in modelos.items():
            for i, (w, b) in enumerate(zip(red.pesos, red.sesgos)):
                w[:] = matrices[f"{especie}_w{i}"]
                b[:] = matrices[f"{especie}_b{i}"]
    return modelos

