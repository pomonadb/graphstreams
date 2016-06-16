##
##  This file is intended to provide helper functions specific to the temporal
##  aspects of this architecture. Here we define implicit and explicit temporal
##  semantics as well as the helper functions and behaviors specific to each
##  semantics.
##
##  N.B. In defining the Enum types we take care to enforce that higher enum
##  numbers are less restrictive.  The Enum type takes an intuitive similarity
##  to "degrees of freedom" without having any formal relationto the concept.
##

from enum import Enum, unique
from sql_helpers import *
from math import inf

class TimeInterval():
    
    ## if start or end is None, then that direction is unbounded, so we define
    ## (None,None) :==: (\infty, \infty). The interval is empty if start > end.
    def __init__(self, start = -inf, end = inf):
        self.start = -inf if start < 0 else start
        self.end = inf if end < 0 else end
        
        if self.is_unbounded():
            self.duration = inf
        else:
            self.duration = end - start

    def __str__(self):
        if self.is_empty():
            return "emptyset"
        else:
            return "({0},{1})".format(self.start,self.end)
            
    def __len__(self):
        return 1

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.start == other.start and self.end == other.end
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    ## this is the contain semantics.
    ## t <= s iff t \subseteq s
    def __le__(self, other):
        return self.start >= other.start and self.end <= other.end

    ## This is the contained semantics
    ## t >= s iff s \subseteq t
    def __ge__(self,other):
        return other.__le__(self)

    ## this is a modified contain semantics for completeness
    ## t < s iff t \subset s
    def __lt__(self,other):
        return self.__le__(other) and self.__ne__(other)

    ## this is a modified contained semantics for completeness
    ## t > s iff s \subset t
    def __gt__(self,other):
        return other.__le__(self)
        
    def is_empty(self):
        return self.duration < 0

    def is_infty(self):
        return self.start == -inf and self.end == inf

    def is_unbounded(self):
        return self.start == -inf or self.end == inf
        
    def union(self, other, check_only):
        if self.is_empty():
            return other
        elif other.is_empty():
            return other
        else:
            new_start = min(self.start, other.start)
            new_end   = max(self.end, other.end)
            return TimeInterval(new_start,new_end)
                            
    def intersect(self, other):
        if self.is_empty():
            return TimeInterval(inf, -inf)
        elif other.is_empty():
            return TimeInterval(inf, -inf)
        else:
            new_start = max(self.start, other.start)
            new_end   = min(self.end, other.end)
            if new_start > new_end:
                return TimeInterval(inf,-inf)
            else:
                return TimeInterval(new_start,new_end)

    def does_intersect(self, other):
        return not self.intersect(other).is_empty()
            
    def tuple(self):
        return(self.start, self.end)

    def polygon_tuple(self,uid = None, vid = None):
        pt =(self.start, self.end,
             self.end,   self.end,
             self.end,   self.start,
             self.start, self.start,
             self.start, self.end )
        
        if uid == None or vid == None:
            return pt
        else:
            return (uid,vid) + pt

    def polygon_string(self):
        return (square(), self.polygon_tuple())
        

@unique
class Explicit(Enum):
    EXACT = 0
    CONTAIN = 1
    CONTAINED = 2
    INTERSECT = 3

    def enforce(sem, giv):
        print("Enforcing", sem.name, "Semantics")
        cond = {
            Explicit.EXACT: Explicit._ex_cond,
            Explicit.CONTAIN: Explicit._cont_cond,
            Explicit.CONTAINED: Explicit._contd_cond,
            Explicit.INTERSECT: Explicit._isect_cond
        }
        glob = {
            Explicit.CONTAINED: Explicit._contd_cond,
            Explicit.INTERSECT: Explicit._isect_cond,
        }
        glob_cond = glob.get(sem, Explicit._cont_cond)
        
        return lambda q, d: Explicit._enf(cond[sem], glob_cond, make_time(giv), q, d)

    ## quer_list one of the following:
    ##      a list of edges, mapped to dat_list, also a list of edges
    ##      a list of pairs of mapped edges, dat_list must be None
    ##      a list of TimeIntervals, matched to dat_list of time windows
    ##      a list of pairs of TimeIntervals, dat_list must be None
    def _enf(rule, glob_rule, global_interval, quer_list, dat_list = None):
        print("enforcing", rule.__name__, "for", global_interval, quer_list, dat_list)
        if quer_list == None or len(quer_list) == 0:
            return True
        elif dat_list != None:  # quer_list must be of pairs
            pairs = zip(quer_list, dat_list)
        else:
            pairs = quer_list
                    
        for (s, t) in pairs:
            print("Comparing", s, "and", t)
            if not (rule(*_to_interval(s,t)) and glob_rule(global_interval, _to_interval(t))):
                print("no match")
                return False
            
        return True
                
    def _ex_cond(t, s):
        print("EXACT", t, s)
        return t == s

    def _cont_cond(t, s):
        print("CONTAIN", t, s)
        return t >= s

    def _contd_cond(t, s):
        print("CONTAINED", t, s)
        return t <= s

    def _isect_cond(t, s):
        print("INTERSECT", t, s)
        return t.does_intersect(s)

                     
