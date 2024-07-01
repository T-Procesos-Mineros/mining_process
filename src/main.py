import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import matplotlib.pyplot as plt
from modules.visualization import load_and_visualize_scenario, load_scenario, generate_histogram, \
    generate_tonnage_grade_curve, visualize_2d, calculate_extracted_rock, compute_upl, visualize_scenario, load_and_visualize_upl
import io
import base64
import pandas as pd
import pyvista as pv

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
    html.Div(id="scenario-content"),

    html.Div(className="bg-gray-200 p-4 mb-4 rounded", children=[
        html.H2("Cálculo para el Bloque", className="text-xl font-bold mb-4"),
        html.Div(className="flex flex-wrap justify-start", children=[
            html.Div(className="flex items-center mr-6", children=[
                html.Label('Precio del Metal:', className="text-sm font-medium text-gray-700 mr-2"),
                dcc.Input(
                    id='metal_price',
                    type='number',
                    value=18000000,
                    step=1,
                    className="text-sm text-center w-24 border border-black"
                ),
            ]),
            html.Div(className="flex items-center mr-6", children=[
                html.Label('Recuperación del Metal:', className="text-sm font-medium text-gray-700 mr-2"),
                dcc.Input(
                    id='metal_recovery',
                    type='number',
                    value=0.85,
                    className="text-sm text-center w-24 border border-black"
                ),
            ]),
            html.Div(className="flex items-center mr-6", children=[
                html.Label('Costo de Minería:', className="text-sm font-medium text-gray-700 mr-2"),
                dcc.Input(
                    id='mining_cost',
                    type='number',
                    value=2.5,
                    className="text-sm text-center w-24 border border-black"
                ),
            ]),
            html.Div(className="flex items-center mr-6", children=[
                html.Label('Costo de Procesamiento:', className="text-sm font-medium text-gray-700 mr-2"),
                dcc.Input(
                    id='processing_cost',
                    type='number',
                    value=5,
                    className="text-sm text-center w-24 border border-black"
                ),
            ]),
            html.Button('Calcular Bloque', id='calculate_button', n_clicks=0,
                        className="bg-yellow-500 text-white px-4 py-2 rounded mx-2"),
            html.Div(id='output', className="mt-4 px-3"),
        ]),
    ]),

    html.Div(className="bg-gray-200 p-4 mb-4 rounded", children=[
        html.H2("Visualizador 2D", className="text-xl font-bold mb-4"),
        html.Div(className="flex flex-wrap justify-start", children=[
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
            html.Div(className="flex items-center mr-6", children=[
                html.Label('Valor del Eje:', className="text-sm font-medium text-gray-700 mr-2"),
                dcc.Input(
                    id='axis-value-input',
                    type='number',
                    value=12,
                    min=0,
                    max=100,
                    step=1,
                    className="text-sm text-center w-24 border border-black"
                )
            ]),
            html.Button('Visualizar en 2D', id='visualize-2d-button', n_clicks=0,
                        className="bg-red-500 text-white px-4 py-2 rounded mx-2"),
        ]),
    ]),

    html.Div(className="bg-gray-200 p-4 mb-4 rounded", children=[
        html.H2("Visualizar 3D con UPL", className="text-xl font-bold mb-4"),
        html.Div(className="flex flex-wrap justify-start", children=[
            html.Label("Seleccione el Período:", className="inline-block mr-2"),
            dcc.Input(
                id='period-input',
                type='number',
                value=0,
                min=0,
                max=5,
                step=1,
                className="text-sm text-center inline-block border border-black w-24"
            ),
            html.Button('Calcular y Visualizar UPL', id='upl-button', n_clicks=0,
                        className="bg-green-500 text-white px-4 py-2 rounded mx-2"),
            html.Button('Visualizar Escenario 3D', id='visualize-button', n_clicks=0,
                        className="bg-blue-500 text-white px-4 py-2 rounded mx-2"),
        ]),
    ]),

    html.Div(id="3d-visualization"),
    html.Div(id='upl-value', className="mt-4 text-red-500 text-2xl"),
    html.Div(className="mt-8 flex flex-col items-start", children=[
        html.Div(className="flex flex-row justify-start mb-4", children=[
            html.Div(className="mx-2", children=[
                html.Img(id='2d-visualization', className="mt-4 object-cover"),
            ]),
            html.Div(className="mx-2", children=[
                html.Img(id='tonnage-grade-curve', className="mt-4 object-cover"),
            ]),
        ]),
        html.Div(className="mt-4", children=[
            html.Img(id='histogram', className="mx-auto object-cover"),
        ]),
    ]),
    html.Div(id='hidden-div', style={'display': 'none'}),
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
     Input('visualize-2d-button', 'n_clicks'),
     Input('upl-button', 'n_clicks')],
    [State('period-input', 'value'),
     State('hidden-div', 'children'),
     State('axis-dropdown', 'value'),
     State('axis-value-input', 'value'),
     State('metal_price', 'value'),
     State('metal_recovery', 'value'),
     State('mining_cost', 'value'),
     State('processing_cost', 'value')]
)
def update_visualization(n_clicks_3d, n_clicks_2d, n_clicks_upl, period, scenario_file, axis, axis_value,
                         metal_price, metal_recovery, mining_cost, processing_cost):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {}, '', '', '', ''

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'visualize-button' and n_clicks_3d > 0:
        if scenario_file:
            load_and_visualize_scenario(scenario_file, period, metal_price, metal_recovery, mining_cost, processing_cost)
        return {}, '', '', '', ''

    elif button_id == 'visualize-2d-button' and n_clicks_2d > 0:
        if scenario_file:
            scenario_data = load_scenario(scenario_file, metal_price, metal_recovery, mining_cost, processing_cost)
            mine_plan = pd.read_csv('src/data/MinePlan/MinePlan.txt')
            hist_fig = generate_histogram(scenario_data)
            hist_buf = io.BytesIO()
            hist_fig.savefig(hist_buf, format='png')
            hist_buf.seek(0)
            hist_img_base64 = base64.b64encode(hist_buf.read()).decode('utf-8')
            hist_img_src = f'data:image/png;base64,{hist_img_base64}'
            plt.close(hist_fig)

            curve_fig = generate_tonnage_grade_curve(scenario_data)
            curve_buf = io.BytesIO()
            curve_fig.savefig(curve_buf, format='png')
            curve_buf.seek(0)
            curve_img_base64 = base64.b64encode(curve_buf.read()).decode('utf-8')
            curve_img_src = f'data:image/png;base64,{curve_img_base64}'
            plt.close(curve_fig)

            fig_2d = visualize_2d(scenario_data, axis, axis_value, mine_plan, period)
            buf = io.BytesIO()
            fig_2d.savefig(buf, format='png')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            img_src = f'data:image/png;base64,{img_base64}'
            plt.close(fig_2d)

            return {}, '', hist_img_src, curve_img_src, img_src

    elif button_id == 'upl-button' and n_clicks_upl > 0:
        if scenario_file:
            upl_value, upl_message = load_and_visualize_scenario(scenario_file, period, metal_price, metal_recovery, mining_cost, processing_cost)
            return {}, upl_message, '', '', ''

    return {}, '', '', '', ''

@app.callback(
    Output('output', 'children'),
    [Input('calculate_button', 'n_clicks')],
    [State('metal_price', 'value'),
     State('metal_recovery', 'value'),
     State('mining_cost', 'value'),
     State('processing_cost', 'value'),
     State('hidden-div', 'children')]
)
def update_block_value(n_clicks, metal_price, metal_recovery, mining_cost, processing_cost, scenario_file):
    if n_clicks > 0:
        try:
            scenario_index = scenario_file.split('Scenario')[-1].split('.')[0]
            file_path = f'src/data/Scenarios/Scenario{scenario_index}.txt'
            load_scenario(file_path, metal_price, metal_recovery, mining_cost, processing_cost)
            return html.Div([f'El bloque ha sido calculado con éxito para el escenario {scenario_index}.'], className="text-green-500")
        except Exception as e:
            return f'Error: {str(e)}'
    return html.Div(['Ingrese los valores y haga clic en "Calcular Bloque" para obtener el valor del bloque.'], className="text-red-500")

if __name__ == '__main__':
    app.run_server(debug=True)
