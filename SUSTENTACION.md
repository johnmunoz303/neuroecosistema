# Guion de sustentación

## Demostración en vivo

1. Ejecutar python demo.py --semilla 1000. Mostrar que el escenario abundante arranca en pausa con la política amplia entrenada.
2. Hacer clic en una presa y pulsar N. Explicar qué representa su energía y cómo se seleccionó la acción permitida con mayor probabilidad. Repetir con un depredador.
3. Pulsar Espacio y observar el consumo de plantas y las capturas. Pulsar 2 para pasar a escasez, luego 3 para aumentar el número de depredadores. Cada cambio comienza un episodio con la misma semilla.
4. Volver con 1 y usar M hasta llegar a Reglas. Repetir unos pasos desde las mismas posiciones y contrastar con los resultados de las diez semillas de cada escenario.
5. Mostrar las gráficas de supervivencia, consumo y capturas. Señalar que la presa neuronal por sí sola no mejoró la supervivencia final frente al depredador de reglas.
6. Abrir configuracion.json. Mostrar la pérdida por época y la norma del cambio de pesos. Ubicar en ecosistema.py la propagación de la red, el filtro de acciones válidas y la actualización de pesos.

## Preguntas para practicar individualmente

**¿Por qué hay dos redes?** La presa usa el alimento y la amenaza para decidir. El depredador usa la posición relativa de la presa. Separar los parámetros permite entrenar y evaluar cada objetivo por su cuenta.

**¿Qué hace cada capa?** Las entradas codifican observaciones. Las dos capas ocultas aplican transformaciones lineales más ReLU. La última aplica Softmax y produce una distribución sobre cinco acciones. Al elegir se excluyen movimientos fuera de la cuadrícula.

**¿Se entrena durante la demo?** La demo carga modelos guardados. El entrenamiento ocurre antes, por lotes de ejemplos etiquetados por el profesor. Se minimiza entropía cruzada y la retropropagación actualiza pesos y sesgos.

**¿Por qué usar semillas separadas?** Las semillas de prueba generan condiciones iniciales que no se usaron para recopilar ejemplos. Dentro de la prueba, todas las políticas comparten las mismas semillas para reducir el efecto de diferencias iniciales.

**¿Qué mostró la comparación entre tamaños?** La amplia entrenada dejó más presas vivas que la compacta en los tres escenarios de esta corrida. Solo se usó una inicialización por arquitectura y especie, por lo que falta repetir el entrenamiento con otras semillas.

**¿La presa aprendió a evadir mejor que la estrategia de reglas?** Frente a un depredador de reglas, la supervivencia final de la presa neuronal fue 0 % en los tres escenarios, igual a la línea base. Además consumió menos alimento en los tres escenarios. La supervivencia de las dos redes juntas dependió en buena medida de quién controlaba a los depredadores.

**¿Qué harías primero para mejorar?** Evaluar al depredador con objetivos de entrenamiento ligados a capturas y energía, con presas de reglas como oposición fija. Comparar después las políticas con semillas compartidas y varias inicializaciones.

**¿Cómo se usó IA generativa?** Codex ayudó a implementar el simulador, automatizar el entrenamiento y preparar la documentación y la lectura inicial de resultados. El equipo debe reproducir la corrida, revisar el código y dejar constancia en el informe de sus propias verificaciones y decisiones.