@unique
class Implicit(Enum):
    CONCUR = 0
    CONSEC_STR = 1
    CONSEC_WK = 2
    
    def simplify(sem):
        if sem == Implicit.CONCUR:
            return big_intersect(lst)
        else:
            return big_union(lst)
                 
    def enforce(sem):
        enf = {
            Implicit.CONCUR: Implicit._enf_conc,
            Implicit.CONSEC_WK: Implicit._enf_consecw,
            Implicit.CONSEC_STR: Implicit._enf_consecs
        }
        return enf.get(sem, lambda x: False)
    
    
    ## Enforce the concurrent semantics
    def _enf_conc(e_set):
        if e_set == None:
            return True
        else:
            t_set = map(lambda e: TimeInterval(e[START_TIME], e[END_TIME]), e_set)
            return not Implicit.simplify(Implicit.CONCUR)(list(t_set)).is_empty()
    
    ## Enforce the strong consecutive semantics
    def _enf_consecs(e_set):
        if e_set == None:
            return True
        for e in e_set:
            for f in e_set:
                e_time = make_time(e)
                f_time = make_time(f)
                if successive_edges(e,f) and not e_time.does_intersect(f_time):
                    return False
                return True
            
    ## enforce the weak consecutive semantics
    def _enf_consecw(e_set):
        if e_set == None:
            return True
        for e in e_set:
            for f in e_set:
                if successive_edges(e,f) and e[START_TIME] > f[END_TIME]:
                    return False
        return True
                
#######
##
##    GENERAL HELPER FUNCTIONS
##
#######


# Create a closed sql polygon as an edge-tuple
#  tf------tf
#   |       |
#  ts------ts
# the repeat of the first and last edge is necessary for MySQL to close it
def polygon_tuple(u,v,ts,tf):
    return (u,v,ts,tf,
            ts,tf,  tf,tf,  tf,ts,   ts,ts,  ts,tf)

## The function successive edges takes two edges, e and f, and returns True if
## they are head-to-tail. i.e \exists v, -e->(v)-f->.
def successive_edges(e,f):
    global TARGET
    global SOURCE
    return e[TARGET] == f[SOURCE]


## Makes a time interval from an edge
def make_time(e):
    if type(e) is TimeInterval:
        return e
    else:
        return TimeInterval(*e[START_TIME:END_TIME+1])


def _to_interval(x, y = None):
    if y == None:
        if len(x) == 1:
            return x
        else:
            return make_time(x)
    else:    
        if len(x) == 1 and len(y) == 1: # x,y are time windows
            return (x,y)
        elif len(x) > 1 and len(y) > 1:
            return (make_time(x), make_time(y))

# makes a time interval as a union of the intervals of all input edges
def big_union(edges):
    if len(edges)<= 0:
        return TimeInterval(inf, -inf)
    else:
        t = make_time(edges[0])
        for e in edges[1:]:
            t.union(make_time(e))
        return t

# makes a time interval as a union of the intervals of all input edges
def big_intersect(edges):
    if len(edges)<= 0:
        return TimeInterval(inf, -inf)
    else:
        t = make_time(edges[0])
        for e in edges[1:]:
            t.intersect(make_time(e))
        return t
