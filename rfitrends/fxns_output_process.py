#
###_________________________________________________________###

#  Code Name: fxns_output_process.py
#  Code Purpose: To compile small functions to be used in processing data from the SQL database

#  For any questions please contact Joy Nicole Skipper at jskipper@nrao.edu

###_________________________________________________________###
################################################################################################################################################################################################################################




print("importing values for fxn output process")
#import random
#import csv


def gather_list(connection_call,query):
    """
    Compiles data from an SQL query and loads it into a list
    param connection_call: is the infomration on the SQL connection call
    param query: is the SQL query to be put into the database

    returns value_list: the list of information from the SQL database
    """
    cursor = connection_call
    cursor.execute(query)


    value_list = []


    row = cursor.fetchone() #getting each row
 
    while row is not None:
        value_list.append(float(row[0]))
        row = cursor.fetchone()

    return(value_list)


def isSorted(x, key = lambda x: x): 
    """
    checks to see if a python list is sorted
    """
    return all([key(x[i]) <= key(x[i + 1]) for i in range(len(x) - 1)])
