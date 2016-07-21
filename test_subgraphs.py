import argparse
import random

def main():
    parser = argparse.ArgumentParser(description="generate query graphs")
    parser.add_argument("structure")
    parser.add_argument("-v","--num-vertices", type=int)
    parser.add_argument("-e","--num-edges", type=int)
    parser.add_argument("-d","--duration", type=int, help="maximum duration of edge-window")
    parser.add_argument("-t","--max-time", type=int, help="maximum end time")
    parser.add_argument("-n","--num-graphs", type=int)

    args = parser.parse_args()

    if args.structure in _valid_similar("subgraph"):
        print(generate_subgraphs(args.num_vertices,
                           args.num_edges,
                           args.duration,
                           args.max_time,
                           args.num_graphs))
        
    elif args.structure in _valid_similar("clique"):
        print("Disregarding edge information, clique size is determined by number of vertices")
        print(generate_cliques(args.num_vertices,
                         args.duration,
                         args.max_time,
                         args.num_graphs))
        
    elif args.structure in _valid_similar("tree"):
        print("Tree size is determined by number of vertices")
        print("Interpreting --num-edges/-e as max degree")
        print(generate_trees(args.num_vertices,
                       args.duration,
                       args.max_time,
                       args.num_graphs))
        
    elif args.structure in _valid_similar("path"):
        print("Disregarding edge information, path size is determined by number of vertices")
        print(generate_paths(args.num_vertices,
                       args.duration,
                       args.max_time,
                       args.num_graphs))

    else:
        print("Action ", args.structure, "not recognized" )
        return False

    return True

def generate_subgraphs(v_num, e_num, max_dur, max_time, num_graphs):
    graphs = []
    for i in range(num_graphs):
        edges = []        
        for eid in eids:
            # the source and dest ids
            sid = random.randrange(v_num)
            did = random.randrange(v_num)
            (start, end) = _random_time(max_dur, max_time)
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
                (start,end) = _random_time(max_dur, max_time)
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
            (start, end) = _random_time(max_dur, max_time)
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
                    (start, end) = _random_times(max_dur, max_time)
                    edges.append((eid, vid, vid+f, start, end))
                    eid += 1
            else:
                next

        graphs.append(edges)
            
    return graphs
    

def _valid_similar(name):
    return (name, name + "s", name.upper(), name.upper() + "S")

def _random_time(max_dur, max_time):
    dur = random.randrange(max_dur)
    start = random.randrange(max_time - dur)
    return (start, start+dur)



if __name__ == "__main__" : main()
