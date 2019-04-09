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

#Section 1: These first functions are for reading in a file and parsing up the data into a single dictionary containing all the necessary values:
#_____________________________________________________________
################################################################################################################################################################################################################################

def read_file(filepath):#use this function to read in a particular file and return a dictionary with all header values and lists of the data
    f = open(filepath, 'r') #open file
    dictionary_per_file = {}
    #these are lists containing column values that will be added to the dictionary later: 
    window = []
    channel = []
    frequency = []
    intensity = []
    has_header = True #assume the file does have a header
    #open file and go line by line: 
    for line_count,line_value in enumerate(f): 
        #looking at each line in the file and deciding what kind of line it is

        #if it doesn't have a header or titles at all:
        if (line_count == 0) and not line_value.startswith("#"):#basically, see if this file doesn't have a header
            has_header = False # signify that file does not have a header
            dictionary_per_file,column_names = ReadFileLine_NoHeader(dictionary_per_file,filepath)

        #if it's a useless line: 
        elif line_value == "################ HEADER #################\n" or line_value == "################   Data  ################\n": #ignoring lines that are just header and data indicators - they give us no information
            continue


        #if it's a header value such as "date: 01-24-1995"
        elif line_value.startswith("#")==True and (":" in line_value) == True:
            dictionary_per_file = ReadFileLine_HeaderValue(dictionary_per_file, line_value,filepath)

        #if it's a column title indicating the names of each column
        elif line_value.startswith("#")==True and (":" in line_value) == False: 
            column_names = list(filter(None,((line_value.strip('#').strip('\n')).split(" "))))#creating a list of all the column names
                
        #if not all other cases then this line must just be the values given in the columns        
        else:
            new_line = list(filter(None,((line_value.strip('\n')).split(" "))))#create a list of all the column values
            window,channel,frequency,intensity = ReadFileLine_ColumnValues(has_header,new_line,column_names,window,channel,frequency,intensity)
            if intensity[-1] == "NaN":#getting rid of bogus values
                del window[-1]
                del channel[-1]
                del frequency[-1]
                del intensity[-1]
    
    window_dictionary = {"Window":window}#update dictionary with a list for each column value
    channel_dictionary = {"Channel": channel}    
    frequency_dictionary = { "Frequency (MHz)": frequency}    
    intensity_dictionary = { "Intensity (Jy)" : intensity}
    #update the file dictionary:
    dictionary_per_file.update(window_dictionary)
    dictionary_per_file.update(channel_dictionary)
    dictionary_per_file.update(frequency_dictionary)
    dictionary_per_file.update(intensity_dictionary)#keep in mind this means that there may be empty dictionaries being added if this file doesn't contain a certain column value
    return(dictionary_per_file)#return that dictionary for this particular file we are looking at


#---subsection: These are all functions used by read_file()---#

def ReadFileLine_NoHeader(dictionary_per_file,filepath):
    #Gleaning information from a file that does not contain a file header for information
    filename = (filepath.split("/")[-1])# splitting filepath back down to just the filename    
    dictionary_per_file.update({"filename": filename})
    filename_temporary = re.split('[_.]',filename)#split the filename into the naming components (there's no header, so we have to glean info from the filename)
    filename = filename_temporary

    unix_timestamp = (os.path.getmtime(filepath))
    date = (datetime.datetime.utcfromtimestamp(unix_timestamp))
    dictionary_per_file.update({"date": (date.strftime('%Y-%m-%d %H:%M:%S'))})# gleaning info from filename
    print(date)
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

    dictionary_per_file.update({"polarization":"NaN"})
    dictionary_per_file.update({"source":"NaN"})
    dictionary_per_file.update({"tsys":"NaN"})
    dictionary_per_file.update({"frequency_type":"NaN"})
    dictionary_per_file.update({"Units":"Jy"})
    dictionary_per_file.update({"scan_number":"NaN"})
    dictionary_per_file.update({"elevation":"NaN"})

    

    column_names = ["Frequency (MHz)","Intensity (Jy)"] # we can't glean the column names from the header either, but we know what they are

    return(dictionary_per_file,column_names)

