import pandas as pd
import pyvista as pv
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64


def load_scenario(file_path):
    columns = ['X', 'Y', 'Z', 'Tonelaje total del bloque', 'metal 1', 'metal 2']
    data = pd.read_csv(file_path, header=None, names=columns)
    data['Z'] = -data['Z']  # Hacer que el valor de Z sea negativo al leer los datos
    data['Ley'] = data['metal 1'] / data['Tonelaje total del bloque']  # Calcular la ley del mineral
    return data


def create_graph(data):
    G = nx.DiGraph()
    source = 's'
    sink = 't'

    for _, row in data.iterrows():
        block_id = (row['X'], row['Y'], row['Z'])
        G.add_node(block_id)
        if row['Z'] == data['Z'].min():
            G.add_edge(source, block_id, capacity=row['Ley'])
        else:
            G.add_edge(block_id, sink, capacity=row['Ley'])

        # Conectar los bloques adyacentes
        for dz in [-1, 1]:
            neighbor = (row['X'], row['Y'], row['Z'] + dz)
            if neighbor in G:
                G.add_edge(block_id, neighbor, capacity=float('inf'))
                G.add_edge(neighbor, block_id, capacity=float('inf'))

    G.add_node(source)
    G.add_node(sink)

    return G, source, sink


def compute_upl(G, source, sink):
    flow_value, flow_dict = nx.maximum_flow(G, source, sink)
    return flow_value, flow_dict


def visualize_scenario(data, mine_plan, period_limit):
    x = data['X'].astype(float)
    y = data['Y'].astype(float)
    z = data['Z'].astype(float)
    tonelaje = data['Tonelaje total del bloque'].astype(float)
    metal_1 = data['metal 1'].astype(float)
    metal_2 = data['metal 2'].astype(float)
    ley = data['Ley'].astype(float)

    points = pv.PolyData(np.column_stack((x, y, z)).astype(np.float32))
    points['Tonelaje'] = tonelaje
    points['Metal 1'] = metal_1
    points['Metal 2'] = metal_2
    points['Ley'] = ley
    points['X'] = x
    points['Y'] = y
    points['Z'] = z

    cube = pv.Cube()
    glyphs = points.glyph(scale=False, geom=cube, orient=False)

    mine_plan['ZIndex'] = -mine_plan['ZIndex']  # Hacer que el valor de Z sea negativo en el plan minero

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
    plotter.add_mesh(glyphs, scalars='Ley', cmap='cividis')  # Usar 'Ley' para el color y la paleta 'cividis' (negro a amarillo)
    surface = glyphs.extract_surface()
    edges = surface.extract_feature_edges()
    plotter.add_mesh(edges, color="black", line_width=3)
    plotter.enable_eye_dome_lighting()
    plotter.show_grid()
    plotter.show(auto_close=False)

    print(f"Rango de X: {x.min()} a {x.max()}")
    print(f"Rango de Y: {y.min()} a {y.max()}")
    print(f"Rango de Z: {z.min()} a {z.max()}")
    print(f"Valores únicos de Z: {z.unique()}")

    return plotter


def load_and_visualize_scenario(scenario_file, period_limit):
    scenario_data = load_scenario(scenario_file)
    mine_plan = pd.read_csv('data/MinePlan/MinePlan.txt')
    visualize_scenario(scenario_data, mine_plan, period_limit)

    graph, source, sink = create_graph(scenario_data)
    upl_value, upl_dict = compute_upl(graph, source, sink)

    print(f"Ultimate Pit Limit (UPL): {upl_value}")
    return upl_value


def generate_histogram(scenario_data):
    metal_1_data = scenario_data['metal 1']
    metal_2_data = scenario_data['metal 2']

    # Configurar la figura y los subplots
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    # Histograma para Metal 1
    axes[0].hist(metal_1_data, bins=20, color='blue', alpha=0.7)
    axes[0].set_title('Histograma de Leyes para Metal 1')
    axes[0].set_xlabel('Ley')
    axes[0].set_ylabel('Frecuencia')

    # Histograma para Metal 2
    axes[1].hist(metal_2_data, bins=20, color='green', alpha=0.7)
    axes[1].set_title('Histograma de Leyes para Metal 2')
    axes[1].set_xlabel('Ley')
    axes[1].set_ylabel('Frecuencia')

    # Ajustar diseño y mostrar gráficos
    plt.tight_layout()
    plt.close(fig)  # Cerrar la figura para que no se muestre fuera de Dash
    return fig


def generate_tonnage_grade_curve(scenario_data):
    sorted_data = scenario_data.sort_values(by='Ley', ascending=False)
    sorted_data['Tonelaje Acumulado'] = sorted_data['Tonelaje total del bloque'].cumsum()
    sorted_data['Ley Media Acumulada'] = (sorted_data['metal 1'].cumsum() / sorted_data['Tonelaje Acumulado'])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sorted_data['Tonelaje Acumulado'], sorted_data['Ley Media Acumulada'], color='red', linewidth=2)
    ax.set_title('Curva Tonelaje-Ley')
    ax.set_xlabel('Tonelaje Acumulado')
    ax.set_ylabel('Ley Media Acumulada')
    plt.grid(True)
    plt.close(fig)  # Cerrar la figura para que no se muestre fuera de Dash
    return fig
