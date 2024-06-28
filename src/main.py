import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import io
import base64
import pandas as pd
import pyvista as pv
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


# Incluir las funciones de visualización y análisis de datos aquí
def read_text_data(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            row = line.strip().split(',')
            data.append(row)
    return data
# Funciones de visualización y análisis de datos
def load_scenario(file_path):
    columns = ['X', 'Y', 'Z', 'Tonelaje total del bloque', 'metal 1', 'metal 2']
    data = pd.read_csv(file_path, header=None, names=columns)
    data['Z'] = -data['Z']
    data['Ley'] = data['metal 1'] / data['Tonelaje total del bloque']
    #Aquí se llama la función para hacer el cálculo del valor del bloque
    data['Valor'] = data.apply(lambda row: calculate_block_value(
        row['Ley'], row['Tonelaje total del bloque']), axis=1)
    return data

def calculate_block_value(ley, tonelaje):
    # Primera fórmula
    formula_1 = ley * metal_price * metal_recovery - (mining_cost + processing_cost) * tonelaje
    # Segunda fórmula
    formula_2 = -(mining_cost * tonelaje)

    # Comparar y devolver el valor correspondiente
    if formula_2 > formula_1:
        return formula_2
    else:
        return formula_1


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


metal_price = 1800000  # Ejemplo de valor
metal_recovery = 0.85 # Ejemplo de valor
mining_cost = 2.5  # Ejemplo de valor
processing_cost = 5  # Ejemplo de valor


external_scripts = [
    {'src': 'https://cdn.tailwindcss.com'}
]
# Definir el layout HTML
app = dash.Dash(__name__, external_scripts=external_scripts)
app.title = "Alto de los Andes"

app.layout = html.Div([
    # Navbar superior
    html.Div([
        html.Div([
            html.Button('Visualizar en 2D', id='visualize-2d-button', n_clicks=0,
                        className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded mr-2"),
            html.Button('Visualizar Escenario', id='visualize-button', n_clicks=0,
                        className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded mr-2"),
            html.Label('Seleccionar el Período:', className="ml-4"),
            dcc.Input(id='period-input', type='number', value=0, className="border-gray-300 border rounded px-2 py-1 ml-2 text-black"),
            
            html.Button('Seleccionar Período', id='select-period-button', n_clicks=0,
                        className="bg-blue-500 hover:bg-blue-700 text-white px-4 py-2 rounded ml-2"),
        ], className="flex items-center justify-center"),
    ], className="bg-gray-800 text-white p-4"),

    # Contenedor principal
    html.Div([
        # Sidebar izquierdo
        html.Div([
            html.Div([
                html.Button(f"Escenario {i}", id=f"btn-scenario-{i}", n_clicks=0,
                            className="bg-blue-700 hover:bg-blue-800 text-white py-2 px-4 rounded mb-2 text-left")
                for i in range(10)
            ], className="flex flex-col items-start"),
        ], className="bg-gray-100 w-1/6 px-5 py-5"),
        # Contenido principal
        html.Div([
            html.H2("Plan Minero", className="text-2xl font-bold mb-4 text-center"),
            html.Div(id='scenario-content', className="mt-8"),
            dcc.Graph(id='3d-visualization', className="mt-4"),
            html.Img(id='histogram', className="mt-4"),
            html.Img(id='tonnage-grade-curve', className="mt-4"),
            html.Div(id='upl-value', className="mt-4 text-center text-2xl font-bold"),
        ], className="flex-1 p-4"),
    ], className="flex"),
    
    # Configuración para visualización 2D
    html.Div([
        html.Label('Configuración Visualización 2D:', className="text-xl font-bold mt-4"),
        html.Div([
            html.Label('Eje:'),
            dcc.Dropdown(
                id='axis-dropdown',
                options=[
                    {'label': 'X', 'value': 'X'},
                    {'label': 'Y', 'value': 'Y'},
                    {'label': 'Z', 'value': 'Z'}
                ],
                value='X'
            ),
            html.Label('Valor del Eje:'),
            dcc.Input(id='axis-value-input', type='number', value=0, className="border-gray-300 border rounded px-2 py-1"),
        ], className="flex flex-col md:flex-row md:items-center md:justify-between mt-4"),
    ], className="mx-auto p-4"),
], className="h-screen")

# Registro de callbacks
@app.callback(
    Output('scenario-content', 'children'),
    [Input(f'btn-scenario-{i}', 'n_clicks') for i in range(10)]
)
def display_scenario(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'btn-scenario-0'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    scenario_index = int(button_id.split('-')[-1])
    scenario_file = f'data/Scenarios/Scenario{str(scenario_index).zfill(2)}.txt'

    return html.Div([
        html.H2(f"Visualizando Escenario {scenario_index}", className="text-2xl font-bold mb-4"),
        html.Div(id='hidden-div', children=scenario_file, style={'display': 'none'})
    ])

@app.callback(
    [Output('3d-visualization', 'figure'),
     Output('upl-value', 'children'),
     Output('histogram', 'src'),
     Output('tonnage-grade-curve', 'src')],
    [Input('visualize-button', 'n_clicks'),
     Input('visualize-2d-button', 'n_clicks')],
    [State('period-input', 'value'),
     State('hidden-div', 'children'),
     State('axis-dropdown', 'value'),
     State('axis-value-input', 'value')]
)
def update_visualization(n_clicks_3d, n_clicks_2d, period, scenario_file, axis, axis_value):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {}, '', '', ''

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'visualize-button' and n_clicks_3d > 0:
        upl_value = load_and_visualize_scenario(scenario_file, period)

        scenario_data = load_scenario(scenario_file)

        # Generar el histograma
        hist_fig = generate_histogram(scenario_data)
        hist_buf = io.BytesIO()
        hist_fig.savefig(hist_buf, format='png')
        hist_buf.seek(0)
        hist_img_base64 = base64.b64encode(hist_buf.read()).decode('utf-8')
        hist_img_src = f'data:image/png;base64,{hist_img_base64}'

        # Generar la curva Tonelaje-Ley
        curve_fig = generate_tonnage_grade_curve(scenario_data)
        curve_buf = io.BytesIO()
        curve_fig.savefig(curve_buf, format='png')
        curve_buf.seek(0)
        curve_img_base64 = base64.b64encode(curve_buf.read()).decode('utf-8')
        curve_img_src = f'data:image/png;base64,{curve_img_base64}'

        # Calcular el tonelaje extraído usando calculate_extracted_rock
        mine_plan = pd.read_csv('data/MinePlan/MinePlan.txt')
        extracted_tonnage = calculate_extracted_rock(scenario_data, mine_plan, period)

        return visualize_scenario(scenario_data), f'Ultimate Pit Limit Value (Total Metal Content): {upl_value}. Cantidad de roca Total (tonelaje) extraído en el Período {period}: {extracted_tonnage}', hist_img_src, curve_img_src

    elif button_id == 'visualize-2d-button' and n_clicks_2d > 0:
        scenario_data = load_scenario(scenario_file)
        fig_2d = visualize_2d(scenario_data, axis, axis_value)

        buf = io.BytesIO()
        fig_2d.savefig(buf, format='png')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        img_src = f'data:image/png;base64,{img_base64}'

        return {}, '', img_src, ''

    return {}, '', '', ''

if __name__ == '__main__':
    app.run_server(debug=True)

