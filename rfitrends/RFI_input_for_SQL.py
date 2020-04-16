"""
.. module:: RFI_input_for_SQL.py
    :synopsis: To read in multiple types of ascii files containing RFI data across several decades. Then insert into a given mySQL database.
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
import getpass
import rfitrends.GBT_receiver_specs
import sys
import rfitrends.connection_manager
import argparse
import math
import rfitrends.Column_fixes
import configparser
from rfitrends.manage_missing_cols import manage_missing_cols
import json
import mysql
import traceback
from mysql import connector
from decimal import *
from pkg_resources import resource_filename,resource_exists,Requirement
from tqdm import tqdm

# Creating RaiseError classes (custom Error messages)
# Even though the object does nothing, it will still allow 
# Us to handle those errors as they are raised

class FreqOutsideRcvrBoundsError(Exception):
    pass

class InvalidColumnValues(Exception):
    pass

class InvalidIntensity(Exception):
    pass

class DuplicateValues(Exception):
    pass

########### File Gathering Functions ##########

def gather_filepaths_to_process(path,files_to_process = "all"):
    """
    Reads in a path to a directory containing files that the user wishes to process. 

    param path : The path to a directory containing files that the user wishes to process
    param files_to_process: An optional argument in which the user can provide a list containing a subset of files within the path that the user wishes
    process, while excluding all other files
    returns filepaths: a list containing all the desired files to process
    """

    filepaths = []
    if files_to_process == "all":
    # making a list of all of the .txt files in the directory so I can just cycle through each full path:
        for filename in os.listdir(path):
            if filename.endswith(".txt") and filename != "URLs.txt" and (filename.startswith('AGBT') or filename.startswith('TRFI') or filename.startswith('TGBT')):# If the files are ones we are actually interested in
                filepaths.append(os.path.join(path,filename))
                continue
    else: 
        # For each file in the path given
        for filename in os.listdir(path):
            # If there is any element from files_to_process contained in the current filename, it is a file to process. I.E. if "TRFI_052819_L1" is 
            # An element in files_to_process, and filename is "TRFI_052819_L1_rfiscan1_s0001_f001_Linr_az357_el045.txt" then it will be included as a file to process
            if any(RFI_file in filename for RFI_file in files_to_process):
                filepaths.append(os.path.join(path,filename))
    return(filepaths)


########### Singular File processing functions ##############


# Use this function to read in a particular file and return a dictionary with all header values and lists of the data
def read_file(filepath,main_database,dirty_database, connection_manager):
    """
    Goes through each file, line by line, processes and cleans the data, then loads it into a dictionary with a marker for the corresponding database
    to which it belongs. 

    param main_database: the primary database to which the person wants their clean data to go
    param dirty_database: the secondary database to which the person wans their "dirty," or nonsensical data to go
    param connection_manager: An object that connects to the database for the user. 
    returns formatted_RFI_file: The dictionary with all of the data formatted and organized. 
    returns all_file_info: contains all information, not just header
    """
    
    # Open the file
    f = open(filepath, 'r')
    # Data is a dictionary containing column values that will be added to the dictionary later:
    data = {}
    # Database is which database (dirty or clean) to which the given line should be assigned
    database = []

    # If there's a # at the beginning of the first line, we know this file has a header and doesn't 
    # Just jump straight into the data. 
    if '#' in f.read(1):
        has_header = True
    else:
        has_header = False
    # Since we read the first line, we want to reset the reader so it will reread the first line
    # When parsing the header. 
    f.seek(0)
    # If it has a header, we want to process it, if it doesn't, we will extrapolate what info we can
    if has_header:
        all_file_info,first_data_line = process_header(f)
    else:
        all_file_info = extrapolate_header(f.name)
        # Get the first line
        first_data_line = f.readline()
        # Set the reader back to the first line
        f.seek(0)
    # Verifies that frontend given exists, otherwise labels it as Unknown. 
    all_file_info["frontend"] = rfitrends.GBT_receiver_specs.FrontendVerification(all_file_info["frontend"])
    # Pulls filename from full path to filename
    all_file_info["filename"] = filepath.split("/")[-1]
    

    # Loop until we find the first valid data line, which we need to lookup the primary key:
    last_pos = f.tell()
    if first_data_line == '\n':
        first_data_line = f.readline()
    while True:
        try:
            first_data_entry = ReadFileLine_ColumnValues(has_header, first_data_line.strip().split(), all_file_info['Column names'], f.name)
            first_data_entry["Frequency_MHz"] = FrequencyVerification(first_data_entry["Frequency_MHz"],all_file_info) 
        except (InvalidIntensity,FreqOutsideRcvrBoundsError) as e:
            # If the velocity is invalid or the Frequency is outside of bounds, then continue to read the next line:
            last_pos = f.tell()
            first_data_line = f.readline()
            continue    
        break
    f.seek(last_pos)
    
    first_line_entry = dict(all_file_info)
    first_line_entry.update(first_data_entry)
    # Getting primary composite key from config file:
    config = configparser.ConfigParser()
    config.read(resource_filename('rfitrends',"rfitrends.conf"))
    composite_keys = json.loads(config['Mandatory Fields']['primary_composite_key'])
    search_query_main = "SELECT * from "+main_database+" WHERE "
    search_query_dirty = "SELECT * from "+dirty_database+" WHERE filename = \'"+first_line_entry['filename']+"\'"
    # Searching by all the values in the composite key
    for composite_key in composite_keys:
        search_query_main += composite_key+" = "+str(first_line_entry[composite_key])+" AND "
    # Removing last " AND "
    search_query_main = search_query_main[:-4]
    # Execute query and see if there's a duplicate primary key with the first line and the database. If so, raise error
    myresult_main = connection_manager.execute_command(search_query_main)
    myresult_dirty = connection_manager.execute_command(search_query_dirty)
    if myresult_main or myresult_dirty:
        raise DuplicateValues

    print("File does not exist in database. Reading in data. This can take a few minutes.")
    # Going through each line in the file one by one:
    for data_line in f:
        # If it's just a new line, we skip the line
        if data_line == '\n':
            continue
        # Read the data in the line and put it in our data_entry dictionary
        try:
            data_entry = ReadFileLine_ColumnValues(has_header, data_line.strip().split(), all_file_info['Column names'], f.name)
        # If the data was flagged for invalid intensity, skip it. Not useful for science. 
        except InvalidIntensity:
            continue
        # Verify that the frequency is a reasonable one
        try:
            data_entry["Frequency_MHz"] = FrequencyVerification(data_entry["Frequency_MHz"],all_file_info)
            database.append(main_database)
            database_value = main_database    
        # If we do get frequencies outside of the bounds that we want, we put it into the dirty table. 
        except FreqOutsideRcvrBoundsError:
            database.append(dirty_database)
            database_value = dirty_database
        # Now that we have the database value (dirty or clean) we want to associate it with our data entry dictionary. 
        data_entry["Database"] = database_value
        # If data entry is already in data, we have a repeat value within a file. We just up the counts, avg the intensity, 
        # And NaN out Window and Channel as they no longer have meaning since it is an average of 2 points
        if data_entry["Frequency_MHz"] in data:
            counts = float(data[data_entry["Frequency_MHz"]]["Counts"])
            old_intensity = float(data[data_entry["Frequency_MHz"]]["Intensity_Jy"])
            new_intensity = float(data_entry["Intensity_Jy"])
            avg_intensity = (old_intensity*counts + new_intensity)/(counts+1)
            data[data_entry["Frequency_MHz"]]["Window"] = "NaN"
            data[data_entry["Frequency_MHz"]]["Channel"] = "NaN"
            data[data_entry["Frequency_MHz"]]["Intensity"] = avg_intensity
            data[data_entry["Frequency_MHz"]]["Counts"] += 1
        # If it's not in there, then we know there's one data point with this frequency, the one we just found.
        # So we append it to the data list and set counts to 1. 
        else:
            frequency_key = data_entry["Frequency_MHz"]
            del data_entry["Frequency_MHz"]
            data_entry['Counts'] = 1
            data[frequency_key] = data_entry
    # We have the header information in our all_file_info, time to add the data
    all_file_info['Data'] = data
    return(all_file_info)

def process_header(file):
    """
    Goes through the header of a given file, and extrapolates the information necessary. 

    param file: the file confirmed to have a header from which we want information
    returns header: a dictionary containing header information
    """
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
                first_data_line = f.readline()
                if "#" not in first_data_line:
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

    return(header,first_data_line)

def extrapolate_header(filepath):
    """
    Gleans as much information that would normally be in a header from a file that has been determined by the read_file function to not have a header 
    and populates it into that file's dictionary.

    param filepath: The path to that particular file

    returns extrapolated_header: dict with extrapolated header information derived from file name
    """
    extrapolated_header = {}
    
    # Gleaning information from a file that does not contain a file header for information
    filename = (filepath.split("/")[-1])# splitting filepath back down to just the filename    
    extrapolated_header.update({"filename": filename})
    filename_temporary = re.split('[_.]',filename)#split the filename into the naming components (there's no header, so we have to glean info from the filename)
    filename = filename_temporary

    # Getting date from numbers in filename (this assumes MMDDYY, which is not always correct)
    # Sometimes people do DDMMYY, so any file without a header should be viewed with some suspicion. 
    unix_timestamp = (os.path.getmtime(filepath))
    date = (datetime.datetime.utcfromtimestamp(unix_timestamp))
    extrapolated_header.update({"date": (date.strftime('%Y-%m-%d %H:%M:%S'))})# gleaning info from filename
    #Calculating MJD...
    jd = julian.to_jd(date+ datetime.timedelta(hours=12),fmt='jd')
    mjd = jd  - 2400000.5
    extrapolated_header.update({"mjd": mjd})
    # Getting Az and El from their location in the filename again, two numbers (this is pretty standard, so we can trust these values unlike dates)
    extrapolated_header.update({"azimuth (deg)":float(filename[7][2:])})
    extrapolated_header.update({"elevation (deg)":float(filename[8][2:])})
    # We don't have feed, so just add a NaN instead.
    extrapolated_header.update({"feed": "NaN"})
    extrapolated_header.update({"frontend": str(filename[2])})
    extrapolated_header.update({"projid": "NaN"})
    extrapolated_header.update({"frequency_resolution (MHz)": "NaN"})
    extrapolated_header.update({"Window": "NaN"})
    extrapolated_header.update({"exposure": "NaN"})
    # Calculating utc from date (again, to be viewed with some suspicion)
    utc_hr = (float(date.strftime("%H")))
    utc_min = (float(date.strftime("%M"))/60.0 )
    utc_sec = (float(date.strftime("%S"))/3600.0)
    utc = utc_hr+utc_min+utc_sec
    extrapolated_header.update({"utc (hrs)": utc})
    extrapolated_header.update({"number_IF_Windows": "NaN"})
    extrapolated_header.update({"Channel": "NaN"})
    extrapolated_header.update({"backend": "NaN"})
    # View LST with suspicion
    year_formatted = date.strftime('%Y')[2:]
    utc_formatted = date.strftime('%m%d'+year_formatted+' %H%M')
    LSThh,LSTmm,LSTss = rfitrends.LST_calculator.LST_calculator(utc_formatted)
    LST = LSThh + LSTmm/60.0 + LSTss/3600.0
    extrapolated_header.update({"lst (hrs)": LST})

    extrapolated_header.update({"polarization":filename[6]})
    extrapolated_header.update({"source":"NaN"})
    extrapolated_header.update({"tsys":"NaN"})
    extrapolated_header.update({"frequency_type":"NaN"})
    extrapolated_header.update({"Units":"Jy"})
    extrapolated_header.update({"scan_number":"NaN"})

    # We assume if there's no header that we will only have frequency and Intensity columns. So far this has not been false, 
    # But it is an assumption to acknowledge. 
    extrapolated_header['Column names'] = ["Frequency (MHz)","Intensity (Jy)"]
    return(extrapolated_header)

    
def ReadFileLine_ColumnValues(has_header,line_value: list,column_names,filepath):
    """
    Reads one line in a file that has been determined by the read_file function to be a row with data as opposed to header information

    param has_header: boolean determining if the file has a header or not
    param line_value: the parsed values containing the information for the particular line of this file 
    param column_names: the names of the columns contained in this file
    param filepath: the path to this particular file
    returns data_entry: This is a dictionary containing the column data
    """
    # Unfortunately, we first have to check if the column names match the length of the column values. For example, if the columns overlapped with themselves anywhere, such as the frequency values bleeding into intensity values to make 1471.456800.000 which should be 
    # something like 1471.456 for frequency and 800.000 for intensity or something (these are made up numbers for example only). 
    if len(column_names) != len(line_value):
        raise InvalidColumnValues("The number of column names and number of column values for this file is not equal. This is an invalid file.")
    # Next we need to streamline the naming conventions for the columns:  
    # Sometimes it's labeled frequency, sometimes Frequency (MHz), sometimes Frequency (GHz)...etc  
    fixed_column_names = []
    for column_name in column_names:
        try: 
            fixed_column_name = rfitrends.Column_fixes.Column_name_corrections[column_name]
        # If we don't recognize the column name, raise that error
        except:
            raise InvalidColumnValues("There is an unrecognized column name "+column_name+". Please check and reformat your file or add it to the list of column names in Column_fixes.py")
        fixed_column_names.append(fixed_column_name)
    # We also need to check that required columns in the configuration file exist somewhere in these columns, as they're needed for any science: 
    config = configparser.ConfigParser()
    config.read(resource_filename('rfitrends','rfitrends.conf'))
    mandatory_columns = json.loads(config['Mandatory Fields']['mandatory_columns'])
    for mandatory_column in mandatory_columns:
        if mandatory_column not in fixed_column_names:
            raise InvalidColumnValues("One of the manditory columns listed in rfitrends.conf is not present in this file. This is required to continue processing this file.")

    # now that we know this is a correctly made line, we can get the data from the lines: 
    data_entry  = dict(zip(fixed_column_names,line_value))

    # Finally, we need to throw away this line if Intensity is NaN, as it's not a useful line for science: 
    intensity_isNaN = math.isnan(float(data_entry["Intensity_Jy"]))
    if intensity_isNaN:
        raise InvalidIntensity()

    # Okay, so there's nothing wrong with the line, so we can actually return a normal line: 
    return data_entry


def FrequencyVerification(frequency_value,header):
    """
    Identifies issues in the frequency value in RFI-data
    1.) Checks for units (MHz vs GHz)
    2.) Checks that the frequency is in the appropriate range for the given receiver, under the assumption that
    they were generated by the understood receivers prior to 2020
    
    :param frequency_value: the frequency value to verify
    :param header: the dictionary made with header information for each file 
    :returns validated_frequency: the validated or verified frequency value
    """
    # Makes the assumption that we're not observing below 245 MHz
    # This is done as opposed to listening to the title labels, because there have been a number 
    # Of files in the past with headers that mislabeled the Frequencies as GHz when it was MHz, or vice versa
    # Additionally, some of our files don't have headers at all, so we are left to guess. 
    if float(frequency_value) < 245.0: # Converting all GHz values to MHz
        validated_frequency = str(float(frequency_value) * 1000.0)
    else:
        validated_frequency = frequency_value

    # Getting receiver ranges (updated as of 2020) so that we know if this value makes 
    # Logical sense. 
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
    # If the frequency we calculated does not fall in that range, then we raise an error. We cannot verify what the
    # Correct frequency should be in this case. 
    if float(validated_frequency) < (freq_min - freq_buffer) or float(validated_frequency) > (freq_max + freq_buffer):
        raise FreqOutsideRcvrBoundsError
    # Make the frequency key the same format as the table. Assumes we never need more than 4 decimals of precision
    validated_frequency = Decimal(validated_frequency).quantize(Decimal('0.0001'),rounding=ROUND_DOWN)
    return validated_frequency


############ Functions that work to upload data to the database ####################

def upload_files(filepaths,connection_manager,main_table,dirty_table):
    """
    Uploads all the processed data into the appropriate tables for a given database 

    param filepaths : a list of paths to all the files that need to be processed
    param connection_manager : a class handling the connection to the SQL database
    param unique_filenames: a list containing all the files that have been processed into the database
    param main_table : the table to put in your clean, primary dataset
    param dirty_table : if a problem is encountered, the data will be dumped into a less-organizable "dirty table"
    """

    # Going through each file one by one: 
    for filenum,filepath in enumerate(filepaths):
        print("Extracting file "+str(filenum+1)+" of "+str(len(filepaths))+", filename: "+str(filepath))
        filename = filepath.split("/")[-1] # Getting filename from last piece in file path
        # if the filename has already been processed, skip it. This assumes the file has been processed if ANY part of the file has been processed. 
        # in other words, if you're halfway through processing a file with this script, kill the process, and restart, it will assume 
        # That the half-finished file has completely been processed and skip the file. 

        # Try reading the file's data and header
        try:
            formatted_RFI_file = read_file(filepath,main_table,dirty_table,connection_manager)
        # Handling any problems along the way:
        except mysql.connector.Error as error:
            print("{}".format(error))
        except InvalidColumnValues:
            print("Column values are invalid. Dropping file.")
            continue
        except DuplicateValues:
            print("File already exists in database, moving on to next file.")
            continue
        print('File extracted. Uploading to database.')
        print(str(len(formatted_RFI_file.get('Data')))+' lines to upload (labeled as \'it\' or \'iterations\' below)')
        print('iterations [time elapsed, iterations per second]')
        # Try uploading that file's data to the appropriate main table
        # For each line of data, upload line to the main database
        dirty_filename_entered = False
        for index,frequency_key in tqdm(enumerate(formatted_RFI_file.get("Data"))):#for each value in that multi-valued set
            # The actual data entry
            data_entry = formatted_RFI_file.get('Data')[frequency_key]
            #print("Uploading line "+str(index)+" of "+str(len(formatted_RFI_file.get("Data")))+" for "+str(filename)+" ("+str(filenum+1)+" of "+str(len(filepaths))+")")
            # We do this again in case this is a dirty table where frequency verification has failed
            frequency_key = Decimal(frequency_key).quantize(Decimal('0.0001'),rounding=ROUND_DOWN)
            # Fill in missing columns if necessary (in other words, if we're missing a window or channel column, fill it with "NaN" values)
            data_entry = manage_missing_cols(data_entry).getdata_entry()
            # Try executing query
            try:
                connection_manager.add_main_values(data_entry,formatted_RFI_file,str(frequency_key))
                if data_entry['Database'] == dirty_table and dirty_filename_entered == False:
                    insert_dirty_filename = 'INSERT INTO Bad_files (filename) VALUES (\''+filename+'\');'
                    connection_manager.execute_command(insert_dirty_filename)
                    dirty_filename_entered = True
                duplicate_entry = False
            # If we find a duplicate entry, we will up the counts and average the intensities
            except mysql.connector.errors.IntegrityError:
                # Get intensity,filename, and counts from the line in the table that the line you're currently trying to upload conflicts with
                responses = connection_manager.grab_values_for_avg_intensity(str(data_entry["Database"]),str(frequency_key),str(formatted_RFI_file.get("mjd")))
                # For each conflicting value (there should only be one, but just in case we iterate through)
                for response in responses:
                    # Calculating average intensity
                    current_counts = response[2]
                    old_intensity = float(response[0])
                    new_intensity = float(data_entry["Intensity_Jy"])
                    intensity_avg = (new_intensity+(old_intensity*float(current_counts)))/(float(current_counts)+1.0)
                    old_filename = response[1]
                    # If this file nas not already been labeled as a duplicate, then we need to insert that file's entry into the duplicate table
                    if old_filename != "Duplicate":
                        connection_manager.insert_duplicate_data(str(frequency_key),str(old_intensity),str(old_filename))
                    # We also need to update the intensity with the average of all the duplicate values, reset counts, set window and channel to nan, and 
                    # Set the filename to duplicate so everyone knows it's in the duplicate database
                    connection_manager.update_avg_intensity(str(data_entry["Database"]),str(int(current_counts)+ 1),str(intensity_avg),str(frequency_key),str(formatted_RFI_file.get("mjd")))
                    # Finally, we need to put the current line being processed into the duplicate data catalog
                    connection_manager.insert_duplicate_data(str(frequency_key),str(new_intensity),str(formatted_RFI_file.get("filename")))   
                duplicate_entry = True
            # We have some receiver names that are too generic or specific for our receiver tables, so we're making that consistent
            frontend_for_rcvr_table = rfitrends.GBT_receiver_specs.PrepareFrontendInput(formatted_RFI_file.get("frontend"))
            # Putting composite key values into the receiver table, as long as it's not a duplicate line, and has
            # been deemed a clean line
            if frontend_for_rcvr_table != 'Unknown' and not duplicate_entry and data_entry["Database"] != dirty_table:
                update_caching_tables(frequency_key,data_entry,frontend_for_rcvr_table,connection_manager,formatted_RFI_file)
        # If there's any other error we encounter not yet handled, print out the error, some other info, and gracefully exit. 
        """
        except mysql.connector.errors.IntegrityError as Error:
            print("There was an error, here is the message: ")
            traceback.print_tb(Error.__traceback__)
            # print(Error)
            print("Frequency: "+str(frequency_key))
            print("Data: "+str(data_entry))
            connection_manager.previous_line_query(data_entry["Database"],str(formatted_RFI_file.get("mjd")),str(frequency_key))
            sys.exit()
        """

        print(str(filename)+" uploaded.")

def update_caching_tables(frequency_key,data_entry,frontend_for_rcvr_table,connection_manager,formatted_RFI_file): 
    # Add frequency and mjd to receiver table
    connection_manager.add_receiver_keys(frontend_for_rcvr_table,str(frequency_key),str(formatted_RFI_file.get("mjd")))
    # Get the latest projects table data
    rows = connection_manager.get_latest_project_data(frontend_for_rcvr_table)
    # Parse latest projects table data
    for row in rows: 
        latest_projid = row[0]
        latest_mjd  = row[1]
    if latest_mjd < Decimal(formatted_RFI_file.get("mjd")) and (formatted_RFI_file.get("projid") != 'NaN'):
        # Now we want to update the project id for the latest-project table:
        connection_manager.update_latest_projid(str(formatted_RFI_file.get("projid")),frontend_for_rcvr_table)
        # and update mjd:
        connection_manager.update_latest_date(str(formatted_RFI_file.get("mjd")),frontend_for_rcvr_table)
        # Before we replace the previous latest project with the current one, we want to drop the table containing the previous latest projects' data:
        if latest_projid != "None":
            connection_manager.drop_table(latest_projid)
        # We want to make a new table containing the previous latest project's data:
        connection_manager.projid_table_maker(str(formatted_RFI_file.get("projid")))
        # The new latest project is the most recent project we just updated
        latest_projid = str(formatted_RFI_file.get("projid"))
           
    if formatted_RFI_file.get("projid") == latest_projid and (formatted_RFI_file.get("projid") != 'NaN'):
        # Populate that table with this info
        connection_manager.projid_populate_table(str(formatted_RFI_file.get("projid")),str(frequency_key),str(formatted_RFI_file.get("mjd")))


########### MAIN #############

def main():
    #import ptvsd 
    # Allow other computers to attach to ptvsd at this IP address and port. 
    # (Remove this is not running through debugger)
    #ptvsd.enable_attach(address=('10.16.96.210', 3001), redirect_output=True) 
    #ptvsd.wait_for_attach()
    # Adding in-line arguments:
    parser = argparse.ArgumentParser(description="Takes .txt files of RFI data and uploads them to the given database")
    parser.add_argument("main_table",help="The string name of the table to which you'd like to upload your clean RFI data")
    parser.add_argument("dirty_table",help="The string name of the table to which you'd like to upload your flagged or bad RFI data")
    parser.add_argument("path",help="The path to the .txt files that need to be uploaded to the database")
    parser.add_argument("IP_address",nargs='?',default= '192.33.116.22',help="The IP address to find the SQL database to which you would like to add this table. Default is the GBO development server address. This would only work for employees.")
    parser.add_argument("database",nargs='?',default='jskipper',help="The name of the SQL database to which you would like to add this table. Default is jskipper, which would only work for employees.")
    # Parse those arguments
    args = parser.parse_args()
    main_table = args.main_table
    dirty_table = args.dirty_table
    IP_address = args.IP_address
    database = args.database
    # The likely path to use for filepath_to_rfi_scans if looking at most recent (last 6 months) of RFI data for GBT:
    #path = '/home/www.gb.nrao.edu/content/IPG/rfiarchive_files/GBTDataImages'
    path = args.path   
    config = configparser.ConfigParser()
    # Create connection to the database
    connection_manager = rfitrends.connection_manager.connection_manager(IP_address,database)
    # Collect filenames/paths from the directory specified and product a list of those names to run
    filepaths_to_process = gather_filepaths_to_process(path)
    # Going through each file one by one
    print("starting to upload files one by one...")
    # Upload files to database
    upload_files(filepaths_to_process,connection_manager,main_table,dirty_table)
    print("All files uploaded.")

if __name__ == "__main__":
    main()
        
    


