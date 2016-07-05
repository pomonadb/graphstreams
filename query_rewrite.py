##
## This file describes the functions and transformations associated with pruning
## the query graph to help enforce more strongly the implicit semantics
##

from temporal_helpers import *
from sql_helpers import *

# This transforms the query into an appropriate query. Assume that the query is
# valid. I.e. <query, interval>  can return results obeying sems.
def transform(query, interval, sems):
    """Enforce the explicit semantics are enforced and then rewrite the query
    based on the rewrite rules"""
    if sems[EXP] == Explicit.EXACT:
        return (query, interval, sems)
    else:
        edges = query.edge_tuples()
        print("START:", len(edges))
        new_query = _tighten(*_rewrite(*_tighten(edges, query, sems, interval)))
        new_q_graph = query.make_copy_with(new_query[0])
        return (new_q_graph, *new_query[1:])


## refine the explicit constraints based on global information and explicit
## semantics
def _tighten(edges, oldq, sem, t = None):
    """Tighten the explicit semantics of the query"""
    global EXP
    global IMP

    new_edges = []
    tq = t
    
    if sem[EXP] == Explicit.CONTAINED:
        # TODO Turn this into one loop
        
        # for a iso f, edge e, T(f(e)) >= t. Since each T(f(e)) >= T(e), If
        # there is an intersection between all the edges, the edges mapped by f,
        # must also contain that intersection. So every edge must intersect with
        # this big_intersect, and with t.  
        tq = big_intersect(edges)
        tq = tq.union(t) if t != None else tq

        # Since every mapped edge needs to contain tq. set the edge interval to
        # be the union of tq and T(e)
        for e in edges:
            new_ti = make_time(e).union(tq)
            new_edges.append(make_new_edge(e, new_ti))
            
    else:
        # otherwise, chop off the parts of the edges that dont intersect with
        # the global interval. But skip it if there's no given interval, or if t
        # is gross.
        if t != None and not t.is_infty():
            for e in edges:            
                new_ti = make_time(e).intersect(t)
                new_edge = make_new_edge(e, new_ti)
                new_edges.append(new_edge)
        else:
            new_edges = edges    
        

    # Return the new edge set, the old query object, the semantics and the query
    # interval.
    return (new_edges, oldq, sem, tq)

## refine the explicit intervals based on local information and implicit and
## explict semantics
def _rewrite(edges, oldq, sem, t = None):
    """Create a new query reducing the search space by shrinking (or expanding)
    the intervals on the edges based on the implicit conditions and their neighbors."""
    new_edges = set()
    
    if sem[IMP] == Implicit.CONSEC_WK: # Wconsec.. No rewrites for now
        return (edges, oldq, sem, t)
    
    elif sem[IMP] == Implicit.CONSEC_STR:  # Sconsec
        if sem[EXP] == Explicit.CONTAINED: # CONTAINED
            for e in edges:
                # create the unions for the incoming and outgoing edges.
                pred_ival = big_union(oldq.epred_in(e))
                succ_ival = big_union(oldq.esucc_in(e))
                curr_ival = make_time(e)

                # if the predecessor, successor, or current interval is empty,
                # do nothing
                if pred_ival.is_empty() or succ_ival.is_empty() \
                   or curr_ival.is_empty():
                    return (edges, oldq, sem, t)

                # if they intersect, compare the intersection with the current
                # interval
                if succ_ival.does_intersect(pred_ival):
                    te = make_time(e)
                    nbhd_ival = succ_ival.intersect(pred_ival)
                    new_st   = min(curr_ival.start, nbhd_ival.end)
                    new_end = max(curr_ival.end, nbhd_ival.start)
                    new_ival = TimeInterval(new_st, new_end)
                else:
                    #otherwise, there is a gap, so the interval must span the gap.
                    new_st  = min(succ_ival.end, pred_ival.end, e[START_TIME])
                    new_end = max(succ_ival.start, pred_ival.start, e[END_TIME])
                    new_ival = TimeInterval(new_st, new_end)

                new_edge = make_new_edge(e,new_ival)
                new_edges.add(new_edge)
                    
        elif sem[EXP] == Explicit.INTERSECT:  # Sconsec and INTERSECT
            for e in edges:
                bounds = big_union(oldq.eneighborhood(*e))
                te = make_time(e)
                new_ival = TimeInterval(max(bounds.start, te.start),
                                        min(bounds.end,  te.end))
                new_edge = make_new_edge(e,new_ival)
                new_edges.add(new_edge)

        else:
            #  Do nothing for CONTAIN for now
            new_edges = edges
            print("No rewrite semantics for", tuple(map(lambda s: s.name, sem)))
                
    else:                       #  CONCUR
        if sem[EXP] == Explicit.CONTAIN or sem[EXP] == Explicit.INTERSECT:
            edges = oldq.edge_tuples()
            new_ival = big_intersect(edges)
            new_edges = set(map(lambda e: make_new_edge(e,new_ival), edges))
        else:
            new_edges = edges

    return (new_edges, oldq, sem, t)



