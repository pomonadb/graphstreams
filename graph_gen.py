from math import *
from random import randrange

from sql_helpers import *

MIN_TIME = 0
MAX_TIME = 2016
TIME_RANGE = 10
DENSITY = 0.5

# This function creates a random graph and inserts it into a specified database
# table. It also creates indices on the table.
def make_graph(tbl_name, num_edges, db, force_clear, dens = -1):
    global DENSITY
    
    # Check whether an appropriate number of edges was given
    if num_edges == None or num_edges <= 0:
        return False

    # use the global default if a bad value was given
    density = DENSITY if dens < 0 else dens

    # Calculate the number of vertices based on the function for a simple graph
    # D = |E|/(|N|(|N|-1))
    # Here we round up so that we can use it in a range object.
    num_vertices = ceil(sqrt(num_edges/density))

    print("Making an edge set for", tbl_name , "with", num_edges, "Edge")
    edges = _generate_random_edge_set(num_edges, num_vertices)
        
    c = db.cursor() # get the cursor

    # if specified as program argument, drop existing tables
    if force_clear:
        c.execute("DROP TABLE IF EXISTS `{0}`".format(tbl_name))

    # create the table withthe given name
    # tbl_name(edg_id, source_id, dest_id, time)
    columns = ("edge_id", "source_id", "dest_id", "time")

    create_params = (tbl_name,) + columns + get_engine(c)
    
    # build the db table
    c.execute("""CREATE TABLE IF NOT EXISTS `{0}`(
                 `{1}` INT AUTO_INCREMENT PRIMARY KEY,
                 `{2}` INT,
                 `{3}` INT,
                 `{4}` GEOMETRY NOT NULL)
                  ENGINE = {5}
               """.format(*(create_params)))


    insert_params = (tbl_name,square()) + columns[1:]
    
    # craft the insertion sql statement
    insert_sql = """INSERT INTO `{0}` (`{2}`, `{3}`, `{4}`)
                    VALUES (%s,%s,{1})
                 """.format(*(insert_params))
    
    # insert everything
    batch_insert(db, insert_sql, edges)

    ## Add indices
    c.execute(index_sql("idx_vids", tbl_name, columns[0:2],
                        is_hash = True))
    
    c.execute("""ALTER TABLE `{0}` ADD SPATIAL INDEX (`time`)""".format(tbl_name))
    
    db.commit()
    c.close()

# this function generates a random edge set given two integers, the number of
# edges, and the number of vertices.    
def _generate_random_edge_set(num_edges, num_vertices):
    global MAX_TIME
    global MIN_TIME
    global TIME_RANGE

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
        times.append(randrange(times[0], times[0] + TIME_RANGE)) # end

        edges.add(polygon_tuple(u,v,times[0],times[1]))
        
    return edges

# Create a closed sql polygon as an edge-tuple
#  tf------tf
#   |       |
#  ts------ts
# the repeat of the first and last edge is necessary for MySQL to close it
def polygon_tuple(u,v,ts,tf):
    return (u,v,
            ts,tf,  tf,tf,  tf,ts,   ts,ts,  ts,tf)

## The function successive edges takes two edges, e and f, and returns True if
## they are head-to-tail. i.e \exists v, -e->(v)-f->.
def successive_edges(e,f):
    global TARGET
    global SOURCE
    return e[TARGET] == f[SOURCE]
