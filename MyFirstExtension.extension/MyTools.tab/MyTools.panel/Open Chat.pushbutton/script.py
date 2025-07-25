import clr
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
clr.AddReference('System.Xaml')
clr.AddReference("System")

from System import Text, IO
from System.Net import WebRequest, WebResponse, HttpWebRequest, HttpWebResponse

from System.Windows import GridLength
from System.Windows import Controls
from System.Windows import GridLength

import System
from System.Windows import Application, Window, Thickness, HorizontalAlignment, VerticalAlignment, FontWeights
from System.Windows.Controls import Grid, TextBox, Button, Label, TabControl, TabItem, StackPanel, RowDefinition, ScrollBarVisibility, Orientation
from System.Windows.Media import SolidColorBrush, Color, Brushes

import System
import json

class NormasWindow(Window):
    def __init__(self, categoria, normas, actualizar_callback=None):
        self.Title = "Normas aplicadas - " + (categoria if categoria else "?")
        self.Width = 520
        self.Height = 660
        self.Background = SolidColorBrush(Color.FromRgb(245,245,245))

        panel = StackPanel()
        label = Label()
        label.Content = "Normas aplicadas para: " + (categoria if categoria else "?")
        label.FontSize = 14
        label.FontWeight = FontWeights.Bold
        label.Foreground = SolidColorBrush(Color.FromRgb(44,62,80))
        label.HorizontalContentAlignment = HorizontalAlignment.Center
        label.Margin = Thickness(0,10,0,10)

        self.normas_box = TextBox()
        self.normas_box.Text = "\r\n".join(normas)
        self.normas_box.IsReadOnly = True
        self.normas_box.VerticalScrollBarVisibility = ScrollBarVisibility.Visible
        self.normas_box.FontFamily = System.Windows.Media.FontFamily("Consolas")
        self.normas_box.FontSize = 12
        self.normas_box.Background = Brushes.White
        self.normas_box.Foreground = SolidColorBrush(Color.FromRgb(44,62,80))
        self.normas_box.Margin = Thickness(10)
        self.normas_box.Height = 460

        # Panel horizontal para input y boton
        update_panel = StackPanel()
        update_panel.Orientation = Orientation.Vertical # Vertical
        update_panel.HorizontalAlignment = HorizontalAlignment.Center
        update_panel.Margin = Thickness(0,10,0,0)

        # Label arriba del input
        contexto_label = Label()
        contexto_label.Content = "Ingrese contexto adicional (opcional):"
        contexto_label.FontSize = 11
        contexto_label.Foreground = SolidColorBrush(Color.FromRgb(44,62,80))
        contexto_label.VerticalAlignment = VerticalAlignment.Center
        contexto_label.Margin = Thickness(0,0,0,5)

        input_and_button_panel = StackPanel()
        input_and_button_panel.Orientation = 0 # Horizontal

        self.contexto_input = TextBox()
        self.contexto_input.Width = 200
        self.contexto_input.Height = 32
        self.contexto_input.FontFamily = System.Windows.Media.FontFamily("Segoe UI")
        self.contexto_input.FontSize = 11
        self.contexto_input.Margin = Thickness(0,0,10,0)
        self.contexto_input.Text = ""

        actualizar_btn = Button()
        actualizar_btn.Content = "Actualizar normas"
        actualizar_btn.Width = 150
        actualizar_btn.Height = 32
        actualizar_btn.Background = SolidColorBrush(Color.FromRgb(52,152,219))
        actualizar_btn.Foreground = Brushes.White
        actualizar_btn.FontWeight = FontWeights.Bold
        actualizar_btn.HorizontalAlignment = HorizontalAlignment.Center
        actualizar_btn.Margin = Thickness(0,0,0,0)
        if actualizar_callback:
            actualizar_btn.Click += lambda s, e: self.actualizar_normas(categoria, actualizar_callback)

        input_and_button_panel.Children.Add(self.contexto_input)
        input_and_button_panel.Children.Add(actualizar_btn)

        update_panel.Children.Add(contexto_label)
        update_panel.Children.Add(input_and_button_panel)

        panel.Children.Add(label)
        panel.Children.Add(self.normas_box)
        panel.Children.Add(update_panel)
        self.Content = panel

    def actualizar_normas(self, categoria, callback):
        contexto = self.contexto_input.Text.strip()
        # Limpiar la caja de texto antes de mostrar el nuevo contenido
        self.normas_box.Text = ""
        # Limpiar la memoria de normas por categoria
        if hasattr(self, 'parent') and hasattr(self.parent, 'normas_por_categoria'):
            self.parent.normas_por_categoria[categoria] = []
        elif callback and hasattr(callback, '__self__') and hasattr(callback.__self__, 'normas_por_categoria'):
            callback.__self__.normas_por_categoria[categoria] = []
        # Construir el JSON
        data = {
            "categoria": categoria,
            "contexto": contexto
        }
        json_str = json.dumps(data)
        resultado = self.enviar_actualizar_normas(json_str)
        # Procesar el resultado para mostrar los elementos como lista
        try:
            resultado_json = json.loads(resultado)
            elementos = resultado_json.get("elementos", [])
            elementos_texto = "\r\n".join(elementos)
            # Guardar los elementos recibidos en la memoria de normas por categoria
            if hasattr(self, 'parent') and hasattr(self.parent, 'normas_por_categoria'):
                self.parent.normas_por_categoria[categoria] = elementos
            elif callback and hasattr(callback, '__self__') and hasattr(callback.__self__, 'normas_por_categoria'):
                callback.__self__.normas_por_categoria[categoria] = elementos
        except Exception:
            elementos_texto = "[Respuesta]\r\n" + resultado

        self.normas_box.Text = "\r\n".join(elementos)

    def enviar_actualizar_normas(self, json_data):
        try:
            url = "http://localhost:8000/actualizarNormas"
            request = WebRequest.Create(url)
            request.Method = "POST"
            request.ContentType = "application/json"

            bytes_data = Text.Encoding.UTF8.GetBytes(json_data)
            request.ContentLength = bytes_data.Length

            stream = request.GetRequestStream()
            stream.Write(bytes_data, 0, bytes_data.Length)
            stream.Close()

            response = request.GetResponse()
            response_stream = response.GetResponseStream()
            reader = IO.StreamReader(response_stream)
            result = reader.ReadToEnd()
            reader.Close()

            return result
        except Exception as ex:  # type: ignore
            return "Error al enviar: " + str(ex)

