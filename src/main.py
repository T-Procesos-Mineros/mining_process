import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from modules.visualization import load_and_visualize_scenario, load_scenario, generate_histogram, \
    generate_tonnage_grade_curve, visualize_2d, calculate_extracted_rock

import io
import base64
import matplotlib.pyplot as plt
import pandas as pd


external_scripts = [
    {'src': 'https://cdn.tailwindcss.com'}
]
app = dash.Dash(__name__,
                external_scripts=external_scripts
                )
app.title = "Minera Alto los Andes"

app.layout = html.Div([
    html.Div(
        [html.Button(f"Escenario {i}", id=f"btn-scenario-{i}", n_clicks=0,
                     className="bg-blue-500 hover:bg-blue-700 text-white py-2 px-4 rounded mx-2 my-2") for i
         in range(10)],
        className="flex flex-wrap justify-center bg-gray-700"
    ),
    html.H1("Plan Minero - Alto los Andes", className="text-3xl font-bold mb-8 py-5 text-center"),
    
    # Inputs para valores de cálculo
    html.Div([
        html.Label("Precio del Metal:", className="inline-block mr-2"),
        dcc.Input(
            id='metal_price',
            type='number',
            value=1800000,
            className="text-sm text-center inline-block border border-black w-24"
        ),
        html.Label("Recuperación del Metal:", className="inline-block mr-2 ml-4"),
        dcc.Input(
            id='metal_recovery',
            type='number',
            value=0.85,
            step=0.01,
            className="text-sm text-center inline-block border border-black w-24"
        ),
        html.Label("Costo de Minado:", className="inline-block mr-2 ml-4"),
        dcc.Input(
            id='mining_cost',
            type='number',
            value=2.5,
            step=0.01,
            className="text-sm text-center inline-block border border-black w-24"
        ),
        html.Label("Costo de Procesamiento:", className="inline-block mr-2 ml-4"),
        dcc.Input(
            id='processing_cost',
            type='number',
            value=5,
            step=0.01,
            className="text-sm text-center inline-block border border-black w-24"
        ),
        html.Button('Calcular Bloque', id='calculate_button', n_clicks=0,
                    className="bg-blue-500 hover:bg-blue-700 text-white py-2 px-4 rounded mx-2 mt-4")
    ], className="mb-4 p-4 rounded-lg text-center"),
    
    html.Div(id='output', className="text-center mt-4"),
    html.Div(id='3d-visualization'),
    html.Div(id='upl-value', className="mt-4 text-center text-red-500 text-2xl"),
    html.Div(id='scenario-content', className="mt-8"),
    html.Div(id='hidden-div', style={'display': 'none'}),
    html.Div([
        html.Label("Seleccione el Período:", className="inline-block mr-2"),
        dcc.Input(
            id='period-input',
            type='number',
            value=0,
            min=0,
            max=5, 
            step=1,  
            className="text-sm text-center inline-block border border-black w-24"
        )
    ], className="mb-4 p-4 rounded-lg text-center"),
    html.Div([
        html.Button('Visualizar Escenario 3D', id='visualize-button', n_clicks=0,
                    className="bg-green-500 text-white px-4 py-2 rounded mx-2"),
        html.Button('Visualizar Escenario 2D', id='visualize-2d-button', n_clicks=0,
                    className="bg-red-500 text-white px-4 py-2 rounded mx-2")
    ], className="mt-4 text-center"),
    
    html.Div(id='2d-visualization-settings', children=[
        html.Div(className="flex flex-wrap justify-center mb-4", children=[
            html.Div(className="flex items-center mr-6", children=[
                html.Label('Eje:', className="text-sm font-medium text-gray-700 mr-2"),
                dcc.Dropdown(
                    id='axis-dropdown',
                    options=[
                        {'label': 'X', 'value': 'X'},
                        {'label': 'Y', 'value': 'Y'},
                        {'label': 'Z', 'value': 'Z'}
                    ],
                    value='X',
                    className="text-sm w-24"
                ),
            ]),
            
            html.Div(className="flex items-center", children=[
                html.Label('Valor del Eje:', className="text-sm font-medium text-gray-700 mr-2"),
                dcc.Input(
                    id='axis-value-input',
                    type='number',
                    value=0,
                    min=0,
                    max=100,
                    step=1,
                    className="text-sm text-center w-24 border border-black"
                )
            ])
        ])
    ], className="mt-4 flex flex-col items-center"),
    
    html.Div(className="mt-8 flex flex-col items-center", children=[
        html.Div(className="flex flex-row justify-center mb-4", children=[
            html.Div(className="mx-2", children=[
                html.Img(id='2d-visualization', className="mt-4  object-cover"),  
            ]),
            html.Div(className="mx-2", children=[
                html.Img(id='tonnage-grade-curve', className="mt-4 object-cover"),
            ]),
        ]),
        html.Div(className="mt-4", children=[
            html.Img(id='histogram', className="mx-auto object-cover"), 
        ]),
    ])
], className="w-full h-full")


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
    scenario_file = f'src/data/Scenarios/Scenario{str(scenario_index).zfill(2)}.txt'

    return html.Div([
        html.H2(f"Visualizando Escenario {scenario_index}", className="text-2xl font-bold mb-4"),
        html.Div(id='hidden-div', children=scenario_file, style={'display': 'none'})
    ], className="text-center")

