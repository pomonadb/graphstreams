from sql_helpers import *
from temporal_helpers import *

class Mapping:
    """The object that provides insert, read, and delete actions for an isomorphism

    The underlying data model is two dictionaries _function and _inverse. where
    for an input pair (e,f) function has key e and value f, and _inverse has key
    f and value e, hence enforcing bijection.

    """
    
    # initialize the mapping given an optional input list of pairs and whether
    # the graph is directed
    def __init__(self,directed = True, lst=[]):
        """
        Initialize the mapping, by default directed, and empty 

        Specify directed = False for undirected, and give a nonempty list of
        pairs to specify starting state of the iso.

        """
        self._directed = directed
        self._function = {}
        self._inverse = {}
        self._buf = ([],[])
        self._exp_okay = True
        self._imp_okay = True
        self._size = 0
        for l in lst:
            if len(l) == 2:
                self.size += 1
                self.M.add(l)

    def __str__(self):
        """Specify the logging method for the isomorphism

           This is currently in a useful state for debugging and readability, not for parsing.
        """
        string = ""
        for k in self._function.keys():
            string += "\t{0} |---> {1}\n".format(k,self._function[k])
        return string

    # Insert an edge pair into the set
    def insert(self,e,f):
        """Insertions the pair (e,f) if it is not already in the iso."""
        if self.already_mapped(e,f):            
            return False
        else:
            self._size += 1
            self._function[e] = f
            self._inverse[f] = e
            return True

    # remove an object from the set if its present
    def remove (self, e, f):
        """remove an object from the isomorphism it is there, otherwise print a warning message"""
        if e in self._function and f in self._inverse:
            self._size -= 1
        else:
            print("WARNING: uh oh. Maps don't have expected keys")
            print("\t\tKey", e, "and value", f)
        self._function.pop(e, None)
        self._inverse.pop(f, None)

    def temp_semantics(self, global_iv, exp, imp):
        """Return TRUE if I match the explicit and implicit (exp, imp) semantics"""
        maybe_domain = self.domain() + self._buf[0]
        maybe_image = self.image_of(self.domain()) + self._buf[1]
        self._exp_okay &= Explicit.enforce(exp, global_iv)(self._buf[0],self._buf[1])
        if self._exp_okay:
            self._imp_okay &= Implicit.enforce(imp)(maybe_image)
            return self._imp_okay
        else:
            return False
        
        
        
    def image_of(self, dom_lst):
        """Gets a list of the image of input iterator (not necessarily a set)"""
        img = []
        ## take the image of the input set (ordered list)
        for e in dom_lst:
            f = self.get(e)
            img.append(f)
            
        return img
        
    def unzip(self):
        """
        Return a list of tuples, (preimage, image) of the mapping
        """
        tuple_list = list(self._function.items())
        if len(tuple_list) <= 0:
            return ((),())
        else:
            return list([t for t in zip(*tuple_list)])
    
    def domain(self):
        """
        Get the domain of the isomorphism
        """
        return list(self._function.keys())

    def image(self):
        """get the image of the isomorphism"""
        return list(self._inverse.keys())

    def get(self, x, warning = "WARNING!"):
        """get the value of the key x with warning message warning"""
        if warning == None or x in self._function:
            return self._function[x]
        else:
            print("!" + ("="*35) + warning + "="*35 + "!")
            print("\tedge ID", x, "not key in", self._function)
            return None

    def inverse(self, y):
        """Get the key for the value y"""
        if y in self._inverse:
            return self._inverse[x]
        else:
            return None

    def already_mapped(self, e, f):
        """A boolean that returns true if e or f is already in the map."""
        return e in self._function or f in self._inverse


    def add_to_buffer(self,e,f):
        """Add e and f to the buffer of edges to be added"""
        self._buf[0].append(e)
        self._buf[1].append(f)
        
    def flush(self):
        for i in range(0,len(self._buf[0])):
            self.insert(self._buf[0][i], self._buf[1][i])
        self.empty_buffer()

    def empty_buffer(self):
        self._buf = ([],[])
            
    def get_size(self):
        """Get the number of pairs in the map"""
        return self._size

    def _check_size(self):
        """A boolean that returns true if the size counter is the same as the set (for
        debugging)

        """
        if self._directed:
            return self._size == len(self.tuple_set)
        else:
            return self.size/2 == len(self.tuple_set)
