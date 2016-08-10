import argparse
import random
from math import inf

def main():
    parser = argparse.ArgumentParser(description="generate query graphs")
    parser.add_argument("implicit")
    parser.add_argument("structure")
    parser.add_argument("-v","--num-vertices", type=int)
    parser.add_argument("-e","--num-edges", type=int)
    parser.add_argument("-d","--duration", type=int, help="maximum duration of edge-window")
    parser.add_argument("-t","--max-time", type=int, help="maximum end time")
    parser.add_argument("-n","--num-graphs", type=int)


    args = parser.parse_args()

    if args.implicit not in ("CONCUR", "SCONSEC", "WCONSEC"):
        print("Unrecognized implicit semantics", implicit)
        print("\tPlease choose from CONCUR, SCONSEC, WCONSEC")
        should_continue = input("Continue anyway? [Y/n]: ")
        if should_continue.upper() == "N":
            print("Exiting..")
            return False
             

    if args.structure in _valid_similar("subgraph"):
        print(generate_subgraphs(args.num_vertices,
                                 args.num_edges,
                                 args.duration,
                                 args.max_time,
                                 args.num_graphs, args.implicit))
        
    elif args.structure in _valid_similar("clique"):
        print("Disregarding edge information, clique size is determined by number of vertices")
        print(generate_cliques(args.num_vertices,
                               args.duration,
                               args.max_time,
                               args.num_graphs,
                               args.implicit))
        
    elif args.structure in _valid_similar("tree"):
        print("Tree size is determined by number of vertices")
        print("Interpreting --num-edges/-e as max degree")
        print(generate_trees(args.num_vertices,
                             args.duration,
                             args.max_time,
                             args.num_graphs,
                             args.implicit))
        
    elif args.structure in _valid_similar("path"):
        print("Disregarding edge information, path size is determined by number of vertices")
        print(generate_paths(args.num_vertices,
                             args.duration,
                             args.max_time,
                             args.num_graphs,
                             args.implicit))

    else:
        print("Action ", args.structure, "not recognized" )
        return False

    return True

def generate_subgraphs(v_num, e_num, max_dur, max_time, num_graphs, implicit):
    graphs = []
    for i in range(num_graphs):
        edges = []        
        for eid in eids:
            # the source and dest ids
            sid = random.randrange(v_num)
            did = random.randrange(v_num)
            (start, end) = _random_time(max_dur, max_time, implicit, edges, src,
                                        dst)
            edges.append((eid,sid,did,start,end))

        graphs.append(edges)

    return graphs

def generate_cliques(v_num, max_dur, max_time, num_graphs):
    graphs = []
    for i in range(num_graphs):
        edges = []
        eid = 0
        for vid in range(vid):
            for uid in set(range(vid)) - set([vid]):
                (start,end) = _random_time(max_dur, max_time, implicit, edges,
                                           src, dst)
                edges.append(eid, vid, uid, start, end)
                eid += 1
            
        graphs.append(edges)    
    return graphs

def generate_paths(v_num, max_dur, max_time, num_graphs):
    graphs = []
    for i in range(num_graphs):
        edges = []
        eid = 0
        for vid in range(v_num-1):
            (start, end) = _random_time(max_dur, max_time, implicit, edges, src,
                                        dst)
            edges.append((eid, vid, vid+1, start, end))
            eid += 1
        graphs.append(edges)
    return graphs

def generate_trees(v_num, max_degree, max_dur, max_time, num_graphs):
    graphs = []
    for i in range(num_graphs):
        edges = []
        eid = 0
        fanout = 0
        for vid in range(v_num-1):
            if fanout == 0:
                fanout = random.randrange(max_degree)
                for f in range(1,fanout):
                    (start, end) = _random_times(max_dur, max_time, implicit,
                                                 edges, src, dst)
                    edges.append((eid, vid, vid+f, start, end))
                    eid += 1
            else:
                next

        graphs.append(edges)
            
    return graphs
    

def _valid_similar(name):
    return (name, name + "s", name.upper(), name.upper() + "S")

def _random_time(max_dur, max_time, implicit, edges, src, dst):
    dur = random.randrange(max_dur)
    if implicit == "CONCUR":
        intersection = _big_isect(edges)
        
        if intersection[0] > intersection[1]:
            print("BAD INTERSECTION", intersection)
            return _random_time(max_dur, max_time, "", edges, src, dst)
        else:
            start = random.randrange(intersection[0]+1-dur,intersection[1])
            end = start + dur

    elif implicit == "SCONSEC":
        pred_isect = _big_isect(_get_pred_edges(edges,src), max_time)
        succ_edges = _big_isect(_get_succ_edges(edges,dest), max_time)
        t = random.randrange(*pred_isect)
        s = random.randrange(*succ_edges)
        start = min(t,s)
        end = max(t,s)
        
    elif implicit == "WCONSEC":
        pred_isect = _big_isect(_get_pred_edges(edges,src), max_time)
        succ_edges = _big_isect(_get_succ_edges(edges,dest), max_time)
        start = random.randrange(succ_edges[1])
        end = random.randrange(max(start + dur, succ_edges[0]), max_time)
    else:
        start = random.randrange(max_time - dur)
    return (start, end)

def _get_pred_edges(edges, src):
    return filter(lambda e: e[2] == src, edges)
    
    
def _get_succ_edges(edges, dest):
    return filter(lambda e: e[1] == dest, edges)

def _big_isect(edges, max_time):
    intersection = (-1, max_time)
    for e in edges:
        if intersection[0] == None:
            intersection = (e[3], intersection[1])
        if intersection[1] == None:
            intersection = (intersection[0], e[4])

        intersection = (max(intersection[0], e[3]),
                        min(intersection[1], e[4]))
    


if __name__ == "__main__" : main()
