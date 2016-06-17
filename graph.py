#  This file presents a very friendly usable interface for a graph. Here is is
#  linked to a database

from sql_helpers import *
from graph_gen import *

class DBGraph():

    def __init__(self,table_name, db, copy_num = 0, es = None):
        self._name = table_name
        self._db = db
        self._copy_num = copy_num
        self._vertices = set()
        self._meta_edges = set()
        self.iterlist = []

        #  if we were given an input edge set, create a graph based on it
        if es == None or len(es) < 0:
            self._edges = set()
            self.edge_tuples(True)
        else:
            self._edges = set(es)
            make_graph(self._name, len(es), self, True, edges = es)

        # calculate the vertices
        self.vertices(True)


    def __len__(self):
        return len(self._edges)

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

    def make_copy_with(self, es = None, vs = None):
        copy_num = self._copy_num + 1
        name = self._name + str(copy_num)
        return DBGraph(name, self._db, copy_num , es, vs)
        
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

    def edge_tuples(self, should_recalc = False):
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

    def edge_tuples_in(self, join_set = None, should_recalc = False):
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
                
            
        
        
    # get and or read the edge set
    def edge_ids(self, should_recalc = False):
        return list(map(lambda e: e[ID], self.edge_tuples(should_recalc)))

    
    # get all the edges that match the edge label-wise 
    def edge_ids_matching(self, edge, e_graph):
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

    def edge_tuples_matching(self,edge,e_graph):
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
        return len(self._vertices)
    
    # Get the number of edges
    def num_edges(self):
        return len(self._edges)

    def edge_tuple(self,eid):
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

    def degree(self,vid):
        return 0

    def edegree(self, edge):
        ## the edge being queried is {2} --> {3}
        degree_sql = """SELECT COUNT(*) FROM `{0}` WHERE `source_id` = {3} OR
                        `dest_id` = {2} OR (`source_id` = {2} AND `dest_id` = {3}
                         AND NOT `edge_id` = {1})
                     """.format(self._name, edge[ID], edge[SOURCE], edge[TARGET],)
    
    # Get the edges going into vertex specified by input vid
    def epred_in(self, e, p_set):
        return [pred for pred in p_set if successive_edges(pred, e)]
        # return self._dir_neighbors_in("dest_id", vid, e_set)

    # Get the dges coming out vertex specified by output uid
    def esucc_in(self, e, s_set):
        return [succ for succ in s_set if successive_edges(e,succ)]
        # return self._dir_neighbors_in("source_id", vid,  e_set)

    def _dir_neighbors_in(self, col_name, vid,  e_set):
        
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
                  
                  
 