@app.callback(
    [Output('3d-visualization', 'children'),
     Output('upl-value', 'children'),
     Output('histogram', 'src'),
     Output('tonnage-grade-curve', 'src'),
     Output('2d-visualization', 'src')],
    [Input('visualize-button', 'n_clicks'),
     Input('visualize-2d-button', 'n_clicks')],
    [State('period-input', 'value'),
     State('hidden-div', 'children'),
     State('axis-dropdown', 'value'),
     State('axis-value-input', 'value'),
     State('metal_price', 'value'),
     State('metal_recovery', 'value'),
     State('mining_cost', 'value'),
     State('processing_cost', 'value')]
)
def update_visualization(n_clicks_3d, n_clicks_2d, period, scenario_file, axis, axis_value,
                         metal_price, metal_recovery, mining_cost, processing_cost):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {}, '', '', '', ''

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'visualize-button' and n_clicks_3d > 0:
        upl_value = load_and_visualize_scenario(scenario_file, period, metal_price, metal_recovery, mining_cost, processing_cost)
        scenario_data = load_scenario(scenario_file, metal_price, metal_recovery, mining_cost, processing_cost)
        mine_plan = pd.read_csv('src/data/MinePlan/MinePlan.txt')
        extracted_tonnage = calculate_extracted_rock(load_scenario(scenario_file, metal_price, metal_recovery, mining_cost, processing_cost), mine_plan, period)

        return {}, f'Ultimate Pit Limit Value (UPL): ${upl_value} USD. Cantidad de roca Total extraído en el Período {period}: {extracted_tonnage} Tm', '', '', ''

    elif button_id == 'visualize-2d-button' and n_clicks_2d > 0:
        scenario_data = load_scenario(scenario_file, metal_price, metal_recovery, mining_cost, processing_cost)
        hist_fig = generate_histogram(scenario_data)
        hist_buf = io.BytesIO()
        hist_fig.savefig(hist_buf, format='png')
        hist_buf.seek(0)
        hist_img_base64 = base64.b64encode(hist_buf.read()).decode('utf-8')
        hist_img_src = f'data:image/png;base64,{hist_img_base64}'

        curve_fig = generate_tonnage_grade_curve(scenario_data)
        curve_buf = io.BytesIO()
        curve_fig.savefig(curve_buf, format='png')
        curve_buf.seek(0)
        curve_img_base64 = base64.b64encode(curve_buf.read()).decode('utf-8')
        curve_img_src = f'data:image/png;base64,{curve_img_base64}'

        fig_2d = visualize_2d(scenario_data, axis, axis_value)
        buf = io.BytesIO()
        fig_2d.savefig(buf, format='png')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        img_src = f'data:image/png;base64,{img_base64}'

        return {}, '', hist_img_src, curve_img_src, img_src

    return {}, '', '', '', ''

@app.callback(
    Output('output', 'children'),
    [Input('calculate_button', 'n_clicks')],
    [State('metal_price', 'value'),
     State('metal_recovery', 'value'),
     State('mining_cost', 'value'),
     State('processing_cost', 'value'),
     State('hidden-div', 'children')]  # Suponiendo que 'hidden-div' contiene el índice del escenario
)
def update_block_value(n_clicks, metal_price, metal_recovery, mining_cost, processing_cost, scenario_file):
    if n_clicks > 0:
        try:
            # Determina el índice del escenario desde el div oculto
            scenario_index = scenario_file.split('Scenario')[-1].split('.')[0]  # Ejemplo: '00'
            file_path = f'src/data/Scenarios/Scenario{scenario_index}.txt'
            
            # Llama a la función load_scenario con los parámetros de entrada
            load_scenario(file_path, metal_price, metal_recovery, mining_cost, processing_cost)
            return 'Los datos se han ingresado correctamente.'
        except Exception as e:
            return f'Error: {str(e)}'
    return 'Introduce los valores y presiona el botón para calcular.'

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)