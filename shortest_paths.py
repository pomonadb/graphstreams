#! /usr/bin/python
import MySQLdb
import time
import argparse
import join_path
import edge_path

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

    if args.join:
        print "Join algorithm"
        join_path.shortest_paths(db.cursor(), time_range, args.max_len, args.timer, args.clear)
    elif args.edge:
        print "Edge-Dijkstra"
        edge_path.shortest_paths(db, time_range, args.timer, args.clear)
        
    print "For", args.start, "to", args.end, "with max length of", args.max_len

    if args.timer:
        end_time = time.time()
        elapsed = end_time - start_time
        print "\t took", elapsed, "seconds"

    db.close()
        
main()
