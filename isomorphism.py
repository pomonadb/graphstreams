#! /usr/bin/python
import argparse
import cProfile
import mysql.connector
from getpass import getpass


from mapping import Mapping
from graph import DBGraph as Graph
from graph_gen import *
from sql_helpers import *




def generic_query_proc(query_graph,data_graph):
    iso_so_far = Mapping(directed = True)
    candidate_set = {}
    for e in query_graph.edges():
        candidate_set[e] = filter_candidates(query_graph, data_graph, e)
        if len(candidate_set[e]) == 0:
            print("No viable candidates for ", e)
            return False
    query_graph.edges(recalc = True)
    
    done = subgraph_search(iso_so_far, query_graph, data_graph, candidate_set,
                           0)
    print("Done searching!")
    return done

    
def subgraph_search(iso_so_far, query_graph, data_graph, candidate_set,
                    depth):

    print("search depth:", depth)
    if iso_so_far.get_size() >= query_graph.num_edges():
        print("Found a match!")
        return record(iso_so_far)
    
    else:
        e = query_graph.iterlist[depth]
        print("Searching matches for:", e)
        candidates = refine_candidates(candidate_set[e], query_graph,
                                       data_graph, iso_so_far)
        
        for f in candidates:
            if is_joinable(query_graph, data_graph, iso_so_far, e, f):
                iso_so_far.insert(e,f)
                subgraph_search(iso_so_far, query_graph, data_graph,
                                candidate_set, depth + 1)
                iso_so_far.remove(e,f)

                
def is_joinable(query_graph,data_graph, iso_so_far, e, f):
    return True

def filter_candidates(query_graph, data_graph, e):
    return data_graph.edges()

def refine_candidates(candidates, query_graph, data_graph, iso_so_far):
    return candidates

def record(iso):
    print(iso)
    return True


## The main function. Parses the command line arguments and sets up the
## computation as specified.
def main():
    
    parser = argparse.ArgumentParser(
        """A command-line interface for running 
        temporal graph isomorphism algorithms"""
        )

    # positional arguments
    parser.add_argument("database", help="The name of the database")
    
    parser.add_argument("query_table_name",
                        help="the name of the table of the query graph")

    parser.add_argument("data_table_name",
                        help="the table of the data graph to be queried")

    # optional flags
    parser.add_argument("-t", "--timer", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-r", "--as-root", action="store_true")

    # graph generation parameters
    parser.add_argument("-q", "--make-query", type=int,
                        help="The number of edges for the query graph")
    
    parser.add_argument("-d", "--make-data", type=int,
                        help="The number pf edges for the data graph")
    
    parser.add_argument("-D", "--density", "--dens", type=float,
                        help="The desired density of the data graph")
                        
    parser.add_argument("-C", "--force-clear", action="store_true",
                        help="clear graph tables if they exist")
    
    parser.add_argument("--no-algo", dest="algo", action="store_false",
                        help="do not run any algorithms, only graph generation")
    
    args = parser.parse_args()

    print(args.database, args.query_table_name, args.data_table_name,
          args.timer, args.verbose, args.as_root, args.make_query,
          args.make_data, args.density, args.force_clear, args.algo)

    try:
        #get the password securely from the cli
        password = getpass()
        # if a password was supplied, or logging in as root
        # This forces the user have a password to log in as root.
        if len(password) > 0:
            if args.as_root:
                print("Logging in as root")
                db = mysql.connector.connect(user="root",
                                             db = args.database,
                                             passwd = password)
            else:
                db = mysql.connector.connect(db = args.database,
                                             passwd = password)
        else:
            print("No password given")
            db = mysql.connector.connect(db = args.database)
            
    except mysql.connector.Error as err:
        print("""Connecting to MySQL failed. If the problem persists check
                 password,
                 username, and
                 whether the database actually exists.""")
    else:

        # make the DATA graph
        make_graph(args.data_table_name, args.make_data, db, args.force_clear,
                   dens = args.density)

        # Make the query graph with default density
        make_graph(args.query_table_name, args.make_query, db, args.force_clear)

        # initalize the graph objects
        query_graph = Graph(args.query_table_name, db)
        data_graph = Graph(args.data_table_name, db)

        print("q has size", len(query_graph.edges()))
        print("G has size", len(data_graph.edges()))

        # find all patterns
        if args.algo:
            generic_query_proc(query_graph, data_graph)
            
        db.commit()
        db.close()
    return 0

if __name__ == "__main__": main()
