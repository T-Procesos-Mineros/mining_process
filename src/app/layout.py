from dash import dcc, html

layout = html.Div([
    # Navbar superior
    html.Div([
        html.Div([
            html.Button('Visualizar en 2D', id='visualize-2d-button', n_clicks=0,
                        className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded mr-2"),
            html.Button('Visualizar Escenario', id='visualize-button', n_clicks=0,
                        className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded mr-2"),
            html.Label('Seleccionar el Período:', className="ml-4"),
            dcc.Input(id='period-input', type='number', value=0, className="border-gray-300 border rounded px-2 py-1 ml-2"),
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