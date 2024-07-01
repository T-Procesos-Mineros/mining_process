import pandas as pd
import pyvista as pv
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64


metal_price = 1800000
metal_recovery = 0.85
mining_cost = 2.5
processing_cost = 5

def load_scenario(file_path):
    columns = ['X', 'Y', 'Z', 'Tonelaje total del bloque', 'metal 1', 'metal 2']
    data = pd.read_csv(file_path, header=None, names=columns)
    data['Z'] = -data['Z']
    data['Ley'] = data['metal 1'] / data['Tonelaje total del bloque']
    data['Valor'] = data.apply(lambda row: calculate_block_value(
        row['Ley'], row['Tonelaje total del bloque']), axis=1)
    return data

def calculate_block_value(ley, tonelaje):
    formula_1 = ley * metal_price * metal_recovery - (mining_cost + processing_cost) * tonelaje
    formula_2 = -(mining_cost * tonelaje)
    return max(formula_1, formula_2)

def create_graph(data):
    G = nx.DiGraph()
    source = 's'
    sink = 't'
    for _, row in data.iterrows():
        block_id = (row['X'], row['Y'], row['Z'])
        G.add_node(block_id)
        if row['Z'] == data['Z'].min():
            G.add_edge(source, block_id, capacity=row['Valor'])
        else:
            G.add_edge(block_id, sink, capacity=row['Valor'])
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
    valor = data['Valor'].astype(float)

    points = pv.PolyData(np.column_stack((x, y, z)).astype(np.float32))
    points['Tonelaje'] = tonelaje
    points['Metal 1'] = metal_1
    points['Metal 2'] = metal_2
    points['Ley'] = ley
    points['Valor'] = valor
    points['X'] = x
    points['Y'] = y
    points['Z'] = z

    cube = pv.Cube()
    glyphs = points.glyph(scale=False, geom=cube, orient=False)
    mine_plan['ZIndex'] = -mine_plan['ZIndex']
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
    plotter.add_mesh(glyphs, scalars='Ley', cmap='cividis')
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

def visualize_2d(data, axis, axis_value):
    if axis == 'X':
        filtered_data = data[data['X'] == axis_value]
        x_vals, y_vals = filtered_data['Y'], filtered_data['Z']
    elif axis == 'Y':
        filtered_data = data[data['Y'] == axis_value]
        x_vals, y_vals = filtered_data['X'], filtered_data['Z']
    elif axis == 'Z':
        filtered_data = data[data['Z'] == -axis_value]
        x_vals, y_vals = filtered_data['X'], filtered_data['Y']
    else:
        raise ValueError("Eje no válido. Debe ser 'X', 'Y' o 'Z'.")

    fig, ax = plt.subplots(figsize=(6, 6))
    scatter = ax.scatter(x_vals, y_vals, c=filtered_data['Ley'], cmap='cividis')
    ax.set_xlabel('Y' if axis == 'X' else 'X')
    ax.set_ylabel('Z' if axis in ['X', 'Y'] else 'Y')
    fig.colorbar(scatter, ax=ax, label='Ley')
    ax.set_title(f'Visualización 2D en el plano {axis} = {axis_value}')
    return fig

def load_and_visualize_scenario(scenario_file, period_limit):
    scenario_data = load_scenario(scenario_file)
    mine_plan = pd.read_csv('src/data/MinePlan/MinePlan.txt')
    visualize_scenario(scenario_data, mine_plan, period_limit)
    graph, source, sink = create_graph(scenario_data)
    upl_value, upl_dict = compute_upl(graph, source, sink)
    print(f"Ultimate Pit Limit (UPL): {upl_value}")
    return round(upl_value,3)

def generate_histogram(scenario_data):
    metal_1_data = scenario_data['metal 1'] / scenario_data['Tonelaje total del bloque']
    metal_2_data = scenario_data['metal 2'] / scenario_data['Tonelaje total del bloque']

    fig, axes = plt.subplots(1, 2, figsize=(10, 6))

    axes[0].hist(metal_1_data, bins=20, color='blue', alpha=0.7)
    axes[0].set_title('Histograma de Leyes para Metal 1')
    axes[0].set_xlabel('Ley')
    axes[0].set_ylabel('Frecuencia')

    axes[1].hist(metal_2_data, bins=20, color='green', alpha=0.7)
    axes[1].set_title('Histograma de Leyes para Metal 2')
    axes[1].set_xlabel('Ley')
    axes[1].set_ylabel('Frecuencia')

    plt.tight_layout()
    plt.close(fig)
    return fig

def generate_tonnage_grade_curve(data):
    # Obtener la ley más alta presente en los datos
    max_grade = data['Ley'].max()
    # Crear un rango de leyes de corte
    a = np.arange(0, max_grade, 0.01)
    datax = []
    datay = []

    for i in a:
        filtered_data = data[data['Ley'] >= i]
        total_tonnage = filtered_data['Tonelaje total del bloque'].sum()
        total_fino = filtered_data['metal 1'].sum()
        datax.append(total_tonnage)
        datay.append(total_fino / total_tonnage if total_tonnage > 0 else 0)

    new_df = pd.DataFrame({
        'Cutoff': a,
        'Tonelaje': datax,
        'Av grade': datay
    })

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(new_df['Cutoff'], new_df['Tonelaje'], 'k', label='Tonelaje')
    ax1.set_xlabel('Ley de corte (%)')
    ax1.set_ylabel('Tonelaje (Mton)', color='k')
    ax1.tick_params(axis='y', labelcolor='k')

    ax2 = ax1.twinx()
    ax2.plot(new_df['Cutoff'], new_df['Av grade'], 'k--', label='Ley media')
    ax2.set_ylabel('Ley media (%)', color='k')
    ax2.tick_params(axis='y', labelcolor='k')

    ax1.legend(loc='upper center', shadow=True, fontsize='x-large')
    ax2.legend(loc='lower center', shadow=True, fontsize='x-large')

    plt.title('Curva tonelaje vs ley', fontsize=15)
    plt.grid(True)
    plt.close(fig)  # Cerrar la figura para que no se muestre fuera de Dash
    return fig

def calculate_extracted_rock(scenario_data, mine_plan, period_limit):
    scenario_data['Z'] = -scenario_data['Z']
    filtered_mine_plan = mine_plan[mine_plan['Period'] == period_limit]

    if filtered_mine_plan.empty:
        print(f"No hay datos para el período {period_limit} en el plan minero.")
        return 0

    print(f"Datos filtrados del plan minero (Periodo {period_limit}):")
    print(filtered_mine_plan.head())

    print("Columnas en scenario_data:")
    print(scenario_data.columns)
    print("Columnas en filtered_mine_plan:")
    print(filtered_mine_plan.columns)

    merged_data = pd.merge(scenario_data, filtered_mine_plan, how='inner', left_on=['X', 'Y', 'Z'],
                           right_on=['XIndex', 'YIndex', 'ZIndex'])

    print("Datos unidos:")
    print(merged_data.head())

    extracted_tonnage = merged_data['Tonelaje total del bloque'].sum()
    print(f"Tonelaje total extraído para el periodo {period_limit}: {extracted_tonnage}")
    return extracted_tonnage
