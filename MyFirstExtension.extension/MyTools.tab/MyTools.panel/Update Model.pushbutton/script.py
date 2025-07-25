#! python3
import os
from pyrevit import revit, DB
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, BuiltInParameter
import csv
import io
from urllib.request import Request, urlopen
import mimetypes
import uuid
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Wall, BuiltInParameter
from RevitServices.Persistence import DocumentManager
from Autodesk.Revit.DB import *

# URL del endpoint Flask para subir CSV
url = 'http://127.0.0.1:8000/upload_csv'

# Para pyRevit: usar __revit__ y __context__ si es necesario
doc = __revit__.ActiveUIDocument.Document  # Reemplazo de DocumentManager en pyRevit

rooms = FilteredElementCollector(__revit__.ActiveUIDocument.Document).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()
print(f"Rooms encontrados: {len(rooms.ToElements())}")

# Clase para almacenar y mostrar información
class ModeloRNE:
    def __init__(self, doc):
        self.doc = doc
        self.ambientes = []

    def cargar_ambientes(self):
        rooms = FilteredElementCollector(self.doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()
        
        print("🔍 Buscando Rooms...")

        for room in rooms:
            try:
                nombre = room.Name or "Sin nombre"

                nivel = room.Level.Name if room.Level else "Sin nivel"
                area = round(room.Area / 10.7639, 2)  # pies² a m²

                altura_param = room.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET)
                altura = round(altura_param.AsDouble() * 0.3048, 2) if altura_param else 0.0

                self.ambientes.append((nombre, nivel, area, altura, nombre))  # usamos 'nombre' como uso
                print(f"✅ Room: {nombre}, Nivel: {nivel}, Área: {area} m², Altura: {altura} m")

            except Exception as e:
                print(f"⚠️ Error procesando un Room: {e}")

# Crear instancia y ejecutar
modelo = ModeloRNE(doc)
modelo.cargar_ambientes()
doc = revit.doc

categorias_clave = {
    "Muros": BuiltInCategory.OST_Walls,
    "Columnas": BuiltInCategory.OST_StructuralColumns,
    "Vigas": BuiltInCategory.OST_StructuralFraming,
    "Losas": BuiltInCategory.OST_Floors,
    "Rampas": BuiltInCategory.OST_Ramps,
    "Escaleras": BuiltInCategory.OST_Stairs,
    "Puertas": BuiltInCategory.OST_Doors,
    "Ventanas": BuiltInCategory.OST_Windows
}

# Función segura para extraer valor de parámetro
def get_param_value(param):
    try:
        if param.StorageType == StorageType.Double:
            return round(param.AsDouble() * 0.3048, 3)  # pies a metros
        elif param.StorageType == StorageType.String:
            return param.AsString()
        elif param.StorageType == StorageType.ElementId:
            ref = doc.GetElement(param.AsElementId())
            return ref.Name if ref else ""
        else:
            return param.AsValueString()
    except:
        return ""

# Diccionario de resultados (una fila por elemento)
elementos_info = []

# Agregar datos de habitaciones (ambientes) al CSV
for ambiente in modelo.ambientes:
    nombre, nivel, area, altura, uso = ambiente
    info_room = {
        "Categoría": "Habitaciones",
        "Elemento": nombre,
        "Tipo": uso,
        "ID": "",
        "Nivel": nivel,
        "Area (m²)": area,
        "Altura (m)": altura
    }
    elementos_info.append(info_room)

for nombre_cat, bicat in categorias_clave.items():
    elementos = FilteredElementCollector(doc)\
        .OfCategory(bicat)\
        .WhereElementIsNotElementType()\
        .ToElements()

    for el in elementos:
        tipo = doc.GetElement(el.GetTypeId())

        info = {
            "Categoría": nombre_cat,
            "Elemento": el.Name,
            "Tipo": tipo.Name if tipo else "",
            "ID": el.Id.IntegerValue,
        }

        # Nivel (si existe)
        nivel = ""
        try:
            if hasattr(el, "LevelId") and el.LevelId.IntegerValue > 0:
                nivel_obj = doc.GetElement(el.LevelId)
                nivel = nivel_obj.Name if nivel_obj else ""
        except:
            pass
        info["Nivel"] = nivel

        # Agregar parámetros de instancia
        for param in el.Parameters:
            nombre_param = param.Definition.Name
            valor = get_param_value(param)
            info[f"[I] {nombre_param}"] = valor

        # Agregar parámetros de tipo
        if tipo:
            for param in tipo.Parameters:
                nombre_param = param.Definition.Name
                valor = get_param_value(param)
                info[f"[T] {nombre_param}"] = valor

        elementos_info.append(info)

# Obtener todos los nombres únicos de columnas
todos_los_campos = set()
for e in elementos_info:
    todos_los_campos.update(e.keys())

# Ordenar columnas de forma útil
campos_ordenados = sorted(todos_los_campos)
campos_fijos = ["Categoría", "Elemento", "Tipo", "ID", "Nivel"]
otros_campos = [c for c in campos_ordenados if c not in campos_fijos]
columnas_finales = campos_fijos + otros_campos

# Crear CSV en memoria (NO se guarda en disco)
csv_buffer = io.StringIO()
writer = csv.DictWriter(csv_buffer, fieldnames=columnas_finales)
writer.writeheader()
for e in elementos_info:
    writer.writerow(e)
csv_content = csv_buffer.getvalue().encode('utf-8')

print("✅ Exportación completa (en memoria)")


# Construir multipart/form-data manualmente
boundary = uuid.uuid4().hex
filename = "revit_detalles_clave_completo.csv"
content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
    f'Content-Type: {content_type}\r\n\r\n'
).encode('utf-8') + csv_content + f'\r\n--{boundary}--\r\n'.encode('utf-8')

headers = {
    'Content-Type': f'multipart/form-data; boundary={boundary}',
    'Content-Length': str(len(body))
}

req = Request(url, data=body, headers=headers, method='POST')

# Enviar y leer respuesta
with urlopen(req) as response:
    response_data = response.read().decode('utf-8')
    print('Respuesta del servidor:')
    print(response_data)
#
