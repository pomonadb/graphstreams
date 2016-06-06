#! /usr/bin/python
import MySQLdb
import time
import argparse

def main ():
    parser = argparse.ArgumentParser(description="Calculate the ST-Paths for a T-Graph")
    parser.add_argument("max_len", type=int, help="The maximum length of a path")
    parser.add_argument("start", type=int, help="The year to begin the calculation")
    parser.add_argument("end", type=int, help="the year to end the calculation")
    parser.add_argument("step", type=int, help="The stepsize for the year")

    parser.add_argument("-t", "--timer", action='store_true')
    parser.add_argument("-C", "--clear", action='store_true')
    parser.add_argument("-e", "--edge" , action='store_true')
    parser.add_argument("-j", "--join" , action='store_true')

    args = parser.parse_args()

    if args.edge and args.join:
        print "Must choose only one algorithm. Please include either the --edge or --join flag"
        return False

    # connect to the database
    db = MySQLdb.connect(db="dblp")

    # get the start time if timing it
    if args.timer:
        start_time = time.time()

    # calculate the shortest paths
    num_steps = (args.end - args.start)/args.step
    time_range = [args.start + args.step*x for x in range(num_steps)]

    shortest_path(db, time_range, args.timer, args.clear)
        
    print "For", args.start, "to", args.end, "with max length of", args.max_len

    if args.timer:
        end_time = time.time()
        elapsed = end_time - start_time
        print "\t took", elapsed, "seconds"

    db.close()

#####################################
##         HELPER METHODS          ##
#####################################

    
def get_dist(db, src, tgt):
    c = db.cursor()
    c.execute("""SELECT `d` FROM `e_dist` 
                 WHERE `source` = {0} 
                   AND `target` = {1}
              """.format(src, tgt))
    dist = c.fetchone()
    print "\tDistance from", src, "to", tgt, "read to be", dist
    c.close()
    if dist == None:
        return None
    else:
        return dist[0]

# updates the database with the value of dist
def update_dist(db,src,tgt, dist):
    c = db.cursor()
    print "\tDistance from", src, "to", tgt, "updated to", dist
    #if get_dist(db, src, tgt) != None:
        #print "Conflict on", src, tgt
        
    c.execute("""INSERT INTO `e_dist`(`source`, `target`, `d`) VALUES
                 ({0},{1},{2})
              """.format(src,tgt,dist))
    c.close()

# Calculates the max of inputs checking against null
def new_dist(cur, old):
    if old == None or cur + 1 < old:
        return cur + 1
    else:
        return old
    
# The definition used for two edges to be concurrent
def concurrent(e,f):
    return e["start_time"] <= f["end_time"] and f["start_time"] <= e["end_time"]

# converts eid into edge
def get_edge(db,eid):
    c = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    c.execute("SELECT * FROM `edge_proj` WHERE edge_id = {0}".format(eid))
    edge = c.fetchone()
    return edge


########################
## THE MAIN ALGORITHM ##
########################

# The algorithm for computing the shortest paths between
# all pairs of edges.   
def shortest_paths(db, t_range, use_timer, clear_db):
    c = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    
    # create the desired table
    if clear_db:
        c.execute("DROP TABLE IF EXISTS `e_dist`")
        
    c.execute("""CREATE TABLE IF NOT EXISTS `e_dist`( 
                    `source` INT NOT NULL, 
                    `target` INT NOT NULL, 
                    `d` INT NOT NULL,
                     PRIMARY KEY (`source`,`target`)
                 )""")
    
    print "Table `e_dist` created \n"

    c.execute("""CREATE TEMPORARY TABLE IF NOT EXISTS `edge_proj` LIKE `edge`""")
    
    c.execute("""INSERT INTO `edge_proj` 
                 SELECT *
                 FROM `edge` as `e`
                 WHERE `e`.`start_time`  <= {0} 
                       AND `e`.`end_time` >= {1}
                 """.format(min(t_range),max(t_range)))

    c.execute("""SELECT * FROM `edge_proj`""")

    source = c.fetchone()
    print "the source is", source["edge_id"]

    while source != None:
        update_dist(db,source["edge_id"],source["edge_id"], 0)
        
        # initialize the tracking sets
        reached = set([source["edge_id"]])
        searched = set([])

        # initialize the inner cursor
        c_inner = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        
        while len(reached) > 0:
            e_curr_id = reached.pop()
            # print "\nThe current id:", e_curr_id, "(source)", source["edge_id"]
            e_curr = get_edge(db,e_curr_id)

            # get the neigbors
            c_inner.execute("""SELECT * FROM `edge_proj` 
                               WHERE `src_id` IN {0} or `dest_id` IN {0}
                            """.format("({0},{1})".format(e_curr["src_id"],e_curr["dest_id"])))

            # get the next neighbor
            e_next = c_inner.fetchone()
            while e_next != None and e_next["edge_id"] != e_curr["edge_id"] and \
                  e_next["edge_id"] not in reached | searched:

                print "Find distance from", source["edge_id"], "to", e_next["edge_id"]
                if concurrent(e_curr, e_next):
                    curr_dist = get_dist(db,source["edge_id"], e_curr["edge_id"])
                    old_dist = get_dist(db,source["edge_id"], e_next["edge_id"])
                
                    update_dist(db,source["edge_id"],e_next["edge_id"], new_dist(curr_dist, old_dist))
                
                    reached.add(e_next["edge_id"])
                    
                # get the next candidate edge
                e_next = c_inner.fetchone()
            
            searched.add(e_curr["edge_id"])


        print "Done with source", source["edge_id"]
            
        c_inner.close()
        source = c.fetchone()
        

    
    c.close()
