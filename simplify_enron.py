print('hello world')
print("HELLO WORLD")

import mysql.connector
from getpass import getpass


def main():
    print("executing main")
    pw = getpass()
    db = mysql.connector.connect(user="root",
                                 db = "enronr",
                                 passwd = pw)

    print("connecting to database, preparing data")
    prep(db)
    print("preparation complete, starting flattening")
    if simplify(db):
        print("done")
    else:
        print("failed")

def simplify(db):
    c = db.cursor(buffered=True)
    c.execute("""SELECT * FROM edge_point ORDER BY source_id, dest_id, time""")
    edges = c.fetchall()
    
    for p_edge in edges:
        print("POINT EDGE", p_edge)
        
        cond_str = """((E.dest_id = {1} AND E.source_id = {2})
                         OR (E.source_id = {1} AND E.dest_id = {2}))
                      AND E.start - 86400 <= {3} AND E.end + 86400 >= {3}
                   """.format(*p_edge)

        mtchstr = """SELECT * FROM edges E WHERE {0}""".format(cond_str)

        print(mtchstr)
        c.execute(mtchstr)

        matched = c.fetchall()
        
        print("MATCHED EDGES", matched)
        
        if matched:
            for e in matched:
                print("Updating with",p_edge, "and", e)
                c.execute("""
                          UPDATE edges E
                          SET E.start = LEAST   (E.start, {3}),
                              E.end   = GREATEST(E.end  , {3})
                          WHERE E.edge_id = {4}
                          """.format(*p_edge, e[0]))
        else:
            print("inserting", p_edge)
            c.execute("""
                      INSERT INTO edges (edge_id,source_id, dest_id, start, end)
                                 VALUES (    {0},      {1},     {2},   {3}, {3})
                      """.format(*p_edge))

        
        print()
        print()
        db.commit()

    c.close()

    return True
    


def prep(db):
    c = db.cursor()
    c.execute("""DELETE FROM edges""")
    c.close()
    db.commit()



if __name__ == "__main__" : main()
