import pandas as pd
from sqlalchemy import create_engine
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_table
#from app import server
app = dash.Dash(__name__,
 external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])

### Data Reading
#postgresql://username:password@host/db_name
engine = create_engine('postgresql://dmunera:1234567dma@database-1.cu06edhpohx2.us-east-2.rds.amazonaws.com/agg_db')
df = pd.read_sql("SELECT * from agg_tb1", engine.connect(),parse_dates = ('entrytime',))

def filter_df(df, exchange, leverage, start_date, end_date):
    df_filter = df[
        (df['exchange'] == exchange) & 
        (df['margin'] == int(leverage)) & 
        ((df['entrytime'] >= start_date) & (df['entrytime'] <= end_date)) ]
    return df_filter
    
## App Layout
app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            # Leverage Selector
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': str(label), 'value': str(label)} for label in df['margin'].unique()
                                        ],
                                        value='1',
                                        labelStyle={'display': 'inline-block'}
                                    ),
                                ]
                            ),
                            html.Div(
                                className="three columns card",
                                children=[
                                    html.H6("Select a Date Range"),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        display_format="MMM YY",
                                        start_date=df['entrytime'].min(),
                                        end_date=df['entrytime'].max()
                                    ),
                                ]
                            ),
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                        'data': []
                   }
                )
            ]
        ), 
        html.Div(
                className="padding row",
                children=[
                    html.Div(
                        className="six columns card",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'number'},
                                    {'name': 'Trade type', 'id': 'tradetype'},
                                    {'name': 'Exposure', 'id': 'exposure'},
                                    {'name': 'Entry balance', 'id': 'entrybalance'},
                                    {'name': 'Exit balance', 'id': 'exitbalance'},
                                    {'name': 'Pnl (incl fees)', 'id': 'pnl'},
                                ],
                                style_cell={'width': '60px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ]
                    ),
                dcc.Graph(
                        id="pnl-types",
                        className="six columns card",
                        figure={},
                        style={'width': 690, 'height' : 470}
                    ), 
                    ]
            ),
    html.Div(
        className="padding row",
                children=[
                     dcc.Graph(
                        id="daily_btc_price",
                        className="six columns card",
                        figure={},
                        style={'width': 690, 'height' : 490}
                    ),
                     dcc.Graph(
                        id="balance_overtime",
                        className="six columns card",
                        figure={},
                        style={'width': 690, 'height' : 490}
                    )

                ]


    ), 
     ])        
])



def calc_returns_over_month(dff):
    out = []
    
    dff['YearMonth'] = df['entrytime'].dt.strftime('%Y-%m')
    
    for name, group in dff.groupby('YearMonth'):
        exit_balance = group.head(1)['exitbalance'].values[0]
        entry_balance = group.tail(1)['entrybalance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': name,
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out


def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['btcprice'].values[0]
    btc_end_value = dff.head(1)['btcprice'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['exitbalance'].values[0]
    end_value = dff.head(1)['entrybalance'].values[0]
    returns = (end_value * 100/ start_value)-100 
    return returns



@app.callback(
    [dash.dependencies.Output('monthly-chart', 'figure'),
    dash.dependencies.Output('market-returns', 'children'),
    dash.dependencies.Output('strat-returns', 'children'),
    dash.dependencies.Output('strat-vs-market', 'children')],
    [
      dash.dependencies.Input('exchange-select', 'value'),
      dash.dependencies.Input('leverage-select', 'value'),
      dash.dependencies.Input('date-range', 'start_date'),
      dash.dependencies.Input('date-range', 'end_date')
    ]
)
## Update CandleStick Chart
def update_monthly_candlestick(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    data = pd.DataFrame(calc_returns_over_month(dff))
    return ({
        'data': [go.Candlestick(
            open=data.entry.values.tolist(),
            close=data.exit.values.tolist(),
            x = data.month.values.tolist(),
            low = data.entry.values.tolist(),
            high = data.exit.values.tolist()
         )],
     'layout': {'title': 'Overview of Monthly performance'}},str(round(btc_returns,2)) + '%',
     str(round(strat_returns,2)) + '%',str(round(strat_vs_market,2)) + '%')




@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')


@app.callback(
    dash.dependencies.Output('pnl-types', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)

def update_barchart(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    dff['Date'] = pd.to_datetime(dff['entrytime'].dt.strftime('%Y-%m-%d'))
    # Filter Trade Types
    dff_lg = dff[dff['tradetype'] == 'Long']
    dff_st = dff[dff['tradetype'] == 'Short']

    return {
        'data': [
            go.Bar(
            x = dff_lg['entrytime'],
            y = dff_lg['pnl'].values.tolist(),
            name = "Long" , 
            marker = {'color':"red"}), 
            go.Bar(
            x = dff_st['entrytime'],
            y = dff_st['pnl'].values.tolist(),
            name = "Short",
            marker = {'color':"black"}) 
             ],
     'layout': {'title': 'Pnl vs Trade Type' ,
                'type':'date'}}



@app.callback(
    dash.dependencies.Output('daily_btc_price', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)

def update_btc(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)

    return {
        'data': [
            go.Scatter(
            x = dff['entrytime'],
            y = dff['btcprice'].values.tolist(),
            mode='lines', 
            marker = {'color':"tomato"})
             ],
     'layout': {'title': 'Daily BTC Price' ,
                'type':'date'}}



@app.callback(
    dash.dependencies.Output('balance_overtime', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)

def update_balance_overtime(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    dff['Balance'] = (dff['exitbalance'] + dff['entrybalance'])/2

    return {
        'data': [
            go.Scatter(
            x = dff['entrytime'],
            y = dff['Balance'].values.tolist(),
            mode='lines')
             ],
     'layout': {'title': 'Balance Overtime' ,
                'type':'date'}}







if __name__ == "__main__":
    app.run_server(debug=True)
