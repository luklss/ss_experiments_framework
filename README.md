Command to temporarly refresh experiment data
psql -P pager=off -c -t -A -F',' -f sql/ng5_one_to_one_experiment.sql -o data/ng5_experiment_base.csv

To do's:
- Find a better deployment solution
- Implement a data extraction per experiment with a set of start/end dates
- Center the ratios around 0 and use percentages, so it gets more intuitive
