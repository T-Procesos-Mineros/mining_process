import matplotlib
matplotlib.use('Agg')  # Usar el backend 'Agg' para evitar problemas de GUI
import re
import pandas as pd
import pyvista as pv
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict
import itertools


metal_price = 600000
metal_recovery = 0.85
mining_cost = 2.5
processing_cost = 5

def parse_rules(file_path):
    rules = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            match = re.match(r'if \(ZIndex == (\d+) and \(\((.*?)\)\)\) TypeOfBlock = "(.*?)";', line)
            if match:
                z_index = int(match.group(1))
                conditions = match.group(2).split('or')
                x_ranges = []
                for condition in conditions:
                    condition = condition.replace(')', '').strip()
                    if '<=' in condition and '>=' in condition:
                        parts = condition.split('and')
                        x_range = [int(parts[0].split('>=')[1].strip()), int(parts[1].split('<=')[1].strip())]
                    elif '<=' in condition:
                        x_range = [int(condition.split('<=')[1].strip())]
                    elif '>=' in condition:
                        x_range = [int(condition.split('>=')[1].strip()), float('inf')]
                    elif '==' in condition:
                        x_range = [int(condition.split('==')[1].strip())]
                    elif '>' in condition:
                        x_range = [int(condition.split('>')[1].strip()) + 1, float('inf')]
                    elif '<' in condition:
                        x_range = [0, int(condition.split('<')[1].strip()) - 1]
                    x_ranges.append(x_range)
                rock_type = match.group(3)
                rules.append({'ZIndex': z_index, 'XRanges': x_ranges, 'TypeOfBlock': rock_type})
    return rules

def load_scenario(file_path, metal_price=None, metal_recovery=None, mining_cost=None, processing_cost=None):
    if metal_price is None:
        metal_price = 18000000  # Valor predeterminado
    if metal_recovery is None:
        metal_recovery = 0.85  # Valor predeterminado
    if mining_cost is None:
        mining_cost = 2.5  # Valor predeterminado
    if processing_cost is None:
        processing_cost = 5  # Valor predeterminado

    # Leer el archivo de reglas
    rules_path = 'src/data/RockTypes/RockTypes.txt'
    rules = parse_rules(rules_path)

    columns = ['X', 'Y', 'Z', 'Tonelaje total del bloque', 'metal 1', 'metal 2']
    data = pd.read_csv(file_path, header=None, names=columns)
    data['Z'] = -data['Z']
    data['Ley'] = data['metal 1'] / data['Tonelaje total del bloque']
    data['Ley2'] = data['metal 2'] / data['Tonelaje total del bloque']
    data['Valor'] = data.apply(lambda row: calculate_block_value(
        row['Ley'], row['Tonelaje total del bloque'], metal_price, metal_recovery, mining_cost, processing_cost), axis=1)

    # Asignar el tipo de roca
    def assign_rock_type(row, rules):
        for rule in rules:
            if row['Z'] == -rule['ZIndex']:  # Invertimos Z de nuevo para la comparación
                for x_range in rule['XRanges']:
                    if len(x_range) == 1 and row['X'] == x_range[0]:
                        return rule['TypeOfBlock']
                    elif len(x_range) == 2 and x_range[0] <= row['X'] <= x_range[1]:
                        return rule['TypeOfBlock']
        return 'A'

    data['TypeOfBlock'] = data.apply(lambda row: assign_rock_type(row, rules), axis=1)
    data['Color'] = data['TypeOfBlock'].apply(map_type_to_color)  # Mapeo de colores
    return data

def map_type_to_color(type_of_block):
    color_map = {
        'A': 'yellow',  # Puedes usar nombres de colores
        'B': 'black',
        'C': 'green',  # Si tienes otros tipos de bloques, añádelos aquí
        'D': 'red'
    }
    return color_map.get(type_of_block, 'black')  # Color predeterminado si no se encuentra el tipo

def calculate_block_value(ley, tonelaje, metal_price, metal_recovery, mining_cost, processing_cost):
    formula_1 = ley * metal_price * metal_recovery - (mining_cost + processing_cost) * tonelaje
    formula_2 = -(mining_cost * tonelaje)
    return max(formula_1, formula_2)

