#! /usr/bin/python
import argparse
import cProfile
import mysql.connector
from math import *
from random import randrange
from getpass import getpass

from mapping import Mapping
from graph import DBGraph as Graph

MIN_TIME = 0
MAX_TIME = 2016
TIME_RANGE = 10
DENSITY = 0.5
BATCH_SIZE = 1000

def main():
    global DENSITY
    
    parser = argparse.ArgumentParser(
        """
        A command-line interface for running temporal graph isomorphism algorithms.
        """
        )
    
    parser.add_argument("database", help="The name of the database")
    parser.add_argument("query_table_name",
                        help="the name of the table of the query graph")
    parser.add_argument("data_table_name",
                        help="the table of the data graph to be queried")
    
    parser.add_argument("-t", "--timer", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-r", "--as-root", action="store_true")
    
    parser.add_argument("-q", "--make-query", type=int)
    parser.add_argument("-d", "--make-data", type=int)
    parser.add_argument("-D", "--density", "--dens", type=float)
    parser.add_argument("-C", "--force-clear", action="store_true")
    args = parser.parse_args()

    print(args.database, args.query_table_name, args.data_table_name,
          args.timer, args.verbose, args.as_root, args.make_query,
          args.make_data, args.density, args.force_clear)

    try: 
        password = getpass()
        if len(password) > 0 or args.as_root:
            if args.as_root:
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
        print(err)
    else:

        if args.make_data != None and args.make_data > 0:
            d = DENSITY if args.density == None else args.density
            make_graph(args.data_table_name, args.make_data, db,
                       args.force_clear, density = d)
        
        if args.make_query != None and args.make_query > 0:
            make_graph(args.query_table_name, args.make_query, db,
                       args.force_clear)

        # initalize the graph objects
        query_graph = Graph(args.query_table_name, db)
        data_graph = Graph(args.data_table_name, db)

        print("q has size", len(query_graph.edges()))
        print("G has size", len(data_graph.edges()))

        # find all patterns
        generic_query_proc(query_graph, data_graph)
        db.commit()
        db.close()
    return 0


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

    # print("|M| = ", iso_so_far.get_size(), "and |V(Q)| =",
    #       query_graph.num_edges())
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

def make_graph(tbl_name, num_edges, db, force_clear, density = 0.5):
    global MIN_TIME
    global MAX_TIME
    
    num_vertices = ceil(sqrt(num_edges/density))

    print("Making an edge set for", tbl_name , "with", num_edges, "Edge")
    
    edges = set()
    for i in range(0,num_edges):
        u = randrange(0, num_vertices)
        v = u
        while v == u:
            v = randrange(0, num_vertices)

        times = []
        times.append(randrange(MIN_TIME, MAX_TIME))
        times.append(randrange(times[0], times[0] + TIME_RANGE))
            
        edges.add((u,v,times[0],times[1],
                   times[1], times[1],
                   times[1], times[0],
                   times[0], times[0],
                   times[0], times[1]
                 ))
        
    c = db.cursor()
    
    if force_clear:
        c.execute("DROP TABLE IF EXISTS `{0}`".format(tbl_name))
    
    c.execute("""CREATE TABLE IF NOT EXISTS `{0}`(
                 `edge_id` INT AUTO_INCREMENT PRIMARY KEY,
                 `source_id` INT,
                 `dest_id` INT,
                 `time` GEOMETRY)""".format(tbl_name)              
              )

    insert_sql = """INSERT INTO `{0}` (`source_id`, `dest_id`, `time`)
                    VALUES (%s,%s,PolyFromText(
                               'POLYGON((%s %s,%s %s,%s %s,%s %s,%s %s))'
                             )
                           )""".format(tbl_name)

    batch_insert(db, insert_sql, edges)
    c.close()

def batch_insert(db, insert_sql, data):
    global BATCH_SIZE

    # get the data
    cursor = db.cursor()
    
    # ensure the data is a list
    data_list = list(data)
    
    for i in range(0, len(data_list), BATCH_SIZE):
        cursor.executemany(insert_sql, data_list[i:i+BATCH_SIZE])

    db.commit()
    
                     
    
if __name__ == "__main__": main()
