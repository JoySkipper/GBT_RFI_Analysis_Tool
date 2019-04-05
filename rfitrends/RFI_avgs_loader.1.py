###_________________________________________________________###

#  Code Name: RFI_avgs_loader_1.py

#  Code Purpose: beginning attempts to select a randomized frequency value


#  For any questions please contact Joy Nicole Skipper at jskipper@nrao.edu

###_________________________________________________________###
################################################################################################################################################################################################################################





import csv
import numpy as np
import pymysql
import math
import random

def get_rando_range(freq_list,mjd_list, intensity_list):
    index_begin = 0
    index_end = 0
    for i in range(7000,50000,5):

        frequency = float(i)/10.0
        selected_freq = [value for value in freq_list if (value<(frequency+0.5) and value>=frequency)]

        
        if i == 7000:#updating index_begin and index_end
            index_end += len(selected_freq)
            continue
        else:
            index_begin = index_end
        index_end += len(selected_freq)
        #print("index begin: "+str(index_begin))
        #print("index end:"+str(index_end))

        #index end and begin are the ranges that we want to use for freq_list

        #getting random values:
        random_index = random.randrange(len(mjd))
        print(random_index)
        print("random mjd: "+str(mjd_list[random_index]))
        print("random freq: "+str(freq_list[random_index]))
        print("random intensity: "+str(intensity_list[random_index]))

        """
        print("value end:" +str(freq_list[index_end-1]))
        print("selected freq end:"+str(selected_freq[-1]))
        print("beginning:")
        print(freq_list[index_begin:index_begin+20])
        print(selected_freq[0:20])
        print("end:")
        print(freq_list[index_end-19:index_end])
        print(selected_freq[-20:-1])
        #print(freq_list[index_begin:index_end])
        #print(selected_freq)
        print("are the two lists equal?")#YES THEY'RE EQUAL!! WOOT WOOT
        print(len((freq_list[index_begin:index_end])))
        print(len(selected_freq))
        print(freq_list[index_begin:index_end]==selected_freq)
        """
        input("stop")

if __name__ == "__main__":
    username = input("Please enter SQL database username... ")
    password = input("Please enter SQL database password... ")
    cnx = pymysql.connect(user=username, password=password,
                            host='192.33.116.22',
                            database='jskipper')
	#cnx is connecting to the sql database
    cursor = cnx.cursor()
failed_list = []

frequency = []
mjd = []
intensity = []
#def read_csv_info(csv_name,lists*):

with open("Ryans_RFI_table_f_i_mjd.csv") as f:

    reader=csv.reader(f)
    for index,row in enumerate(reader):
        frequency.append(float(row[1]))
        intensity.append(float(row[2]))	
        mjd.append(float(row[0]))
        print("progress: "+str((index*100.0)/14000000.0)+"%")

print(frequency[0:10])
print(intensity[0:10])
print(mjd[0:10])
print(len(frequency))
print(len(intensity))
print(len(mjd))

get_rando_range(frequency,mjd,intensity)



