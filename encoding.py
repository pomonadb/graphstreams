# This file establishes the encoding methodology for temporal neigborhood
# encodings. An encoding is a double that includes the sorted list of pairs
# edge-vertex labels, and 


# This method calculates the encodings of the temporal r-neighborhoods of edge
# in graph, where r = desired_depth
def encoding(imp_sem, graph, edge, desired_depth = 2):
    nsg_set = _temp_nbh_subgraphs(imp_sem,graph, edge, desired_depth)
    encodings = [_encode(nsg) for nsg in nsg_set]
    return encodings


def _temp_nbh_subgraphs(imp_sem, graph, edge, desired_depth):
    curr_depth = 0
    reached, searched = [(curr_depth, edge)], list()
    in_encoding, out_encoding = list(), list()
    
    # until there are no more nodes that can be reached
    idx = 0
    while i < len(reached):
        (depth, e) = reached.pop()
        if depth <= desired_depth and e not in searched and e not in reached:
            searched.add(e)
            reached.add(graph.eneighbors(ne))
            i += 1
        else:
            break
                
    
    
