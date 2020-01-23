"""
.. module:: RFI_input_for_SQL.py
    :synopsis: To read in multiple types of ascii files containing RFI data across several decades. Then output in a form usable by a mySQL database.
.. moduleauthor:: Joy Skipper <jskipper@nrao.edu>
Code Origin: https://github.com/JoySkipper/GBT_RFI_Analysis_Tool
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import copy
import re
import julian
import datetime
import rfitrends.LST_calculator
from mysql import connector
import getpass
import rfitrends.GBT_receiver_specs
import sys
import rfitrends.fxns_output_process
import argparse

class FreqOutsideRcvrBoundsError(Exception):
    pass



def read_file(filepath,main_database,dirty_database):#use this function to read in a particular file and return a dictionary with all header values and lists of the data
    """
    Goes through each file, line by line, processes and cleans the data, then loads it into a dictionary with a marker for the corresponding database
    to which it belongs. 

    param main_database: the primary database to which the person wants their clean data to go
    param dirty_database: the secondary database to which the person wans their "dirty," or nonsensical data to go
    returns formatted_RFI_file: The dictionary with all of the data formatted and organized. 
    returns header_map: contains all information, not just header
    """
    
    f = open(filepath, 'r') #open file
    #these are lists containing column values that will be added to the dictionary later:
    data = [] 
    database = []
    if '#' in f.read(1):
        has_header = True
    else:
        has_header = False
    f.seek(0)


    if has_header:
        def process_header(file):
            f = file
            # Dict of header fields and values
            header = {}
            previous_line_position = f.tell()
            # emulating a do while loop because it doesn't exist in Python
            line = f.readline()
            # Read the file
            while line:
                # Header entries are denoted via '#' symbol
                if '#' in line:
                    # Standard header entries are denoted via "key: value" 
                    try:
                        header_entry = line.strip('#').strip().split(":")
                        header[header_entry[0]] = header_entry[1].strip()
                    except:
                        # If not, there are two possibilities:
                        # (1) Title lines (meant to be skipped)
                        # (2) Column names (in which case it is directly preceded by data (non header line))

                        # Peek ahead at next line
                        current_position = f.tell()
                        # If there is no '#' symbol, the next line is data, therefore this line denotes the column names
                        if "#" not in f.readline():
                            # Assumes column names are separated by variable number of spaces/tabs
                            column_entries = line.strip('#').split()
                            header['Column names'] = column_entries
                        # Otherwise it's either a title line, or we don't support the syntax. Regardless, we should skip it
                        else:
                            #print("Skipping header line: " + line)
                            pass
                        # Undo our peek so we can process appropriately
                        f.seek(current_position)

                # If there is no header indicator ('#'), we've reached our data entries
                # Works under assumption that data entries are last in file
                else:
                    # Revert to last line and exit loop. We've finished parsing our header
                    f.seek(previous_line_position)
                    break

                # Again emulating a do while loop
                previous_line_position = f.tell()
                line = f.readline()

            return header
        header_map = process_header(f)
    else:
        header_map = extrapolate_header(f.name)

    # Verifies that frontend given exists, otherwise labels it as Unknown. 
    header_map["frontend"] = rfitrends.GBT_receiver_specs.FrontendVerification(header_map["frontend"])
    # Pulls filename from full path to filename
    header_map["filename"] = filepath.split("/")[-1]
     
    for data_line in f:
        if data_line == '\n':
            continue
        data_entry = ReadFileLine_ColumnValues(has_header, data_line.strip().split(), header_map['Column names'], f.name)
        # If Intensity is NaN or overlapping, skip this line, not useful for science
        if data_entry[3] == "NaN" or data_entry[4]:
                continue
        try:
            def FrequencyVerification(frequency_value,header):
                """
                Identifies issues in the frequency value in RFI-data
                1.) Checks for units (MHz vs GHz)
                2.) Checks that the frequency is in the appropriate range for the given receiver, under the assumption that
                they were generated by the understood receivers prior to 2019
                
                :param frequency_value: the frequency value to verify
                :param header_information: the dictionary made with header information for each file 
                :returns validated_frequency: the validated frequency value
                """
                # Makes the assumption that we're not observing below 245 MHz
                if float(frequency_value) < 245.0: # Converting all GHz values to MHz
                    validated_frequency = str(float(frequency_value) * 1000.0)
                else:
                    validated_frequency = frequency_value


                freq_min = rfitrends.GBT_receiver_specs.GBT_receiver_ranges[header["frontend"]]['freq_min']
                freq_max = rfitrends.GBT_receiver_specs.GBT_receiver_ranges[header["frontend"]]['freq_max']

                # If we don't know the receiver, then we can't give a required frequency range.
                if rfitrends.GBT_receiver_specs.GBT_receiver_ranges[header["frontend"]] == "Unknown": 
                    freq_buffer = 0
                else:
                    buffer_factor = .1
                    # If we do know the receiver, then we take the range of that receiver and allow 1/10th of that range on either end to be included for
                    # That receiver
                    freq_buffer = (freq_max - freq_min)* buffer_factor
                if float(validated_frequency) < (freq_min - freq_buffer) or float(validated_frequency) > (freq_max + freq_buffer):
                    raise FreqOutsideRcvrBoundsError
                return validated_frequency
            validated_frequency = FrequencyVerification(data_entry[2],header_map)
            database.append(main_database)
            database_value = main_database
            
        # IF we do get frequencies outside of the bounds that we want, we put it into the dirty table. 
        except FreqOutsideRcvrBoundsError:
            database.append(dirty_database)
            database_value = dirty_database
            validated_frequency = data_entry[2]
        data_line = list(data_entry)
        data_line[2] = validated_frequency
        data_line.append(database_value)

        data.append(data_line)

    header_map['Data'] = data
    return(header_map)

def extrapolate_header(filepath):
    """
    Gleans as much information that would normally be in a header from a file that has been determined by the read_file function to not have a header 
    and populates it into that file's dictionary.

    param filepath: The path to that particular file

    returns extrapolated_header: dict with extrapolated header information derived from file name
    """
    extrapolated_header = {}
    
    #Gleaning information from a file that does not contain a file header for information
    filename = (filepath.split("/")[-1])# splitting filepath back down to just the filename    
    extrapolated_header.update({"filename": filename})
    filename_temporary = re.split('[_.]',filename)#split the filename into the naming components (there's no header, so we have to glean info from the filename)
    filename = filename_temporary

    unix_timestamp = (os.path.getmtime(filepath))
    date = (datetime.datetime.utcfromtimestamp(unix_timestamp))
    extrapolated_header.update({"date": (date.strftime('%Y-%m-%d %H:%M:%S'))})# gleaning info from filename
    #Calculating MJD...
    jd = julian.to_jd(date+ datetime.timedelta(hours=12),fmt='jd')
    mjd = jd  - 2400000.5
    extrapolated_header.update({"mjd": mjd})
    extrapolated_header.update({"azimuth (deg)":float(filename[7][2:])})
    extrapolated_header.update({"elevation (deg)":float(filename[8][2:])})
    extrapolated_header.update({"feed": "NaN"})
    extrapolated_header.update({"frontend": str(filename[2])})
    extrapolated_header.update({"projid": "NaN"})
    extrapolated_header.update({"frequency_resolution (MHz)": "NaN"})
    extrapolated_header.update({"Window": "NaN"})
    extrapolated_header.update({"exposure": "NaN"})
    utc_hr = (float(date.strftime("%H")))
    utc_min = (float(date.strftime("%M"))/60.0 )
    utc_sec = (float(date.strftime("%S"))/3600.0)
    utc = utc_hr+utc_min+utc_sec
    extrapolated_header.update({"utc (hrs)": utc})
    extrapolated_header.update({"number_IF_Windows": "NaN"})
    extrapolated_header.update({"Channel": "NaN"})
    extrapolated_header.update({"backend": "NaN"})

    year_formatted = date.strftime('%Y')[2:]
    utc_formatted = date.strftime('%m%d'+year_formatted+' %H%M')
    LSThh,LSTmm,LSTss = LST_calculator.LST_calculator(utc_formatted)
    LST = LSThh + LSTmm/60.0 + LSTss/3600.0
    extrapolated_header.update({"lst (hrs)": LST})

    extrapolated_header.update({"polarization":filename[6]})
    extrapolated_header.update({"source":"NaN"})
    extrapolated_header.update({"tsys":"NaN"})
    extrapolated_header.update({"frequency_type":"NaN"})
    extrapolated_header.update({"Units":"Jy"})
    extrapolated_header.update({"scan_number":"NaN"})

    #column_names = ["Frequency (MHz)","Intensity (Jy)"] # we can't glean the column names from the header either, but we know what they are
    extrapolated_header['Column names'] = ["Frequency (MHz)","Intensity (Jy)"]
    return(extrapolated_header)

def CheckFor_OverlappingColumns(line_value):
    """
    Checks for overlapping columns in a particular line of a file. 

    param line_value: The current line of the file in a raw unaltered string

    returns overlapping: Boolean to determine if there are overlapping columns in a particular line of file
    returns column_count: the number of columns in the file

    """
    overlapping = False
    column_count = 0
    for column_count,column_value in enumerate(line_value): 
        if column_value.count(".") == 2:
            overlapping = True
            break
    return overlapping,column_count

def DealWith_Overlapping(column_count,line_value):
        """
        when one column value bleeds into another. I.E. your frequency/intensity column is 400.1000.00 meaning a frequency of 400 and a intensity of 1000.0
        Fixes value based on input from user

        param column_count: number of columns in this particular file
        param line_value: the string representing the particular line on which there is overlapping

        returns window_value: the value for the "window" column for this line
        returns channel_value: the value for the "channel" column for this line
        returns frequency_value: the value for the "frequency" column for this line
        returns intensity_value: the value for the "intensity" column for this line

        """

        #split_value = int(input("Please input the character number at which the columns need to be split, counting from the left (default is 8): \n") or "8")
        split_value = 8


        if column_count == 0:
            window_value = (line_value[0][0:split_value])
            channel_value = (line_value[0][split_value:])
            frequency_value = (line_value[1])
            intensity_value = (line_value[2])
        elif column_count == 1: 
            window_value = (line_value[0])
            channel_value = (line_value[1][0:split_value])
            frequency_value = (line_value[1][split_value:])
            intensity_value = (line_value[2])    
        elif column_count ==2: 
            window_value = (line_value[0])
            channel_value = (line_value[1])
            frequency_value = (line_value[2][0:split_value])
            intensity_value = (line_value[2][split_value:0])
        return window_value,channel_value,frequency_value,intensity_value
    
def ReadFileLine_ColumnValues(has_header,line_value: list,column_names,filepath):
    """
    Reads one line in a file that has been determined by the read_file function to be a row with data as opposed to header information
    param has_header: boolean determining if the file has a header or not
    param line_value: the parsed values containing the information for the particular line of this file 
    param column_names: the names of the columns contained in this file
    param filepath: the path to this particular file


    returns window_value: the value for the "window" column for this line
    returns channel_value: the value for the "channel" column for this line
    returns frequency_value: the value for the "frequency" column for this line
    returns intensity_value: the value for the "intensity" column for this line
    returns overlapping: a boolean determining if this particular line contains column overlapping

    """
    # Unfortunately, we first have to check if the columns overlapped with themselves anywhere, such as the frequency values bleeding into intensity values to make 1471.456800.000 which should be 
    # something like 1471.456 for frequency and 800.000 for intensity or something (these are made up numbers for example only)
    overlapping,column_count = CheckFor_OverlappingColumns(line_value)
    if overlapping:
        print("There is a file you have input that contains a column which has merged into the other. Here is the line: \n")
        print(line_value)
        print("Skipping merged line")
        window_value,channel_value,frequency_value,intensity_value = DealWith_Overlapping(column_count, line_value)
        return window_value,channel_value,frequency_value,intensity_value,overlapping
       
    #now that we know this is a correctly made line, we check which format this file is in, is it 4 columns? 3? What are the values in these columns? 
    elif (column_names[0] == "Window" or column_names[0] == "IFWindow") and column_names[1] == "Channel" and (column_names[2] == "Frequency(MHz)" or column_names[2] == "Frequency (MHz)") and column_names[3] == "Intensity(Jy)":#4 regular columns

        window_value = (line_value[0])
        channel_value = (line_value[1])
        frequency_value = (line_value[2])
        intensity_value = (line_value[3])



    elif (column_names[0] == "Window" or column_names[0] == "IFWindow") and column_names[1] == "Channel" and (column_names[2] == "Frequency(GHz)" or column_names[2] == "Frequency GHz)") and column_names[3] == "Intensity(Jy)":
        window_value = (line_value[0])
        channel_value = (line_value[1])
        frequency_value = (line_value[2])
        intensity_value = (line_value[3])
      


    elif column_names[0] == "Frequency(MHz)" and column_names[1] == "Intensity(Jy)":#2 regular columns)
        frequency_value = (line_value[0])
        intensity_value = (line_value[1])
        window_value = "NaN"
        channel_value = "NaN"
 

    elif column_names[0] == "Channel" and column_names[1] == "Frequency(MHz)" or column_names[1] == "Frequency (MHz)" and column_names[2] == "Intensity(Jy)":#3 regular columns
        channel_value = (line_value[0])
        frequency_value = (line_value[1])
        intensity_value = (line_value[2])
        window_value = "NaN"


    elif column_names[0] == "Channel" and column_names[1] == "Frequency(GHz)" and column_names[2] == "Intensity(Jy)":# 3 columns, but the person decided to put the frequency in GHz, so change back to MHz and add
        frequency_value = (line_value[1])        
        channel_value = (line_value[0])
        intensity_value = (line_value[2])
        window_value = "NaN"  
    
    elif has_header == False:# Finally, if the file does not have a header, it has two columns that are frequency and intensity
        frequency_value = (line_value[0])
        intensity_value = (line_value[1])    
        window_value = "NaN"
        channel_value = "NaN"

    else:               
        raise SystemExit("There is a problem. The file reader could not parse a file. Please look at the file format and try again. \n This is the filepath: "+str(filepath)+"\n These are the column names: "+str(column_names)+"\n This is the line that the file parser broke on: "+str(line_value))

    
    return(window_value,channel_value,frequency_value,intensity_value,overlapping)

def prompt_user_login_to_database(IP_address, database):
    
    while True:
        try:
            print("Connecting to database: " + str(database) + " on host: " + str(IP_address))
            username = input("Please enter SQL database username: ")
            password = getpass.getpass("Please enter the password: ",stream=None)
            connector.connect(user=username, password=password,
                                host=IP_address,
                                database=database)
            #cursor = cnx.cursor()
            return(username, password)
        except:
            print("Incorrect username or password. Please try again.")


def write_to_database(username,password,IP_address,database,main_table,dirty_table,path,files_to_process = "all"):

    list_o_paths = []

    if files_to_process == "all":
    # making a list of all of the .txt files in the directory so I can just cycle through each full path:
        for filename in os.listdir(path):
            if filename.endswith(".txt") and filename != "URLs.txt":# If the files are ones we are actually interested in
                list_o_paths.append(os.path.join(path,filename))
                continue
    else: 
        # For each file in the path given
        for filename in os.listdir(path):
            # If there is any element from files_to_process contained in the current filename, it is a file to process. I.E. if "TRFI_052819_L1" is 
            # An element in files_to_process, and filename is "TRFI_052819_L1_rfiscan1_s0001_f001_Linr_az357_el045.txt" then it will be included as a file to process
            if any(RFI_file in filename for RFI_file in files_to_process):
                list_o_paths.append(os.path.join(path,filename))


    
    cnx = connector.connect(user=username, password=password,
                        host=IP_address,
                        database=database)
    cursor = cnx.cursor()


    print("gathering filename set...")

    unique_filename = rfitrends.fxns_output_process.gather_list(cursor, "SELECT DISTINCT filename FROM "+main_table)


    #going thru each file one by one
    print("starting to upload files one by one...")
    for filenum,filepath in enumerate(list_o_paths):
        print("Extracting file "+str(filenum+1)+" of "+str(len(list_o_paths))+", filename: "+str(filepath))
        filename = filepath.split("/")[-1]
        if filename in unique_filename:
            print("File already exists in database, moving on to next file.")
            continue
        
        formatted_RFI_file = read_file(filepath,main_table,dirty_table)

        with open('/users/jskipper/Documents/scripts/RFI/test_writing_files/test_file_'+filename, 'w') as writer:
            for data_entry in formatted_RFI_file.get("Data"):#for each value in that multi-valued set
                writer.write("         "+str(data_entry[0]+"         "+str(data_entry[1]+"         "+str(data_entry[2]+"         "+str(data_entry[3]+"\n")))))
                add_values = "INSERT INTO "+str(data_entry[5])+" (feed,frontend,`azimuth (deg)`,projid,`resolution (MHz)`,Window,exposure,utc_hrs,date,number_IF_Windows,Channel,backend,mjd,Frequency_MHz,lst,filename,polarization,source,tsys,frequency_type,units,Intensity_Jy,scan_number,`elevation (deg)`) VALUES (\""+str(formatted_RFI_file.get("feed"))+"\",\""+str(formatted_RFI_file.get("frontend"))+"\",\""+str(formatted_RFI_file.get("azimuth (deg)"))+"\",\""+str(formatted_RFI_file.get("projid"))+"\",\""+str(formatted_RFI_file.get("frequency_resolution (MHz)"))+"\",\""+str(data_entry[0])+"\",\""+str(formatted_RFI_file.get("exposure (sec)"))+"\",\""+str(formatted_RFI_file.get("utc (hrs)"))+"\",\""+str(formatted_RFI_file.get("date"))+"\",\""+str(formatted_RFI_file.get("number_IF_Windows"))+"\",\""+str(data_entry[1])+"\",\""+str(formatted_RFI_file.get("backend"))+"\",\""+str(formatted_RFI_file.get("mjd"))+"\",\""+str(data_entry[2])+"\",\""+str(formatted_RFI_file.get("lst (hrs)"))+"\",\""+str(formatted_RFI_file.get("filename"))+"\",\""+str(formatted_RFI_file.get("polarization"))+"\",\""+str(formatted_RFI_file.get("source"))+"\",\""+str(formatted_RFI_file.get("tsys"))+"\",\""+str(formatted_RFI_file.get("frequency_type"))+"\",\""+str(formatted_RFI_file.get("units"))+"\",\""+str(data_entry[3])+"\",\""+str(formatted_RFI_file.get("scan_number"))+"\",\""+str(formatted_RFI_file.get("elevation (deg)"))+"\");"
                cursor.execute(add_values)

        print(str(filename)+" uploaded.")

    print("All files uploaded.")

        


    cnx.close()

if __name__ == "__main__":
    import ptvsd 
    # Allow other computers to attach to ptvsd at this IP address and port. 
    ptvsd.enable_attach(address=('10.16.96.210', 3001), redirect_output=True) 
    # Adding in-line arguments:
    parser = argparse.ArgumentParser(description="Takes .txt files of RFI data and uploads them to the given database")
    parser.add_argument("main_table",help="The string name of the table to which you'd like to upload your clean RFI data")
    parser.add_argument("dirty_table",help="The string name of the table to which you'd like to upload your flagged or bad RFI data")
    parser.add_argument("path",help="The path to the .txt files that need to be uploaded to the database")
    parser.add_argument("IP_address",nargs='?',default= '192.33.116.22',help="The IP address to find the SQL database to which you would like to add this table. Default is the GBO development server address. This would only work for employees.")
    parser.add_argument("database",nargs='?',default='jskipper',help="The name of the SQL database to which you would like to add this table. Default is jskipper, which would only work for employees.")
    args = parser.parse_args()
    main_table = args.main_table
    dirty_table = args.dirty_table
    IP_address = args.IP_address
    database = args.database
    # The likely path to use if looking at most recent (last 6 months) of RFI data for GBT:
    #path = '/home/www.gb.nrao.edu/content/IPG/rfiarchive_files/GBTDataImages'
    path = args.path
    username, password = prompt_user_login_to_database(IP_address,database)
    write_to_database(username, password, IP_address, database, main_table,dirty_table,path)


        
    