def ReadFileLine_HeaderValue(dictionary_per_file, line_value,filepath):
    filename = (filepath.split("/")[-1])# splitting filepath back down to just the filename    
    dictionary_per_file.update({"filename": filename})
    #Reading the line of a file that is a part of a header
    header_name, header_value = line_value.split(":") # get the name assigned to the header and it's associated value, say "Date: 01-24-1995" or something
    header_name = header_name.strip(' \t\n\r#') #get rid of hashtags and anything but the text we need from these headers
    header_value = header_value.strip(' \t\n\r#')
    if header_name == "Frequency(GHz)": #This is corrected in the column values as well, we basically want all our frequencies in the same units
        header_name = "Frequency (Mhz)"
    header_line_dict = {header_name:header_value}#creating a dictionary with the header category and its value
    dictionary_per_file.update(header_line_dict)#adding that dictionary to the dictionary for this particular file

    return dictionary_per_file

def CheckFor_OverlappingColumns(line_value):
    for column_count,column_value in enumerate(line_value): 
        if column_value.count(".") == 2:
            overlapping = "True"
            break
        else:
            overlapping = "False"
    return overlapping,column_count

def DealWith_Overlapping(column_count,line_value,window,channel,frequency,intensity):#NOTE: this happened only with one type of column set for me, needs to be modified to be workable with all column sets
        #This function deals with overlapping columns, when one column value bleeds into another. I.E. your frequency/intensity column is 400.1000.00 meaning a frequency of 400 and a intensity of 1000.0

        split_value = int(raw_input("Please input the character number at which the columns need to be split, counting from the left (default is 8): \n") or "8")

        if column_count == 0:
            window.append(line_value[0][0:split_value])
            channel.append(line_value[0][split_value:])
            frequency.append(line_value[1])
            intensity.append(line_value[2])
        elif column_count == 1: 
            window.append(line_value[0])
            channel.append(line_value[1][0:split_value])
            frequency.append(line_value[1][split_value:])
            intensity.append(line_value[2])    
        elif column_count ==2: 
            window.append(line_value[0])
            channel.append(line_value[1])
            frequency.append(line_value[2][0:split_value])
            intensity.append(line_value[2][split_value:0])
        return window,channel,frequency,intensity
    
    

def ReadFileLine_ColumnValues(has_header,line_value,column_names,window,channel,frequency,intensity):
    # Unfortunately, we first have to check if the columns overlapped with themselves anywhere, such as the frequency values bleeding into intensity values to make 1471.456800.000 which should be 
    # something like 1471.456 for frequency and 800.000 for intensity or something (these are made up numbers for example only)
    overlapping,column_count = CheckFor_OverlappingColumns(line_value)
    if overlapping == "True":
        print("There is a file you have input that contains a column which has merged into the other. Here is the line: \n")
        print(line_value)
        window,channel,frequency,intensity = DealWith_Overlapping(column_count, line_value,window,channel,frequency,intensity)
        return window,channel,frequency,intensity
                    
    #now that we know this is a correctly made line, we check which format this file is in, is it 4 columns? 3? What are the values in these columns? 
    elif (column_names[0] == "Window" or column_names[0] == "IFWindow") and column_names[1] == "Channel" and (column_names[2] == "Frequency(MHz)" or column_names[2] == "Frequency MHz)") and column_names[3] == "Intensity(Jy)":#4 regular columns
        window.append(line_value[0])
        channel.append(line_value[1])
        frequency.append(line_value[2])
        intensity.append(line_value[3])

    elif column_names[0] == "Frequency(MHz)" and column_names[1] == "Intensity(Jy)":#2 regular columns)
        frequency.append(line_value[0])
        intensity.append(line_value[1])

    elif column_names[0] == "Channel" and column_names[1] == "Frequency(MHz)" and column_names[2] == "Intensity(Jy)":#3 regular columns
        channel.append(line_value[0])
        frequency.append(line_value[1])
        intensity.append(line_value[2])
    elif column_names[0] == "Channel" and column_names[1] == "Frequency(GHz)" and column_names[2] == "Intensity(Jy)":# 3 columns, but the person decided to put the frequency in GHz, so change back to MHz and add
        channel.append(line_value[0])
        frequency.append(str(float(line_value[1])*1000.0))
        intensity.append(line_value[2])        
    elif has_header == False:# Finally, if the file does not have a header, it has two columns that are frequency and intensity
        frequency.append(line_value[0])
        intensity.append(line_value[1])    
    else:    
        print("there is a problem. The file reader could not parse this file. Please look at the file format and try again.")
        print("this is the filepath:\n")
        print(filepath)
        print("these are the column names:\n")
        print(column_names)
        print("this is the line in the file that this file parser broke on:\n")
        print(line_value)                
        problem = raw_input()#this is just to make the code stop
    return(window,channel,frequency,intensity)


