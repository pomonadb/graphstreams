import mysql.connector
from getpass import getpass

table_name = "edges_twenty"
num_days   = "20"


def main():
    print("executing main")
    pw = getpass()
    db = mysql.connector.connect(user="root",
                                 db = "enron",
                                 passwd = pw)

    print("connecting to database, preparing data")
    prep(db)
    print("preparation complete, starting flattening")
    if simplify(db):
        print("done")
    else:
        print("failed")

def simplify(db):
    global table_name
    c = db.cursor(buffered=True)
    print("loading edge_point")
    c.execute("""SELECT * FROM edge_point ORDER BY source_id, dest_id, time""")
    edges = c.fetchall()
    print("writing to", table_name)    
    for p_edge in edges:
        # print("POINT EDGE", p_edge)
        
        cond_str = """((E.dest_id = {1} AND E.source_id = {2})
                         OR (E.source_id = {1} AND E.dest_id = {2}))
                      AND E.start - {4}*86400 <= {3} AND E.end + {4}*86400 >= {3}
                   """.format(*p_edge, num_days)

        mtchstr = """SELECT * FROM {1} E WHERE {0}""".format(cond_str, table_name)

        # print(mtchstr)
        c.execute(mtchstr)

        matched = c.fetchall()
        
        # print("MATCHED EDGES", matched)
        
        if matched:
            for e in matched:
                # print("\tUpdating with", p_edge, "and", e)
                c.execute("""
                          UPDATE {5} E
                          SET E.start = LEAST   (E.start, {3}),
                              E.end   = GREATEST(E.end  , {3})
                          WHERE E.edge_id = {4} AND ({3} < E.start OR E.end < {3})
                          """.format(*p_edge, e[0], table_name))
        else:
            # print("\tinserting", p_edge, "into", table_name)
            c.execute("""
                      INSERT INTO {4} (edge_id,source_id, dest_id, start, end)
                                 VALUES (    {0},      {1},     {2},   {3}, {3})
                      """.format(*p_edge, table_name))

        
        # print()
        # print()
        db.commit()

    c.close()

    return True
    


def prep(db):
    global table_name
    c = db.cursor()
    create = """CREATE TABLE IF NOT EXISTS
                              {0} (edge_id INT PRIMARY KEY, 
                                    source_id INT, 
                                    dest_id INT, 
                                    start INT, 
                                    end INT)
              """.format(table_name)
    empty = """DELETE FROM {0}""".format(table_name)
    source_dest_idx = """ALTER TABLE {0} ADD INDEX (source_id, dest_id)""".format(table_name)
    start_end_idx = """ALTER TABLE {0} ADD INDEX (source_id, dest_id)""".format(table_name)
    c.execute(create)
    c.execute(empty)
    c.close()
    db.commit()



if __name__ == "__main__" : main()
