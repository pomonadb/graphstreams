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

    args = parser.parse_args()

    # connect to the database
    db = MySQLdb.connect(passwd="password",db="dblp")

    # get the start time if timing it
    if args.timer:
        start_time = time.time()

    # calculate the shortest paths
    num_steps = (args.end - args.start)/args.step
    time_range = [args.start + args.step*x for x in range(num_steps)]
    
    join_shortest_path(db.cursor(), time_range, args.max_len, args.timer, args.clear)
        
    print "calculating for", args.start, "to", args.end, "with max length of", args.max_len

    if args.timer:
        end_time = time.time()
        elapsed = end_time - start_time
        print "\t took", elapsed, "seconds"

    
def join_shortest_path(c, t_range, max_len, is_timing, clear):
    # create the desired table
    if clear:
        c.execute("DROP TABLE IF EXISTS `dist{0}`".format(max_len))
    c.execute("""CREATE TABLE IF NOT EXISTS `dist{0}`( 
                    `did` INT PRIMARY KEY AUTO_INCREMENT, 
                    `t` INT NOT NULL, 
                    `source` INT NOT NULL, 
                    `target` INT NOT NULL, 
                    `d` INT NOT NULL, 
                    `start` INT NOT NULL, 
                    `end` INT)""".format(max_len))
    print "Table `dist{0}` created \n".format(max_len)

    # Iterate through each year
    for t in t_range:
        if is_timing:
            ts = time.time()
        c.execute("""INSERT INTO `dist{1}` (`t`,`source`,`target`,`d`,`start`,`end`)
                     SELECT {0}, `source`, `target`, 1, `year` - 2, `year` + 2
                     FROM `graph_tbl1`
                     WHERE
                        {0} >= `year` - 2 AND {0} <= `year` + 2; 
                     """.format(t,max_len))
        
        print "Inserted adjacency matrix at time", t
        print "\t Step at l =", 0
        
        for l in range(1, max_len):
            if is_timing:
                s = time.time()
            c.execute("""INSERT INTO `dist{2}`(`t`,`source`,`target`,`d`,`start`,`end`)
                         SELECT {0}, `Dl`.`source`, `D1`.`target`, 
                               `Dl`.`d` + `D1`.`d`,`D1`.`start`, `D1`.`end`
                         FROM `dist{2}` as `Dl`, `dist{2}` as `D1`
                         WHERE `Dl`.`start` <= `D1`.`end` AND `D1`.`start` <= `Dl`.`end`
                               AND `Dl`.`target` = `D1`.`source`
                               AND `Dl`.`d` + `D1`.`d` <= {1} + 1
                               AND `Dl`.`d` = {1} 
                               AND `D1`.`d` = 1""".format(t,l,max_len))
            
            print "\t Step at l =", l
            if is_timing:
                e = time.time()
                print "\t took", (e - s), "seconds"

        if is_timing:    
            te = time.time()
            print "\t year", t, "took", (te-ts), "seconds"

        
main()
