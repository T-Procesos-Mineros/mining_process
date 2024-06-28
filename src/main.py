import dash
from app.layout import layout
from app.callbacks import register_callbacks

# Call the ability to add external scripts
external_scripts = [
    {'src': 'https://cdn.tailwindcss.com'}
]

app = dash.Dash(__name__, external_scripts=external_scripts)
app.layout = layout

# Register callbacks
register_callbacks(app)

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)