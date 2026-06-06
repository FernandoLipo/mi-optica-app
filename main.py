from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
import sqlite3
import os

try:
    from fpdf import FPDF
except Exception as e:
    import sys
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

            layout_principal = BoxLayout(orientation='vertical', padding=20, spacing=12)
            layout_principal.add_widget(Label(text="ADMINISTRADOR DE PRECIOS", size_hint_y=None, height=40, font_size=20))
            layout_principal.add_widget(Label(text="Código de Barras:", size_hint_y=None, height=20))
            self.input_codigo = TextInput(text="12345", multiline=False, size_hint_y=None, height=40)
            layout_principal.add_widget(self.input_codigo)

            boton_buscar = Button(text="BUSCAR / ESCANEAR", size_hint_y=None, height=45, background_color=(0.1, 0.6, 0.3, 1))
            boton_buscar.bind(on_release=self.buscar_producto)
            layout_principal.add_widget(boton_buscar)

            layout_principal.add_widget(Label(text="Nombre del Producto:", size_hint_y=None, height=20))
            self.input_nombre = TextInput(multiline=False, size_hint_y=None, height=40)
            layout_principal.add_widget(self.input_nombre)

            layout_principal.add_widget(Label(text="Precio ($):", size_hint_y=None, height=20))
            self.input_precio = TextInput(multiline=False, size_hint_y=None, height=40)
            layout_principal.add_widget(self.input_precio)

            self.lbl_estado = Label(text="Ingrese un código para empezar.", size_hint_y=None, height=30, color=(1, 1, 0, 1))
            layout_principal.add_widget(self.lbl_estado)

            layout_botones = BoxLayout(orientation='horizontal', size_hint_y=None, height=55, spacing=10)
            
            self.boton_guardar = Button(text="GUARDAR", background_color=(0.1, 0.5, 0.8, 1))
            self.boton_guardar.bind(on_release=self.guardar_producto)
            layout_botones.add_widget(self.boton_guardar)

            boton_pdf = Button(text="EXPORTAR PDF", background_color=(0.7, 0.2, 0.2, 1))
            boton_pdf.bind(on_release=self.generar_pdf)
            layout_botones.add_widget(boton_pdf)

            layout_principal.add_widget(layout_botones)
            return layout_principal

        except Exception as e:
            layout_error = BoxLayout(orientation='vertical', padding=20)
            layout_error.add_widget(Label(text="⚠️ ERROR DE ARRANQUE EN EL TELÉFONO:", size_hint_y=None, height=40, color=(1,0,0,1)))
            scroll = ScrollView()
            lbl_detalle = Label(text=str(e), size_hint_y=None, font_size=14)
            lbl_detalle.bind(texture_size=lbl_detalle.setter('size'))
            scroll.add_widget(lbl_detalle)
            layout_error.add_widget(scroll)
            return layout_error

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
                self.lbl_estado.text = "Error: Librería FPDF no disponible."
                return

            self.cursor.execute("SELECT codigo, nombre, precio FROM productos ORDER BY nombre ASC")
            todos_los_productos = self.cursor.fetchall()

            if not todos_los_productos:
                self.lbl_estado.text = "No hay productos para exportar."
                return

            try:
                ruta_pdf = "/sdcard/Download/Lista_de_Precios.pdf"
                pdf = FPDF(orientation="P", unit="mm", format="A4")
            except:
                ruta_pdf = os.path.join(self.user_data_dir, "Lista_de_Precios.pdf")
                pdf = FPDF(orientation="P", unit="mm", format="A4")
                
            pdf.add_page()
            pdf.set_margins(15, 15, 15)
            
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, text="LISTA GENERAL DE PRECIOS", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(8)

            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(13, 71, 161)
            pdf.set_text_color(255, 255, 255)
            
            pdf.cell(40, 10, text="CÓDIGO", border=1, align="C", fill=True)
            pdf.cell(100, 10, text="DESCRIPCIÓN DEL PRODUCTO", border=1, align="L", fill=True)
            pdf.cell(40, 10, text="PRECIO", border=1, align="R", fill=True, new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(0, 0, 0)
            
            for prod in todos_los_productos:
                precio_formateado = f"${prod[2]:,.2f}"
                pdf.set_fill_color(245, 245, 245)
                pdf.cell(40, 8, text=str(prod[0]), border=1, align="C", fill=True)
                pdf.cell(100, 8, text=str(prod[1]), border=1, align="L", fill=True)
                pdf.cell(40, 8, text=precio_formateado, border=1, align="R", fill=True, new_x="LMARGIN", new_y="NEXT")

            pdf.output(ruta_pdf)
            self.lbl_estado.text = "¡PDF generado con éxito!"
            
        except Exception as e:
            self.lbl_estado.text = f"Error al crear PDF: {str(e)}"

    def on_stop(self):
        try:
            self.conexion.close()
        except:
            pass

if __name__ == "__main__":
    MiAppEscanner().run()