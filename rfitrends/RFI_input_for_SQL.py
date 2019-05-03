###_________________________________________________________###

#  Code Name: RFI_input_for_SQL.py

#  Code Purpose: To read in multiple types of ascii files containing RFI data across several decades. Then output in a form usable by a mySQL database.


#  For any questions please contact Joy Nicole Skipper at jskipper@nrao.edu

###_________________________________________________________###
################################################################################################################################################################################################################################

#ISSUES: 
#Need to reload values into SQL
#Need to make it possible to add new values without redoing everything

#DONE:
#2.added mjd to non-headers, need to reload into SQL
#3. filled non-headers with values so they're not skipped out on when loaded into SQL






import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import copy
import re
import julian
import datetime
import LST_calculator
import mysql.connector
import getpass
import GBT_receiver_specs
import sys
import fxns_output_process

class FreqOutsideRcvrBoundsError(Exception):
    pass


#Section 1: These first functions are for reading in a file and parsing up the data into a single dictionary containing all the necessary values:
#_____________________________________________________________
################################################################################################################################################################################################################################

def read_file(filepath):#use this function to read in a particular file and return a dictionary with all header values and lists of the data
    #database_to_put = 'RFI_3'
    
    f = open(filepath, 'r') #open file
    formatted_RFI_file = {}
    #these are lists containing column values that will be added to the dictionary later:
    data = [] 
    window = []
    channel = []
    frequency = []
    intensity = []
    database = []
    has_header = True #assume the file does have a header
    #open file and go line by line: 
    counter = 0
    for line_count,line_value in enumerate(f): 

        #looking at each line in the file and deciding what kind of line it is

        #if it doesn't have a header or titles at all:
        if (line_count == 0) and not line_value.startswith("#"):#basically, see if this file doesn't have a header
            has_header = False # signify that file does not have a header
            formatted_RFI_file,column_names = ReadFileLine_NoHeader(formatted_RFI_file,filepath)

        #if it's a useless line: 
        elif line_value == "################ HEADER #################\n" or line_value == "################   Data  ################\n" or line_value == '\n': #ignoring lines that are just header and data indicators - they give us no information
            continue


        #if it's a header value such as "date: 01-24-1995"
        elif line_value.startswith("#")==True and (":" in line_value) == True:
            formatted_RFI_file = ReadFileLine_HeaderValue(formatted_RFI_file, line_value,filepath)

        #if it's a column title indicating the names of each column
        elif line_value.startswith("#")==True and (":" in line_value) == False: 
            column_names = list(filter(None,((line_value.strip('#').strip('\n')).split(" "))))#creating a list of all the column names
                
        #if not all other cases then this line must just be the values given in the columns   
        #    
        else:
            new_line = list(filter(None,((line_value.strip('\n')).split(" "))))#create a list of all the column values
            window_value,channel_value,frequency_value,intensity_value,overlapping = ReadFileLine_ColumnValues(has_header,new_line,column_names,filepath)
            if overlapping: 
                continue
            try:
                #print(counter)
                validated_frequency = FrequencyVerification(frequency_value,formatted_RFI_file)
                database.append('RFI_3')
                database_value = 'RFI_3'
                counter += 1
                
            except FreqOutsideRcvrBoundsError:
                database.append('RFI_dirty')
                database_value = 'RFI_dirty'
                #print(database[-1])
                #print(counter)
                validated_frequency = frequency_value
                #database_to_put = 'RFI_dirty'
            data_line = [window_value, channel_value, validated_frequency,intensity_value,database_value]
            data.append(data_line)
            window.append(window_value)
            channel.append(channel_value)
            frequency.append(validated_frequency)
            intensity.append(intensity_value)
            data.append(data_line)

            if intensity[-1] == "NaN":#getting rid of bogus values
                del window[-1]
                del channel[-1]
                del frequency[-1]
                del intensity[-1]
            #freqarray = np.asarray(frequency)
            #if np.min(freqarray.astype(float)) >= 150.0 == False:
                #print(frequency)
                #exit()
    
    #window_dictionary = {"Window":window}#update dictionary with a list for each column value
    #channel_dictionary = {"Channel": channel}    
    #frequency_dictionary = { "Frequency (MHz)": frequency}    
    #intensity_dictionary = { "Intensity (Jy)" : intensity}
    #database_dictionary = { "database" : database}
    #update the file dictionary:
    
    formatted_RFI_file["Window"] = window
    formatted_RFI_file["Channel"] = channel
    formatted_RFI_file["Intensity (Jy)"] = intensity
    formatted_RFI_file["Frequency (MHz)"] = frequency
    formatted_RFI_file["Database"] = database
    formatted_RFI_file["Data"] = data
    #keep in mind this means that there may be empty lists being added if this file doesn't contain a certain column value
    return(formatted_RFI_file)#return that dictionary for this particular file we are looking at