def compute_upl(data):
    graph = nx.DiGraph()
    for index, row in data.iterrows():
        graph.add_node(index, value=row['Valor'])
    for index, row in data.iterrows():
        neighbors = find_neighbors(data, row['X'], row['Y'], row['Z'])
        for neighbor in neighbors:
            graph.add_edge(index, neighbor, weight=-data.loc[neighbor, 'Valor'])
    _s = 'source'
    _t = 'sink'
    
    graph.add_node(_s)
    graph.add_node(_t)
    
    for index, row in data.iterrows():
        if row['Valor'] > 0:
            graph.add_edge(_s, index, weight=row['Valor'])
        else:
            graph.add_edge(index, _t, weight=-row['Valor'])
    
    flow_value, partition = nx.minimum_cut(graph, _s, _t, capacity='weight')
    upl_nodes = list(partition[0] if _s in partition[0] else partition[1])
    
    # Excluir los nodos _s y _t
    upl_nodes = [node for node in upl_nodes if node not in [_s, _t]]
    
    upl_blocks = data.loc[upl_nodes]
    upl_blocks['UPL'] = True
    
    return upl_blocks

def find_neighbors(data, x, y, z):
    neighbors = []
    for dx, dy, dz in itertools.product([-1, 0, 1], repeat=3):
        if dx == 0 and dy == 0 and dz == 0:
            continue
        neighbor = data[(data['X'] == x + dx) & (data['Y'] == y + dy) & (data['Z'] == z + dz)]
        if not neighbor.empty:
            neighbors.append(neighbor.index[0])
    return neighbors

def visualize_scenario(data, mine_plan, period_limit=None,):
    # Convertir columnas a tipo float
    x = data['X'].astype(float)
    y = data['Y'].astype(float)
    z = data['Z'].astype(float)
    tonelaje = data['Tonelaje total del bloque'].astype(float)
    metal_1 = data['metal 1'].astype(float)
    
    # Verificar si la columna 'metal_2' existe
    if 'metal_2' in data.columns:
        metal_2 = data['metal_2'].astype(float)
    else:
        metal_2 = np.zeros(len(data))  # Si no existe, usar una columna de ceros
    
    ley = data['Ley'].astype(float)
    ley2 = data['Ley2'].astype(float)
    valor = data['Valor'].astype(float)
    TypeOfBlock = data['TypeOfBlock'].astype(str)

    # Crear puntos de PyVista
    points = pv.PolyData(np.column_stack((x, y, z)).astype(np.float32))
    points['Tonelaje'] = tonelaje
    points['Metal 1'] = metal_1
    points['Metal 2'] = metal_2
    points['Ley'] = ley
    points['Ley2'] = ley2
    points['Valor'] = valor
    points['X'] = x
    points['Y'] = y
    points['Z'] = z
    points['TypeOfBlock'] = TypeOfBlock

    # Crear cubo para visualización
    cube = pv.Cube()
    glyphs = points.glyph(scale=False, geom=cube, orient=False)

    # Filtrar puntos si period_limit es proporcionado
    if period_limit is not None and period_limit != 'Ver yacimiento sin periodo':
        try:
            period_limit = int(period_limit)  # Asegurarse de que period_limit es un entero
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
        except ValueError:
            # Manejar el caso en que period_limit no pueda convertirse a entero
            print(f"Error: period_limit no es un valor válido: {period_limit}")
    else:
        # Si period_limit es None o 'Ver yacimiento sin periodo', se muestran todos los puntos
        glyphs = points.glyph(scale=False, geom=cube, orient=False)

    # Configurar visualización con PyVista
    plotter = pv.Plotter()
    filterType = 'TypeOfBlock'
    plotter.add_mesh(glyphs, scalars=filterType, cmap='cividis')
    surface = glyphs.extract_surface()
    edges = surface.extract_feature_edges()
    plotter.add_mesh(edges, color="black", line_width=3)
    plotter.enable_eye_dome_lighting()
    plotter.show_grid()
    plotter.show(auto_close=False)

    return plotter

