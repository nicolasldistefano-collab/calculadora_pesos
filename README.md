# Calculadora de Pesos – Hipódromo

Calcula el peso que debe cargar cada ejemplar según las condiciones de la carrera
(peso base, peso por edad, descargo de hembras y recargos por victorias y por clásicos) y avisa si un caballo no es elegible.
Pensada para correr en equipos con pocos recursos (Lubuntu).

## Archivos

| Archivo | Qué hace |
|---|---|
| `reglas.py` | Lógica del cálculo. No depende de la interfaz. |
| `condiciones.json` | Condiciones de las carreras (anticipo HSI 1/11). Se editan sin tocar código. |
| `app.py` | Interfaz gráfica con tkinter. |

## Instalación en Lubuntu / Ubuntu

```bash
sudo apt update
sudo apt install -y python3 python3-tk
cd calculadora_pesos
python3 app.py              # abrir la calculadora
```

Sin entorno gráfico: `python3 reglas.py` lista las carreras y muestra un cálculo de ejemplo.

## Agregar una carrera

Copiar un bloque de `condiciones.json` y editar sus campos:
`sexos` (`"M"`, `"H"`), `edad_min`/`edad_max` (`null` = "y más edad"),
`victorias_min`/`victorias_max`, `peso_base`, `peso_por_edad`, `descargo_hembras`,
`recargo_por_victorias`, `recargo_clasico`, `recargo_clasico_acumulativo`.

## Limitaciones

No calcula handicaps (los asigna el handicapper) ni la escala de "peso por edad" de los
clásicos, porque esas tablas no figuran en el anticipo.

- **Video de presentación:** [Ver en YouTube](https://www.youtube.com/watch?v=wuaF_YRsxBU)
