import dash
import math
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime
import numpy as np
import time
import base64
from data_extractor import DataExtractor


def load_data():
    df = DataExtractor().get_data()

    #df = pd.read_csv("data/data_extraction_data.csv")

    #df = pd.read_csv("data/ng5_experiment_base.csv",
    #                 delimiter = ",")


    df['theday'] = df['theday'].astype('str')
    df['thedayunix'] = pd.to_datetime(df['theday']).astype(np.int64) // 10**9
    # some dates are empty
    df = df.dropna()
    return df

def unixTimeMillis(dt):
    ''' Convert datetime to unix timestamp '''
    return int(time.mktime(dt.timetuple()))

def getMarks(data, n):
    daterange = pd.date_range(start=pd.to_datetime(data.min(),unit='s'),end=pd.to_datetime(data.max(), unit = 's'),freq='d')
    result = {}
    for index, date in enumerate(daterange):
        if(index%n == 0):
            result[unixTimeMillis(date)] = str(date.strftime('%Y-%m-%d'))

    if not unixTimeMillis(daterange.max()) in result:
        result[unixTimeMillis(daterange.max())] = str(daterange.max().strftime('%Y-%m-%d'))


    return result



df = load_data()
unique_experiments = df['experimenttypename'].unique()
unique_languages = df['culturekey'].unique()


image_filename = 'test.jpg' # replace with your own image
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

app = dash.Dash()
server = app.server

# adds a nice look to the app
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})


app.layout = html.Div(children=[
    html.Img(src='data:image/png;base64,{}'.format(encoded_image),
	style={'display': 'block',
		'margin-left': 'auto',
		'margin-right': 'auto',
		'width': '20%',
		'height': 'auto'}),
    html.H1(children='Experiments Dashboard', style={
        'textAlign': 'center',
    }),
    html.Div([
	html.Label('device'),
        dcc.Dropdown(
            id='device-dropdown',
            options=[{'label': 'desktop', 'value': 1},
                     {'label': 'other', 'value': 0}]
        ),
	html.Label('experiment'),
        dcc.Dropdown(
            id='experiment-id',
            options=[{'label': i, 'value': i} for i in unique_experiments],
            value = unique_experiments[0],
            clearable = False
        )
    ],
    style={'width': '48%', 'display': 'inline-block'}),
    html.Div([
	html.Label('metric'),
        dcc.Dropdown(
            id='metric-dropdown',
            options=[{'label': 'trial', 'value': 'trial'},
                     {'label': 'sco30m', 'value': 'sco30m'},
                     {'label': 'qp6h', 'value': 'qp6h'},
                     {'label': 'completedcheckout30m', 'value': 'completedcheckout30m'}],
            value = 'trial',
            clearable = False
        ),
        html.Label('language'),
        dcc.Dropdown(
            id='language-id',
            options=[{'label': i, 'value': i} for i in unique_languages],
            multi = True
        )
    ],
    style={'width': '48%', 'display': 'inline-block'}),
    html.Div([
        html.Div([
            html.H4("Absolute metrics", style = {'textAlign': 'center'}),
            dcc.Graph(id = 'metrics-per-period')],
                 className="six columns"),
        html.Div([
            html.H4("Ratio: experiment/regular", style = {'textAlign': 'center'}),
            dcc.Graph(id = 'ratio-per-period')],
                 className="six columns")
    ], className="row"),
    html.Div([
        dcc.RangeSlider(
            id = 'theday-slider',
            min = df['thedayunix'].min(),
            max = df['thedayunix'].max(),
            value = [df['thedayunix'].min(), df['thedayunix'].max()],
            step = None,
            marks= getMarks(df['thedayunix'], 14)
        ),
    ],
    style={'width': '100%', 'display': 'inline-block', 'textAlign': 'center'}),
    # this guy is a way of caching data within the browser, to share data among callbacks
    html.Div(id='caching-in-browser', style={'display': 'none'})
])

# caching filtered data for sharing
@app.callback(dash.dependencies.Output('caching-in-browser', 'children'),
              [dash.dependencies.Input('theday-slider', 'value'),
               dash.dependencies.Input('device-dropdown', 'value'),
               dash.dependencies.Input('experiment-id', 'value'),
               dash.dependencies.Input('language-id', 'value')
               ])
