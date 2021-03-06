#  This file presents a very friendly usable interface for a graph. Here is is
#  linked to a database

from sql_helpers import *
from graph_gen import *
from encoding import *

class DBGraph():
    """
    A graph object providing read access to an edge-relational table
    """

    def __init__(self,table_name, db, copy_num = 0, es = None):
        """
        Initialize the table. If edges are provided create the table with the given
        edges, otherwise read the given table.
        """
        self._name = table_name
        self._db = db
        self._copy_num = copy_num
        self._vertices = set()
        self._meta_edges = set()
        self.iterlist = []
        self.clique_tbl_name = get_hn_name(self,KLQS)
        self.clique_cts_tbl_name = get_hn_name(self, KLQ_CTS)
        self.label_tbl_name = label_table_name(self._name)


        #  if we were given an input edge set, create a graph based on it
        if es == None or len(es) < 0:
            self._edges = set()
        else:
            self._edges = set(es)
            self._iterlist = list(es)
            make_graph(self._name, len(es), self._db, True, edges = es)

        # calculate the vertices 
        self.vertices(True)
        self._iterlist = self.edge_tuples(True)


    def __len__(self):
        """The number of edges in the set"""
        return len(self._edges)

    def __iter__(self, edge=True):
        """iterate over the edges,no order specified"""
        self._iteration = 0
        
        if edge:
            if len(self._iterlist) != len(self._edges):
                self._iterlist = list(self._edges)
        else:
            if len(self._iterlist) != len(self._vertices):
                self._iterlist = list(self._vertices)

        return self

    def __next__(self):
        """Get the next step of the iteration"""
        if self._iteration >= len(self._edges):
            raise StopIteration
        else:
            eid = self._iterlist[self._iteration]
            self._iteration += 1
            return eid

    def make_copy_with(self, es = None):
        """Make a copy of the edges"""
        copy_num = self._copy_num + 1
        name = self._name + str(copy_num)
        return DBGraph(name, self._db, copy_num , es=es)
        
    # get and/or read the vertex-set
    def vertices(self, recalc = False):
        """Get the vertices, If recalc is True, reread the vertices from the db table"""
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

    def edge_tuples(self, should_recalc = False):
        """Get the edge tuples, if should_recalc is True, reread the edges from
        the table"""
        if should_recalc or len(self._edges) <= 0:
            # open the cursor and execute the query
            self._edges = set()
            c = self._db.cursor()
            c.execute("""SELECT `edge_id`,`source_id`,`dest_id`, `start`, `end` 
                         FROM `{0}`""".format(self._name))

            # add all edges to the edge set
            self._edges = self._edges.union(c.fetchall())
                
            # clean up
            c.close()
            self.iterlist = list(self._edges)

        return self._edges


    def match_hypernodes(self, other):
        """
        Return a dictionary where a query of the form
           dict [self clique_id][other clique_id][self edge_id] 
                    -> [Set of other edge_id]
        that represents the edges matching self.edge_id within the clique pair.
        There is the invariant that the edges are within the respective clique.
        """
        
        candidates = {}

        # for all of the query- and data- hypernodes (hn) prospective pairs, make
        # adjacent and containing edge pairs

        hyprnod_qry = """
              SELECT Qklq.kid, Dklq.kid, Qcts.eid, Dcts.eid 
              FROM {0} AS Qklq, {1} AS Dklq, 
                   {2} AS Qcts, {3} AS Dcts, 
                   {4} AS Qlab, {5} AS Dlab
              WHERE Qklq.num_verts = Dklq.num_verts AND Qklq.encoding = Dklq.encoding
                    AND Qcts.kid = Qklq.kid AND Dcts.kid = Dcts.kid
                    AND Qlab.edge_id = Qcts.eid AND Dlab.edge_id = Dcts.eid
                    AND Qlab.label = Dlab.label
              """.format(self.clique_tbl_name,     other.clique_tbl_name,
                         self.clique_cts_tbl_name, other.clique_cts_tbl_name,
                         self.label_tbl_name,      other.label_tbl_name)

        c = self._db.cursor()
        c.execute(hyprnod_qry)
        
        for (qkid, dkid, eid, fid) in c:
            if candidates.setdefault(qkid, {})\
                         .setdefault(dkid, {})\
                         .setdefault(eid, {}) == {}:
                candidates[qkid][dkid][eid] = {fid}
            else:
                candidates[qkid][dkid][eid].add(fid)
            
        return candidates
    
    def induce(self, vid_set):
        """Returns the edge-set of the subgraph induced on vid_set"""
        sql = """(SELECT edge_id, source_id, dest_id, start, end FROM {0} as E
                 WHERE E.source_id IN({1}))
                 UNION (SELECT edge_id, source_id, dest_id, start, end FROM {0} as E
                 WHERE E.dest_id IN({1}))
 
              """.format(self.name(), ",".join(map(str,vid_set)))

        c = self._db.cursor()
        c.execute(sql)
        eset = c.fetchall()
                         
        return set(eset)
        

    def edge_tuples_in(self, join_set = None, should_recalc = False):
        """Get the edge tuples in the specified join_set. Perform in memory
        intersection if should_recalc is False, and SQL operations otherwise."""
        if should_recalc or len(self._edges) <= 0:

            if join_set == None:
                isect_sfx = ""
            elif len(join_set) <= 0:
                return set()
            else:
                isect_sfx == edge_intersection_suffix(join_set)

                                                       
            selection = """SELECT `edge_id`,`source_id`,`dest_id`, `start`, `end` 
                           FROM `{0}` {1}""".format(self._name, isect_sfx)
                
            # execute the sql
            c = self._db.cursor() # open the cursor
            c.execute(selection)  # execute the query
            edges = c.fetchall()  # save the results
            c.close()             # close the connection
            
            if edges == None:   # if no matching results, return an empty set
                return set()
            else:               # otherwise return the set
                return set(edges)
            
        else:
            return self._edges & set(join_set)
                
            
    def adjacent_to(self, vid_set):
        vert_intersect = set()

        for vid in vid_set:
            vert_intersect &= set(self.vneighborhood(vid))

        return vert_intersect

        
    # get and or read the edge set
    def edge_ids(self, should_recalc = False):
        """Perform an in-memory traversal of the edge_tuples to get the edge ids."""
        return list(map(lambda e: e[ID], self.edge_tuples(should_recalc)))

    
    # get all the edges that match the edge label-wise 
    def edge_ids_matching(self, edge, e_graph):
        """Get the edge ids that have labels matching the label of edge in
           e_graph
          
           SQL OPERATION
        """
        selection = """
                      SELECT DISTINCT `l`.`edge_id` 
                      FROM `{0}` AS `e`, `{1}` AS `l`  
                      WHERE `e`.`edge_id` = {2} 
                            AND `e`.`label` = `l`.`label`
                    """.format(label_table_name(e_graph._name),
                               label_table_name(self._name),
                               edge[ID])
        
        c = self._db.cursor()
        c.execute(selection)
        edge_ids = c.fetchall()
        c.close
        return set(edge_ids)

    def name(self):
        return self._name

    def edge_tuples_matching(self,edge,e_graph):
        """
        Get the edge tuples in self matching the label of edge in e_graph.
        """
        
        selection = """
                      SELECT DISTINCT `edges`.`edge_id`, `edges`.`source_id`, 
                                      `edges`.`dest_id`, `edges`.`start`,
                                      `edges`.`end`                  
                      FROM `{0}` AS `other`, `{1}` AS `labels`, `{2}` AS `edges`
                      WHERE `other`.`edge_id` = {3} 
                            AND `other`.`label` = `labels`.`label`
                            AND `labels`.`edge_id` = `edges`.`edge_id`
                    """.format(label_table_name(e_graph._name),
                               label_table_name(self._name),
                               self._name, edge[ID])
        
        c = self._db.cursor()
        c.execute(selection)
        edges = c.fetchall()
        c.close
        return set(edges)
    
    # Get the number of vertices
    def num_vertices(self):
        """Get the number of vertices in the graph"""
        return len(self._vertices)
    
    # Get the number of edges
    def num_edges(self):
        """Get the number of edges in the graph, the number of rows in the table"""
        return len(self._edges)

    def edge_tuple(self,eid):
        """Get the tuple from the given edge id (SQL)"""
        if eid == None:
            return None
        else:
            c = self._db.cursor() # get the cursor
            sql = """SELECT `edge_id`, `source_id`, `dest_id`, `start`, `end` FROM `{0}` 
                     WHERE `edge_id` = {1}""".format(self._name, eid)                     

            c.execute(sql)
            e = c.fetchone()
            c.close()
            return e

    def edegree(self, edge):
        """Get the degree of the edge, i.e. the number of successor and
        predecessor edges to edge (SQL)"""
        ## the edge being queried is {2} --> {3}
        degree_sql = """SELECT COUNT(*) FROM `{0}` WHERE `source_id` = {3} OR
                        `dest_id` = {2} OR (`source_id` = {2} AND `dest_id` = {3}
                         AND NOT `edge_id` = {1})
                     """.format(self._name, edge[ID], edge[SOURCE], edge[TARGET])

    def eneighborhood(self,eid, src, tgt, *args):
        """
        Get the edges that go into src and out of tgt. *args collects the
        remaining fields of the input edge, allowing this to be called as 
        eneighborhood(*edge) where edge is an edge_tuple.
        """
        c = self._db.cursor()
        c.execute("""
                     SELECT `edge_id`, `source_id`, `dest_id`, `start`, `end` 
                     FROM `{0}` 
                     WHERE `dest_id` = {1} 
                           OR `source_id` = {2}
                  """.format(self._name, src, tgt))

        return c.fetchall()

    def vneighborhood(self, vid):
        """Get the preds and succs of vid"""
        c = self._db.cursor()
        c.execute(""" (SELECT source_id FROM {0} WHERE source_id = {1})
                      UNION (SELECT dest_id FROM {0} WHERE source_id = {1})
                  """.format(self.name(), vid))
        return c.fetchall()
        

        
    # Get the edges going into vertex specified by input vid
    def epred_in(self, e, p_set = None):
        """Gets the predecessors of e in the predecessor set p_set. If no set is given,
        return all predecessors (SQL)

        """
        if p_set == None:
            iterset = self._edges
        else:
            iterset = set(p_set) & self._edges
                
        return [pred for pred in iterset if successive_edges(pred, e)]
        # return self._dir_neighbors_in("dest_id", vid, e_set)

    # Get the dges coming out vertex specified by output uid
    def esucc_in(self, e, s_set = None):
        """get the successors of e in the successor set s_set, if s_set is None
        return all edges (SQL)"""
        if s_set == None:
            iterset = self._edges
        else:
            iterset = set(s_set) & self._edges
        return [succ for succ in iterset if successive_edges(e,succ)]
        # return self._dir_neighbors_in("source_id", vid,  e_set)

    def _dir_neighbors_in(self, col_name, vid,  e_set):
        """"
        Get the directed neighbors of vid that are in the given edge set.
        col_name allows the user to specify whether which column should be
        matched to vid.
        """
        
        c = self._db.cursor()
        
        select_params = (self._name, col_name, vid)
        selection = """SELECT `edge_id`, `source_id`, `dest_id`, `start`, `end` 
                       FROM `{0}` WHERE `{1}` = {2} """.format(*select_params)
        
        if e_set == None:
            selection += ""
        elif len(e_set) > 0:
            selection += edge_intersect_suffix(e_set)
        else:
            return []

        c.execute(selection)
        neighbors = c.fetchall()
        return neighbors
                  
                  
 
