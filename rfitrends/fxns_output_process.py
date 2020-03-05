"""
.. module:: fxns_output_process.py
    :synopsis: To compile small functions to be used in processing data from the SQL database
.. moduleauthor:: Joy Skipper <jskipper@nrao.edu>
Code Origin: https://github.com/JoySkipper/GBT_RFI_Analysis_Tool
"""

from pymysql import connect
#import pymysql.connect
from pymysql import cursors
from pymysql.cursors import Cursor
from mysql import connector
import getpass

class connection_manager():
    def __init__(self,host,database):
        self.host=host
        self.database=database
        while True:
            try:
                print("Connecting to database: " + str(self.database) + " on host: " + str(self.host))
                username = input("Please enter SQL database username: ")
                password = getpass.getpass("Please enter the password: ",stream=None)
                connector.connect(user=username, password=password,
                                    host=host,
                                    database=database)
                self.username=username
                self.password=password
                break
            except(connector.errors.ProgrammingError):
                print("Incorrect username or password. Please try again.")

    def execute_command(self,query):
        cnx = connector.connect(user=self.username, password=self.password,
                        host=self.host,
                        database=self.database)
        cursor = cnx.cursor(buffered=True)
        cursor.execute(query)
        cnx.commit()
        try:
            result = cursor.fetchall()
        except(connector.errors.InterfaceError):
            result = None
        finally:
            cursor.close()
        return(result)
    
    
    



