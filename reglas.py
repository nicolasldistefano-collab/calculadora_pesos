"""
reglas.py - Lógica de cálculo de pesos para carreras de caballos.

Este módulo NO depende de la interfaz gráfica: se puede usar desde la
terminal, desde tests o desde cualquier otra interfaz. Así, si la ventana
falla (por ejemplo, porque falta tkinter), el cálculo sigue funcionando.

Las condiciones de cada carrera se cargan desde condiciones.json, de modo
que para agregar una carrera nueva no hace falta tocar el código.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

# Sexo del ejemplar: M = macho (potrillo / caballo), H = hembra (potranca / yegua)
SEXOS = {"M": "Macho", "H": "Hembra"}


@dataclass
class Condicion:
    """Condiciones de una carrera, tal como aparecen en el anticipo."""
    nombre: str
    distancia: int
    descripcion: str
    sexos: list                 # sexos admitidos, ej. ["M"] o ["M", "H"]
    edad_min: int
    edad_max: int | None        # None = "y más edad"
    victorias_min: int
    victorias_max: int
    peso_base: float
    # Peso según edad, ej. {5: 54, 6: 52} -> 5 años 54 kg, 6 y más 52 kg
    peso_por_edad: dict = field(default_factory=dict)
    descargo_hembras: float = 0.0          # "las yeguas descargarán 2 kilos"
    # Recargo según cantidad de victorias, ej. {3: 3} -> +3 kg a ganadoras de 3
    recargo_por_victorias: dict = field(default_factory=dict)
    recargo_clasico: float = 0.0           # kg por clásico ganado
    recargo_clasico_acumulativo: bool = False  # True = "por cada clásico"


@dataclass
class Caballo:
    """Datos del ejemplar que carga el usuario."""
    nombre: str
    edad: int
    sexo: str                    # "M" o "H"
    victorias: int = 0
    clasicos_ganados: int = 0


@dataclass
class Resultado:
    peso: float            # peso asignado al caballo: el que figura en el programa
    detalle: list          # pasos del cálculo, para mostrar y verificar a mano
    advertencias: list     # problemas de elegibilidad u otros avisos


def _claves_a_int(d):
    """JSON guarda las claves de los diccionarios como texto: las pasamos a int."""
    return {int(k): v for k, v in d.items()}


def cargar_condiciones(ruta=None):
    """Lee condiciones.json y devuelve una lista de Condicion."""
    if ruta is None:
        ruta = Path(__file__).with_name("condiciones.json")
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    condiciones = []
    for c in datos["carreras"]:
        c["peso_por_edad"] = _claves_a_int(c.get("peso_por_edad", {}))
        c["recargo_por_victorias"] = _claves_a_int(c.get("recargo_por_victorias", {}))
        condiciones.append(Condicion(**c))
    return condiciones


def verificar_elegibilidad(cond, caballo):
    """Devuelve una lista de motivos por los que el caballo NO entra en la carrera."""
    problemas = []
    if caballo.sexo not in cond.sexos:
        problemas.append(f"La carrera no admite {SEXOS[caballo.sexo].lower()}s.")
    if caballo.edad < cond.edad_min or (cond.edad_max is not None and caballo.edad > cond.edad_max):
        rango = f"{cond.edad_min}" if cond.edad_max == cond.edad_min else (
            f"{cond.edad_min} y más" if cond.edad_max is None else f"{cond.edad_min} a {cond.edad_max}")
        problemas.append(f"Edad {caballo.edad} fuera de la condición ({rango} años).")
    if not cond.victorias_min <= caballo.victorias <= cond.victorias_max:
        problemas.append(
            f"{caballo.victorias} victoria(s): la condición pide entre "
            f"{cond.victorias_min} y {cond.victorias_max}.")
    if caballo.clasicos_ganados > caballo.victorias:
        problemas.append("Tiene más clásicos ganados que victorias: revisar los datos.")
    return problemas


def peso_base_para(cond, edad):
    """Peso base de la carrera; si hay escala por edad, usa el tramo que corresponde."""
    if not cond.peso_por_edad:
        return cond.peso_base
    # Tomamos la edad más alta de la tabla que no supere la del caballo.
    # Ej. tabla {5: 54, 6: 52}: un caballo de 7 años usa el tramo de 6 (52 kg).
    tramos = [e for e in cond.peso_por_edad if e <= edad]
    return cond.peso_por_edad[max(tramos)] if tramos else cond.peso_base


def calcular_peso(cond, caballo):
    """Calcula el peso que debe cargar el caballo y explica cada paso."""
    detalle = []
    advertencias = verificar_elegibilidad(cond, caballo)

    peso = peso_base_para(cond, caballo.edad)
    detalle.append(f"Peso base: {peso:g} kg")

    if caballo.sexo == "H" and cond.descargo_hembras:
        peso -= cond.descargo_hembras
        detalle.append(f"Descargo hembras: -{cond.descargo_hembras:g} kg")

    recargo_v = cond.recargo_por_victorias.get(caballo.victorias, 0)
    if recargo_v:
        peso += recargo_v
        detalle.append(f"Recargo por {caballo.victorias} victorias: +{recargo_v:g} kg")

    if cond.recargo_clasico and caballo.clasicos_ganados > 0:
        veces = caballo.clasicos_ganados if cond.recargo_clasico_acumulativo else 1
        recargo_c = cond.recargo_clasico * veces
        peso += recargo_c
        detalle.append(f"Recargo por clásico ({caballo.clasicos_ganados} ganado/s): +{recargo_c:g} kg")

    detalle.append(f"PESO DEL PROGRAMA: {peso:g} kg")
    return Resultado(peso=peso, detalle=detalle, advertencias=advertencias)


# Uso rápido desde la terminal, sin interfaz gráfica:
#   python3 reglas.py
if __name__ == "__main__":
    for cond in cargar_condiciones():
        print(f"- {cond.nombre} ({cond.distancia} m): {cond.descripcion}")
    ejemplo = Caballo("Ejemplo", edad=3, sexo="M", victorias=2, clasicos_ganados=1)
    cond = next(c for c in cargar_condiciones() if c.nombre == "COLIFATO NOVO")
    r = calcular_peso(cond, ejemplo)
    print(f"\n{ejemplo.nombre} en {cond.nombre}:")
    print("\n".join("  " + linea for linea in r.detalle))
