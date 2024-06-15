import pandas as pd
import pyvista as pv
import numpy as np

def load_scenario(file_path):
    columns = ['X', 'Y', 'Z', 'Tonelaje total del bloque', 'metal 1', 'metal 2']
    data = pd.read_csv(file_path, header=None, names=columns)
    data['Z'] = -data['Z']  # Invertir el eje Z al leer los datos
    return data

def visualize_scenario(data, mine_plan, period_limit):
    x = data['X'].astype(float)
    y = data['Y'].astype(float)
    z = data['Z'].astype(float)
    tonelaje = data['Tonelaje total del bloque'].astype(float)
    metal_1 = data['metal 1'].astype(float)
    metal_2 = data['metal 2'].astype(float)

    points = pv.PolyData(np.column_stack((x, y, z)).astype(np.float32))
    points['Tonelaje'] = tonelaje
    points['Metal 1'] = metal_1
    points['Metal 2'] = metal_2
    points['X'] = x
    points['Y'] = y
    points['Z'] = z

    cube = pv.Cube()
    glyphs = points.glyph(scale=False, geom=cube, orient=False)

    mine_plan['ZIndex'] = -mine_plan['ZIndex']  # Invertir el eje Z en el plan minero

    filtered_mine_plan = mine_plan[mine_plan['Period'] <= period_limit]
    mask = np.ones(len(points.points), dtype=bool)

    for index, row in filtered_mine_plan.iterrows():
        x_index = row['XIndex']
        y_index = row['YIndex']
        z_index = row['ZIndex']
        mask &= ~((points['X'] == x_index) & (points['Y'] == y_index) & (points['Z'] == z_index))

    filtered_points = points.extract_points(mask)
    glyphs = filtered_points.glyph(scale=False, geom=cube, orient=False)

    plotter = pv.Plotter()
    plotter.add_mesh(glyphs, scalars='Tonelaje', cmap='viridis')
    surface = glyphs.extract_surface()
    edges = surface.extract_feature_edges()
    plotter.add_mesh(edges, color="black", line_width=3)
    plotter.add_scalar_bar(title='Tonelaje', label_font_size=12)
    plotter.enable_eye_dome_lighting()
    plotter.show_grid()
    plotter.show(auto_close=False)

    print(f"Rango de X: {x.min()} a {x.max()}")
    print(f"Rango de Y: {y.min()} a {y.max()}")
    print(f"Rango de Z: {z.min()} a {z.max()}")
    print(f"Valores únicos de Z: {z.unique()}")

    return plotter