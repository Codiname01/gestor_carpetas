import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from controllers import CarpetaController
from models import Base, engine

# Crea las tablas al inicio
Base.metadata.create_all(engine)

class CarpetaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Carpetas y Archivos v11.0")
        self.controller = CarpetaController()

        # Configuración inicial de la interfaz
        self.crear_interfaz()

    def crear_interfaz(self):
        """
        Configura la interfaz gráfica, incluyendo menús y widgets.
        """
        menubar = tk.Menu(self.root)

        # Menú Archivo
        archivo_menu = tk.Menu(menubar, tearoff=0)
        archivo_menu.add_command(label="Agregar Carpeta/Archivo", command=self.agregar_carpeta)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=archivo_menu)

        self.root.config(menu=menubar)

        # Agregar otros widgets (ejemplo: Treeview)
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True)

        self.treeview = ttk.Treeview(frame, columns=("Ruta", "Atajo"), show="headings")
        self.treeview.heading("Ruta", text="Ruta")
        self.treeview.heading("Atajo", text="Atajo")
        self.treeview.pack(fill="both", expand=True)

    def agregar_carpeta(self):
        """
        Abre una ventana para agregar una carpeta y llama al controller.
        """
        # Aquí podrías implementar una ventana emergente para pedir datos al usuario.
        messagebox.showinfo("Agregar Carpeta", "Función no implementada aún.")

if __name__ == "__main__":
    # Inicializa la aplicación usando TkinterDnD para arrastrar y soltar
    root = TkinterDnD.Tk()
    app = CarpetaApp(root)
    root.mainloop()
