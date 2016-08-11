ID = 0
SOURCE = 1
TARGET = 2
START_TIME = 3
END_TIME = 4
BATCH_SIZE = 1000

## create an index named on tbl(cols). That is_unique, is_spatial, and is_hash
## accordingly.  Note that you can only create a spatial index if you do not
## create a hash index
def index_sql(idx_name, tbl, cols, is_spatial = False, is_hash = False,
              is_unique = False):
    """Create an index on a SQL table based on the input conditions"

    idx_name -- the string specifying the name of the index
    tbl      -- the str name of the table to be indexed
    cols     -- list of the columns to be indexed
    is_spatial = True if the index is to be spatial
    is_hash    = True if the index is to be a hash-index
    is_unique  = True if the index is to be a unique index

    note that is_spatial and is_hash are mutually exclusive
    """
    sql = "CREATE "

    if is_unique:
        sql = "UNIQUE "
    elif is_spatial:
        sql = "SPATIAL "

    sql += """INDEX IF NOT EXISTS `{0}` """.format(idx_name)

    if is_hash:
        sql += "USING HASH "
        
    sql +=  """ON `{0}` (""".format(tbl)
    
    for c in cols:
        sql += """`{0}`,""".format(c)
        
    sql = sql[:-1] + """)"""
    
    return sql

def batch_insert(db, insert_sql, data):
    """Insert a set of data into the database db based on the sql command inser_sql
    by manual batching to get around write-size limits. """
    global BATCH_SIZE

    # get the data
    cursor = db.cursor()
    
    # ensure the data is a list
    data_list = list(data)

    # print("Batch inserting", data, " with", insert_sql)    
    for i in range(0, len(data_list), BATCH_SIZE):
        cursor.executemany(insert_sql, data_list[i:i+BATCH_SIZE])

    db.commit()

# Query the database for versioning info and set the engine information
# accordingly
def get_engine(cursor):
    """Do some basic (and naive) string parsing to determine which MySQL engine to use
       based on which supports spatial index.

    If MariaDB use Aria
    If Mysql version 5.7+ use InnoDB
    Otherwise use MyISAM
    """
    # get the version information
    cursor.execute("""SELECT VERSION();""")
    version = cursor.fetchone()[0]

    # select engine based on db engine to allow for spatial indexing
    if version.find("Maria") >= 0: # using MariaDB
        return ("ARIA",)
    
    elif int(version[version.find("5.")+2]) >= 7: # using MySQL 5.7
        return ("INNODB",)
    
    else:                          # using other
        return ("MYISAM",)

# return a SQL square for query building
def square():
    """
    return the SQL string for creating a polygon
    """
    return """PolyFromText('POLYGON((%s %s,%s %s,%s %s,%s %s,%s %s))')"""

def edge_intersect_suffix(isect_set):
    """A SQL query string suffix for processing a set of indices and enforcing the
    edge_id to be in that set isect_set"""
    
    sql_set = ",".join(map(str, list(isect_set)))
    return "AND `edge_id` IN ({0})".format(sql_set)


def label_table_name(base_name):
    """Calculate the label_table_name based on the base_name"""
    return "{0}_edge_label".format(base_name)

