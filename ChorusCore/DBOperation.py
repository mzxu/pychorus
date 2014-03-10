'''
Created on May 30, 2013

@author: mxu
@target: Provide Database operations
@requires: db_info is a dict, contains host, port, username, password, database keys.
'''

import mysql.connector
import ChorusGlobals

def execute_sql(sql, db_info):
    '''execute sql and return a list format data'''
    try:
        data = []
        conn_info = __get_db_info(db_info)
        print conn_info
        conn = __init_connection(conn_info)
        cursor = conn.cursor()            
        cursor.execute(sql)
        for row in cursor:
            data.append(row) 
        conn.commit()
                      
    except Exception, e:
        ChorusGlobals.get_logger().critical("Errors in sql execution: %s" % e)
        raise Exception("Errors in sql execution: %s" % e)
                    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()   
        return data 

def execute_sql_dict(sql,db_info):
    '''execute sql and return a dict format data'''
    try:
        data = []
        datadict=[]
        conn_info = __get_db_info(db_info)
        conn = __init_connection(conn_info)
        cursor = conn.cursor()            
        cursor.execute(sql)
        for row in cursor:
            data.append(row)
        for row in data:
            rid=data.index(row)
            celldict={}
            for i in range(len(row)):
                celldict[cursor.column_names[i]]=row[i]
            datadict.append(celldict)
        conn.commit()
                      
    except Exception, e:
        ChorusGlobals.get_logger().critical("Errors in sql execution: %s" % e)
        raise Exception("Errors in sql execution: %s" % e)
                    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()   
        return datadict 

def __init_connection(connection):
    host = connection["host"]
    port = connection["port"]
    user = connection["username"]
    passwd = connection["password"]
    database = connection["database"]
    conn = mysql.connector.connect(host = host,
                                   port = int(port),
                                   user = user,
                                   passwd = passwd,
                                   database = database)
    
    return conn

def __get_db_info(db_info):
    parameters = ChorusGlobals.get_parameters()
    try:
        db_config = parameters[db_info]

        connection = {
                      "host": db_config['addr'],
                      "port": db_config['port'],
                      "username": db_config['username'],
                      "password": db_config['password'],
                      "database": db_config['database']
                      }

        return connection
    except Exception,e:
        ChorusGlobals.get_logger().critical("The %s in config file is not correctly configured, errors: %s" % (db_info,str(e)))
        raise Exception("The %s in config file is not correctly configured, errors: %s" % (db_info,str(e)))