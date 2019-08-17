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
import yaml
import os
from flask_caching import Cache
from data_extractor import DataExtractor
import time

CACHE_TIMEOUT = 60*30 # every three hours
README_CONTENT = open('help.md', 'r').read()
LOGO = 'imgs/logo.jpg'

# Because callbacks run in paralell, this is needed in order to prevent the db from being called 
# multiple times
global LOADING_DB_DATA
LOADING_DB_DATA = False

# if the caching location is defined, it will try to load the data from there.
# if it is None, then it will fetch from the DB
#CSV_LOCATION = "data.csv"
CSV_LOCATION = None


# the path for the exp config file
EXP_PARAMS_PATH = "experiment_config.yaml"

# define the app globally
app = dash.Dash(__name__)
server = app.server



# set up caching folder and system
cache_folder = "cache"

if not os.path.exists(cache_folder):
    os.makedirs(cache_folder)

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': cache_folder,
    'CACHE_THRESHOLD': 5
})


# load experiment descriptions and check length
experiments_params = yaml.load(open('experiment_config.yaml', 'r'))
for key, value in experiments_params.iteritems():
    assert len(value['description']) < 572, "experiment description has to have less than 572 characters"

def dataframe():
    ''' Reloads the main dataframe used for this application '''
    exp_params = yaml.load(open(EXP_PARAMS_PATH, 'r'))
    return pd.read_json(load_data(exp_params), orient='split')


@cache.memoize(timeout=CACHE_TIMEOUT)
def load_data(exp_params):
    ''' Loads the data from a CSV or from the db, and it will cache the results '''
    start = time.time()

    if CSV_LOCATION: # uses a global variable, ugly but prettier than passing it every time
        print "reading data from local csv"
        df = pd.read_csv(CSV_LOCATION)
    elif not LOADING_DB_DATA:
        print "fetching data from db or cache"
        global LOADING_DB_DATA
        LOADING_DB_DATA = True
        df = DataExtractor(exp_params).get_data()
        LOADING_DB_DATA = False

    else:
        print "waiting for query to end"
        while (LOADING_DB_DATA):
            time.sleep(1)
        df = DataExtractor(exp_params).get_data()


    # get date to be a string and also saves the unix time for every date
    df['theday'] = df['theday'].astype('str')
    df['thedayunix'] = pd.to_datetime(df['theday']).astype(np.int64) // 10**9

    # drop any empty values
    df = df.dropna()

    end = time.time()
    print "loading data took {} seconds".format(end - start)

    return df.to_json(date_format='iso', orient='split')

def datetime_tounix(dt):
    ''' Convert datetime to unix timestamp '''
    return int(time.mktime(dt.timetuple()))

def get_marks(data, n):
    '''
    Get the marks for the dash graph based on the data series and how many intervals should be displayed

    Args:
        data: a pandas series of dates as ints in the unix format.
        n: how many intervals should be in the marks

    Examples:
        if the data ranges from 2018-02-01 to 2018-02-21 and n = 4
        then the output will be:
            {unixdate: 2018-02-01, unixdate: 2018-02-07, unixdate: 2018-02-14, unixdate: 2018-02-21}

    returns:
        a dictonary mapping a unix value to a string representing a date in the format YYYY-mm-dd
    '''

    result = {}
    # initialize a data range with every date from min to max in the df
    daterange = pd.date_range(start=pd.to_datetime(data.min(),unit='s'),end=pd.to_datetime(data.max(), unit = 's'),freq='d')

    # include the smallest and large dates first 
    result[datetime_tounix(daterange.max())] = str(daterange.max().strftime('%Y-%m-%d'))
    result[datetime_tounix(daterange.min())] = str(daterange.min().strftime('%Y-%m-%d'))

    # if the remaining dates are smaller than the number of date points to include, just include all of them
    if n > len(daterange) - 2:
        for index, date in enumerate(daterange):
            result[datetime_tounix(date)] = str(date.strftime('%Y-%m-%d'))

    # otherwise calculate how many to include and include them evenly spaced
    else:
        days_per_interval = len(daterange) / n # get how many days per interval there should be
        for index, date in enumerate(daterange):
            if(index % days_per_interval == 0): # only include evenly spaced 
                result[datetime_tounix(date)] = str(date.strftime('%Y-%m-%d'))


    return result



