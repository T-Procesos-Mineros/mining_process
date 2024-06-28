import dash
from app.layout import layout
from app.callbacks import register_callbacks

external_scripts = [
    {'src': 'https://cdn.tailwindcss.com'}
]

app = dash.Dash(__name__, external_scripts=external_scripts)
app.title = "Alto de los Andes"
app.layout = layout

register_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True)