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

    # Get the edges going into vertex specified by input vid
    def pred(self, vid):
        return self._dir_neighbors(True)

    # Get the dges coming out vertex specified by output uid
    def succ(self, vid):
        return self._dir_neighbors(False)

    def _dir_neighbors(self, pred):
        
        col_name = "`dest_id`" if pred else "`source_id`"
        
        c = self._db.cursor()
        c.execute("SELECT UNIQUE(`edge_id`) FROM `edge` "
                  "WHERE `{0}` = {1}".format(col_name, vid))
        return c.fetchall()
        
        
