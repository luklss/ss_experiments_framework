import argparse
import psycopg2
import os
import datetime
import pandas as pd
import yaml


class DataExtractor:
    """
    This class purpouse is to extract experiments related data from the DB.

    Args:
        experiment_params: The path with the YAML file containing the experiment configurations.
            The format is as follows:
            myninceexperiment1:
              dates: ["2018-07-23", "2018-08-27"]
              description: This is the the description of the experiment.

        base_query: The path to the query that is later modified by this class. inserting
            the propoer where statements to filter for the proper experiments

    """

    def __init__(self,
                 experiment_params = None,
                 base_query = 'sql/base_sql_grouped.sql'):
        self.experiment_params = experiment_params
        self.base_query = open(base_query).read()
        self.yesterday_date = self.get_yesterday()
        self.query = self.mount_query()
        self.data = self.extract_data()



    def get_yesterday(self):
        """ Gets yesterday's date """
        return (datetime.date.today() - datetime.timedelta(1)).strftime('%Y-%m-%d')



    def connect(self):
        """ Returns a connection to the database """
        conn_str = "dbname={} user={} host={} port={} password={}".format(
            os.environ['PGDATABASE'],
            os.environ['PGUSER'],
            os.environ['PGHOST'],
            os.environ['PGPORT'],
            os.environ['RSPASSWORD'])
        try:
            conn = psycopg2.connect(conn_str)
            # the command below will force the connection not to use cashing
            conn.set_session(readonly=True, autocommit = True)
        except Exception as e:
            print "Could not establish a connection with Redshit because of the following exception"
            print e
        return conn

    def mount_query(self):
        """ Creates the text SQL query based on the experiment parameters """

        where_statements = []
        for key, value in self.experiment_params.iteritems():
            # get params from yaml 
            exp_name = key
            date_start = value['dates'][0] if value['dates'][0] else self.yesterday_date
            date_end = value['dates'][1] if value['dates'][1] else self.yesterday_date


            where_statements.append("(theday >= '{}' and theday <= '{}' "\
            "and experimenttypename = '{}')".format(date_start,
                                                          date_end,
                                                          exp_name))

        where = " or \n".join(where_statements)

        #return '{} where {}'.format(self.base_query, where)
	return self.base_query.format(where)


    def extract_data(self):
        """ Uses the created query to extract the data """


        conn = self.connect()
        data = pd.read_sql_query(self.query, conn)
	conn.close()

        return data

    def output_csv(self, path):
        """ Outputs the data to a csv file """
        self.data.to_csv(path)

    def output_stdout(self):
        """ Outputs the data to stdout """
        print self.data.to_string()

    def get_data(self):
        """ Returns the data as a pandas data frame """
        return self.data


def main(**kwargs):

    base_query = kwargs['base_query']
    exp_config = yaml.load(open(kwargs['config'], 'r'))
    data_extractor = DataExtractor(exp_config, base_query)
    if kwargs['output_path']:
        data_extractor.output_csv(kwargs['output_path'])
    else:
        data_extractor.output_stdout()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = "This program extracts data from RS based on two things: the first is a base query which specifies what parameters and the db table logic for it to be extracted, the second is a YAML config file which specifies which experiments should be extracted and for which dates"
    )
    parser.add_argument('-c', '--config',
                        help="YAML file to be processed")
    parser.add_argument('-q', '--base_query',
                        help = 'sql file with the base query string')
    parser.add_argument('-o', '--output_path',
                        help = 'if the output is to be saved in a csv, specify the path here')

    main(**vars(parser.parse_args()))