def visualize_upl(data):
    if 'Ley' not in data.columns:
        raise KeyError("La columna 'Ley' no está presente en los datos.")

    x = data['X'].astype(float)
    y = data['Y'].astype(float)
    z = data['Z'].astype(float)
    tonelaje = data['Tonelaje total del bloque'].astype(float)
    metal_1 = data['metal 1'].astype(float)
    
    # Verificar si la columna 'metal_2' existe
    if 'metal_2' in data.columns:
        metal_2 = data['metal_2'].astype(float)
    else:
        metal_2 = np.zeros(len(data))  # Si no existe, usar una columna de ceros
    
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

    upl_mask = data['UPL']
    points['UPL'] = upl_mask

    cube = pv.Cube()
    glyphs = points.glyph(scale=False, geom=cube, orient=False)

    plotter = pv.Plotter()
    surface = glyphs.extract_surface()
    edges = surface.extract_feature_edges()
    plotter.add_mesh(edges, color="black", line_width=3)
    
    upl_points = points.extract_points(points['UPL'] == True)
    upl_glyphs = upl_points.glyph(scale=False, geom=cube, orient=False)
    plotter.add_mesh(upl_glyphs, color='red')

    plotter.enable_eye_dome_lighting()
    plotter.show_grid()
    plotter.show(auto_close=False)

    return plotter

def visualize_2d(data, axis, axis_value, mine_plan, period):
    if period == 'Ver yacimiento sin periodo':
        period = -1

    mine_plan['ZIndex'] = -mine_plan['ZIndex']  # Hacer que el valor de Z sea negativo en el plan minero
    filtered_mine_plan = mine_plan[mine_plan['Period'] <= period]

    for index, row in filtered_mine_plan.iterrows():
        data = data[~((data['X'] == row['XIndex']) & (data['Y'] == row['YIndex']) & (data['Z'] == row['ZIndex']))]
    
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

    filterType = 'Color'  # Cambiado a la columna de colores

    # Crear la visualización en 2D
    fig, ax = plt.subplots(figsize=(6, 6))
    scatter = ax.scatter(x_vals, y_vals, c=filtered_data[filterType], marker='s', s=500)
    ax.set_xlabel('Y' if axis == 'X' else 'X')
    ax.set_ylabel('Z' if axis in ['X', 'Y'] else 'Y')
    ax.set_title(f'Visualización 2D en el plano {axis} = {axis_value}')

    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    return fig

def load_and_visualize_scenario(scenario_file, period_limit=None, metal_price=None, metal_recovery=None, mining_cost=None, processing_cost=None):
    if metal_price is None:
        metal_price = 0
    if metal_recovery is None:
        metal_recovery = 0
    if mining_cost is None:
        mining_cost = 0
    if processing_cost is None:
        processing_cost = 0
    if period_limit == 'Ver yacimiento sin periodo' or period_limit is None:
        period_limit = None  # Asegurarse de que sea None si se selecciona 'Ver yacimiento sin periodo'

    # Cargar los datos del escenario
    scenario_data = load_scenario(scenario_file, metal_price, metal_recovery, mining_cost, processing_cost)
    # Cargar el plan minero
    mine_plan = pd.read_csv('src/data/MinePlan/MinePlan.txt')

    # Si period_limit es None o tiene el valor especial 'Ver yacimiento sin periodo', visualiza sin aplicar filtro de periodo
    if period_limit is None or period_limit == 'Ver yacimiento sin periodo':
        visualize_scenario(scenario_data, mine_plan)  # Llamar a visualize_scenario sin period_limit
    else:
        visualize_scenario(scenario_data, mine_plan, period_limit)  # Pasar period_limit cuando esté presente

    # Imprimir el valor total del escenario
    print_total_value(scenario_data)
    print(scenario_data.head())

def print_total_value(scenario_data):
    total_value = scenario_data['Valor'].sum()
    print(f"Valor total del yacimiento: ${total_value:.2f} USD")

def load_and_visualize_upl(scenario_file, metal_price, metal_recovery, mining_cost, processing_cost):
    scenario_data = load_scenario(scenario_file, metal_price, metal_recovery, mining_cost, processing_cost)
    upl_data = compute_upl(scenario_data)
    if upl_data.empty or upl_data['Valor'].sum() == 0:
        print("No se puede visualizar el UPL, ya que no es rentable extraer el mineral del yacimiento.")
        return 0, "No se puede visualizar el UPL, ya que no es rentable extraer el mineral del yacimiento."
    visualize_upl(upl_data)
    upl_value = upl_data['Valor'].sum()
    return round(upl_value, 3), f'Ultimate Pit Limit Value (UPL): ${round(upl_value, 3)} USD'

def generate_histogram(scenario_data):
    metal_1_data = scenario_data['Ley']
    metal_2_data = scenario_data['Ley2']

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
    max_grade = data['Ley'].max()
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
    plt.close(fig)
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