def generate_layout():
    ''' Generates the app layout '''
    enconded_logo = base64.b64encode(open(LOGO, 'rb').read())
    df = dataframe()
    unique_experiments = df['experimenttypename'].unique()
    unique_languages = df['culturekey'].unique()
    unique_channels = df['channel'].unique()
    unique_segments = df['segment'].unique()

    return html.Div(children=[
        html.Img(src='data:image/png;base64,{}'.format(enconded_logo),
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
            html.P(id = 'experiment-description',
                   style = {'margin-top': 20}),
        ],
                 style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top', 'textAlign': 'justify', 'marginRight':'50', 'marginLeft': '50'}),
        html.Div([
            html.Label('Metric', style = {'fontWeight':'bold'}),
            dcc.Dropdown(
                id='metric-dropdown',
                options=[{'label': 'trial - signups', 'value': 'trial'},
                         {'label': 'sco30m - seen the checkout within 30m of signup', 'value': 'sco30m'},
                         {'label': 'completed checkout within 30 minutes', 'value': 'completedcheckout30m'},
                         {'label': 'qp6h - became payer within 6 hours of the trial ', 'value': 'qp6h'},
                         {'label': 'paid - became payer ', 'value': 'paid'},
                         {'label': 'edit30m - edit type of content edit/save in the first 30m', 'value': 'edit30m'},
                         {'label': 'w1return - any login in the first week of lifetime', 'value': 'w1return'},
                         {'label': 'lowqualret - low quality users', 'value': 'lowqualret'},
                         {'label': 'medqualret - medium quality users', 'value': 'medqualret'},
                         {'label': 'highqualret - high quality users', 'value': 'highqualret'}],
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
            ),
            html.Label('Channel', style = {'fontWeight':'bold'}),
            dcc.Dropdown(
                id='channel-dropdown',
                options=[{'label': i, 'value': i} for i in unique_channels],
                multi = True
            ),
            html.Label('Segment', style = {'fontWeight':'bold'}),
            dcc.Dropdown(
                id='segment-dropdown',
                options=[{'label': i, 'value': i} for i in unique_segments],
                multi = True
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
            dcc.RangeSlider(id = 'theday-slider'),
        ],
        style={'width': '95%',  'marginRight':'50', 'marginLeft':'50'}),
        # this guy is a way of caching data within the browser, to share data among callbacks
        html.Div([
            dcc.Markdown(children=README_CONTENT),
        ],
                 style = {'marginTop': 100, 'font-size': '110%', 'marginRight' : 50, 'marginLeft': 50}),
        html.Div(id='caching-in-browser', style={'display': 'none'})
    ])





app.layout = generate_layout()



# app callbacks

@app.callback(dash.dependencies.Output('experiment-description', 'children'),
              [dash.dependencies.Input('experiment-id', 'value')
               ])
def update_description(experiment):
    ''' Update experiment descriptions '''
    return experiments_params[experiment]['description']


@app.callback(dash.dependencies.Output('theday-slider', 'min'),
              [dash.dependencies.Input('experiment-id', 'value')
               ])
def update_slider(experiment):
    ''' Updates the date sliders min date '''
    df = dataframe()
    local_df = df[df['experimenttypename'] == experiment]
    return local_df['thedayunix'].min()


@app.callback(dash.dependencies.Output('theday-slider', 'max'),
              [dash.dependencies.Input('experiment-id', 'value')])
def update_slider(experiment):
    ''' Updates the date sliders date '''
    df = dataframe()
    local_df = df[df['experimenttypename'] == experiment]
    return local_df['thedayunix'].max()

@app.callback(dash.dependencies.Output('theday-slider', 'marks'),
              [dash.dependencies.Input('experiment-id', 'value')])
def update_slider(experiment):
    ''' Updates the date sliders marks '''
    df = dataframe()
    local_df = df[df['experimenttypename'] == experiment]
    return get_marks(local_df['thedayunix'], 10)


@app.callback(dash.dependencies.Output('theday-slider', 'value'),
              [dash.dependencies.Input('experiment-id', 'value')])
def update_slider(experiment):
    ''' Updates the date sliders value '''
    df = dataframe()
    local_df = df[df['experimenttypename'] == experiment]
    return [local_df['thedayunix'].min(), local_df['thedayunix'].max()]


# caching filtered data for sharing
@app.callback(dash.dependencies.Output('caching-in-browser', 'children'),
              [dash.dependencies.Input('theday-slider', 'value'),
               dash.dependencies.Input('device-dropdown', 'value'),
               dash.dependencies.Input('experiment-id', 'value'),
               dash.dependencies.Input('language-id', 'value'),
               dash.dependencies.Input('channel-dropdown', 'value'),
               dash.dependencies.Input('segment-dropdown', 'value')
               ])
def clean_data(date_range, isdesktop, experiment, language, channels, segments):
    ''' Clean data based on all the dropdowns '''
    df = dataframe()
    start = time.time()
    date_start = date_range[0]
    date_end = date_range[1]
    filtered_df = df[(df.thedayunix >= date_start) & (df.thedayunix <= date_end)]
    filtered_df = filtered_df[filtered_df['isdesktop'] == isdesktop] if isdesktop is not None else filtered_df
    filtered_df = filtered_df[filtered_df['experimenttypename'] == experiment] if experiment is not None else filtered_df
    filtered_df = filtered_df[filtered_df['culturekey'].isin(language)] if language else filtered_df
    filtered_df = filtered_df[filtered_df['channel'].isin(channels)] if channels else filtered_df
    filtered_df = filtered_df[filtered_df['segment'].isin(segments)] if segments else filtered_df

    end = time.time()
    print "recalculating data took {} seconds".format(end - start)

    return filtered_df.to_json(orient = 'split')




# metric scatter plot
@app.callback(
    dash.dependencies.Output('metrics-per-period', 'figure'),
    [dash.dependencies.Input('caching-in-browser', 'children'),
     dash.dependencies.Input('metric-dropdown', 'value')
     ])
def update_ratios_plot(cleaned_json_data, metric):
    """ Callback for the "ratios" plot """
    start = time.time()
    local_df = pd.read_json(cleaned_json_data, orient='split')
    end = time.time()
    print "reading cached json for the metrics plot took {} seconds".format(end - start)

    traces = []
    for i in local_df['experimentmodename'].unique():
        df_by_experiment = local_df[local_df['experimentmodename'] == i]
        grouped_df = df_by_experiment.groupby('theday').sum()[metric].reset_index()
        traces.append(go.Scatter(
            x = grouped_df['theday'],
            y = grouped_df[metric],
            name = i,
            line = {'color': 'rgb(50,200,50)' if i == 'Regular' else None}
        ))



    end = time.time()
    print "builinding the underlying objects for the metrics plot took {} seconds".format(end - start)

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
    """ Callback for the normal metrics plot """
    start = time.time()
    local_df = pd.read_json(cleaned_json_data, orient='split')
    end = time.time()
    print "reading cached json for the ratios plot took {} seconds".format(end - start)

    num_unique_exp_modes = len(local_df['experimentmodeid'].unique())

    # if there are more than 2 expeirment modes, we return an empty figure
    if num_unique_exp_modes > 2:
        return {
            'data': [],
            'layoyt': go.Layout(
                margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                hovermode='closest'
            )
        }

    # otherwise, lets build the plot

    regular_df = local_df[local_df['experimentmodeid'] == 1]\
        .groupby('theday').sum()[metric].reset_index()\
        .rename(index=str, columns={metric: "regular"})

    experiment_df = local_df[local_df['experimentmodeid'] == 2]\
        .groupby('theday').sum()[metric].reset_index()\
        .rename(index=str, columns={metric: "experiment"})

    ratio_df = regular_df.merge(experiment_df, on = 'theday')


    # calculate ratio metrics
    ratio_df['performance'] = ratio_df["experiment"] / ratio_df["regular"]
    ratio_df['7_day_average_performance'] = ratio_df['experiment'].rolling(7, min_periods = 7).sum() / ratio_df['regular'].rolling(7, min_periods = 1).sum()


    # try calculating a mean if there is enough data in both tracks
    try:
        mean = float(ratio_df["experiment"].sum()) / float(ratio_df["regular"].sum())
    except ZeroDivisionError:
        mean = 0

    ratio_df['total_performance'] = mean


    # try calculating the error 4 sigmas above and below, if there is enough data as well
    try:
        error = 4 / math.sqrt(ratio_df["regular"].sum())
    except ZeroDivisionError:
        error = 0
    ratio_df['total_performance_upperbound'] = ratio_df['total_performance'] + error
    ratio_df['total_performance_lowerbound'] = ratio_df['total_performance'] - error


    # build the figure
    traces = []

    lines = ['performance', '7_day_average_performance', 'total_performance', 'total_performance_upperbound', 'total_performance_lowerbound' ]
    for line in lines:
        x = ratio_df['theday']
        y = (ratio_df[line] - 1) * 100
        mode = 'markers' if line == 'performance' else 'lines'
        traces.append(go.Scatter(
            x = x,
            y = y,
            mode = mode,
            name = line,
            line =  {
                'dash': "dot" if line == "total_performance_upperbound" or line == "total_performance_lowerbound" else "solid",
                'color': 'rgb(50,200,50)' if 'total_performance' in line else None
            }
        ))

    end = time.time()
    print "builinding the underlying objects for the ratio plot took {} seconds".format(end - start)


    return {
        'data': traces,
	'layoyt': go.Layout(
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            hovermode='closest'
        )
    }






if __name__ == '__main__':
    cache.delete_memoized(load_data)
    app.run_server(debug = True) # use to run locally    