class ChatBotWindow(Window):
    def __init__(self):
        self.Title = "Chatbot"
        self.Width = 540
        self.Height = 500
        self.Background = SolidColorBrush(Color.FromRgb(245,245,245))

        grid = Grid()
        grid.Margin = Thickness(10)

        # Define rows: 0-title, 1-tabs, 2-bottom
        row1 = RowDefinition()
        row1.Height = System.Windows.GridLength(50)
        row2 = RowDefinition()
        row2.Height = System.Windows.GridLength(1, System.Windows.GridUnitType.Star)
        row3 = RowDefinition()
        row3.Height = System.Windows.GridLength(70)
        grid.RowDefinitions.Add(row1)
        grid.RowDefinitions.Add(row2)
        grid.RowDefinitions.Add(row3)

        # Title
        title_label = Label()
        title_label.Content = "Verificador de normas del RNE"
        title_label.FontSize = 18
        title_label.FontWeight = FontWeights.Bold
        title_label.Foreground = SolidColorBrush(Color.FromRgb(44,62,80))
        title_label.HorizontalContentAlignment = HorizontalAlignment.Center
        title_label.Background = SolidColorBrush(Color.FromRgb(230,230,250))
        title_label.Height = 50
        Grid.SetRow(title_label, 0)
        grid.Children.Add(title_label)

        # Tabs
        self.tab_control = TabControl()
        self.tab_control.Margin = Thickness(0,0,0,0)
        self.categorias = ["Muros", "Puertas", "Ventanas", "Columnas", "Habitaciones"]  # <-- Agregada "Habitaciones"
        self.tab_boxes = {}
        for cat in self.categorias:
            tab = TabItem()
            tab.Header = cat
            box = TextBox()
            box.Text = "Sin elementos\r\n"
            box.IsReadOnly = True
            box.VerticalScrollBarVisibility = ScrollBarVisibility.Visible
            box.FontFamily = System.Windows.Media.FontFamily("Consolas")
            box.FontSize = 11
            box.Background = Brushes.White
            box.Foreground = SolidColorBrush(Color.FromRgb(44,62,80))
            tab.Content = box
            self.tab_control.Items.Add(tab)
            self.tab_boxes[cat] = box
        Grid.SetRow(self.tab_control, 1)
        grid.Children.Add(self.tab_control)

        # Bottom panel
        bottom_panel = StackPanel()
        bottom_panel.Orientation = 0 # Horizontal
        bottom_panel.HorizontalAlignment = HorizontalAlignment.Center  # <-- Centraliza los botones
        bottom_panel.VerticalAlignment = VerticalAlignment.Bottom
        bottom_panel.Margin = Thickness(0,0,0,10)

        self.send_button = Button()
        self.send_button.Content = "Verificar cumplimiento de normas"
        self.send_button.Width = 210
        self.send_button.Height = 34
        self.send_button.Background = SolidColorBrush(Color.FromRgb(52,152,219))
        self.send_button.Foreground = Brushes.White
        self.send_button.FontWeight = FontWeights.Bold
        self.send_button.Click += self.on_send_click
        self.send_button.Margin = Thickness(0,0,10,0)

        self.normas_button = Button()
        self.normas_button.Content = "Ver normas aplicadas"
        self.normas_button.Width = 180
        self.normas_button.Height = 34
        self.normas_button.Background = SolidColorBrush(Color.FromRgb(39,174,96))
        self.normas_button.Foreground = Brushes.White
        self.normas_button.FontWeight = FontWeights.Bold
        self.normas_button.Click += self.on_normas_click

        bottom_panel.Children.Add(self.send_button)
        bottom_panel.Children.Add(self.normas_button)
        Grid.SetRow(bottom_panel, 2)
        grid.Children.Add(bottom_panel)

        self.normas_por_categoria = {
            "Muros": [],
            "Puertas": [],
            "Ventanas": [],
            "Columnas": [],
            "Habitaciones": []
        }
        self.Content = grid

    def actualizar_normas_categoria(self, categoria, contexto=""):
        # Limpiar el input de ChatBotWindow cada vez que se actualizan normas
        self.input_box.Text = ""
        # Ejemplo: agregar una norma nueva, usando el contexto si se provee
        if categoria in self.normas_por_categoria:
            if contexto:
                self.normas_por_categoria[categoria].append("Norma actualizada con contexto: " + contexto)
            else:
                self.normas_por_categoria[categoria].append("Norma actualizada")
        return self.normas_por_categoria.get(categoria, ["No hay normas para esta categoria"])

    def on_normas_click(self, sender, event):
        selected_tab = self.tab_control.SelectedItem
        categoria = selected_tab.Header if selected_tab else None
        normas = self.normas_por_categoria.get(categoria, ["No hay normas para esta categoria"])
        win = NormasWindow(categoria, normas, self.actualizar_normas_categoria)
        win.ShowDialog()

    def on_send_click(self, sender, event):
        selected_tab = self.tab_control.SelectedItem
        if selected_tab:
            categoria = selected_tab.Header
            normas = self.normas_por_categoria.get(categoria, [])
            data = { "categoria": categoria, "normas": normas }
            json_str = json.dumps(data, ensure_ascii=False)
            resultado = self.enviar_a_verificar_normas(json_str)

            # Solo listar la respuesta en la pestana
            try:
                resultado_json = json.loads(resultado)
                elementos = resultado_json.get("elementos", [])
                elementos_texto = "\r\n".join(elementos)
            except Exception:
                elementos_texto = resultado

            self.tab_boxes[categoria].Text = elementos_texto

    def enviar_a_verificar_normas(self, json_data):
        try:
            url = "http://localhost:8000/verificarNormas"
            request = WebRequest.Create(url)
            request.Method = "POST"
            request.ContentType = "application/json"

            bytes_data = Text.Encoding.UTF8.GetBytes(json_data)
            request.ContentLength = bytes_data.Length

            stream = request.GetRequestStream()
            stream.Write(bytes_data, 0, bytes_data.Length)
            stream.Close()

            response = request.GetResponse()
            response_stream = response.GetResponseStream()
            reader = IO.StreamReader(response_stream)
            result = reader.ReadToEnd()
            reader.Close()

            return result

        except Exception as ex:  # type: ignore
            return "Error al enviar: " + str(ex)

win = ChatBotWindow()
win.ShowDialog()
