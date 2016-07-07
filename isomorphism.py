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
from query_rewrite import transform # the query rewriter
from encoding import profile_graph  # the hypernode

GRAPH = 0                       # index of the Query graph
IVAL = 1                        # index of the Query Global Interval
SEMS = 2                        # Index of the semantics

# This function outlines the generic query process for any/every
# branch-and-bound style subgraph-isomorphism algorithm.  It takes two DBGraph
# objects, query_graph and datagraph, and the three semantics processing
# functions, allowing it to be semantics-agnostic.
# TODO: inject all functional dependencies for more CLI control?
def generic_query_proc(query, data_graph, exp_enforce,imp_enforce,imp_simplify, options):
    """
    Execute the generic query subgraph isomorphism function
 
    PARAMS:
       query        -- a tuple of the query graph, global_interval, and semantics tuple
       data_graph   -- a Graph object representing the graph to be queried
       exp_enforce  -- a function object enforcing the explicit semantics
       imp_enforce  -- a function object enforcing the explicit semantics
       imp_simplify -- a function object defining the implicit simplification
       options      -- dictionary specifying the modularity options
       
    """
    global EXP
    global IMP
    global GRAPH
    global IVAL
    global SEMS
    
    iso_so_far = Mapping(directed = True) # set up the isomorphism
    candidate_set = {}                    # initialize the isomorphism
    
    hn_isos = query[GRAPH].match_hypernodes(data_graph)
    
    # iterate through the edges to generate candidate sets of locally
    # label-matching edges
    for edge in query[GRAPH].edge_tuples(): 
        candidate_set[edge[ID]] = filter_candidates(query, data_graph, edge,
                                                    exp_enforce,
                                                    options["filter"], hn_isos)

        # make sure there are viable results
        if len(candidate_set[edge[ID]]) == 0:
            print("No viable candidates for ", edge)
            return False

    # Search for a matching subgraph!
    done = subgraph_search(iso_so_far, query, data_graph, candidate_set,
                           exp_enforce, imp_enforce, imp_simplify, options, depth = 0)
    print("Done searching!")
    return done


# This function recursively traverses the search space, taking the isomorphism as
# it stands `iso_so_far`, the query and data graphs, the set of candidate sets,
# the three semantics processing functions, and the search_depth
def subgraph_search(iso_so_far, query, data_graph, candidate_set,
                    exp_enforce, imp_enforce, imp_simplify, options, depth = 0):
    """
    The recursive subroutine that that searches the sample space

    iso_so_far    -- the state of the isomorphism to be searched
    query         -- the tuple of graph, global interval, and semantic tuple
    data_graph    -- the graph object being queried
    candidate_set -- the list of candidate sets for each tuple
    exp_enforce   -- the function enforcing the explicit semantics
    imp_enforce   -- the function enforcing the implicit semantics
    imp_simplify  -- the simplification function for implicit semantics
    options       -- dictionary specifying the modularity options
    depth         -- the search depth (also the size of the current iso)
    """
    
    global GRAPH

    # the depth represents ths size of the mapping. Ensure that this is consistent
    if depth != iso_so_far.get_size():
        print("!" + ("="*35) +"WARNING" + ("="*35)  + "! ")
        print("\tsearch depth:", depth, "should be equal to |ISO|:", iso_so_far.get_size(),
              depth == iso_so_far.get_size())

    # if the mapping and the query graph are the same size, i.e. every edge has
    # been mapped, record the result.
    if depth >= query[GRAPH].num_edges():
        mapping = iso_so_far.unzip()
        if exp_enforce(*mapping) and imp_enforce(mapping[1]):
            print("Found a match with depth: ",depth," and |q| = ", query[GRAPH].num_edges())
            return record(iso_so_far)
    
    else:
        # grab a new edgeid
        edge = query[GRAPH].iterlist[depth]
        # print("  "*depth,"Searching matches for:", edge[ID])

        # refine the candidate set
        candidates = refine_candidates(candidate_set[edge[ID]], query[GRAPH],
                                       data_graph, iso_so_far)
        
        # travese the candidates looking for a match
        for fdge in candidates:
            # print("   "*depth, edge[ID], "|--?-->", fdge[ID])
            
            # Test whether the edge pair (e,f) can safely be added to the iso
            if is_joinable(exp_enforce, imp_enforce, query, data_graph,
                           iso_so_far, edge, fdge, options["naive"]):

                # insert the insertable pair
                iso_so_far.insert(edge,fdge)
                # perform recursion
                # print("   "*depth, edge[ID],"|----->", fdge[ID], "Added successfully")
                subgraph_search(iso_so_far, query, data_graph,
                                candidate_set, exp_enforce, imp_enforce,
                                imp_simplify, options, depth + 1)
                    
                # either an iso was or wasnt found. either way, prune the branch
                iso_so_far.remove(edge,fdge)
                

