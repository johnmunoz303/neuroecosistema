"""Demostración interactiva de NeuroEcosistema."""

import argparse
from pathlib import Path

import pygame

from ecosistema import ACCIONES, CONFIGURACIONES, ESCENARIOS, Mundo, cargar_modelos, politica_neuronal, regla

RAIZ = Path(__file__).resolve().parent
CELDA = 30
TABLERO = 20 * CELDA
FONDO = "#101c22"
PANEL = "#16262e"
TEXTO = "#ebf4f0"
SUAVE = "#a9c4c0"
PLANTA = "#a7d76a"
PRESA = "#59ccb8"
DEPREDADOR = "#ff816a"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semilla", type=int, default=1000)
    parser.add_argument("--resultados", type=Path, default=RAIZ / "resultados")
    parser.add_argument("--fotogramas", type=int, default=0, help="Cerrar después de N cuadros")
    args = parser.parse_args()
    politicas = {"Reglas": regla}
    for configuracion in CONFIGURACIONES:
        for estado in ("inicial", "entrenada"):
            ruta = args.resultados / f"{configuracion}_{estado}.npz"
            if not ruta.is_file():
                parser.error(f"Falta {ruta.name}. Ejecuta python experimentar.py.")
            modelos = cargar_modelos(ruta, configuracion)
            politicas[f"{configuracion.capitalize()} {estado}"] = politica_neuronal(modelos)
            if configuracion == "amplia" and estado == "entrenada":
                amplia = politicas["Amplia entrenada"]
    politicas["Amplia solo presa"] = lambda especie, x: (
        amplia(especie, x) if especie == "presa" else regla(especie, x)
    )
    politicas["Amplia solo depredador"] = lambda especie, x: (
        amplia(especie, x) if especie == "depredador" else regla(especie, x)
    )

    pygame.init()
    ventana = pygame.display.set_mode((1000, 675))
    pygame.display.set_caption("NeuroEcosistema | USTA Tunja")
    reloj = pygame.time.Clock()
    titulo = pygame.font.SysFont("segoeui", 30, bold=True)
    cuerpo = pygame.font.SysFont("segoeui", 20)
    chico = pygame.font.SysFont("segoeui", 16)
    escenarios = list(ESCENARIOS)
    nombres = list(politicas)
    escenario = escenarios[0]
    politica = nombres.index("Amplia entrenada")
    mundo = Mundo(ESCENARIOS[escenario], args.semilla)
    pausado, seleccionado, acumulado, cuadros, abierto = True, None, 0, 0, True

    def texto(cadena, x, y, fuente=cuerpo, color=TEXTO):
        ventana.blit(fuente.render(cadena, True, color), (x, y))

    while abierto:
        intervalo = reloj.tick(60)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                abierto = False
            if evento.type == pygame.KEYDOWN:
                tecla = evento.key
                cambio = False
                if pygame.K_1 <= tecla <= pygame.K_3:
                    escenario = escenarios[tecla - pygame.K_1]
                    cambio = True
                if tecla == pygame.K_m:
                    politica = (politica + 1) % len(nombres)
                    cambio = True
                if cambio or tecla == pygame.K_r:
                    mundo = Mundo(ESCENARIOS[escenario], args.semilla)
                    seleccionado, acumulado, pausado = None, 0, True
                if tecla == pygame.K_SPACE:
                    pausado = not pausado
                if tecla == pygame.K_n:
                    pausado = True
                    mundo.avanzar(politicas[nombres[politica]])
                if tecla == pygame.K_ESCAPE:
                    abierto = False
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                celda = (evento.pos[0] // CELDA, (evento.pos[1] - 45) // CELDA)
                seleccionado = next((a for a in mundo.agentes if tuple(a.posicion) == celda), None)

        if not pausado:
            acumulado += intervalo
            if acumulado >= 160:
                mundo.avanzar(politicas[nombres[politica]])
                acumulado -= 160

        ventana.fill(FONDO)
        pygame.draw.rect(ventana, PANEL, (610, 0, 390, 675))
        texto("NeuroEcosistema", 16, 5, titulo)
        texto(f"{escenario.capitalize()}  ·  Semilla {args.semilla}", 325, 14, chico, SUAVE)
        for y in range(20):
            for x in range(20):
                pygame.draw.rect(ventana, "#1e3435" if (x + y) % 2 else "#223b3b",
                                 (x * CELDA, y * CELDA + 45, CELDA - 1, CELDA - 1))
        def centro(pos):
            return (int(pos[0]) * CELDA + CELDA // 2, int(pos[1]) * CELDA + 45 + CELDA // 2)

        for planta in mundo.plantas:
            x, y = centro(planta)
            pygame.draw.rect(ventana, PLANTA, (x - 4, y - 4, 8, 8), border_radius=2)
        for agente in mundo.agentes:
            x, y = centro(agente.posicion)
            if agente.especie == "presa":
                pygame.draw.circle(ventana, PRESA, (x, y), 9)
            else:
                pygame.draw.polygon(ventana, DEPREDADOR, [(x, y - 12), (x + 11, y), (x, y + 12), (x - 11, y)])
            if agente is seleccionado:
                pygame.draw.circle(ventana, TEXTO, (x, y), 14, 2)

        texto("Plantas", 20, 649, chico, PLANTA)
        texto("Presas", 96, 649, chico, PRESA)
        texto("Depredadores", 162, 649, chico, DEPREDADOR)
        texto("Clic en un agente para inspeccionarlo", 315, 649, chico, SUAVE)
        metricas = mundo.metricas()
        estado = "Finalizado" if mundo.terminado else "Pausa" if pausado else "En ejecución"
        texto(nombres[politica], 632, 19, titulo)
        texto(f"{estado}    ·    Paso {mundo.paso}/{mundo.escenario.pasos}", 632, 63, chico, SUAVE)
        presas = sum(a.especie == "presa" for a in mundo.agentes)
        texto(f"Presas vivas  {presas}/{mundo.escenario.presas}", 632, 103)
        depredadores = len(mundo.agentes) - presas
        texto(f"Depredadores vivos  {depredadores}/{mundo.escenario.depredadores}", 632, 135)
        texto(f"Plantas consumidas  {metricas['alimento']}     Capturas  {metricas['capturas']}", 632, 167)
        pygame.draw.line(ventana, "#355052", (632, 213), (978, 213))
        if seleccionado is not None:
            a = seleccionado
            texto(a.especie.capitalize(), 632, 230, titulo)
            en_mapa = any(vivo is a for vivo in mundo.agentes)
            if a.observacion is not None:
                detalle = f"Acción decidida  {ACCIONES[a.accion]}"
            else:
                detalle = "Avanza un paso para ver su decisión"
            texto(f"Energía  {max(0, a.energia)}/100   ·   {'Activo' if en_mapa else 'Retirado'}", 632, 275)
            texto(detalle, 632, 305, chico, SUAVE)
            if a.probabilidades is not None:
                for i, prob in enumerate(a.probabilidades):
                    y = 342 + i * 27
                    habilitada = bool(a.observacion[7 + i])
                    texto(ACCIONES[i], 632, y, chico)
                    pygame.draw.rect(ventana, "#263c41", (718, y + 5, 147, 8), border_radius=3)
                    pygame.draw.rect(ventana, PRESA if i == a.accion else "#648d89",
                                     (718, y + 5, round(147 * float(prob)), 8), border_radius=3)
                    texto(f"{prob:.0%}" if habilitada else f"{prob:.0%} · bloqueada",
                          875, y, chico, SUAVE)
        else:
            texto("Selecciona un agente", 632, 234)
            texto("Consulta su energía, decisión y salida de la red.", 632, 266, chico, SUAVE)

        pygame.draw.line(ventana, "#355052", (632, 511), (978, 511))
        texto("Espacio  Ejecutar / pausar     N  Avanzar un paso", 632, 530, chico)
        texto("M  Cambiar política          R  Reiniciar", 632, 560, chico)
        texto("1  Abundante    2  Escasez    3  Presión", 632, 590, chico)
        texto("Esc  Cerrar", 632, 620, chico, SUAVE)
        pygame.display.flip()
        cuadros += 1
        if args.fotogramas and cuadros >= args.fotogramas:
            abierto = False

    pygame.quit()


if __name__ == "__main__":
    main()
