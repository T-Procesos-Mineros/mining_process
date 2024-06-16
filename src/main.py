import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from modules.visualization import load_and_visualize_scenario, load_scenario, generate_histogram, \
    generate_tonnage_grade_curve
import io
import base64
import matplotlib.pyplot as plt

# call the ability to add external scripts
external_scripts = [
    {'src': 'https://cdn.tailwindcss.com'}
]

app = dash.Dash(__name__,
                external_scripts=external_scripts
                )

# Define la estructura de la interfaz
app.layout = html.Div([
    html.H1("Plan Minero", className="text-4xl font-bold mb-8 text-center"),
    html.Div(
        [html.Button(f"ESCENARIO {i}", id=f"btn-scenario-{i}", n_clicks=0,
                     className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mx-2 my-2") for i
         in range(10)],
        className="flex flex-wrap justify-center"
    ),
    html.Div(id='scenario-content', className="mt-8"),
    dcc.Graph(id='3d-visualization', className="mt-4"),
    html.Img(id='histogram', className="mt-4"),  # Para mostrar el histograma
    html.Img(id='tonnage-grade-curve', className="mt-4"),  # Para mostrar la curva Tonelaje-Ley
    html.Div(id='upl-value', className="mt-4 text-center text-2xl font-bold")
], className="container mx-auto p-4")


# Callback para manejar la visualización del escenario seleccionado
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
        html.Label("Seleccione el Período:", className="block mb-2"),
        dcc.Input(id='period-input', type='number', value=0, className="block mb-4"),
        html.Button('Visualizar Escenario', id='visualize-button', n_clicks=0,
                    className="bg-green-500 text-white px-4 py-2 rounded"),
        html.Div(id='hidden-div', children=scenario_file, style={'display': 'none'})
    ])


# Callback para actualizar la visualización 3D, mostrar el valor del UPL, el histograma y la curva Tonelaje-Ley
@app.callback(
    [Output('3d-visualization', 'figure'),
     Output('upl-value', 'children'),
     Output('histogram', 'src'),
     Output('tonnage-grade-curve', 'src')],
    [Input('visualize-button', 'n_clicks')],
    [State('period-input', 'value'),
     State('hidden-div', 'children')]
)
def update_visualization(n_clicks, period, scenario_file):
    if n_clicks > 0:
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

        return {}, f'Ultimate Pit Limit Value (Total Metal Content): {upl_value}', hist_img_src, curve_img_src
    return {}, '', '', ''


# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)
