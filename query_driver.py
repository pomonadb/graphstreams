#! /usr/bin/python

from graph_tool.all import *
try:
     import MySQLdb
except ImportError:
     print \
          "Please install the mysqldb plugin using one of the following commands \n" \
          "\t pip install mysql-python \n " \
          "\t easy_install install mysql-python # deprecated \n " \
          "\t sudo apt-get install python-mysqldb \n" \
          "\t yum install MySQL-python \n" \
          "or follow the link below for Windows instructions: \n" \
          "\t http://stackoverflow.com/questions/21440230/install-mysql-python-windows"

import getpass
import argparse
from sets import Set
from collections import namedtuple

def main ():
    parser = argparse.ArgumentParser(description='Drive the queries to be executed')

    # the code to be executed. The existence of these is mutually exclusive
    parser.add_argument('--script', help='filepath tothe script to be run')
    parser.add_argument('--sql', help='filepath to the sql query to be executed')

    # The arguements required to enter the database
    parser.add_argument('-db', '--database', help= 'The MySQl Database')
    parser.add_argument('-u','--username', help='the MySQl username')
    parser.add_argument('-p', '--password', action='store_true',
        help='Indicates intent to supply a MySQL password')

    # get the arguments
    args = parser.parse_args()

    # Stop execution if the connection to the database failed
    conn = db_connect(args.database, args.username, args.password)
    if conn == None:
        return

    if (args.script != None and args.sql != None):
        print "Please execute either SQL or python script"
        return

    elif (args.script != None):
        print "Execute python in file: " + args.script
        execfile(args.script)

    elif (args.sql != None):
        print "Excute SQL: \n"

        query = ""
        with file(args.sql) as f:
            query = f.read()

        conn.cursor.execute(query)

        print conn.cursor.fetchall()

def db_connect(db_name, username, needs_password):

    pw = "\n"
    if needs_password:
        pw = getpass.getpass()

    # try:
        # Connect to the database and create the access point (cursor)
        db = MySQLdb.connect(passwd=pw, db=db_name, local_infile=1)
        c = db.cursor()

        conn = namedtuple("database", ['db','cursor'])
        return conn(db = db, cursor=c)

    # except:
        # print "Connection error"
        # return None


def load_sql_as_graph(is_directed, query, cursor, prop_names, prop_types):

    # create the graph
    g = Graph(directed = is_directed)
    id_vprop = g.new_vertex_property("string")

    # make id an internal vertex property of the graph
    g.vp.id = id_vprop

    # collect and add the edge properties/labels
    edge_props = []
    for i in range(0,min(len(prop_names), len(prop_types))):
        eprop = g.new_edge_property(prop_types[i])
        edge_props.append(eprop)
        g.edge_properties[prop_names[i]] = eprop

    # execute the query
    cursor.execute(query)

    # create the vertices and edges
    edges = []
    if is_directed:
        edges = cursor.fetchall()
    else:
        edges = list(set(cursor.fetchall()))

    # keeps record. the index
    vertex_ids = []
    v_vnames = {} # pairs vertex names with graph index

    # Iterate through edges
    for e in edges:

        # create or get the head and tail vertices
        head = add_or_get_vertex(e[1], vertex_ids, g, v_vnames)
        tail = add_or_get_vertex(e[0], vertex_ids, g, v_vnames)

        # create the edge from tail to head
        edge = g.add_edge(tail, head)

        # add the properties to the currend edge
        for i in range(2, len(e)):
            edge_props[i-2][edge] = e[i]

    return g


def add_or_get_vertex(vid, vertex_ids, graph, v_vnames):
    # either add the vertex, or find it
    if vid not in vertex_ids:
        # add the id to the unique list
        vertex_ids.append(vid)

        # create a vertex for this id
        vtx = graph.add_vertex()

        # set the id of tail to the value from the query
        graph.vp.id[vtx] = vid

        # collect reverse mapping in dictionary
        v_vnames[vid] = int(vtx)
    else:
        vtx = graph.vertex(vertex_ids.index(vid))

    return vtx

if __name__ == "__main__" : main()