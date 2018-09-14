import argparse
import psycopg2
import os
import json
import datetime
import pandas as pd


class DataExtractor:

    def __init__(self, experiment_params, base_query):
        self.experiment_params = experiment_params
        self.base_query = base_query
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

        #data = self.cursor.execute(self.query)
        #rows = self.cursor.fetchall()

        data = pd.read_sql_query(self.query, self.conn)
        return data

    def output_csv(self, path):
        self.data.to_csv("test.csv")


def main(**kwargs):

    file_contents = json.load(kwargs['config'][0])
    base_query = kwargs['base_query'][0].read()
    data_extractor = DataExtractor(file_contents, base_query)
    data_extractor.output_csv('test')





    #assert (kwargs['expid'] is None or kwargs['query'] is None) , "you should provide one or other"
    #fd = open('sql/base_query.sql', 'r')
    #sql = fd.read().format(kwargs['expid'])
    #fd.close()
    #conn_str = "dbname={} user={} host={} port={} password={}".format(
    #    os.environ['PGDATABASE'],
    #    os.environ['PGUSER'],
    #    os.environ['PGHOST'],
    #    os.environ['PGPORT'],
    #    os.environ['RSPASSWORD'])
    #try:
    #    conn = psycopg2.connect(conn_str)
    #except:
    #    print "did not connect"
    #cur = conn.cursor()
    #cur.execute(sql)
    #rows = cur.fetchall()
    #print(rows)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = "to be filled",
        description = "to be filled"
    )
    parser.add_argument('-c', '--config', nargs = 1,
                        help="JSON file to be processed",
                        type=argparse.FileType('r'))
    parser.add_argument('-q', '--base_query', nargs = 1,
                        help = 'sql file with the base query string',
                        type=argparse.FileType('r'))

    main(**vars(parser.parse_args()))
