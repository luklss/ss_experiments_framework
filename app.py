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



readme_content = '''
### Need some help?

#### Interacting

You can interact with the graphs in a few ways:
* You can filter the data using the dropwdowns and the date bar below the plots. All filtering happens simultaneously for both graphs.
* You can also zoom in by selecting an area of a given chart, and double clicking in the graph to go back to the full view of the currently filtered data. But remember, zooming in this way **does not** filter the data.
* Lastly, you can also remove a given line in the chart by clicking on it at the legend.

#### Interpreting

The plot on the left (absolute metrics) should be straight forward, it simply shows the **absolute value** of the currently selected metric for the given period and filters.

The right plot can be a bit trickier. It shows much better (or worst) the experiment is performing when compared to the regular track (in percentage points) for the given metric selected. If, for instance, this ratio is 5 in a given day, that means that in that day the experiment track performed 5\% better than the regular. However, how do we know when this is statistically significant? This can get hairy very fast, and is out of this cope of this help, but here is a list of the other lines in the graph that can help us to have a bigger picture statistically:

* **ratio**: the percentage difference between tracks for a given day as described above. A positive value means that the experiment has more of that metric.
* **rolling_ratio**: the seven day average of the percentage difference between the tracks. This is the same as above but fluctuates less since is the average of the past week.
* **mean**: the percentage difference between tracks for the **totality** of the filtered data.
* **mean_upper_bound** and **mean_lower_bound**: a statistical approximation of the confidence of the mean measure given plus or minus 4 sigmas. This is an attempt in estimating how wrong we can be or how much we can trust that measure statistically speaking. For instance, every one can related to when in a presidential election we have a candidate that has 32 plus or minus 3 percent of the vote intentions. This is analogous.
'''



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
    days_per_interval = len(daterange) / n
    for index, date in enumerate(daterange):
        if(index % days_per_interval == 0):
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
        html.Label('Experiment', style = {'fontWeight':'bold'}),
        dcc.Dropdown(
            id='experiment-id',
            options=[{'label': i, 'value': i} for i in unique_experiments],
            value = unique_experiments[0],
            clearable = False
        ),
        html.P(children = 'esting this component testing this component testing this component testing this component testing this component testing this component testing this component testing this component testing this component testing this component testing this component testing this component', style = {'margin-top': 20}),
    ],
             style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top', 'textAlign': 'justify', 'marginRight':'50', 'marginLeft': '50'}),
    html.Div([
	html.Label('Metric', style = {'fontWeight':'bold'}),
        dcc.Dropdown(
            id='metric-dropdown',
            options=[{'label': 'trial - signups', 'value': 'trial'},
                     {'label': 'sco30m - seen the checkout within 30m of signup', 'value': 'sco30m'},
                     {'label': 'qp6h - became payer within 6 hours of the trial ', 'value': 'qp6h'},
                     {'label': 'completed checkout within 30 minutes', 'value': 'completedcheckout30m'}],
            value = 'trial',
            clearable = False
        ),
        html.Label('Language', style = {'fontWeight':'bold'}),
        dcc.Dropdown(
            id='language-id',
            options=[{'label': i, 'value': i} for i in unique_languages],
            multi = True
        ),
        html.Label('Device', style = {'fontWeight':'bold'}),
        dcc.Dropdown(
            id='device-dropdown',
            options=[{'label': 'desktop', 'value': 1},
                     {'label': 'other', 'value': 0}]
        )
    ],
    style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top', 'textAlign': 'justify', 'marginRight':'50', 'marginLeft': '50'}),
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
            marks= getMarks(df['thedayunix'], 10)
        ),
    ],
    style={'width': '95%',  'marginRight':'50', 'marginLeft':'50'}),
    # this guy is a way of caching data within the browser, to share data among callbacks
    html.Div([
        dcc.Markdown(children=readme_content),
    ],
             style = {'marginTop': 100, 'font-size': '110%', 'marginRight' : 50, 'marginLeft': 50}),
    html.Div(id='caching-in-browser', style={'display': 'none'})
])


@app.callback(dash.dependencies.Output('theday-slider', 'min'),
              [dash.dependencies.Input('experiment-id', 'value')
               ])
def update_slider(experiment):
    local_df = df[df['experimenttypename'] == experiment]
    return local_df['thedayunix'].min()


@app.callback(dash.dependencies.Output('theday-slider', 'max'),
              [dash.dependencies.Input('experiment-id', 'value')])
def update_slider(experiment):
    local_df = df[df['experimenttypename'] == experiment]
    return local_df['thedayunix'].max()

@app.callback(dash.dependencies.Output('theday-slider', 'marks'),
              [dash.dependencies.Input('experiment-id', 'value')])
def update_slider(experiment):
    local_df = df[df['experimenttypename'] == experiment]
    return getMarks(local_df['thedayunix'], 10)


@app.callback(dash.dependencies.Output('theday-slider', 'value'),
              [dash.dependencies.Input('experiment-id', 'value')])
def update_slider(experiment):
    local_df = df[df['experimenttypename'] == experiment]
    print [local_df['thedayunix'].min(), local_df['thedayunix'].max()]
    print [local_df['theday'].min(), local_df['theday'].max()]
    return [local_df['thedayunix'].min(), local_df['thedayunix'].max()]


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


    # build the figure
    traces = []

    lines = ['ratio', 'rolling_ratio', 'mean', 'mean_upper_bound', 'mean_lower_bound' ]
    for line in lines:
        x = ratio_df['theday']
        y = (ratio_df[line] - 1) * 100
        mode = 'markers' if line == 'ratio' else 'lines'
        traces.append(go.Scatter(
            x = x,
            y = y,
            mode = mode,
            name = line,
            line =  {
                'dash': "dot" if line == "mean_upper_bound" or line == "mean_lower_bound" else "solid",
                'color': 'rgb(50,200,50)' if 'mean' in line else None
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
