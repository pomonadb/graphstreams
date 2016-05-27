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

    shortest_path(db.cursor(), time_range, args.timer, args.clear)
        
    print "For", args.start, "to", args.end, "with max length of", args.max_len

    if args.timer:
        end_time = time.time()
        elapsed = end_time - start_time
        print "\t took", elapsed, "seconds"


def shortest_paths(c,t_range, use_timer, clear_db):
     # create the desired table
    if clear_db:
        c.execute("DROP TABLE IF EXISTS `e_dist`")
        
    c.execute("""CREATE TABLE IF NOT EXISTS `e_dist`( 
                    `did` INT PRIMARY KEY AUTO_INCREMENT, 
                    `t` INT NOT NULL, 
                    `source` INT NOT NULL, 
                    `target` INT NOT NULL, 
                    `d` INT NOT NULL, 
                    `start` INT NOT NULL, 
                    `end` INT)""")
    print "Table `dist` created \n"
