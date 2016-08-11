# This file was initially a graph generator file, but has merged to be a graph
# general helper file, specifying construction, constant, and construction
# functions.

from math import ceil, sqrt
from random import randrange, choice
import string

from sql_helpers import *
from temporal_helpers import *

MIN_TIME = 0
MAX_TIME = 10
TIME_RANGE = 20
DENSITY = 0.5
NUM_LABELS = 5
MAX_SQL_INT = 2147483647

# This function creates a random graph and inserts it into a specified database
# table. It also creates indices on the table.
def make_graph(tbl_name, num_edges, db, force_clear, dens = -1, edges = None):
    """
    Create a database table in db called tbl_name, with num_edges edges. If the
    graph is there, and the force-clear flag is given, remove the table
    first. If edges are given, create a table with a copy of tbl_name.

    tbl_name -- str representing the base-name of the table
    num_edges -- the number of edges in the graph, should correspond to number
                 of table rows
    db -- the database connection object in which to create the table
    force_clear -- a boolean flag specifying to 
    
    """
    
    global DENSITY
    
    # tbl_name(edg_id, source_id, dest_id, time)
    columns = ("edge_id", "source_id", "dest_id", "start", "end", "time")
    
    c = db.cursor() # get the cursor
    create_params = (tbl_name,) + columns + get_engine(c)
    insert_params = (tbl_name,square()) + columns
            

    # if specified as program argument, drop existing tables
    if force_clear:
        c.execute("DROP TABLE IF EXISTS `{0}`".format(tbl_name))
        c.execute("DROP TABLE IF EXISTS `{0}`".format(label_table_name(tbl_name)))

    if edges == None:
        # Check whether an appropriate number of edges was given
        if num_edges == None or num_edges <= 0:
            return False

        # use the global default if a bad value was given
        density = DENSITY if dens == None or dens < 0 else dens

        # Calculate the number of vertices based on the function for a simple graph
        # D = |E|/(|N|(|N|-1))
        # Here we round up so that we can use it in a range object.
        num_vertices = ceil(sqrt(num_edges/density))

        print("Making an edge set for", tbl_name , "with", num_edges, "Edge")
        edges = _generate_random_edge_set(num_edges, num_vertices)
        
        # generate the edges, create the graph, and then the labels
        _make_edge_table(create_params, insert_params, edges, db)
        _make_label_table(tbl_name, columns[0], edges, create_params[-1], db,
                          NUM_LABELS)
    else:
        edges = [polygon_tuple_with_id(*e) for e in edges]
        _make_edge_table(create_params, insert_params, edges, db, with_id = True)
        _copy_label_table(db,tbl_name)



    # clean up
    db.commit()
    c.close()

    return True

# this function generates a random edge set given two integers, the number of
# edges, and the number of vertices.    
def _generate_random_edge_set(num_edges, num_vertices):
    """ 
    generates a random set of edges using num_edges edges and num_vertices
    vertices.
    """
    
    global MAX_TIME
    global MIN_TIME
    global TIME_RANGE

    while True:
        edges = set() # initialize accumulator

        # for every edge
        for i in range(0,num_edges):
        
            # pick a random start vertex
            u = randrange(0, num_vertices)

            # get a random end vertex that is not a self-loop
            v = u
            while v == u:
                v = randrange(0, num_vertices)

                # pick an arbitrary start and end time
                times = []
                times.append(randrange(MIN_TIME, MAX_TIME)) #start
                times.append(randrange(times[0]+1, times[0] + TIME_RANGE)) # end

                edges.add(polygon_tuple(u,v,times[0],times[1]))

        time_edges = map(lambda e: (-1,) + e, edges)
        if Implicit.enforce(Implicit.CONCUR)(time_edges):
            break
        else:
            edges = set()
        
    return edges


