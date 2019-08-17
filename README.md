# Experiments analysis framework

### Version 

The app is built under python version ```2.7.15``` and it looks like the screenshot below


![The app!](https://github.com/simplesite/analytics-experiments-framework/blob/master/imgs/app_look.png)

### Running the app

Please check the general documentation on the Analytics apps [here](https://github.com/simplesite/analytics-wiki/wiki/Dashboard-apps)


### Configurations

If set to be hooked from the db, the app will fetch data for each experiment in the given period as specified by the contents of an ```yaml``` config file, which can look like this:

``` yaml
MyFirstExperiment:
  dates: ["2018-07-23", "2018-08-27"]
  description: This is the the description of the experiment.
               Add somenthing that makes sense here.

MySecondExperiment:
  dates: ["2018-04-21", ""]
  description: This is the the description of the experiment.
               Add somenthing that makes sense here.
```

If the second date is not specified, then it indicates that the experiment is still running and data until yesterday will be fetched.

The database fetching happens using a base query that controls which parameters are to be fetched, then the ```data_extractor.py``` takes care of modifying the ```where``` part of the sql statement based on the ```yaml``` config file.


### Expected behaviour

There are a few design decisions enforced:
- Any day of data containing an ```NA``` value will be dropped to avoid issues.
- Redshift automatically caches a repeated query, and the application will also cache the data for whatever ```TIMEOUT``` period is set. However, whenever the query changes (e.g. new day) new data will be fetched.


### Using the data_extractor.py as stand alone

You can also extract data from the DB based on the same ```yaml``` file by using ```data_extractor.py``` as a stand alone. Just do for instance:
```bash
python data_extractor.py -c experiment_config.yaml -q sql/base_sql_grouped.sql -o data.csv
```
