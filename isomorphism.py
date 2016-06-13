#! /usr/bin/python

import argparse
import cProfile
import MySQLdb

def main():
    parser = argparse.ArgumentParser(
        """
        A command-line interface for running temporal graph isomorphism algorithms.
        """
        )
    
    parser.add_argument("database", help="The name of the database")
    parser.add_argument("query_table_name",
                        help="the name of the table of the query graph")
    parser.add_argument("data_table_name",
                        help="the name of the table of the data graph to be queried")
    parser.add_argument("-t", "--timer", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    print(args.database, args.query_table_name, args.data_table_name,
          args.timer, args.verbose)
        
    return 0





if __name__ == "__main__": main()
