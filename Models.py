# controllers.py
import os
import subprocess
import platform
import time
import logging
import plyer
import keyboard
from tkinter import messagebox
from models import SessionLocal, Carpeta, Etiqueta, Alerta, Historial

class CarpetaController:
    def __init__(self):
        self.session = SessionLocal()
        self.configurar_atajos()

    def configurar_atajos(self):
        # Limpiamos atajos anteriores
        keyboard.unhook_all()
        carpetas = self.session.query(Carpeta).all()
        for carpeta in carpetas:
            self.configurar_atajo(carpeta)

    def configurar_atajo(self, carpeta):
        try:
            keyboard.add_hotkey(
                carpeta.atajo, 
                lambda ruta=carpeta.ruta: self.abrir_carpeta_por_ruta(ruta)
            )
        except Exception as e:
            raise e

    def agregar_carpeta(self, nombre, ruta, atajo, tipo, etiquetas):
        # Validar si el atajo ya existe
        if self.session.query(Carpeta).filter_by(atajo=atajo).first():
            raise ValueError("El atajo ya está en uso.")

        nueva_carpeta = Carpeta(nombre, ruta, atajo, tipo)

        # Agregar etiquetas
        for et in etiquetas:
            etiqueta_obj = self.session.query(Etiqueta).filter_by(nombre=et).first()
            if not etiqueta_obj:
                etiqueta_obj = Etiqueta(et)
            nueva_carpeta.etiquetas.append(etiqueta_obj)

        self.session.add(nueva_carpeta)
        self.session.commit()

        # Reconfigurar atajos
        self.configurar_atajo(nueva_carpeta)

    def abrir_carpeta_por_ruta(self, ruta):
        if os.path.exists(ruta):
            try:
                if platform.system() == 'Windows':
                    os.startfile(ruta)
                elif platform.system() == 'Darwin':
                    subprocess.Popen(['open', ruta])
                else:
                    subprocess.Popen(['xdg-open', ruta])
                
                # Actualizar historial
                carpeta = self.session.query(Carpeta).filter_by(ruta=ruta).first()
                if carpeta:
                    historial = Historial(ruta)
                    carpeta.historial.append(historial)
                    self.session.commit()

                # Notificación con plyer
                plyer.notification.notify(
                    title="Acceso Abierto",
                    message=f"Se ha abierto '{carpeta.nombre}'",
                    timeout=5
                )
            except Exception as e:
                logging.error(f"Error al abrir: {e}")
                messagebox.showerror("Error", f"Error al abrir: {e}")
        else:
            logging.error(f"La ruta '{ruta}' no existe.")
            messagebox.showerror("Error", f"La ruta '{ruta}' no existe.")

    # Continúa con tus métodos: editar_carpeta, eliminar_carpeta, agregar_alerta, etc.
    # ...