def None_string(value,value_len):
    if value == None: 
        value = "None"
    elif value == []:
        value = np.zeros(value_len)
    return value

# Section 5: Code!
###____________________start of actual code (not functions)_____________________###
################################################################################################################################################################################################################################


path = '/home/www.gb.nrao.edu/content/IPG/rfiarchive_files/GBTDataImages'
#path = '/users/jskipper/Documents/scripts/2017_deleted'
list_o_paths = []
list_o_structs = []

# making a list of all of the .txt files in the directory so I can just cycle through each full path:
for filename in os.listdir(path):
    if filename.endswith(".txt") and filename != "URLs.txt":# If the files are ones we are actually interested in
        list_o_paths.append(os.path.join(path,filename))
        continue


#going thru each file one by one
for i in list_o_paths:
    print("reading "+str(i)+"...")
    dictionary = read_file(i)
    list_o_structs.append(dictionary)#creating a structure of dictionaries with header info for each file, and lists of the values



exit()

import mysql.connector

username = input("Please enter SQL database username... ")
password = input("Please enter SQL database password... ")
cnx = mysql.connector.connect(user=username, password=password,
                              host='192.33.116.22',
                              database='jskipper')
cursor = cnx.cursor()



"""
for count,SQL_dict in enumerate(list_o_structs): 
    if count%10 == 0:
        f = open('data_for_SQL'+str(count)+'.csv','w')
        print "starting to write data to file number "+str(count)+"...\n"
        #keys = []
        for key0, value0 in SQL_dict.iteritems():
            if key0 != "elevation (deg)": 
                f.write("\""+str(key0)+"\",")
            else:
                f.write("\""+str(key0)+"\"")
        f.write("\n")
#    if count == 0:
#        test = open('title_for_SQL.txt','w')
#        for key0, value0 in SQL_dict.iteritems():
#            test.write(str(key0)+",")
#        test.write("\n")
    for key,value in SQL_dict.iteritems():
        if str(type(value)) == "<type \'list\'>":
            for fnum,fval in enumerate(value):
                for key2,value2 in SQL_dict.iteritems():
                    if (str(type(value2)) == "<type \'list\'>"):
                        f.write("\""+str(value2[fnum])+"\",")
                    elif key2 != "elevation (deg)": 
                        f.write("\""+str(value2)+"\",")
                     else:
                        f.write("\""+str(value2)+"\"")
                f.write("\n")
            continue
    if count == 0:
        break
    
    print "file "+str(count)+" written \n"


"""




