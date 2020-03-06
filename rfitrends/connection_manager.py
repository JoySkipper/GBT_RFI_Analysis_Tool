"""
.. module:: fxns_output_process.py
    :synopsis: To compile small functions to be used in processing data from the SQL database
.. moduleauthor:: Joy Skipper <jskipper@nrao.edu>
Code Origin: https://github.com/JoySkipper/GBT_RFI_Analysis_Tool
"""

from pymysql import connect
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

    def get_distinct_filenames(self,main_table):
        result = execute_command("SELECT DISTINCT filename FROM "+main_table)
        return(result)

    def add_main_values(self,data_entry,formatted_RFI_file,frequency):
        execute_command("INSERT INTO "+str(data_entry["Database"])+" (feed,frontend,`azimuth_deg`,projid,`resolution_MHz`,Window,exposure,utc_hrs,date,number_IF_Windows,Channel,backend,mjd,Frequency_MHz,lst,filename,polarization,source,tsys,frequency_type,units,Intensity_Jy,scan_number,`elevation_deg`, `Counts`) VALUES (\""+str(formatted_RFI_file.get("feed"))+"\",\""+str(formatted_RFI_file.get("frontend"))+"\",\""+str(formatted_RFI_file.get("azimuth (deg)"))+"\",\""+str(formatted_RFI_file.get("projid"))+"\",\""+str(formatted_RFI_file.get("frequency_resolution (MHz)"))+"\",\""+str(data_entry["Window"])+"\",\""+str(formatted_RFI_file.get("exposure (sec)"))+"\",\""+str(formatted_RFI_file.get("utc (hrs)"))+"\",\""+str(formatted_RFI_file.get("date"))+"\",\""+str(formatted_RFI_file.get("number_IF_Windows"))+"\",\""+str(data_entry["Channel"])+"\",\""+str(formatted_RFI_file.get("backend"))+"\",\""+str(formatted_RFI_file.get("mjd"))+"\",\""+frequency+"\",\""+str(formatted_RFI_file.get("lst (hrs)"))+"\",\""+str(formatted_RFI_file.get("filename"))+"\",\""+str(formatted_RFI_file.get("polarization"))+"\",\""+str(formatted_RFI_file.get("source"))+"\",\""+str(formatted_RFI_file.get("tsys"))+"\",\""+str(formatted_RFI_file.get("frequency_type"))+"\",\""+str(formatted_RFI_file.get("units"))+"\",\""+str(data_entry["Intensity_Jy"])+"\",\""+str(formatted_RFI_file.get("scan_number"))+"\",\""+str(formatted_RFI_file.get("elevation (deg)"))+"\",\""+str(data_entry["Counts"])+"\");")
    
    def grab_values_for_avg_intensity(self,table,frequency,mjd):
        result = execute_command("SELECT Intensity_Jy,filename,Counts from "+table+" WHERE Frequency_MHz = "+frequency+" AND mjd = "+mjd)
        return result

    def insert_duplicate_data(self,frequency,intensity,filename):
        execute_command("INSERT INTO duplicate_data_catalog (Frequency_MHz,Intensity_Jy,filename) VALUES (\'"+frequency+"\',\'"+intensity+"\',\'"+filename+"\')")

    def update_avg_intensity(self,table,counts,intensity,frequency,mjd):
        execute_command("UPDATE "+table+" SET Counts = "+counts+", Intensity_Jy = "+intensity+", Window = \'NaN\', Channel = \'NaN\', filename = \'Duplicate\' where Frequency_MHz = "+frequency+" AND mjd = "+mjd)

    def previous_line_query(self,table,mjd,frequency):
        execute_command("SELECT * from "+table+" WHERE mjd = "+mjd+" and Frequency_MHz = "+frequency)

    def add_receiver_keys(self,frontend,frequency,mjd):
        execute_command("INSERT INTO "+frontend+" (Frequency_MHz,mjd) VALUES (\""+frequency+"\", \""+mjd+"\");")
    
    def get_latest_project_data(self,frontend):
        result = execute_command("SELECT projid,mjd from latest_projects WHERE frontend= \""+frontend+"\"")
        return result

    def update_latest_projid(self,mjd,frontend):
        execute_command("UPDATE latest_projects SET projid=\""+mjd+"\" WHERE frontend = \""+frontend+"\";")

    def update_latest_date(self,mjd,frontend):
        execute_command("UPDATE latest_projects SET mjd=\""+mjd+"\" WHERE frontend = \""+frontend+"\";")

    def drop_table(self,table):
        execute_command("DROP table "+table)

    def projid_table_maker(self,projid_table):
        execute_command("CREATE TABLE IF NOT EXISTS "+projid_table+" (Frequency_MHz Decimal(12,6), mjd Decimal(8,3), PRIMARY KEY (Frequency_MHz,mjd));")

    def projid_populate_table(self,projid,frequency,mjd):
        execute_command("INSERT INTO "+projid+" (Frequency_MHz,mjd) VALUES (\""+frequency+"\", \""+mjd+"\");")