def clean_data(date_range, isdesktop, experiment, language):
    date_start = date_range[0]
    date_end = date_range[1]
    filtered_df = df[(df.thedayunix >= date_start) & (df.thedayunix <= date_end)]
    filtered_df = filtered_df[filtered_df['isdesktop'] == isdesktop] if isdesktop is not None else filtered_df
    filtered_df = filtered_df[filtered_df['experimenttypename'] == experiment] if experiment is not None else filtered_df
    filtered_df = filtered_df[filtered_df['culturekey'].isin(language)] if language else filtered_df
    return filtered_df.to_json(orient = 'split')



# metric scatter plot
@app.callback(
    dash.dependencies.Output('metrics-per-period', 'figure'),
    [dash.dependencies.Input('caching-in-browser', 'children'),
     dash.dependencies.Input('metric-dropdown', 'value')
     ])
def update_ratios_plot(cleaned_json_data, metric):
    local_df = pd.read_json(cleaned_json_data, orient='split')
    traces = []
    for i in local_df['experimentmodename'].unique():
        df_by_experiment = local_df[local_df['experimentmodename'] == i]
        grouped_df = df_by_experiment.groupby('theday').sum()[metric].reset_index()
        traces.append(go.Scatter(
            x = grouped_df['theday'],
            y = grouped_df[metric],
            name = i
        ))


    return {
        'data': traces,
	'layoyt': go.Layout(
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            hovermode='closest'
        )
    }


# ratios scatter plot
@app.callback(
    dash.dependencies.Output('ratio-per-period', 'figure'),
    [dash.dependencies.Input('caching-in-browser', 'children'),
     dash.dependencies.Input('metric-dropdown', 'value')
     ])
def update_metrics_plot(cleaned_json_data, metric):
    local_df = pd.read_json(cleaned_json_data, orient='split')

    regular_df = local_df[local_df['experimentmodeid'] == 1]\
        .groupby('theday').sum()[metric].reset_index()\
        .rename(index=str, columns={metric: "regular"})

    experiment_df = local_df[local_df['experimentmodeid'] == 2]\
        .groupby('theday').sum()[metric].reset_index()\
        .rename(index=str, columns={metric: "experiment"})

    ratio_df = regular_df.merge(experiment_df, on = 'theday')


    # calculate ratio metrics
    ratio_df['ratio'] = ratio_df["experiment"] / ratio_df["regular"]
    ratio_df['rolling_ratio'] = ratio_df['experiment'].rolling(7, min_periods = 7).sum() / ratio_df['regular'].rolling(7, min_periods = 1).sum()


    # try calculating a mean if there is enough data in both tracks
    try:
        mean = float(ratio_df["experiment"].sum()) / float(ratio_df["regular"].sum())
    except ZeroDivisionError:
        mean = 0

    ratio_df['mean'] = mean


    # try calculating the error 4 sigmas above and below, if there is enough data as well
    try:
        error = 4 / math.sqrt(ratio_df["regular"].sum())
    except ZeroDivisionError:
        error = 0
    ratio_df['mean_upper_bound'] = ratio_df['mean'] + error
    ratio_df['mean_lower_bound'] = ratio_df['mean'] - error


    # base line
    ratio_df['baseline'] = 1


    # build the figure
    traces = []

    lines = ['ratio', 'baseline','rolling_ratio', 'mean', 'mean_upper_bound', 'mean_lower_bound' ]
    for line in lines:
        x = ratio_df['theday']
        y = ratio_df[line]
        mode = 'markers' if line == 'ratio' else 'lines'
        traces.append(go.Scatter(
            x = x,
            y = y,
            mode = mode,
            name = line,
            line =  {
                'dash': "dot" if line == "mean_upper_bound" or line == "mean_lower_bound" else "solid",
                'color': 'rgb(0,0,0)' if 'mean' in line else None
            }
        ))



    return {
        'data': traces,
	'layoyt': go.Layout(
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            hovermode='closest'
        )
    }




if __name__ == '__main__':
    app.run_server(debug=True)
