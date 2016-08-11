#! /usr/bin/python

## This file is a bunch of unit tests for the Temporal semantics

from temporal_helpers import *

concurrent = [TimeInterval(*t) for t in [(0,10), (3,7), (2,6), (1, 4)]]
not_concurrent = concurrent + [TimeInterval(50,100)]

nedges = 10
str_consec = []
for i in range(0,nedges):
    str_consec.append((-1, i, i + 1, i, i + .5*nedges))

step = 6
wk_consec = []
for i in range(0,step*nedges,step):
    wk_consec.append((-1, i, i+step, i + step, i + (step/2)))

not_wk_consec = []
for i in range(0,nedges):
    not_wk_consec.append((-1, i, i+1, nedges - (2*i) - 1, nedges - 2*i ))
    

tests = [
    str(TimeInterval(inf, -inf)) == "emptyset",
    TimeInterval(-inf, inf).is_infty(),
    not TimeInterval(-inf,7).is_infty(),
    not TimeInterval(7,inf).is_infty(),
    not TimeInterval(7,8).is_infty(),
    not TimeInterval(8,7).is_infty(),
    TimeInterval(inf,7).is_empty(),
    TimeInterval(-inf, inf).is_infty(),
    not TimeInterval(0,10).is_unbounded(),
    TimeInterval(-inf, inf).is_unbounded(),
    TimeInterval(-inf, 8).is_unbounded(),
    TimeInterval(10,8).is_empty(),

    TimeInterval(inf,7).intersect(TimeInterval(6,7)).is_empty(),
    TimeInterval(0,5).intersect(TimeInterval(3,9)) == TimeInterval(3,5),
    TimeInterval(-inf,inf).intersect(TimeInterval(0,10)) == TimeInterval(0,10),
    TimeInterval(-inf,inf).intersect(TimeInterval(-inf, inf)) == TimeInterval(-inf,inf),
    TimeInterval(inf,inf).intersect(TimeInterval(0,10)).is_empty(),
    TimeInterval(inf,inf).intersect(TimeInterval(inf, -inf)).is_empty(),
    TimeInterval(inf,inf).intersect(TimeInterval(inf, -inf)) == TimeInterval(inf, -inf),

    TimeInterval(-inf,inf).union(TimeInterval(-inf, inf)).is_infty(),
    TimeInterval(10, 15).union(TimeInterval(12,20)) == TimeInterval(10,20),
    TimeInterval(-inf, inf).union(TimeInterval(0,10)).is_infty(),
    TimeInterval(inf, -inf).union(TimeInterval(0,10)) == TimeInterval(0,10),

    Implicit.enforce(Implicit.CONCUR)(concurrent),
    # Implicit.enforce(Implicit.CONSEC_WK)(concurrent),
    # Implicit.enforce(Implicit.CONSEC_STR)(concurrent),
    
    not Implicit.enforce(Implicit.CONCUR)(not_concurrent),
    not Implicit.enforce(Implicit.CONCUR)(str_consec),
    not Implicit.enforce(Implicit.CONCUR)(wk_consec),

    Implicit.enforce(Implicit.CONSEC_STR)(str_consec),
    Implicit.enforce(Implicit.CONSEC_WK)(str_consec),

    not Implicit.enforce(Implicit.CONSEC_STR)(wk_consec),
    
    Implicit.enforce(Implicit.CONSEC_WK)(wk_consec),

    not Implicit.enforce(Implicit.CONSEC_WK)(not_wk_consec)    
]



print("Testing Temporal Semantics")
ts = True
counter = 0
for t in tests:
    if not t:
        print("\t Test", counter, "failed")        
    ts = ts and t
    counter += 1


if ts:
    print("All tests passed!")
else:
    print("SOME TESTS FAILED.")
