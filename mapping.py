class Mapping:
    
    # initialize the mapping given an optional input list of pairs and whether
    # the graph is directed
    def __init__(self,directed = True, lst=[]):
        self._directed = directed
        self.tuple_set = set()
        self._size = 0
        for l in lst:
            if len(l) == 2:
                self.size += 1
                self.M.add(l)

    def __str__(self):
        string = ""
        for t in self.tuple_set:
            string += "\t{0} |---> {1}\n".format(t[0],t[1])
        return string

    # Insert an edge pair into the set
    def insert(self,e,f):
        self._size += 1
        self.tuple_set.add((e,f))
        if not self._directed:
            self.M.add((f,e))

    # remove an object from the set if its present
    def remove (self, e, f):
        self._size -= 1
        self.tuple_set.remove((e,f))
        if not self._directed:
            self.tuple_set.remove((f,e))

    def get_size(self):
        return self._size

    def _check_size(self):
        if self._directed:
            return self._size == len(self.tuple_set)
        else:
            return self.size/2 == len(self.tuple_set)
