"""
app.py - Interfaz gráfica de la Calculadora de Pesos.

Usa tkinter, que viene con Python y consume muy poca memoria, ideal para
equipos con pocos recursos (Lubuntu). En Ubuntu/Lubuntu hay que instalarlo
aparte:   sudo apt install python3-tk

Ejecutar:  python3 app.py
"""

import csv
import sys

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ModuleNotFoundError:
    # Error típico en Lubuntu recién instalado: Python está, tkinter no.
    print("ERROR: falta el módulo tkinter.\n"
          "Instalalo con:  sudo apt install python3-tk\n"
          "Mientras tanto podés probar el cálculo con:  python3 reglas.py")
    sys.exit(1)

from reglas import Caballo, SEXOS, cargar_condiciones, calcular_peso


class CalculadoraApp:
    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Calculadora de Pesos - Hipódromo")
        self.raiz.geometry("900x600")

        self.condiciones = cargar_condiciones()
        self.caballos = []   # lista de Caballo cargados para la carrera elegida

        self._armar_selector_carrera()
        self._armar_formulario()
        self._armar_tabla()
        self._armar_detalle()
        self.on_cambio_carrera()

    # ---------- Construcción de la ventana ----------

    def _armar_selector_carrera(self):
        marco = ttk.LabelFrame(self.raiz, text="Carrera", padding=8)
        marco.pack(fill="x", padx=10, pady=(10, 5))

        nombres = [f"{c.nombre} - {c.distancia} m" for c in self.condiciones]
        self.combo_carrera = ttk.Combobox(marco, values=nombres, state="readonly", width=45)
        self.combo_carrera.current(0)
        self.combo_carrera.bind("<<ComboboxSelected>>", self.on_cambio_carrera)
        self.combo_carrera.pack(anchor="w")

        self.lbl_condicion = ttk.Label(marco, wraplength=850, foreground="#444")
        self.lbl_condicion.pack(anchor="w", pady=(5, 0))

    def _armar_formulario(self):
        marco = ttk.LabelFrame(self.raiz, text="Datos del ejemplar", padding=8)
        marco.pack(fill="x", padx=10, pady=5)

        self.var_nombre = tk.StringVar()
        self.var_edad = tk.IntVar(value=3)
        self.var_sexo = tk.StringVar(value="Macho")
        self.var_victorias = tk.IntVar(value=0)
        self.var_clasicos = tk.IntVar(value=0)

        campos = [
            ("Nombre", ttk.Entry(marco, textvariable=self.var_nombre, width=22)),
            ("Edad", ttk.Spinbox(marco, from_=2, to=12, textvariable=self.var_edad, width=5)),
            ("Sexo", ttk.Combobox(marco, values=list(SEXOS.values()), textvariable=self.var_sexo,
                                  state="readonly", width=8)),
            ("Victorias", ttk.Spinbox(marco, from_=0, to=30, textvariable=self.var_victorias, width=5)),
            ("Clásicos ganados", ttk.Spinbox(marco, from_=0, to=30, textvariable=self.var_clasicos, width=5)),
        ]
        for col, (texto, widget) in enumerate(campos):
            ttk.Label(marco, text=texto).grid(row=0, column=col, sticky="w", padx=4)
            widget.grid(row=1, column=col, sticky="w", padx=4)

        ttk.Button(marco, text="Calcular y agregar", command=self.on_agregar).grid(
            row=1, column=len(campos), padx=8)

    def _armar_tabla(self):
        marco = ttk.Frame(self.raiz)
        marco.pack(fill="both", expand=True, padx=10, pady=5)

        columnas = ("nombre", "edad", "sexo", "vict", "clas", "peso", "obs")
        titulos = ("Nombre", "Edad", "Sexo", "Vict.", "Clás.", "Peso programa (kg)", "Observaciones")
        anchos = (180, 50, 70, 50, 50, 130, 320)
        self.tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=10)
        for col, titulo, ancho in zip(columnas, titulos, anchos):
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("nombre", "obs") else "center")
        self.tabla.tag_configure("no_elegible", background="#ffd6d6")
        self.tabla.bind("<<TreeviewSelect>>", self.on_seleccion)
        self.tabla.pack(side="left", fill="both", expand=True)

        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")

        botones = ttk.Frame(self.raiz)
        botones.pack(fill="x", padx=10)
        ttk.Button(botones, text="Eliminar seleccionado", command=self.on_eliminar).pack(side="left")
        ttk.Button(botones, text="Limpiar lista", command=self.on_limpiar).pack(side="left", padx=5)
        ttk.Button(botones, text="Exportar CSV", command=self.on_exportar).pack(side="right")

    def _armar_detalle(self):
        marco = ttk.LabelFrame(self.raiz, text="Detalle del cálculo (seleccioná un ejemplar)", padding=8)
        marco.pack(fill="x", padx=10, pady=(5, 10))
        self.txt_detalle = tk.Text(marco, height=6, state="disabled", font=("monospace", 10))
        self.txt_detalle.pack(fill="x")

    # ---------- Lógica de la interfaz ----------

    def carrera_actual(self):
        return self.condiciones[self.combo_carrera.current()]

    def on_cambio_carrera(self, _evento=None):
        """Al cambiar de carrera se muestran sus condiciones y se recalcula todo."""
        self.lbl_condicion.config(text=self.carrera_actual().descripcion)
        self.refrescar_tabla()

    def on_agregar(self):
        try:
            caballo = Caballo(
                nombre=self.var_nombre.get().strip().upper(),
                edad=self.var_edad.get(),
                sexo="M" if self.var_sexo.get() == "Macho" else "H",
                victorias=self.var_victorias.get(),
                clasicos_ganados=self.var_clasicos.get(),
            )
        except tk.TclError:
            messagebox.showerror("Dato inválido", "Revisá que edad, victorias y clásicos sean números.")
            return
        if not caballo.nombre:
            messagebox.showwarning("Falta el nombre", "Ingresá el nombre del ejemplar.")
            return
        self.caballos.append(caballo)
        self.var_nombre.set("")
        self.refrescar_tabla()

    def refrescar_tabla(self):
        self.tabla.delete(*self.tabla.get_children())
        cond = self.carrera_actual()
        for i, cab in enumerate(self.caballos):
            r = calcular_peso(cond, cab)
            obs = "NO ELEGIBLE: " + " ".join(r.advertencias) if r.advertencias else "OK"
            self.tabla.insert("", "end", iid=str(i), values=(
                cab.nombre, cab.edad, SEXOS[cab.sexo], cab.victorias, cab.clasicos_ganados,
                f"{r.peso:g}", obs),
                tags=("no_elegible",) if r.advertencias else ())
        self.mostrar_detalle("")

    def on_seleccion(self, _evento=None):
        sel = self.tabla.selection()
        if not sel:
            return
        cab = self.caballos[int(sel[0])]
        r = calcular_peso(self.carrera_actual(), cab)
        lineas = [cab.nombre] + ["  " + l for l in r.detalle]
        lineas += ["  ATENCIÓN: " + a for a in r.advertencias]
        self.mostrar_detalle("\n".join(lineas))

    def mostrar_detalle(self, texto):
        self.txt_detalle.config(state="normal")
        self.txt_detalle.delete("1.0", "end")
        self.txt_detalle.insert("1.0", texto)
        self.txt_detalle.config(state="disabled")

    def on_eliminar(self):
        sel = self.tabla.selection()
        if sel:
            del self.caballos[int(sel[0])]
            self.refrescar_tabla()

    def on_limpiar(self):
        if self.caballos and messagebox.askyesno("Limpiar", "¿Borrar todos los ejemplares de la lista?"):
            self.caballos.clear()
            self.refrescar_tabla()

    def on_exportar(self):
        if not self.caballos:
            messagebox.showinfo("Exportar", "No hay ejemplares para exportar.")
            return
        cond = self.carrera_actual()
        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile=f"pesos_{cond.nombre.replace(' ', '_')}.csv",
            filetypes=[("CSV", "*.csv")])
        if not ruta:
            return
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Carrera", "Nombre", "Edad", "Sexo", "Victorias", "Clasicos",
                        "Peso programa", "Observaciones"])
            for cab in self.caballos:
                r = calcular_peso(cond, cab)
                w.writerow([cond.nombre, cab.nombre, cab.edad, SEXOS[cab.sexo], cab.victorias,
                            cab.clasicos_ganados, f"{r.peso:g}",
                            " ".join(r.advertencias) or "OK"])
        messagebox.showinfo("Exportar", f"Archivo guardado en:\n{ruta}")


if __name__ == "__main__":
    raiz = tk.Tk()
    CalculadoraApp(raiz)
    raiz.mainloop()