#---subsection: These are all functions used by read_file()---#


def FrequencyVerification(frequency_value,header_information):
    """
    Identifies issues in the frequency value in RFI-data
    1.) Checks for units (MHz vs GHz)
    2.) Checks that the frequency is in the appropriate range for the given receiver, under the assumption that
    they were generated by the understood receivers prior to 2019
    
    :param frequency_value: the frequency value to verify
    :param header_information: the dictionary made with header information for each file 
    :returns validated_frequency: the validated frequency value
    """

    if float(frequency_value) < 245.0: # Converting all GHz values to MHz
        validated_frequency = str(float(frequency_value) * 1000.0)
    else:
        validated_frequency = frequency_value

    """
    frontend_aliases = {
        'P1': 'Prime Focus 1',
        'RcvrPF_1': 'Prime Focus 1'
    }

    GBT_receiver_ranges = { 
        'Prime Focus 1': {'freq_min': 290.0, 'freq_max': 920.0},
        'Rcvr_342': {'freq_min': 290.0, 'freq_max': 395.0},
        'Rcvr_450': {'freq_min': 385.0, 'freq_max': 520.0}
    }
    """

    frontend_shorthand = header_information["frontend"]
 #   try:
    frontend_name = GBT_receiver_specs.frontend_aliases[frontend_shorthand]
 #   except:
 #       frontend_name = 'Unknown'
    freq_min = GBT_receiver_specs.GBT_receiver_ranges[frontend_name]['freq_min']
    freq_max = GBT_receiver_specs.GBT_receiver_ranges[frontend_name]['freq_max']
    buffer_factor = .1
    freq_buffer = (freq_max - freq_min)* buffer_factor
    if GBT_receiver_specs.GBT_receiver_ranges[frontend_name] == "Unknown": 
        freq_buffer = 0
    if float(validated_frequency) < (freq_min - freq_buffer) or float(validated_frequency) > (freq_max + freq_buffer):
        raise FreqOutsideRcvrBoundsError
    #if str(validated_frequency) == "1.788023":
    #    print(validated_frequency)
    return validated_frequency

def ReadFileLine_NoHeader(dictionary_per_file,filepath):
    #Gleaning information from a file that does not contain a file header for information
    filename = (filepath.split("/")[-1])# splitting filepath back down to just the filename    
    dictionary_per_file.update({"filename": filename})
    filename_temporary = re.split('[_.]',filename)#split the filename into the naming components (there's no header, so we have to glean info from the filename)
    filename = filename_temporary

    unix_timestamp = (os.path.getmtime(filepath))
    date = (datetime.datetime.utcfromtimestamp(unix_timestamp))
    dictionary_per_file.update({"date": (date.strftime('%Y-%m-%d %H:%M:%S'))})# gleaning info from filename
    #Calculating MJD...
    jd = julian.to_jd(date+ datetime.timedelta(hours=12),fmt='jd')
    mjd = jd  - 2400000.5
    dictionary_per_file.update({"mjd": mjd})
    dictionary_per_file.update({"azimuth (deg)":float(filename[7][2:])})
    dictionary_per_file.update({"elevation (deg)":float(filename[8][2:])})
    dictionary_per_file.update({"feed": "NaN"})
    dictionary_per_file.update({"frontend": str(filename[2])})
    dictionary_per_file.update({"projid": "NaN"})
    dictionary_per_file.update({"frequency_resolution": "NaN"})
    dictionary_per_file.update({"Window": "NaN"})
    dictionary_per_file.update({"exposure": "NaN"})
    utc_hr = (float(date.strftime("%H")))
    utc_min = (float(date.strftime("%M"))/60.0 )
    utc_sec = (float(date.strftime("%S"))/3600.0)
    utc = utc_hr+utc_min+utc_sec
    dictionary_per_file.update({"utc": str(utc)})
    dictionary_per_file.update({"number_IF_Windows": "NaN"})
    dictionary_per_file.update({"Channel": "NaN"})
    dictionary_per_file.update({"backend": "NaN"})

    year_formatted = date.strftime('%Y')[2:]
    utc_formatted = date.strftime('%m%d'+year_formatted+' %H%M')
    LSThh,LSTmm,LSTss = LST_calculator.LST_calculator(utc_formatted)
    LST = LSThh + LSTmm/60.0 + LSTss/3600.0
    dictionary_per_file.update({"lst": LST})

    dictionary_per_file.update({"polarization":filename[6]})
    dictionary_per_file.update({"source":"NaN"})
    dictionary_per_file.update({"tsys":"NaN"})
    dictionary_per_file.update({"frequency_type":"NaN"})
    dictionary_per_file.update({"Units":"Jy"})
    dictionary_per_file.update({"scan_number":"NaN"})
    dictionary_per_file.update({"elevation": float(filename[8][2:])})

    

    column_names = ["Frequency (MHz)","Intensity (Jy)"] # we can't glean the column names from the header either, but we know what they are

    return(dictionary_per_file,column_names)

