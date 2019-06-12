"""
.. module:: fxns_output_process.py
    :synopsis: To compile small functions to be used in processing data from the SQL database
.. moduleauthor:: Joy Skipper <jskipper@nrao.edu>
"""

import pymysql.connect
from pymysql.cursors import Cursor

def gather_list(cursor: Cursor,query):
    """
    Compiles data from an SQL query and loads it into a list
    param cursor: is the information on the SQL connection call
    param query: is the SQL query to be put into the database

    returns value_list: the list of information from the SQL database
    """

    cursor.execute(query)
    value_list = []
    row = cursor.fetchone() #getting each row
 
    while row is not None:
        value_list.append(float(row[0]))
        row = cursor.fetchone()

    return(value_list)

def connect_to_database():
    """
    Connects to the main SQL database being used for this project

    :returns cnx: the pymysql connection call to the database
    :returns cursor: the pymysql cursor of the connection call
    """
    username = input("Please enter SQL database username... ")
    password = input("Please enter SQL database password... ")
    cnx = pymysql.connect(user=username, password=password,
                                host='192.33.116.22',
                                database='jskipper')
    #cnx is connecting to the sql database
    cursor = cnx.cursor()

    return(cursor,cnx)
