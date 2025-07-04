

import os
import subprocess
import platform
import time
import logging
import keyboard
import plyer
from tkinter import messagebox
from models import SessionLocal, Carpeta, Etiqueta, Alerta, Historial

class CarpetaController:
    def __init__(self):
        self.session = SessionLocal()
        self.configurar_atajos()

    # ---------------------------------------------------------
    # GESTIÓN DE ATAJOS
    # ---------------------------------------------------------
    def configurar_atajos(self):
        """
        Desengancha todos los atajos previos y vuelve a cargar
        cada atajo para las carpetas registradas.
        """
        keyboard.unhook_all()
        carpetas = self.session.query(Carpeta).all()
        for carpeta in carpetas:
            self.configurar_atajo(carpeta)

    def configurar_atajo(self, carpeta):
        """
        Asigna un atajo de teclado a la carpeta/archivo proporcionado.
        """
        try:
            keyboard.add_hotkey(
                carpeta.atajo, 
                lambda ruta=carpeta.ruta: self.abrir_carpeta_por_ruta(ruta)
            )
        except Exception as e:
            raise e

    # ---------------------------------------------------------
    # GESTIÓN DE CARPETAS
    # ---------------------------------------------------------
    def agregar_carpeta(self, nombre, ruta, atajo, tipo, etiquetas):
        """
        Crea una nueva carpeta (o archivo) en la base de datos y asigna
        las etiquetas correspondientes. Verifica si el atajo está en uso.
        """
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

        # Reconfigurar el atajo para que funcione de inmediato
        self.configurar_atajo(nueva_carpeta)

    def abrir_carpeta_por_ruta(self, ruta):
        """
        Abre la carpeta/archivo según el sistema operativo. Si la ruta
        existe, registra el historial y lanza una notificación.
        """
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

    def abrir_carpeta(self, carpeta):
        """
        Atajo adicional para abrir por objeto `carpeta`.
        """
        self.abrir_carpeta_por_ruta(carpeta.ruta)

    def eliminar_carpeta(self, carpeta):
        """
        Elimina la carpeta seleccionada de la base de datos,
        y reconfigura los atajos.
        """
        self.session.delete(carpeta)
        self.session.commit()
        self.configurar_atajos()

    def actualizar_carpeta(self, carpeta, nuevo_nombre, nueva_ruta, nuevo_atajo, nuevo_tipo, nuevas_etiquetas):
        """
        Actualiza la información de una carpeta/archivo existente,
        incluyendo su nombre, ruta, atajo, tipo y etiquetas.
        """
        # Verificar conflictos de atajos
        if nuevo_atajo != carpeta.atajo and self.session.query(Carpeta).filter_by(atajo=nuevo_atajo).first():
            raise ValueError("El atajo ya está en uso.")

        carpeta.nombre = nuevo_nombre
        carpeta.ruta = nueva_ruta
        carpeta.atajo = nuevo_atajo
        carpeta.tipo = nuevo_tipo

        # Actualizar etiquetas
        carpeta.etiquetas.clear()
        for etiqueta_nombre in nuevas_etiquetas:
            etiqueta = self.session.query(Etiqueta).filter_by(nombre=etiqueta_nombre).first()
            if not etiqueta:
                etiqueta = Etiqueta(etiqueta_nombre)
            carpeta.etiquetas.append(etiqueta)

        self.session.commit()
        self.configurar_atajo(carpeta)

    # ---------------------------------------------------------
    # GESTIÓN DE ALERTAS
    # ---------------------------------------------------------
    def agregar_alerta(self, carpeta, timestamp, mensaje, recurrencia):
        """
        Crea una nueva alerta para la carpeta especificada, con
        la fecha/hora de activación (timestamp) y la recurrencia.
        """
        nueva_alerta = Alerta(timestamp, mensaje, recurrencia)
        carpeta.alertas.append(nueva_alerta)
        self.session.commit()

    def verificar_alertas(self):
        """
        Revisa continuamente si hay alertas cuyo timestamp
        ya ha llegado o pasado, y lanza la notificación.
        Maneja la recurrencia: diaria, semanal, mensual o ninguna.
        """
        while True:
            ahora = int(time.time())
            alertas = self.session.query(Alerta).filter(Alerta.timestamp <= ahora).all()
            for alerta in alertas:
                carpeta = alerta.carpeta
                mensaje = alerta.mensaje or f"Es hora de abrir '{carpeta.nombre}'"
                plyer.notification.notify(
                    title="Alerta Programada",
                    message=mensaje,
                    timeout=10
                )
                # Manejar recurrencia
                if alerta.recurrencia == 'diaria':
                    alerta.timestamp += 86400  # 24 horas
                elif alerta.recurrencia == 'semanal':
                    alerta.timestamp += 604800  # 7 días
                elif alerta.recurrencia == 'mensual':
                    alerta.timestamp += 2629746  # 1 mes aproximado
                else:
                    # Si no hay recurrencia, se elimina la alerta
                    self.session.delete(alerta)
                self.session.commit()
            # Revisa cada cierto tiempo (60 seg)
            time.sleep(60)

    def eliminar_alerta(self, alerta):
        """
        Elimina la alerta dada de la base de datos.
        """
        self.session.delete(alerta)
        self.session.commit()

    def obtener_alertas(self):
        """
        Devuelve todas las alertas de la base de datos.
        """
        return self.session.query(Alerta).all()

    # ---------------------------------------------------------
    # GESTIÓN DE CONSULTAS DE CARPETAS
    # ---------------------------------------------------------
    def obtener_carpetas(self, filtro_nombre='', filtro_etiqueta='Todas', filtro_tipo='Todos', orden='Nombre', ascendente=True):
        """
        Retorna la lista de carpetas filtradas por nombre, etiqueta y tipo,
        además de un criterio de orden ('Nombre' o 'Ruta', etc.).
        """
        query = self.session.query(Carpeta)

        # Filtrar por nombre
        if filtro_nombre:
            query = query.filter(Carpeta.nombre.contains(filtro_nombre))

        # Filtrar por etiqueta
        if filtro_etiqueta != 'Todas':
            query = query.join(Carpeta.etiquetas).filter(Etiqueta.nombre == filtro_etiqueta)

        # Filtrar por tipo
        if filtro_tipo != 'Todos':
            query = query.filter(Carpeta.tipo == filtro_tipo)

        # Ordenar
        if orden == 'Nombre':
            orden_campo = Carpeta.nombre
        elif orden == 'Ruta':
            orden_campo = Carpeta.ruta
        else:
            orden_campo = Carpeta.nombre  # Valor por defecto

        query = query.order_by(orden_campo.asc() if ascendente else orden_campo.desc())

        return query.all()

    # ---------------------------------------------------------
    # GESTIÓN DE ETIQUETAS
    # ---------------------------------------------------------
    def obtener_etiquetas(self):
        """
        Devuelve todas las etiquetas de la base de datos.
        """
        return self.session.query(Etiqueta).all()

    def agregar_etiqueta(self, nombre):
        """
        Crea una nueva etiqueta si no existe.
        """
        etiqueta = self.session.query(Etiqueta).filter_by(nombre=nombre).first()
        if etiqueta:
            raise ValueError("La etiqueta ya existe.")
        nueva_etiqueta = Etiqueta(nombre)
        self.session.add(nueva_etiqueta)
        self.session.commit()

    def eliminar_etiqueta(self, etiqueta):
        """
        Elimina la etiqueta dada de la base de datos.
        """
        self.session.delete(etiqueta)
        self.session.commit()