def _make_label_table(edge_tbl, edge_key, edges, engine, db, num_labels):
    """
    Create a randoms set of labels. And add it to the database.

    edge_tbl   -- the str name of the base table of edges
    edge_key   -- the str name of the column
    edges      -- the set of edges in the base table
    engine     -- the engine to be used in constructing the table
    db         -- the database connection object
    num_labels -- the cardinality of the label set.
    """
    
    new_tbl_name = label_table_name(edge_tbl)
    
    params = (new_tbl_name, edge_key, edge_tbl, engine)
    
    make_table = """
             CREATE TABLE `{0}` (
               `{1}` INT NOT NULL, 
               `label` CHAR(1), 
                FOREIGN KEY (`{1}`) REFERENCES `{2}`(`{1}`)
                ON DELETE CASCADE ON UPDATE CASCADE)
                ENGINE = {3}
          """.format(*params)

    populate_table = """
        INSERT INTO `{0}`(`{1}`, `label`) VALUES (%s,%s)
        """.format(*params)
    
    labels = []
    for idx in range(1,len(edges)+1):
        n = randrange(1,num_labels)
        for i in range(0,n):
            l = choice(string.ascii_lowercase[:num_labels])
            labels.append((idx,l))
   
    key_idx = """ALTER TABLE `{0}` ADD INDEX (`{1}`) USING HASH""".format(*params)
    lbl_idx = """ALTER TABLE `{0}` ADD INDEX (`label`) USING HASH""".format(*params)


    # establish the connection and insert everything
    c = db.cursor()
    c.execute(make_table)                 # create the table
    c.executemany(populate_table, labels) # insert all labels

    db.commit()                 # save changes

    # create the indices
    c.execute(key_idx)
    c.execute(lbl_idx)

    # clean up
    c.close()
    db.commit()
    
    return True
    
    
def _make_edge_table(create_params, insert_params, edges, db, with_id = False):
    """
    Build a database table based on the number of edges.
    
    create_params -- a tuple of the table name, the 6 columns and the engine.
    insert_params -- a tuple of the table name, the polygon object and the
                     column names
    edges         -- the edges to be added
    db            -- the db connection object
    with_id       -- the optional flag specifying whether edge_id has been given. 
    """

    if len(create_params) < 8 or len(insert_params) < 7:
        print("ERROR: UNABLE TO BUILD TABLE, MALFORMED SQL")
        return False
    else:            
        create = """CREATE TABLE IF NOT EXISTS `{0}`(
                       `{1}` INT AUTO_INCREMENT NOT NULL,
                       `{2}` INT,
                       `{3}` INT,
                       `{4}` INT,
                       `{5}` INT,
                       `{6}` GEOMETRY NOT NULL,
                        PRIMARY KEY(`{1}`))
                        ENGINE = {7}
                 """.format(*create_params)
        
        # craft the insertion sql statement
        if with_id:
            insert_sql = """INSERT INTO `{0}` (`{2}`, `{3}`, `{4}`, `{5}`, `{6}`,`{7}`)
                            VALUES (%s,%s,%s,%s,%s,{1})
                         """.format(*insert_params)
        else:
            insert_sql = """INSERT INTO `{0}` (`{3}`, `{4}`, `{5}`, `{6}`, `{7}`)
                            VALUES (%s,%s,%s,%s,{1})
                         """.format(*insert_params)

        # craft the index creation statements
        vid_idx = index_sql("idx_vids", create_params[0], create_params[1:2],
                            is_hash = True)
        time_idx = index_sql("idx_start_end",create_params[0], create_params[1:5])
        rtree_idx = """ALTER TABLE `{0}` ADD SPATIAL INDEX
        (`time`)""".format(*create_params)
    
        # establish connection and insert everything
        c = db.cursor()
        c.execute(create)                                 # create the table
        linted_edges = _lint_inftys(edges)
        print(linted_edges)
        batch_insert(db, insert_sql, linted_edges) # insert in chunks
        
        # add the indices
        c.execute(vid_idx)
        c.execute(time_idx)
        c.execute(rtree_idx)

        # clean up
        c.close()
        db.commit()
        
        return True


def _copy_label_table(db, table_name):
    """
    Create a duplicate label table, same data, different name

    see label_table_name in sql_helpers for the naming scheme.
    """
    old_name = label_table_name(table_name[:-1])
    new_name = label_table_name(table_name)
    c = db.cursor()
    c.execute("""CREATE TABLE `{0}` LIKE `{1}`""".format(new_name, old_name))
    c.execute("""INSERT `{0}` SELECT * FROM `{1}`""".format(new_name, old_name))
    db.commit()
    c.close()
    
def _lint_inftys(edges):
    effect_inf = "~0"
    return [_lint_edge(e) for e in edges]

def _lint_edge(e):
    el = list(e)
    no_inf  = lambda x : MAX_SQL_INT if x == inf else x
    no_ninf = lambda x : -1 if x == -inf else x        
    return tuple([no_inf(no_ninf(x))for x in el])
            
