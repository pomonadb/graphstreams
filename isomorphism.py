#! /usr/bin/python
import argparse
import cProfile
import mysql.connector
from getpass import getpass

from mapping import Mapping
from graph import DBGraph as Graph
from graph_gen import *
from sql_helpers import *


def generic_query_proc(query_graph, data_graph, exp_enforce, imp_enforce,
                       imp_simplify):
    iso_so_far = Mapping(directed = True)
    candidate_set = {}
    for e in query_graph.edge_ids():
        candidate_set[e] = filter_candidates(query_graph, data_graph, e)
        if len(candidate_set[e]) == 0:
            print("No viable candidates for ", e)
            return False
        
    done = subgraph_search(iso_so_far, query_graph, data_graph, candidate_set,
                           exp_enforce, imp_enforce, imp_simplify)
    print("Done searching!")
    return done

    
def subgraph_search(iso_so_far, query_graph, data_graph, candidate_set,
                    exp_enforce, imp_enforce, imp_simplify, depth = 0):

    if depth != iso_so_far.get_size():
        print("!" + ("="*35) +"WARNING" + ("="*35)  + "! ")
        print("\tsearch depth:", depth, "should be equal to |ISO|", iso_so_far.get_size(),
              depth == iso_so_far.get_size())
        
    if depth >= query_graph.num_edges():
        print("Found a match!")
        return record(iso_so_far)
    
    else:
        e = query_graph.iterlist[depth][ID]
        # print("  "*depth,"Searching matches for:", e)
        candidates = refine_candidates(candidate_set[e], query_graph,
                                       data_graph, iso_so_far)
        
        for f in candidates:
            # print("  "*depth, e, "|--?-->", f, "\t?")
            if is_joinable(exp_enforce, imp_enforce, query_graph, data_graph,
                           iso_so_far, e, f):
                # Try to insert the pair and make a recursive call If it fails
                # (because e was already mapped) skip this iteration
                if iso_so_far.insert(e,f):
                    subgraph_search(iso_so_far, query_graph, data_graph,
                                    candidate_set, exp_enforce, imp_enforce,
                                    imp_simplify, depth + 1)
                    iso_so_far.remove(e,f)
                else:
                    next


                    
def is_joinable(exp_enforce, imp_enforce, query_graph, data_graph, iso_so_far, eid, fid):
    edge = query_graph.edge_tuple(eid)
    fdge = data_graph.edge_tuple(fid)
    edge_tuples = list(query_graph.edge_tuples_in(iso_so_far.domain()))
    fdge_tuples = iso_so_far.matched_ordered_list(edge_tuples).append(fdge)
    
    return exp_enforce(edge_tuples, fdge_tuples) and \
           imp_enforce(fdge_tuples) and \
           struct_sems(query_graph, data_graph, iso_so_far, edge, fdge)
    

## determines whether the addition of the pair edge-fdge to the mapping
## iso_so_far violates the structural conditions specified by query_graph.
## data_graph is the data graph,
def struct_sems(query_graph, data_graph, iso_so_far, edge, fdge):
    params = lambda x: (query_graph, data_graph, iso_so_far, edge, fdge, x)
    
    return _coincident_sems(*(params(True))) and \
           _coincident_sems(*(params(False)))
    

def _coincident_sems(query_graph, data_graph, iso_so_far, edge, fdge, pred):
    global SOURCE
    global TARGET

    # select the appropriate functions
    if pred:
        coincident_in = query_graph.epred_in
        vid = edge[SOURCE]
    else:
        coincident_in = query_graph.esucc_in
        vid = edge[TARGET]
    
    # for every coincident edge mapped by the iso
    for eeid in coincident_in(vid, iso_so_far.domain()):
        # for every e in query_graph there is an f in data_graph
        ffid = iso_so_far.get(eeid[ID])
        ffdge = data_graph.edge_tuple(ffid)
        if pred and not successive_edges(ffdge,fdge):
            return False
        if not pred and not successive_edges(fdge,ffdge):
            return False

    return True

    
def filter_candidates(query_graph, data_graph, e):
    return data_graph.edge_ids()

def refine_candidates(candidates, query_graph, data_graph, iso_so_far):
    return candidates

def record(iso):
    print(iso)
    return True

def _label_match(e,f):
    return True


def check_temp_semantics(imp_sem, exp_sem):
    return sum(exp_sem) + sum(imp_sem) == 2

def assign_semantics(args):
    e = None
    i = None
    if args.EXACT:
        e = Explicit.EXACT
    elif args.CONTAINED:
        e = Explicit.CONTAINED
    elif args.CONTAINED:
        e = Explicit.CONTAINED
    else:
        e = Explicit.INTERSECT

    if args.CONCUR:
        i = Implicit.CONCUR
    elif args.WCONSEC:
        i = Implicit.CONSEC_WK
    elif args.SCONSEC:
        i = Implicit.CONSEC_STR

    return (e,i)
        

## The main function. Parses the command line arguments and sets up the
## computation as specified.
def main():
    
    parser = argparse.ArgumentParser(
        """A command-line interface for running 
        temporal graph isomorphism algorithms""",
        prefix_chars = "-+"
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
    parser.add_argument("--no-password", dest="password", action="store_false")

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

    parser.add_argument("--interval", nargs=2, type=int,
                        help="The global query interval. Negative values"\
                             "represent an unbounded interval")

    ## Arguments for the explicit semantics
    parser.add_argument("+E", "--EXACT", action="store_true",
                        help="select the EXACT explicit semantics")
    parser.add_argument("+C", "--CONTAIN", action="store_true",
                        help="select the CONTAIN explicit semantics")
    parser.add_argument("+D", "--CONTAINED", action="store_true",
                        help="select the intersect explicit semantics")
    parser.add_argument("+I", "--INTERSECT", action="store_true",
                        help="select the intersect explicit semantics")

    # Arguments for the implicit semantics
    parser.add_argument("-R", "--CONCUR", action="store_true",
                        help="select the CONCUR implict semantics")
    parser.add_argument("-W", "--WCONSEC", action="store_true",
                        help="select the CONSEC_WK implicit semantics")
    parser.add_argument("-S", "--SCONSEC", action="store_true",
                        help="select the CONSEC_STR implicit semantics")    
    
    args = parser.parse_args()
    print(args)

    try:
        #get the password securely from the cli
        if args.password:
            password = getpass()
        else:
            password = ""
            
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

        print("q has size", len(query_graph))
        print("G has size", len(data_graph))

        # find all patterns
        if args.algo:
            imp = [args.CONCUR, args.WCONSEC, args.SCONSEC]
            exp = [args.EXACT, args.CONTAIN, args.CONTAINED, args.INTERSECT]
            
            if not check_temp_semantics(imp, exp):
                print("ERROR: Must specify EXACTLY ONE explicit semantics and EXACTLY "
                      "ONE implicit semantics")
                return False
        
            (exp_sem, imp_sem) = assign_semantics(args)
            
            if args.interval == None:
                global_interval = TimeInterval()
            else:
                global_interval = TimeInterval(*args.interval)
                
            global_interval = TimeInterval(int())
            temp_semantics = (Explicit.enforce(exp_sem, global_interval),
                              Implicit.enforce(imp_sem),
                              Implicit.simplify(imp_sem))
            generic_query_proc(query_graph, data_graph, *temp_semantics)
            
        db.commit()
        db.close()
    return 0

if __name__ == "__main__": main()
