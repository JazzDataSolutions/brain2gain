import dash
import pandas as pd
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output

from app.core.database import engine

dash_app = dash.Dash(__name__, requests_pathname_prefix="/dash/")


def fetch_revenue():
    with engine.sync_engine.connect() as conn:
        df = pd.read_sql(
            """
            SELECT date_trunc('day', order_date) AS fecha,
                   SUM(qty*unit_price)::float AS revenue
            FROM sales_items si JOIN sales_orders so USING(so_id)
            GROUP BY fecha ORDER BY fecha
        """,
            conn,
        )
    return df


dash_app.layout = html.Div([html.H1("Ingresos diarios"), dcc.Graph(id="rev-diaria")])


@dash_app.callback(Output("rev-diaria", "figure"), Input("rev-diaria", "id"))
def update_graph(_):
    df = fetch_revenue()
    fig = px.line(df, x="fecha", y="revenue", title="Ventas diarias")
    return fig
