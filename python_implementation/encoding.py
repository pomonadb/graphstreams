from sql_helpers import *
from temporal_helpers import *

KLQS = "cliques"
KLQ_CTS = "clq_cts"

def profile_graph(db, graph, clique_size):
    _cliques(db, graph, clique_size)


def _cliques(db, graph, sz):
    global KLQS
    global KLQ_CTS
    
    # clique (klq) _ name (nm)
    klq_nm = get_hn_name(graph, KLQS)
    cts_nm = get_hn_name(graph, KLQ_CTS)
        
    # make the clique tables
    _make_cliques(db,graph,sz, klq_nm, cts_nm)

    # fill the clique tables
    for i in range(sz):
        _find_cliques(db, graph,sz, klq_nm, cts_nm)

    db.commit()

def _make_cliques(db, graph, sz, klq_nm, cts_nm):
    """
    _make_cliques creates the clique id table, klq_nm, and the clique
                  contents table, cts_nm. Cliques are up to size, sz and
                  found within graph.  db is the database connection object"""
    
    drop_cliques = """DROP TABLE IF EXISTS {0}""".format(klq_nm)
    drop_clq_cts = """DROP TABLE IF EXISTS {0}""".format(cts_nm)
    
    c = db.cursor()
    eng = get_engine(c)[0]

    create_cliques = """
      CREATE TABLE {0}(
         kid INT PRIMARY KEY,
         num_verts INT,
         encoding CHAR({1}),
         window_st INT,
         window_nd INT,
         FOREIGN KEY (kid) REFERENCES {2}(kid),
         INDEX USING BTREE (kid, num_verts))
      ENGINE = {3}
    """.format(klq_nm, sz, cts_nm, eng)
    create_clq_cts = """
     CREATE TABLE {0}(
         kid INT,
         eid INT NOT NULL,
         FOREIGN KEY (eid) REFERENCES {1}(edge_id))
     ENGINE = {2} ;""".format(cts_nm,graph.name(),eng)
    
    c.execute(drop_cliques)
    c.execute(drop_clq_cts)
    c.execute(create_clq_cts)
    c.execute(create_cliques)
    c.close()

def _find_cliques(db, graph, sz, klq_nm, cts_nm):
    """
    _find_cliques mines graph (via the database connection object db) for
                  cliques of size sz, populating klq_nm and cts_nm with the
                  results.
    """
    if sz <= 0:
        return []

    cursor = db.cursor()
    
    cliques = []
    for v in graph.vertices():
        reached, searched = [], []
        reached = [set([v[0]])]
        while len(reached) > 0 :
            c = reached.pop()
            searched.append(c)
            if len(c) >= sz:
                next
            else:
                for vid in graph.adjacent_to(c):
                    reached.append(c | set([vid]))
                    
        cliques.extend(searched)


    clq_lst = list(cliques)
    for i in range(len(clq_lst)):
        cursor.executemany(
            """INSERT IGNORE INTO {0} VALUES ({1}, %s)""".format(cts_nm,i),
            map(lambda x: (x,), list(clq_lst[i])))
        start, end = simplify(graph, clq_lst[i])
        isrt_sql = """
                      INSERT IGNORE INTO {5} (kid, num_verts, encoding, window_st, window_nd) 
                      VALUES ({0}, {1}, "{2}", {3}, {4})
                   """.format(i, len(clq_lst),
                                  encode(db,graph,clq_lst[i]),
                                  start, end, klq_nm)
        cursor.execute(isrt_sql)
    cursor.close()
        
def encode(db, graph,clq):
    conds = ",".join((map(str,list(clq))))
    c = db.cursor()
    sql = """SELECT label FROM {0} as L
             WHERE L.edge_id IN ({1})
          """.format(label_table_name(graph.name()), conds)

    c.execute(sql)
    code = "".join([l[0] for l in c.fetchall()])
    c.close()
    return code
    
    


def simplify(graph, clq_lst):
    ival = Implicit.simplify(Implicit.CONCUR)(graph.induce(clq_lst))
    return (ival.start, ival.end)


def get_hn_name(graph, nm):
    return "{0}_{1}".format(graph.name(), nm)
    


###########################
######## DEAD CODE ########
##########################


def nbh_subgraphs(imp_sem, graph, edge, desired_depth=2):
    curr_depth = 0
    reached, searched = [(curr_depth, edge)], list()
    in_encoding, out_encoding = list(), list()

    temp_tbl = nbhd_tbl_name(graph)
    edge_tbl = graph.name()
    lbl_tbl = label_table_name(edge_tbl)
    
    create_table = """
    CREATE TABLE {0}(
       edge_id INT,
       fdge_id INT,
       label CHAR(1),
       PRIMARY KEY (edge_id, label),
       INDEX USING BTREE (edge_id))
    """.format(temp_tbl)

    loop = """
    DECLARE num_steps SMALLINT DEFAULT 0;
    WHILE num_steps <= {0}:
      INSERT IGNORE INTO {1}
         SELECT DISTINCT root.eid, edges.eid, label, NULL
         FROM {1} as reached, {2} as root, {2} as edges, {3} as lbls
         WHERE 
            reached.edge_id = root.edge_id 
            AND (root.source_id = edges.target_id 
            OR root.target_id = root.source_id)
            AND edges.edge_id = lbls.edge_id;
    """.format(str(desired_depth), temp_tbl, edge_table, lbl_tbl)

    def _triangles(db,graph):
        mk_triangles = """
           DROP TABLE IF EXISTS triangles;
           CREATE TABLE triangles(
              tid INT PRIMARY KEY AUTO INCREMENT,
              eid1 INT, 
              eid2 INT,
              eid3 INT,
              encoding CHAR(3),
              window_st INT,
              window_nd INT,
              INDEX USING BTREE (eid1, eid2, eid3),
              FOREIGN KEY eid1 REFERENCES {0}(edge_id),
              FOREIGN KEY eid2 REFERENCES {0}(edge_id),
              FOREIGN KEY eid3 REFERENCES {0}(edge_id)
           );
           INSERT IGNORE INTO triangles
           SELECT E1.edge_id as eid1, E2.edge_id as eid2, E3.edge_id as eid3, 
                  L1.label+L2.label+L3.label as encoding, E3.start as window_st, 
                  LEAST(E3.end, E2.end, E1.end) as window_nd
           FROM {0} AS E1, {0} AS E2, {0} AS E3, {1} AS L1, {1} AS L2, {3} AS L3
           WHERE
              E1.dest_id = E2.source_id AND E2.dest_id = E3.source_id
              AND E3.dest_id = E1.source
               AND E1.start <= E2.start AND E2.start <= E3.start
               AND E3.start <= E1.end AND E3.start <= E3.end 
               AND E3.start <= E3.end AND E1.edge_id = L1.edge_id 
               AND E2.edge_id = L2.edge_id AND E3.edge_id = L3.edge_id;
        """

        c = db.cursor()
        c.execute(mk_triangles, multi=True)
        db.commit()
        c.close()
