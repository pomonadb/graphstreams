##
## This file describes the functions and transformations associated with pruning
## the query graph to help enforce more strongly the implicit semantics
##

from temporal_helpers import *
from sql_helpers import *

EXP = 0
IMP = 1

def transform(query, interval, sem):
    if sem[EXP] == Explicit.EXACT:
        return (query, interval, sem)
    else:
        return tighten(*rewrite(*tighten(query, sem, interval)))[0]


## refine the explicit constraints based on global information and explicit
## semantics
def tighten(q, sem, t = None):
    global EXP
    global IMP
    
    edges = q.edge_tuples()
    
    if sem[EXP] == Explicit.CONTAINED:
        tt = TimeInterval(inf, -inf)
        for e in edges:
            te = make_time(e)
            if te <= t:
                next
            else:
                if te.start < t.start:
                    tt = TimeInterval(te.start, tt.end)
                if te.end > t.end:
                    tt = TimeInterval(tt.start, te.end)
        return (q, sem, tt)
    else:
        new_edges = set()
        for e in edges:            
            new_ti = make_time(e).intersect(interval)
            new_edge = e[:START_TIME] + (new_ti.start, new_ti.end)+ e[END_TIME:]
            new_edges.add(new_edge)

        
        return (q, sem, t)

## refine the explicit intervals based on local information and implicit and
## explict semantics
def rewrite(q, sem, t = None):
    new_edges = set()
    
    if sem[IMP] == Implicit.CONSEC_WK: # Wconsec.. No rewrites for now
        return (q, sem, t)
    
    elif sem[IMP] == Explicit.CONSEC_STR:  # Sconsec
        if sem[EXP] == Explicit.CONTAINED: # CONTAINED
            for e in q.edge_tuples():
                # create the unions for the incoming and outgoing edges.
                pred_ival = big_union(q.pred_in(e))
                succ_ival = big_union(q.succ_in(e))
                curr_ival = make_time(e)

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
                    
        else:                   # Sconsec and CONTAIN or INTERSECT
            for e in q.edge_tuples():
                new_ival = big_union(q.neighborhood(e)))
                new_edge = make_new_edge(e,new_ival)
                new_edges.add(new_edge)
                
    else:                       #  CONCUR
        if sem[EXP] == Explicit.CONTAIN or sem[EXP] == Explicit.INTERSECT:
            edges = q.edge_tuples()
            new_ival = big_intersect(edges))
            new_edges = set(map(lambda e: make_new_edge(e,new_ival), edges)) 
                


    return (q.with_edges(new_edges), sem, t)



def make_new_edge(old, new_ival):
    return e[:START_TIME] + (new_ival.start, new_ival.end) + e[END_TIME:])
