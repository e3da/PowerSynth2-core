import sqlite3
import csv


def create_connection(db_file):

    try:

        conn = sqlite3.connect(db_file)
        #print(sqlite3.version)
    except :
        print("unable to create a file")
    return conn




def create_table(conn,name=None):
    #print "Saved to database: ",name
    cur = conn.cursor()
    sql_command="""CREATE TABLE IF NOT EXISTS LAYOUT_DATA (ID INTEGER NOT NULL, Layer_name TEXT NOT NULL, Layout_info BLOB NOT NULL, PRIMARY KEY (ID, Layer_name)); """


    cur.execute(sql_command)

    conn.commit()


def insert_record(conn,data,name,temp_file):

    """
    Create a new project into the projects table
    :param conn:
    :param project:
    :return: project id
    """


    #sql = ''' INSERT INTO LAYOUT_DATA (ID, Layer_name, Layout_info) VALUES(?,?,?) '''


    cur = conn.cursor()
    try:
        with open(temp_file, 'rb') as f:
            ablob = f.read()
            
            cur.execute("INSERT INTO LAYOUT_DATA VALUES (?,?,?)", [data[0],name, ablob])
            #cur.execute("INSERT INTO LAYOUT_DATA(ID,Layout_info) VALUES (?,?)", [data[0], buffer(ablob)])
            #cur.execute(sql, (lite.Binary(data), ))
            # [id,buffer(info)])
            conn.commit()
        f.close()
    except:
        print("layout_info not found")

    return cur.lastrowid
def retrieve_data(conn,ID,layer_name):
    """
    retrieve a table
    :param conn: connect object to the database
    :param ID: layout ID
    :return:
    """
    cur = conn.cursor()
    #cur.execute("SELECT * FROM " +table)
    #return cur.fetchall()
    #cur.execute("SELECT Layout_info FROM LAYOUT_DATA where ID=?",ID )
    sql = "SELECT Layout_info FROM LAYOUT_DATA WHERE ID = :id and Layer_name = :layer_name"
    param = {'id': ID,'layer_name':layer_name}
    cur.execute(sql, param)
    return cur.fetchone()


def main():
    database = "D:\\sqlite\db\pythonsqlite.db"

    # create a database connection
    conn = create_connection(database)
    with conn:
        # create a new project
        table='Layout_0'
        create_table(conn)

        with open('C:\\Users\ialrazi\PowerSynth\CornerStitch_Dev\PowerCAD-full\src\powercad\sym_layout\Recursive_test_cases\Mode_1\Layout 0.csv','rb') as fin:
            readCSV = csv.reader(fin, delimiter=',')
            for row in readCSV:
                insert_record(conn,table,row)
        '''
        project = ('Cool App with SQLite & Python', '2015-01-01', '2015-01-30');
        project_id = create_project(conn, project)

        # tasks
        task_1 = ('Analyze the requirements of the app', 1, 1, project_id, '2015-01-01', '2015-01-02')
        task_2 = ('Confirm with user about the top requirements', 1, 1, project_id, '2015-01-03', '2015-01-05')

        # create tasks
        create_task(conn, task_1)
        create_task(conn, task_2)
        '''
        all_data=retrieve_data(conn, table)
        file_name='D:\\sqlite\db'+'\out.csv'
        with open(file_name, 'wb') as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=',')

            # csv_writer.writerow(data) #Name, [x,y,w,h,color,zorder],......,W,H
            for i in all_data:
                csv_writer.writerow(i)

        my_csv.close()
        print(len(all_data),all_data)

if __name__ == '__main__':
    '''
    conn=create_connection("D:\\sqlite\db\pythonsqlite.db")
    curs=conn.cursor()
    #x	y	width	height	facecolor	zorder	linewidth	edgecolor

    create_table(curs,conn,id=1)
    curs.execute("Insert into layout_1 values(1,0,0,33.974,2.007,'White',1,'None','None')")
    #data=[0,0,33.974,2.007,'White',1,'None','None']
    curs.execute("SELECT * FROM layout_1 where ID=1")
    print(curs.fetchone())




    print "Table created successfully";
    '''
    main()
"""


import csv, sqlite3

con = sqlite3.connect("D:\\sqlite\db\pythonsqlite.db")
cur = con.cursor()
cur.execute("CREATE TABLE t (col1, col2, col3, col4,col5,col6,col7,col8);") # use your column names here

with open('C:\\Users\ialrazi\PowerSynth\CornerStitch_Dev\PowerCAD-full\src\powercad\sym_layout\Recursive_test_cases\Mode_1\Layout 0.csv','rb') as fin: # `with` statement available in 2.5+
    # csv.DictReader uses first line in file for column headings by default
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['col1'], i['col2'],i['col3'], i['col4'],i['col5'],i['col6'],i['col7'],i['col8']) for i in dr]

cur.executemany("INSERT INTO t (col1, col2,col3, col4,col5,col6,col7,col8) VALUES (?, ?,?,?,?,?,?,?);", to_db)
con.commit()
con.close()
con = sqlite3.connect("D:\\sqlite\db\pythonsqlite.db")
cur = con.cursor()
cur.execute("SELECT * FROM t" )
print(cur.fetchall())


"""


