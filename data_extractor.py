import argparse
import psycopg2
import os
import json
import datetime
import pandas as pd


class DataExtractor:

    def __init__(self,
                 experiment_params = 'experiment_config.json',
                 base_query = 'sql/base_sql.sql'):
        self.experiment_params = json.load(open(experiment_params))
        self.base_query = open(base_query).read()
        self.conn = self.__connect__()
        self.yesterday_date = self.__get_yesterday__()
        self.query = self.__mount_query__()
        self.data = self.__extract_data__()



    def __get_yesterday__(self):
        return (datetime.date.today() - datetime.timedelta(1)).strftime('%Y-%m-%d')



    def __connect__(self):
        conn_str = "dbname={} user={} host={} port={} password={}".format(
            os.environ['PGDATABASE'],
            os.environ['PGUSER'],
            os.environ['PGHOST'],
            os.environ['PGPORT'],
            os.environ['RSPASSWORD'])
        try:
            conn = psycopg2.connect(conn_str)
        except:
            print "did not connect"
        return conn

    def __mount_query__(self):

        where_statements = []
        for key, value in self.experiment_params.iteritems():
            # get params from json 
            exp_name = key
            date_start = value[0] if value[0] else self.yesterday_date
            date_end = value[1] if value[1] else self.yesterday_date

            where_statements.append("(theday >= '{}' and c.creationdate <= '{}' "\
            "and expnames.experimenttypename = '{}')".format(date_start,
                                                          date_end,
                                                          exp_name))

        where = " or \n".join(where_statements)

        return '{} where {}'.format(self.base_query, where)


    def __extract_data__(self):

        print "extracting data from db..."

        data = pd.read_sql_query(self.query, self.conn)

        print "data extraction done!!"
        return data

    def output_csv(self, path):
        self.data.to_csv(path)

    def output_stdout(self):
        print self.data.to_string()

    def get_data(self):
        return self.data


def main(**kwargs):

    file_contents = kwargs['config']
    base_query = kwargs['base_query']
    data_extractor = DataExtractor(file_contents, base_query)
    if kwargs['output_path']:
        data_extractor.output_csv(kwargs['output_path'])
    else:
        data_extractor.output_stdout()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = "to be filled",
        description = "to be filled"
    )
    parser.add_argument('-c', '--config',
                        help="JSON file to be processed")
    parser.add_argument('-q', '--base_query',
                        help = 'sql file with the base query string')
    parser.add_argument('-o', '--output_path',
                        help = 'if the output is to be saved in a csv, specify the path here')

    main(**vars(parser.parse_args()))
