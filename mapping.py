class Mapping:
    
    # initialize the mapping given an optional input list of pairs and whether
    # the graph is directed
    def __init__(self,directed = True, lst=[]):
        self._directed = directed
        self._function = {}
        self._inverse = {}
        self._size = 0
        for l in lst:
            if len(l) == 2:
                self.size += 1
                self.M.add(l)

    def __str__(self):
        string = ""
        for k in self._function.keys():
            string += "\t{0} |---> {1}\n".format(k,self._function[k])
        return string

    # Insert an edge pair into the set
    def insert(self,e,f):
        if e in self._function or f in self._inverse:
            return False
        else:
            self._size += 1
            self._function[e] = f
            self._inverse[f] = e
            return True

    # remove an object from the set if its present
    def remove (self, e, f):
        if e in self._function and f in self._inverse:
            self._size -= 1
        else:
            print("uh oh. Maps don't have expected keys")
            print("Key", e, "and value", f)
        self._function.pop(e, None)
        self._inverse.pop(f, None)


    def domain(self):
        return list(self._function.keys())

    def image(self):
        return list(self._inverse.keys())

    def get(self, x):
        if x in self._function:
            return self._function[x]
        else:
            print("edge ID", x, "not key in", self._function)
            return None

    def inverse(self, y):
        if y in self._inverse:
            return self._inverse[x]
        else:
            return None
            
    def get_size(self):
        return self._size

    def _check_size(self):
        if self._directed:
            return self._size == len(self.tuple_set)
        else:
            return self.size/2 == len(self.tuple_set)
