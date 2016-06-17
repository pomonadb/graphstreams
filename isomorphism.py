#! /usr/bin/python

## This file presents the command-line interface for the isomorphism
## calculation, as well as provides the outline for the subgraph isomorphism procedure
## Notable functions are
##     generic_query_proc
##       filter_candidates
##       subgraph_search
##         refine_candidates
##         is_joinable
##         subgraph_search
##
## N.B. The standard NextQueryEdge() function is missing, it is currently
## defined in the order of query_graph.iterlist.

# python library dependencies
import argparse
import mysql.connector
from getpass import getpass

# local dependencies
from mapping import Mapping         # for containing the isomorphism
from graph import DBGraph as Graph  # for modeling the graphs
from graph_gen import *             # general graph helpers (tuple operations)
from sql_helpers import *           # general sql helpers


# This function outlines the generic query process for any/every
# branch-and-bound style subgraph-isomorphism algorithm.  It takes two DBGraph
# objects, query_graph and datagraph, and the three semantics processing
# functions, allowing it to be semantics-agnostic.
# TODO: inject all functional dependencies for more CLI control?
def generic_query_proc(query_graph, data_graph, exp_enforce, imp_enforce,
                       imp_simplify):
    iso_so_far = Mapping(directed = True) # set up the isomorphism
    candidate_set = {}                    # initialize the isomorphism


    # TODO: preprocess the query graph

    # iterate through the edges to generate candidate sets of locally
    # label-matching edges
    for edge in query_graph.edge_tuples(): 
        candidate_set[edge[ID]] = filter_candidates(query_graph, data_graph,
                                                    edge, exp_enforce)

        # make sure there are viable results
        if len(candidate_set[edge[ID]]) == 0:
            print("No viable candidates for ", edge)
            return False

    # Search for a matching subgraph!
    done = subgraph_search(iso_so_far, query_graph, data_graph, candidate_set,
                           exp_enforce, imp_enforce, imp_simplify)
    print("Done searching!")
    return done


# This function recursively traverses the search space, taking the isomorphism as
# it stands `iso_so_far`, the query and data graphs, the set of candidate sets,
# the three semantics processing functions, and the search_depth
def subgraph_search(iso_so_far, query_graph, data_graph, candidate_set,
                    exp_enforce, imp_enforce, imp_simplify, depth = 0):

    # the depth represents ths size of the mapping. Ensure that this is consistent
    if depth != iso_so_far.get_size():
        print("!" + ("="*35) +"WARNING" + ("="*35)  + "! ")
        print("\tsearch depth:", depth, "should be equal to |ISO|:", iso_so_far.get_size(),
              depth == iso_so_far.get_size())

    # if the mapping and the query graph are the same size, i.e. every edge has
    # been mapped, record the result.
    if depth >= query_graph.num_edges():
        print("Found a match!")
        return record(iso_so_far)
    
    else:
        # grab a new edgeid
        edge = query_graph.iterlist[depth]
        # print("  "*depth,"Searching matches for:", edge[ID])

        # refine the candidate set
        candidates = refine_candidates(candidate_set[edge[ID]], query_graph,
                                       data_graph, iso_so_far)
        
        # travese the candidates looking for a match
        for fdge in candidates:
            # print("   "*depth, edge[ID], "|--?-->", fdge[ID])
            
            # Test whether the edge pair (e,f) can safely be added to the iso
            if is_joinable(exp_enforce, imp_enforce, query_graph, data_graph,
                           iso_so_far, edge, fdge):

                # insert the insertable pair
                iso_so_far.insert(edge,fdge)
                # perform recursion
                # print("   "*depth, edge[ID],"|----->", fdge[ID], "Added successfully")
                subgraph_search(iso_so_far, query_graph, data_graph,
                                candidate_set, exp_enforce, imp_enforce,
                                imp_simplify, depth + 1)
                    
                # either an iso was or wasnt found. either way, prune the branch
                iso_so_far.remove(edge,fdge)
                
                    



# This function tests whether eid and fid can be added to iso_so_far based on
# their topological and temporal semantics. In addition to these three, it takes
# the boolean temporal semantics functions, the query graph and the data_graph
def is_joinable(exp_enforce, imp_enforce, query_graph, data_graph, iso_so_far,
                edge, fdge):

    # if edge or fdge is already mapped in some way, cant join
    if iso_so_far.already_mapped(edge,fdge):
        return False
    
    pre = 0
    img = 1

    # Get the matched edge tuples. fdge_tuples should be sorted based on the
    # order of edge_tuples, so that edge_tuples[i] |---> fdge_tuples[i]
    mapping = iso_so_far.unzip()
    
    # add the current edges to check semantic consistency of new edges
    # print("mapping", mapping)
    # print("mapping[img]", mapping[img])
    preimg = mapping[pre] + (edge,)
    image  = mapping[img] + (fdge,)
    # print("preimage", preimg)
    # print("image", image)

    # print("trying to join")
    # print("      ", edge, "|-?->", fdge, "to")
    # print(iso_so_far)
    if exp_enforce(preimg,image):
        # print("  "*30, "Explicit Sems passed")
        if imp_enforce(image):
            # print("  "*30, "Implicit Sems Passed!")
            if struct_sems(query_graph, data_graph, iso_so_far, preimg[-1],
                           image[-1]): 
                # print("  "*30, "Structural Sems Passed!")
                return True
            else:
                # print("  "*30,"STRUCT SEMS FAILED!")
                return False
        else:
            # print("IMPLICIT SEMS", imp_enforce.__name__,"FAILED")
            return False
    else:
        # print("EXPLICIT SEMS", exp_enforce.__name__, "FAILED")
        return False
    

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
        # print("Find Preds of", edge)
    else:
        coincident_in = query_graph.esucc_in
        # print("find Succs of", edge)
    
    # for every coincident edge mapped by the iso
    for eedge in coincident_in(edge, iso_so_far.domain()):
        # for every e in query_graph there is an f in data_graph
        ffdge = iso_so_far.get(eedge)
        # print("\t", fdge)
        
        if pred and not successive_edges(ffdge,fdge):
            return False
        if not pred and not successive_edges(fdge,ffdge):
            return False

    return True

# returns a set of edge tuples from data_graph that could possibly be matched to
# edge in the query graph, based on the explicit constraint defined by exp_enforce
def filter_candidates(query_graph, data_graph, edge, exp_enforce):
    
    cands = data_graph.edge_tuples_matching(edge, query_graph)
    # print("There are", len(cands), "edges with matching labels for", edge)
    cands = [fdge for fdge in cands if exp_enforce([edge],[fdge])]
    # print("There are", len(cands), "candidates for edge", edge)
    return cands

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
    elif args.CONTAIN:
        e = Explicit.CONTAIN
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
