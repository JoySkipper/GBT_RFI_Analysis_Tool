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
	cursor = connection_call
	cursor.execute(query)


	value_list = []


	row = cursor.fetchone() #getting each row
 
	while row is not None:
	#print(row)
		row = cursor.fetchone()
		try:
			value_list.append(float(row[0]))
		except: continue

	return(value_list)

"""
def read_csv_info(csv_name):

    with open(csv_name) as f:
        reader=csv.reader(f)
        energy_total = 0.0
        for index,row in enumerate(reader):
            frequency = float(row[0])
            intensity = float(row[1])		
            energy = intensity*0.70*7863.98 #multiplying by 70% of the area of the dish (aperture efficiency)
            energy_total += energy



            print("progress: "+str((index*100.0)/14000000.0)+"%")

    return(energy_total)
"""

"""
def total_energy(intensity):
    energy_total = 0.0
    for index,value in enumerate(intensity):
        energy = value*0.70*7863.98 #multiplying by 70% of the area of the dish (aperture efficiency)
        energy_total += energy

    return(energy_total)


def total_energy_from_file(connection_call):
    csv_name = input("What is the file for which you are calculating the total energy (press enter if you want to use /users/jskipper/Documents/scripts/RFI/Ryans_RFI_table_f_i.csv):")
    if csv_name == '':
        total_energy = read_csv_info("/users/jskipper/Documents/scripts/RFI/Ryans_RFI_table_f_i.csv")
    else:
        total_energy = read_csv_info(csv_name)
    return(total_energy)
"""

def isSorted(x, key = lambda x: x): 
    return all([key(x[i]) <= key(x[i + 1]) for i in range(len(x) - 1)])
"""
def get_rando_range(freq_list,mjd_list,intensity_list):
    index_begin = 0
    index_end = 0
    for i in range(7000,50000,5):

        frequency = float(i)/10.0
        selected_freq = [value for value in freq_list if (value<(frequency+0.5) and value>=frequency)]

        
        if i == 7000:#updating index_begin and index_end
            index_end += len(selected_freq)
            #print("index begin: "+str(index_begin))
            #print("index end:"+str(index_end))
            #print("value end:"+str(freq_list[index_end]))
            #print("selected freq end:"+str(selected_freq[-1]))
            #print(freq_list[index_begin:index_begin+20])
            #print(selected_freq[0:20])
            continue
        else:
            index_begin = index_end
        index_end += len(selected_freq)
        #index end and begin are the ranges that we want to use for freq_list

        #getting random values:
        random_index = random.randrange(len(mjd))
        print(random_index)
        print("random mjd: "+str(mjd_list[random_index]))
        print("random freq: "+str(freq_list[random_index]))
        print("random intensity: "+str(intensity_list[random_index]))


        #print("index begin: "+str(index_begin))
        #print("index end:"+str(index_end))
        print("value end:" +str(freq_list[index_end-1]))
        print("selected freq end:"+str(selected_freq[-1]))
        print("beginning:")
        print(freq_list[index_begin:index_begin+20])
        print(selected_freq[0:20])
        print("end:")
        print(freq_list[index_end-20:index_end])
        print(selected_freq[-20:-1])
        #print(freq_list[index_begin:index_end])
        #print(selected_freq)
        print("are the two lists equal?")
        print(len((freq_list[index_begin:index_end])))
        print(len(selected_freq))
        print(freq_list==selected_freq)
"""
        
       

"""
def get_rando(freq_list,intensity_list,mjd_list):
    for i in range(100):
        rando_choice = random.choice(mjd)
        mjd_rando.append(rando_choice)
        index = mjd.index(rando_choice)
        frequency_rando.append(frequency[index])
        intensity_rando.append(intensity[index])
        NRG = total_energy(intensity_rando)
"""
"""
def time_series_data(connection_call):
    mjd_rando = []
    frequency_rando = []
    intensity_rando = []
    frequency_query = ("SELECT frequency from Ryans_RFI_table")
    intensity_query = ("SELECT intensity from Ryans_RFI_table")
    mjd_query = ("SELECT mjd from Ryans_RFI_table")
    print("gathering list frequency...")
    frequency = gather_list(connection_call,frequency_query)
    print("gathering list intensity...")
    intensity = gather_list(connection_call,intensity_query)
    print("gathering list mjd...")
    mjd = gather_list(connection_call,mjd_query)
    print("selecting random choice...")
    get_rando_range(frequency)


    return NRG
"""