# This function tests whether eid and fid can be added to iso_so_far based on
# their topological and temporal semantics. In addition to these three, it takes
# the boolean temporal semantics functions, the query graph and the data_graph
def is_joinable(exp_enforce, imp_enforce, query, data_graph, iso_so_far,
                edge, fdge, skip_temp):
    """
    Determines whether the pair (edge, fdge) can be added to iso_so_fair

    exp_enforce -- a function that enforces the explicit semantics
    imp_enforce -- a function that enforces the implicit semantics
    query       -- the query tuples graph * global interval * semantics tuple
    data_graph  -- the graph to be queried
    iso_so_far  -- the current search state of the isomorphism
    edge        -- the edge in the query graph to be matched with fdge
    fdge        -- the edge in the data graph to be matched with edge
    """
    
    global GRAPH
    
    # if edge or fdge is already mapped in some way, cant join
    if iso_so_far.already_mapped(edge,fdge):
        return False
    else:
        
        iso_so_far.add_to_buffer(edge,fdge)
    
    # print("trying to join")
    # print("      ", edge, "|-?->", fdge, "to")
    # print(iso_so_far)
    if skip_temp or iso_so_far.temp_semantics(query[IVAL], *query[SEMS]):
        if struct_sems(query[GRAPH], data_graph, iso_so_far, edge,
                       fdge):
            iso_so_far.flush()
            return True
        else:
            # print("  "*30,"STRUCT SEMS FAILED!")
            print()
    else:
        # print("TEMPORAL SEMS", imp_enforce.__name__,"FAILED")
        print()

    iso_so_far.empty_buffer()
    return False
    

## determines whether the addition of the pair edge-fdge to the mapping
## iso_so_far violates the structural conditions specified by query_graph.
## data_graph is the data graph,
def struct_sems(query_graph, data_graph, iso_so_far, edge, fdge):
    """
    A boolean helper function that returns true if the addition of edge and fdge
    matches the structural or topological basis. This is the static isJoinable

    query_graph -- the graph object representing the pattern to be matched
    data_graph  -- the graph object to be queried
    iso_so_far  -- the current state of the isomorphism
    edge        -- the query edge to be matched with fdge in iso_so_far
    fdge        -- the data  edge to be matched with edge in iso_so_far
    """
    
    params = lambda x: (query_graph, data_graph, iso_so_far, edge, fdge, x)

    return _coincident_sems(*(params(True))) and \
           _coincident_sems(*(params(False)))
    
# Determines whether the addition of the edge pair edge, fdge violates the
# predecessor or the successor semantics depending on the boolean value of pred
def _coincident_sems(query_graph, data_graph, iso_so_far, edge, fdge, pred):
    """
    A boolean helper function that returns true if the addition of edge and fdge
    matches the structural semantics for predecessor if pred is True or
    successor if pred is false.

    query_graph -- the graph object representing the pattern to be matched
    data_graph  -- the graph object to be queried
    iso_so_far  -- the current state of the isomorphism
    edge        -- the query edge to be matched with fdge in iso_so_far
    fdge        -- the data  edge to be matched with edge in iso_so_far
    pred        -- Whether the predecessor or the successor edes should be checked.
    """
    
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
def filter_candidates(query, data_graph, edge, exp_enforce, do_filter, hn_pairs):
    """
    A function that reduces the sample space for edge in the data graph based on
    the explicit semantics and label matching.

    query -- A query Graph object representing the pattern to be matched
    data_graph -- A query Graph object to be queried
    edge -- the edge for which we must find candidate matches
    exp_enforce -- the function defining the explicit semantics
    """
    global GRAPH
    
    cands = data_graph.edge_tuples_matching(edge, query[GRAPH])
    print("There are", len(cands), "edges with matching labels for", edge)
    if do_filter:
        cands = [fdge for fdge in cands if exp_enforce([edge],[fdge])
                 and hn_check(edge,fdge, hn_pairs)]
        print("There are", len(cands), "candidates for edge", edge)
    return cands

