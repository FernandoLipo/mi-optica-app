from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.camera import Camera
from kivy.metrics import dp
import sqlite3
import os

# Forzamos la importación correcta y compatible de la librería moderna de PDF
try:
    from fpdf import FPDF
except Exception as e:
    FPDF = None

class MiAppEscanner(App):
    def build(self):
        try:
            ruta_app = self.user_data_dir
            self.base_datos = os.path.join(ruta_app, "precios.db")
            
            self.conexion = sqlite3.connect(self.base_datos)
            self.cursor = self.conexion.cursor()
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    codigo TEXT PRIMARY KEY,
                    nombre TEXT,
                    precio REAL
                )
            """)
            self.conexion.commit()

            # Diseño principal con tipografías y espaciados adaptados (dp)
            layout_principal = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
            
            # Título más imponente
            layout_principal.add_widget(Label(text="ADMINISTRADOR DE PRECIOS", size_hint_y=None, height=dp(45), font_size='22sp', bold=True))
            
            # SECCIÓN CÁMARA: Espacio para el visor en vivo integrado en la interfaz
            self.visor_camara = Camera(play=False, resolution=(640, 480), size_hint_y=None, height=dp(180))
            layout_principal.add_widget(self.visor_camara)

            # Contenedor del código de barras
            layout_principal.add_widget(Label(text="Código de Barras:", size_hint_y=None, height=dp(20), halign='left'))
            self.input_codigo = TextInput(text="", multiline=False, size_hint_y=None, height=dp(48), font_size='18sp', input_type='number')
            layout_principal.add_widget(self.input_codigo)

            # Botón Buscar / Activar escáner (Más grueso y fácil de presionar)
            self.boton_buscar = Button(text="ENCENDER / APAGAR CÁMARA", size_hint_y=None, height=dp(50), font_size='16sp', bold=True, background_color=(0.1, 0.6, 0.3, 1))
            self.boton_buscar.bind(on_release=self.alternar_camara)
            layout_principal.add_widget(self.boton_buscar)

            # Formulario de carga
            layout_principal.add_widget(Label(text="Nombre del Producto:", size_hint_y=None, height=dp(20)))
            self.input_nombre = TextInput(multiline=False, size_hint_y=None, height=dp(48), font_size='18sp')
            layout_principal.add_widget(self.input_nombre)

            layout_principal.add_widget(Label(text="Precio ($):", size_hint_y=None, height=dp(20)))
            self.input_precio = TextInput(multiline=False, size_hint_y=None, height=dp(48), font_size='18sp', input_type='number')
            layout_principal.add_widget(self.input_precio)

            # Barra de estado visible
            self.lbl_estado = Label(text="Ingrese un código para empezar.", size_hint_y=None, height=dp(35), color=(1, 1, 0, 1), font_size='15sp')
            layout_principal.add_widget(self.lbl_estado)

            # Botonera inferior ampliada
            layout_botones = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=dp(12))
            
            self.boton_guardar = Button(text="GUARDAR", font_size='16sp', bold=True, background_color=(0.1, 0.5, 0.8, 1))
            self.boton_guardar.bind(on_release=self.guardar_producto)
            layout_botones.add_widget(self.boton_guardar)

            boton_pdf = Button(text="EXPORTAR PDF", font_size='16sp', bold=True, background_color=(0.7, 0.2, 0.2, 1))
            boton_pdf.bind(on_release=self.generar_pdf)
            layout_botones.add_widget(boton_pdf)

            layout_principal.add_widget(layout_botones)
            return layout_principal

        except Exception as e:
            layout_error = BoxLayout(orientation='vertical', padding=dp(20))
            layout_error.add_widget(Label(text="⚠️ ERROR DE ARRANQUE EN EL TELÉFONO:", size_hint_y=None, height=dp(40), color=(1,0,0,1)))
            scroll = ScrollView()
            lbl_detalle = Label(text=str(e), size_hint_y=None, font_size=14)
            lbl_detalle.bind(texture_size=lbl_detalle.setter('size'))
            scroll.add_widget(lbl_detalle)
            layout_error.add_widget(scroll)
            return layout_error

    def alternar_camara(self, instance):
        # Enciende o apaga el hardware de la cámara del celular con un clic
        if self.visor_camara.play:
            self.visor_camara.play = False
            self.lbl_estado.text = "Cámara apagada."
        else:
            self.visor_camara.play = True
            self.lbl_estado.text = "Cámara encendida. Apunte al código."

    def buscar_producto(self, instance):
        codigo = self.input_codigo.text.strip()
        if not codigo:
            self.lbl_estado.text = "Por favor, escriba o escanee un código."
            return
        self.cursor.execute("SELECT nombre, precio FROM productos WHERE codigo = ?", (codigo,))
        resultado = self.cursor.fetchone()
        if resultado:
            nombre, precio = resultado
            self.input_nombre.text = nombre
            self.input_precio.text = str(precio)
            self.lbl_estado.text = "Producto encontrado. Puede editarlo."
        else:
            self.input_nombre.text = ""
            self.input_precio.text = ""
            self.lbl_estado.text = "Código NUEVO. Ingrese datos y guarde."

    def guardar_producto(self, instance):
        codigo = self.input_codigo.text.strip()
        nombre = self.input_nombre.text.strip()
        precio_texto = self.input_precio.text.strip()

        if not codigo or not nombre or not precio_texto:
            self.lbl_estado.text = "Error: Todos los campos son obligatorios."
            return
        try:
            precio = float(precio_texto)
        except ValueError:
            self.lbl_estado.text = "Error: El precio debe ser un número."
            return

        self.cursor.execute("INSERT OR REPLACE INTO productos VALUES (?, ?, ?)", (codigo, nombre, precio))
        self.conexion.commit()
        self.lbl_estado.text = f"¡Producto {codigo} guardado con éxito!"

    def generar_pdf(self, instance):
        try:
            if FPDF is None:
                self.lbl_estado.text = "Error: Librería FPDF no disponible de origen."
                return

            self.cursor.execute("SELECT codigo, nombre, precio FROM productos ORDER BY nombre ASC")
            todos_los_productos = self.cursor.fetchall()

            if not todos_los_productos:
                self.lbl_estado.text = "No hay productos para exportar."
                return

            # Forzamos almacenamiento local seguro dentro de las carpetas internas del entorno Android
            ruta_pdf = os.path.join(self.user_data_dir, "Lista_de_Precios.pdf")
            
            # Sintaxis corregida compatible al 100% con fpdf2 móvil
            pdf = FPDF(orientation="P", unit="mm", format="A4")
            pdf.add_page()
            pdf.set_margins(15, 15, 15)
            
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, text="LISTA GENERAL DE PRECIOS", align="C")
            pdf.ln(12)

            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(13, 71, 161)
            pdf.set_text_color(255, 255, 255)
            
            pdf.cell(40, 10, text="CÓDIGO", border=1, align="C", fill=True)
            pdf.cell(100, 10, text="DESCRIPCIÓN DEL PRODUCTO", border=1, align="L", fill=True)
            pdf.cell(40, 10, text="PRECIO", border=1, align="R", fill=True)
            pdf.ln(10)

            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(0, 0, 0)
            
            for prod in todos_los_productos:
                precio_formateado = f"${prod[2]:,.2f}"
                pdf.set_fill_color(245, 245, 245)
                pdf.cell(40, 8, text=str(prod[0]), border=1, align="C", fill=True)
                pdf.cell(100, 8, text=str(prod[1]), border=1, align="L", fill=True)
                pdf.cell(40, 8, text=precio_formateado, border=1, align="R", fill=True)
                pdf.ln(8)

            pdf.output(ruta_pdf)
            self.lbl_estado.text = f"PDF guardado en: {ruta_pdf}"
            
        except Exception as e:
            self.lbl_estado.text = f"Error al crear PDF: {str(e)}"

    def on_stop(self):
        try:
            self.conexion.close()
        except:
            pass

if __name__ == "__main__":
    MiAppEscanner().run()
