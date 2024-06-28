from dash import dcc, html

layout = html.Div([
    html.H1("Plan Minero", className="text-4xl font-bold mb-8 text-center"),
    html.Div(
        [html.Button(f"ESCENARIO {i}", id=f"btn-scenario-{i}", n_clicks=0,
                     className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mx-2 my-2") for i
         in range(10)],
        className="flex flex-wrap justify-center"
    ),
    html.Div(id='scenario-content', className="mt-8"),
    dcc.Graph(id='3d-visualization', className="mt-4"),
    html.Img(id='histogram', className="mt-4"),
    html.Img(id='tonnage-grade-curve', className="mt-4"),
    html.Div(id='upl-value', className="mt-4 text-center text-2xl font-bold"),
    html.Button('Visualizar en 2D', id='visualize-2d-button', n_clicks=0,
                className="bg-red-500 text-white px-4 py-2 rounded"),
    html.Div(id='2d-visualization-settings', children=[
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
        dcc.Input(id='axis-value-input', type='number', value=0)
    ], className="mt-4")
], className="container mx-auto p-4")