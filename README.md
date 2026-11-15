# NeuroEcosistema

Proyecto final de Electiva I de Profundización – Inteligencia Artificial, USTA Tunja. Simula presas y depredadores en una cuadrícula 2D. La presa busca plantas y evita amenazas. El depredador persigue presas para recuperar energía. El laberinto de Neurito inspiró el movimiento discreto y el entrenamiento supervisado con un agente profesor.

## Ejecutar en Windows

Abre PowerShell en esta carpeta. Con Python 3.13 instalado:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe demo.py
```

La aplicación incluye los pesos iniciales y entrenados. Abre en pausa con el escenario abundante y la red amplia entrenada. Usa **Espacio** para iniciar o pausar, **N** para avanzar un turno, **M** para cambiar de política, **R** para reiniciar con la misma semilla y **1**, **2** o **3** para cambiar de escenario. Haz clic en una presa o depredador para inspeccionar su energía, acción y probabilidades de la red. La acción elegida es el máximo entre movimientos permitidos. Una presa decide todos los turnos, pero descansa cada cuarto turno.

Para cambiar la semilla de la demo:

```powershell
.\.venv\Scripts\python.exe demo.py --semilla 1006
```

## Reproducir el entrenamiento y la evaluación

```powershell
.\.venv\Scripts\python.exe experimentar.py --salida resultados_reproducidos
.\.venv\Scripts\python.exe graficar.py --resultados resultados_reproducidos
.\.venv\Scripts\python.exe demo.py --resultados resultados_reproducidos
```

- [resultados/configuracion.json](resultados/configuracion.json) registra semillas, escenarios, arquitecturas, pérdidas de entrenamiento y cambio de pesos por especie.
- [resultados/episodios.csv](resultados/episodios.csv) contiene 210 episodios de evaluación, uno por combinación de escenario, política y semilla.
- [resultados/resumen.csv](resultados/resumen.csv) contiene medias, desviaciones estándar muestrales y número de observaciones.
- [resultados/graficas](resultados/graficas) contiene gráficas PNG y SVG de supervivencia, consumo y capturas.
- [Informe técnico en Word](Informe_NeuroEcosistema.docx) con metodología, resultados, discusión y recomendaciones.
- [BITACORA.md](BITACORA.md) registra las alternativas y criterios de diseño.
- [SUSTENTACION.md](SUSTENTACION.md) contiene la secuencia de la demostración y preguntas de práctica.

## Cómo funciona

El mapa tiene 20 × 20 celdas y comienza con 12 presas. Los escenarios cambian la cantidad inicial y el máximo de plantas (22, 6 y 22) o la cantidad inicial de depredadores (2, 2 y 5). Cada episodio dura hasta 120 pasos o hasta que se extinguen las presas. Cada tres pasos se propone una celda aleatoria para reponer una planta si hay espacio y el recurso no llegó al máximo. Las plantas recuperan 27 unidades de energía y las capturas recuperan 35. Presas y depredadores gastan 1 y 2 unidades por turno, respectivamente.

Cada especie tiene sus propios pesos. Sus 12 entradas representan dos posibles objetivos (desplazamiento horizontal, vertical e indicador de presencia para cada uno), su energía normalizada y cinco indicadores de movimiento válido. La presa observa la planta y el depredador más cercanos por distancia Manhattan. El depredador observa la presa más cercana y recibe ceros en el espacio reservado al alimento. Las redes comparadas son **12 → 16 → 8 → 5** y **12 → 32 → 16 → 5**, con ReLU en las capas ocultas y Softmax para las cinco acciones. La observación de cada turno se toma antes de mover.

El profesor por reglas busca alimento y prioriza huir si detecta un depredador a cuatro celdas Manhattan o menos. Los depredadores por reglas se acercan a la presa más próxima. Para entrenar, se recopilaron etiquetas del profesor en 30 episodios y se exploraron acciones válidas aleatorias el 20 % de las veces, manteniendo la etiqueta original del profesor. En entrenamiento se usaron entropía cruzada, retropropagación, 25 épocas, lotes de 128 y tasa 0,08.

La evaluación usa las semillas 1000–1009 para las siete políticas de cada escenario. Una semilla fija posiciones iniciales y la secuencia de celdas propuestas para reponer alimento. Cada trayectoria determina cuáles reposiciones se hacen efectivas. El tiempo medio hasta captura utiliza solo las capturas observadas y se deja vacío cuando no hubo ninguna. La energía final se divide entre el número inicial de agentes por especie, con cero para los que ya no están vivos.

## Lectura rápida de la evidencia

En la configuración amplia entrenada, la supervivencia media fue 35,0 %, 30,8 % y 17,5 % en abundancia, escasez y presión, respectivamente. La referencia de reglas terminó con 0 % en los tres. Al probar solo la presa neuronal, volvió a 0 %. Al probar solo el depredador neuronal, quedaron vivas entre 54,2 % y 57,5 % de las presas. Esto indica que la ventaja de supervivencia observada con ambas redes depende de qué política lleva el depredador.

La evaluación repite condiciones del entorno con una inicialización por arquitectura. Los resultados no estiman la variabilidad entre inicializaciones del entrenamiento. Las barras de las gráficas muestran dispersión entre episodios, no intervalos de confianza.

