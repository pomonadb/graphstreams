class DBGraph():

    def __init__(self,table_name, db):
        self._name = table_name
        self._db = db
        self._vertices = set()
        self._edges = set()
        self._meta_edges = set()
        self.iterlist = []
        self.vertices(True)
        self.edges(True)

    def __iter__(self, edge=True):
        self._iteration = 0
        
        if edge:
            if len(self._iterlist) != len(self._edges):
                self._iterlist = list(self._edges)
        else:
            if len(self._iterlist) != len(self._vertices):
                self._iterlist = list(self._vertices)

        return self

    def __next__(self):
        if self._iteration >= len(self._edges):
            raise StopIteration
        else:
            eid = self._iterlist[self._iteration]
            self._iteration += 1
            return eid
        
        
    # get and/or read the vertex-set
    def vertices(self, recalc = False):
        if recalc or len(self._vertices) <= 0:
            self._vertices = set()
            # open the cursor and execute the query
            cursor = self._db.cursor()
            cursor.execute(
                """
                (SELECT DISTINCT(`source_id`) FROM {0})
                UNION
                (SELECT DISTINCT(`dest_id`) FROM {0})
                """.format(self._name)
            )
            
            # add each vertex id to the vertex set
            for vid in cursor:
                self._vertices.add(vid)
                
            # clean up and return the result set
            cursor.close()
            return self._vertices
        else: 
            return self._vertices 

    # get and or read the edge set
    def edges(self, recalc = False):
        if recalc or len(self._edges) <= 0:
            self._vertices = set()
            # open the cursor and execute the query
            c = self._db.cursor()
            c.execute("""SELECT `edge_id` FROM `{0}`""".format(self._name))

            # add each edge to the vertex set
            for eid in c:
                self._edges.add(eid[0])
                
            # clean up and return the result set
            c.close()
            self.iterlist = list(self._edges)
            return self._edges
        else: 
            return self._edges

    # Get the number of vertices
    def num_vertices(self):
        return len(self._vertices)
    
    # Get the number of edges
    def num_edges(self):
        return len(self._edges)

    def edge_tuple(self,eid):
        if eid == None:
            return None
        else:
            c = self._db.cursor() # get the cursor
            sql = """SELECT DISTINCT * FROM {0} 
                     WHERE `edge_id` = {1}""".format(self._name, eid)
            c.execute(sql)
            e = c.fetchone()
            c.close()
            return e

    def degree(self,vid):
        return 0
    
    # Get the edges going into vertex specified by input vid
    def epred_in(self, vid, e_set):
        return self._dir_neighbors_in("dest_id", vid, e_set)

    # Get the dges coming out vertex specified by output uid
    def esucc_in(self, vid, e_set):
        return self._dir_neighbors_in("source_id", vid,  e_set)

    def _dir_neighbors_in(self, col_name, vid,  e_set):
        
        
        c = self._db.cursor()
        
        select_params = (self._name, col_name, vid)
        
        selection = """SELECT `edge_id`, `source_id`, `dest_id` FROM `{0}` 
                     WHERE `{1}` = {2} """.format(*select_params)


        if e_set == None:
            selection += ""
        elif len(e_set) > 0:
            selection += "AND `edge_id` IN ({0})".format(",".join(map(str, list(e_set))))
        else:
            return []

        c.execute(selection)
        neighbors = c.fetchall()
        return neighbors
                  
                  
