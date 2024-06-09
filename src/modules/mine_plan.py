import pandas as pd
import pyvista as pv
import numpy as np

# Nombre del archivo de texto
scenario01 = '../data/Scenarios/Scenario03.txt'
mine_plan_file = '../data/MinePlan/MinePlan.txt'

# Especificar los nombres de las columnas
columns = ['X', 'Y', 'Z', 'Tonelaje total del bloque', 'metal 1', 'metal 2']

# Leer el archivo de texto sin encabezados
data = pd.read_csv(scenario01, header=None, names=columns)

# Verificar que todas las columnas necesarias están presentes
required_columns = set(columns)
if not required_columns.issubset(data.columns):
    raise ValueError(f"Faltan columnas en el archivo de entrada. Se requieren: {required_columns}")

# Extraer las columnas
x = data['X'].astype(float)
y = data['Y'].astype(float)
z = data['Z'].astype(float)
tonelaje = data['Tonelaje total del bloque'].astype(float)
metal_1 = data['metal 1'].astype(float)
metal_2 = data['metal 2'].astype(float)

# Crear un objeto PolyData para la visualización
points = pv.PolyData(np.column_stack((x, y, z)).astype(np.float32))

# Añadir los datos de tonelaje y metales como arrays de datos a los puntos
points['Tonelaje'] = tonelaje
points['Metal 1'] = metal_1
points['Metal 2'] = metal_2
points['X'] = x
points['Y'] = y
points['Z'] = z

# Crear los glifos (cubos)
cube = pv.Cube()

# Crear los glifos (cubos) y asignarlos a una malla
glyphs = points.glyph(scale=False, geom=cube, orient=False)

# Leer el archivo de plan minero
mine_plan = pd.read_csv(mine_plan_file)

# Variable que representa el periodo límite
x = 5  # Puedes cambiar este valor para ajustar el periodo límite

# Filtrar el plan minero hasta el periodo x
filtered_mine_plan = mine_plan[mine_plan['Period'] <= x]

# Crear una máscara para los puntos a eliminar
mask = np.ones(len(points.points), dtype=bool)

# Iterar sobre cada fila del plan minero filtrado y marcar los bloques correspondientes
for index, row in filtered_mine_plan.iterrows():
    x_index = row['XIndex']
    y_index = row['YIndex']
    z_index = row['ZIndex']

    # Encontrar los puntos correspondientes en los glifos y marcarlos para eliminación
    mask &= ~((points['X'] == x_index) & (points['Y'] == y_index) & (points['Z'] == z_index))

# Filtrar los puntos que no están marcados para eliminación
filtered_points = points.extract_points(mask)

# Crear los glifos actualizados después de la eliminación
glyphs = filtered_points.glyph(scale=False, geom=cube, orient=False)

# Añadir los cubos a la escena
plotter = pv.Plotter()
plotter.add_mesh(glyphs, scalars='Tonelaje', cmap='viridis')

# Obtener los bordes de los cubos
surface = glyphs.extract_surface()
edges = surface.extract_feature_edges()

# Añadir los bordes a la escena con color personalizado
plotter.add_mesh(edges, color="black", line_width=3)

# Añadir una barra de color (leyenda)
plotter.add_scalar_bar(title='Tonelaje', label_font_size=12)

# Permitir la rotación en tiempo real
plotter.enable_eye_dome_lighting()
plotter.show_grid()

# Mostrar la trama 3D
plotter.show(auto_close=False)

# Imprimir rangos de los ejes y valores únicos de Z
print(f"Rango de X: {x.min()} a {x.max()}")
print(f"Rango de Y: {y.min()} a {y.max()}")
print(f"Rango de Z: {z.min()} a {z.max()}")
print(f"Valores únicos de Z: {z.unique()}")


# Función para visualización 2D basada en coordenada específica
def view_2d(axis, value, tolerance=0.1):
    if axis == 'x':
        if not (x.min() <= value <= x.max()):
            raise ValueError(f"Valor {value} fuera del rango de datos para el eje X")
        sliced = points.threshold([value - tolerance, value + tolerance], scalars='X')
    elif axis == 'y':
        if not (y.min() <= value <= y.max()):
            raise ValueError(f"Valor {value} fuera del rango de datos para el eje Y")
        sliced = points.threshold([value - tolerance, value + tolerance], scalars='Y')
    elif axis == 'z':
        if not (z.min() <= value <= z.max()):
            raise ValueError(f"Valor {value} fuera del rango de datos para el eje Z")
        sliced = points.threshold([value - tolerance, value + tolerance], scalars='Z')
    else:
        raise ValueError(f"Eje no válido: {axis}. Use 'x', 'y' o 'z'.")

    if sliced.n_points == 0:
        raise ValueError(f"El corte en el eje {axis} con valor {value} no produce puntos.")

    plotter_2d = pv.Plotter()
    plotter_2d.add_mesh(sliced, scalars='Tonelaje', cmap='viridis')
    plotter_2d.add_scalar_bar(title='Tonelaje', label_font_size=12)
    plotter_2d.show()

# Ejemplo de uso para visualizar en 2D con respecto a la coordenada Z dentro del rango
view_2d('z', 7, tolerance=0.5)  # Usamos una tolerancia para aumentar el grosor del corte

# Otras opciones:
# view_2d('x', 20, tolerance=0.5)  # 20 es un valor dentro del rango de X: 6.0 a 30.0
# view_2d('y', 15, tolerance=0.5)  # 15 es un valor dentro del rango de Y: 10.0 a 21.0