def ReadFileLine_HeaderValue(dictionary_per_file, line_value,filepath):
    filename = (filepath.split("/")[-1])# splitting filepath back down to just the filename    
    dictionary_per_file.update({"filename": filename})
    #Reading the line of a file that is a part of a header
    header_name, header_value = line_value.split(":") # get the name assigned to the header and it's associated value, say "Date: 01-24-1995" or something
    header_name = header_name.strip(' \t\n\r#') #get rid of hashtags and anything but the text we need from these headers
    header_value = header_value.strip(' \t\n\r#')

    header_line_dict = {header_name:header_value}#creating a dictionary with the header category and its value
    dictionary_per_file.update(header_line_dict)#adding that dictionary to the dictionary for this particular file

    return dictionary_per_file

def CheckFor_OverlappingColumns(line_value):
    overlapping = False
    column_count = 0
    for column_count,column_value in enumerate(line_value): 
        if column_value.count(".") == 2:
            overlapping = True
            break
    return overlapping,column_count

def DealWith_Overlapping(column_count,line_value):#NOTE: this happened only with one type of column set for me, needs to be modified to be workable with all column sets
        #This function deals with overlapping columns, when one column value bleeds into another. I.E. your frequency/intensity column is 400.1000.00 meaning a frequency of 400 and a intensity of 1000.0

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
    
    

def ReadFileLine_ColumnValues(has_header,line_value,column_names,filepath):
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
        print("there is a problem. The file reader could not parse this file. Please look at the file format and try again.")
        print("this is the filepath:\n")
        print(filepath)
        print("these are the column names:\n")
        print(column_names)
        print("this is the line in the file that this file parser broke on:\n")
        print(line_value)                
        input()#this is just to make the code stop

    
    return(window_value,channel_value,frequency_value,intensity_value,overlapping)


def None_string(value,value_len):
    if value == None: 
        value = "None"
    elif value == []:
        value = np.zeros(value_len)
    return value

# Section 5: Code!
###____________________start of actual code (not functions)_____________________###
################################################################################################################################################################################################################################