def hn_check(edge,fdge, hn_pairs):
    """
    Returns True if edge and fdge have matching hypernode endpoints, or if the
    none of the endpoints are hypernodes
    """
    okay = True
    if edge[SOURCE] in hn_pairs:
        okay &= fdge[SOURCE] in hn_pairs[edge[SOURCE]]

    if edge[TARGET] in hn_pairs:
        okay &= fdge[TARGET] in hn_pairs[edge[TARGET]]

    data_hns = set().union(*hn_pairs.values())
    fdge_has_hn = fdge[SOURCE] in data_hns or fdge[TARGET] in data_hns

    return  (fdge_has_hn and okay) or (not fdge_has_hn and not okay)

def refine_candidates(candidates, query, data_graph, iso_so_far):
    """
    STUB METHOD: Find a way to reduce the product sample space
    """
    return candidates

def record(iso):
    """
    Record the value of the iso

    Currently just printo out the value.
    """
    
    print(iso)
    return True

def check_temp_semantics(imp_sem, exp_sem):
    """
    Ensure that only one explicit semantics and one implicit semantics were chosen
    """
    return sum(exp_sem) + sum(imp_sem) == 2

def assign_semantics(args):
    """
    Parse the input arguments and return a tuple of enum types identifying the
    temporal semantics pair
    """
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
    global IMP
    global EXP
    global GRAPH
    global IVAL
    global SEMS
    
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
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-r", "--as-root", action="store_true")
    parser.add_argument("+p","--no-password", dest="password", action="store_false")

    # graph generation parameters
    parser.add_argument("-q", "--make-query", type=int,
                        help="The number of edges for the query graph")
    
    parser.add_argument("-d", "--make-data", type=int,
                        help="The number pf edges for the data graph")
    
    parser.add_argument("-D", "--density", "--dens", type=float,
                        help="The desired density of the data graph")
                        
    parser.add_argument("-C", "--force-clear", action="store_true",
                        help="clear graph tables if they exist")
    
    parser.add_argument("+na","--no-algo", dest="algo", action="store_false",
                        help="do not run any algorithms, only graph generation")

    parser.add_argument("+iv","--interval", nargs=2, type=int,
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

    # Flags for Modular testing
    parser.add_argument("-e","--rewrite", action="store_true",
                        help="Use flag to perform query rewriting?")
    parser.add_argument("-n","--naive", action="store_true",
                        help="Naively post-filter results with temporal condition.")
    parser.add_argument("-f","--use-filter", action="store_true",
                        help="Use a temporal FilterCandidates")
    parser.add_argument("-p","--profiles", action="store_true",
                        help="Use neighborhood profiles/encodings")
    parser.add_argument("-i","--index", action="store_true",
                        help="Use temporal index")
    parser.add_argument("-s","--search-order", action="store_true",
                        help="Use temporal search order")
    parser.add_argument("-g", "--hypergraph",action="store_true",
                        help="Include Hypergraph in rewriting technique")
    parser.add_argument("-t", "--deconstruct",type=int,
                        help="Deconstruct the datagrarh to construct profiles")

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
        
            sems = assign_semantics(args)
            
            if args.interval == None:
                global_interval = TimeInterval(inf,-inf) if args.CONTAINED else TimeInterval() 
            else:
                global_interval = TimeInterval(*args.interval)
                
            temp_semantics = (Explicit.enforce(sems[EXP], global_interval),
                              Implicit.enforce(sems[IMP]),
                              Implicit.simplify(sems[IMP]))

            # create the query tuple and rewrite if necessary
            query = (query_graph, global_interval, sems)
            query = transform(*query) if args.rewrite else query

            if args.deconstruct != None and args.deconstruct > 0:
                profile_graph(db, data_graph, args.deconstruct)
                profile_graph(db, query_graph, args.deconstruct)

            execution_plan = { "naive"     : args.naive,
                               "filter"    : args.use_filter and not args.naive,
                               "profiles"  : args.profiles and not args.naive,
                               "index"     : args.index and not args.naive,
                               "search"    : args.search_order and not args.naive,
                               "hypergraph": args.hypergraph and not args.naive
            }

            generic_query_proc(query, data_graph, *temp_semantics, execution_plan)
            
        db.commit()
        db.close()
    return 0

if __name__ == "__main__": main()
