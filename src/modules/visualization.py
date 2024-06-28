import pandas as pd
import pyvista as pv
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

def load_scenario(file_path):
    columns = ['X', 'Y', 'Z', 'Tonelaje total del bloque', 'metal 1', 'metal 2']
    data = pd.read_csv(file_path, header=None, names=columns)
    data['Z'] = -data['Z']
    data['Ley'] = data['metal 1'] / data['Tonelaje total del bloque']
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

        for dz in [-1, 1]:
            neighbor = (row['X'], row['Y'], row['Z'] + dz)
            if neighbor in G:
                G.add_edge(block_id, neighbor, capacity=row['Ley'])
                G.add_edge(neighbor, block_id, capacity=row['Ley'])

    return G, source, sink

def max_flow(G, source, sink):
    flow_value, flow_dict = nx.maximum_flow(G, source, sink)
    return flow_value, flow_dict

def visualize_scenario(data):
    grid = pv.PolyData(data[['X', 'Y', 'Z']].values)
    plotter = pv.Plotter()
    plotter.add_mesh(grid, scalars=data['Ley'].values, cmap='viridis', point_size=5, render_points_as_spheres=True)
    return plotter.show(screenshot='temp.png')

def load_and_visualize_scenario(file_path, period):
    data = load_scenario(file_path)
    G, source, sink = create_graph(data)
    upl_value, _ = max_flow(G, source, sink)
    return upl_value

def generate_histogram(data):
    plt.figure()
    plt.hist(data['Ley'], bins=20, color='blue', edgecolor='black')
    plt.title('Histograma de Leyes')
    plt.xlabel('Ley')
    plt.ylabel('Frecuencia')
    return plt.gcf()

def generate_tonnage_grade_curve(data):
    sorted_data = data.sort_values(by='Ley', ascending=False)
    sorted_data['Tonelaje acumulado'] = sorted_data['Tonelaje total del bloque'].cumsum()
    plt.figure()
    plt.plot(sorted_data['Tonelaje acumulado'], sorted_data['Ley'])
    plt.title('Curva Tonelaje-Ley')
    plt.xlabel('Tonelaje Acumulado')
    plt.ylabel('Ley')
    return plt.gcf()

def visualize_2d(data, axis, axis_value):
    filtered_data = data[data[axis] == axis_value]
    plt.figure()
    plt.scatter(filtered_data['X'], filtered_data['Y'], c=filtered_data['Ley'], cmap='viridis')
    plt.title(f'Visualización 2D en el plano {axis}={axis_value}')
    plt.xlabel('X')
    plt.ylabel('Y')
    return plt.gcf()

def calculate_extracted_rock(data, mine_plan, period):
    extracted_rock = mine_plan[mine_plan['Period'] == period]['Tonnage'].sum()
    return extracted_rock