def main():
    path = '/home/www.gb.nrao.edu/content/IPG/rfiarchive_files/GBTDataImages'
    #path = '/users/jskipper/Documents/scripts/RFI/problem_files/single_line_test/'
    list_o_paths = []
    list_o_structs = []

    # making a list of all of the .txt files in the directory so I can just cycle through each full path:
    for filename in os.listdir(path):
        if filename.endswith(".txt") and filename != "URLs.txt":# If the files are ones we are actually interested in
            list_o_paths.append(os.path.join(path,filename))
            continue


    username = input("Please enter SQL database username: ")

    password = getpass.getpass("Please enter the password: ",stream=None)

    cnx = mysql.connector.connect(user=username, password=password,
                                host='192.33.116.22',
                                database='jskipper')
    cursor = cnx.cursor()

    print("gathering filename set...")
    def gather_list(connection_call,query):
        cursor = connection_call
        cursor.execute(query)


        value_list = []


        row = cursor.fetchone() #getting each row
    
        while row is not None:
            value_list.append(row[0])
            row = cursor.fetchone()

        return(value_list)
    unique_filename = gather_list(cursor, "SELECT DISTINCT filename FROM RFI_3")


    #going thru each file one by one
    print("starting to upload files one by one...")
    for filenum,filepath in enumerate(list_o_paths):
        print("Extracting file "+str(filenum+1)+" of "+str(len(list_o_paths))+", filename: "+str(filepath))
        filename = filepath.split("/")[7]
        #print(filename)
        #print(unique_filename[filenum])
        if filename in unique_filename:
            print("File already exists in database, moving on to next file.")
            continue
        #input("stopping")
        
        formatted_RFI_file = read_file(filepath)
        def check_data_lengths(formatted_RFI_file): 
            data_lengths = {
                'Frequency length': len(formatted_RFI_file.get("Frequency (MHz)")),
                'Window length': len(formatted_RFI_file.get("Window")),
                'Channel length': len(formatted_RFI_file.get("Channel")),
                'Intensity length': len(formatted_RFI_file.get("Intensity (Jy)"))
            }
            if len(set(data_lengths.values())) != 1:
                print("Could not extract: Frequency, Intensity, Channel, and Window fields are not one to one. Check your data")
                print(data_lengths)
                exit()
        check_data_lengths(formatted_RFI_file)
        
        for linenum in range(len(formatted_RFI_file.get("Frequency (MHz)"))):#for each value in that multi-valued set
            #if str(formatted_RFI_file.get("Frequency (MHz)")[linenum]) == "1.788023":
                #print(str(formatted_RFI_file.get("Database")[linenum]))
                #print(formatted_RFI_file.get("Data"))
            add_values = "INSERT INTO "+str(formatted_RFI_file.get("Data")[linenum][4])+" (feed,frontend,azimuth,projid,frequency_resolution,Window,exposure,utc,date,number_IF_Windows,Channel,backend,mjd,Frequency,lst,filename,polarization,source,tsys,frequency_type,units,Intensity,scan_number,elevation) VALUES (\""+str(formatted_RFI_file.get("feed"))+"\",\""+str(formatted_RFI_file.get("frontend"))+"\",\""+str(formatted_RFI_file.get("azimuth (deg)"))+"\",\""+str(formatted_RFI_file.get("projid"))+"\",\""+str(formatted_RFI_file.get("frequency_resolution"))+"\",\""+str(formatted_RFI_file.get("Data")[linenum][0])+"\",\""+str(formatted_RFI_file.get("exposure (sec)"))+"\",\""+str(formatted_RFI_file.get("utc (hrs)"))+"\",\""+str(formatted_RFI_file.get("date"))+"\",\""+str(formatted_RFI_file.get("number_IF_Windows"))+"\",\""+str(formatted_RFI_file.get("Data")[linenum][1])+"\",\""+str(formatted_RFI_file.get("backend"))+"\",\""+str(formatted_RFI_file.get("mjd"))+"\",\""+str(formatted_RFI_file.get("Data")[linenum][2])+"\",\""+str(formatted_RFI_file.get("lst (hrs)"))+"\",\""+str(formatted_RFI_file.get("filename"))+"\",\""+str(formatted_RFI_file.get("polarization"))+"\",\""+str(formatted_RFI_file.get("source"))+"\",\""+str(formatted_RFI_file.get("tsys"))+"\",\""+str(formatted_RFI_file.get("frequency_type"))+"\",\""+str(formatted_RFI_file.get("units"))+"\",\""+str(formatted_RFI_file.get("Data")[linenum][3])+"\",\""+str(formatted_RFI_file.get("scan_number"))+"\",\""+str(formatted_RFI_file.get("elevation (deg)"))+"\");"
            cursor.execute(add_values)

        


    cnx.close()

if __name__ == "__main__":
    import ptvsd 
    # Allow other computers to attach to ptvsd at this IP address and port. 
    ptvsd.enable_attach(address=('10.16.96.210', 3001), redirect_output=True) 
    # # Pause the program until a remote debugger is attached 
    print("Waiting for debugger attach...") 
    #ptvsd.wait_for_attach()
    main()


        
    