for count,SQL_dict in enumerate(list_o_structs): #iterating through each dictionary one by one
    print("starting to write data to file number "+str(count)+"...\n")
    #keys = []
    for key,value in SQL_dict.iteritems():#iterating through each field in that dictionary
        if str(type(value)) == "<type \'list\'>":#if that field is multi-valued
            for fnum,fval in enumerate(value):#for each value in that multi-valued set
        #        keys = []
                for key0,value0 in SQL_dict.iteritems():
                    SQL_dict.update({key0:None_string(SQL_dict.get(key0),len(value))})


        #             else:
        #                keys.append("\""+str(value2)+"\"")
                #this is each time we should add
                """
                print SQL_dict
                print SQL_dict.get("feed")
                print SQL_dict.get("frontend")
                print SQL_dict.get("azimuth (deg)")
                print SQL_dict.get("projid")
                print SQL_dict.get("frequency_resolution")
                print SQL_dict.get("Window")[0:10]
                print SQL_dict.get("exposure (sec)")
                print SQL_dict.get("utc (hrs)")
                print SQL_dict.get("date")
                print SQL_dict.get("number_IF_Windows")
                print SQL_dict.get("channel")[0:10]
                print SQL_dict.get("backend")
                print SQL_dict.get("mjd")
                print SQL_dict.get("Frequency (MHz)")[0:10]
                print SQL_dict.get("lst (hrs)")
                print SQL_dict.get("filename")
                print SQL_dict.get("polarization")
                print SQL_dict.get("source")
                print SQL_dict.get("tsys")
                print SQL_dict.get("frequency_type")
                print SQL_dict.get("units")
                print SQL_dict.get("Intensity (Jy)")[0:10]
                print SQL_dict.get("scan_number")
                print SQL_dict.get("elevation (deg)")
                """


                add_values = "INSERT INTO RFI_2 (feed,frontend,azimuth,projid,frequency_resolution,Window,exposure,utc,date,number_IF_Windows,Channel,backend,mjd,Frequency,lst,filename,polarization,source,tsys,frequency_type,units,Intensity,scan_number,elevation) VALUES (\""+str(SQL_dict.get("feed"))+"\",\""+str(SQL_dict.get("frontend"))+"\",\""+str(SQL_dict.get("azimuth (deg)"))+"\",\""+str(SQL_dict.get("projid"))+"\",\""+str(SQL_dict.get("frequency_resolution"))+"\",\""+str(SQL_dict.get("Window")[fnum])+"\",\""+str(SQL_dict.get("exposure (sec)"))+"\",\""+str(SQL_dict.get("utc (hrs)"))+"\",\""+str(SQL_dict.get("date"))+"\",\""+str(SQL_dict.get("number_IF_Windows"))+"\",\""+str(SQL_dict.get("Channel")[fnum])+"\",\""+str(SQL_dict.get("backend"))+"\",\""+str(SQL_dict.get("mjd"))+"\",\""+str(SQL_dict.get("Frequency (MHz)")[fnum])+"\",\""+str(SQL_dict.get("lst (hrs)"))+"\",\""+str(SQL_dict.get("filename"))+"\",\""+str(SQL_dict.get("polarization"))+"\",\""+str(SQL_dict.get("source"))+"\",\""+str(SQL_dict.get("tsys"))+"\",\""+str(SQL_dict.get("frequency_type"))+"\",\""+str(SQL_dict.get("units"))+"\",\""+str(SQL_dict.get("Intensity (Jy)")[fnum])+"\",\""+str(SQL_dict.get("scan_number"))+"\",\""+str(SQL_dict.get("elevation (deg)"))+"\");"
                cursor.execute(add_values)

            break

    

            
    #add_values = "INSERT INTO RFI_2 VALUES ("+keys[0]+","+keys[1]+","+keys[2]+","+keys[3]+","+keys[4]+","+keys[5]+","+keys[6]+","+keys[7]+","+keys[8]+","+keys[9]+","+keys[10]+","+keys[11]+","+keys[12]+","+keys[13]+","+keys[14]+","+keys[15]+","+keys[16]+","+keys[17]+","+keys[18]+","+keys[19]+","+keys[20]+","+keys[21]+","+keys[22]+");"

    #cursor.execute(add_values)
    #if count == 0:
    #    break
    print("file "+str(count)+" written out of "+str(len(list_o_structs))+" \n")  


cnx.close()




        
    


