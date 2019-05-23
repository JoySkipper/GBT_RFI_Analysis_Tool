###_________________________________________________________###

#  Code Name: RFI_input_for_SQL.py

#  Code Purpose: To take data from regular SQL database, calculate averages and statistics, and load it into SQL-avgs database. 

#  For any questions please contact Joy Nicole Skipper at jskipper@nrao.edu

###_________________________________________________________###
################################################################################################################################################################################################################################



import csv
import numpy as np
import pymysql
import math
import fxns_output_process



def calculate_avgs_load_into_database():
    """
    Takes data from the main SQL database table, calculates the averages of that main table, 
    and then creates an averaged table and loads it back into the SQL database
    """

    table_to_read = "Ryans_RFI_table_expanded_f_i_sorted.txt"
    table_to_make = "RFI_Avgs_expanded"

    cursor,cnx = fxns_output_process.connect_to_database()


    with open(table_to_read) as f:
        reader=csv.reader(f)
        cached_frequency = 0.00
        cached_intensity = np.array([])
        number_of_repeat_frequencies = 0
        
        for index,row in enumerate(reader):
            #Row 0 is just both the frequency and intensity separated by a space. I'm splitting those two into frequency and intensity
            frequency = float(row[0].split(" ")[0])
            intensity = float(row[0].split(" ")[1])
            print(frequency)
            #math.isclose sees which list of frequencies are the same to 1e-9 (basically almost the same frequencies. We have multiple intensity values for each Frequency)
            #We then calculate the max, min, etc statistics for those intensities of the same frequencies
            if math.isclose(cached_frequency,frequency)or (cached_frequency) == 0.00:
                
                cached_frequency = frequency 
                cached_intensity = np.append(cached_intensity,intensity)
                number_of_repeat_frequencies += 1
            else: 
                
                average_intensity = np.average(cached_intensity)
                max_intensity = np.max(cached_intensity)
                min_intensity = np.min(cached_intensity)
                median_intensity = np.median(cached_intensity)
                low_percentile_intensity = np.percentile(cached_intensity,2.75)
                high_percentile_intensity = np.percentile(cached_intensity,97.5)
                print("progress: "+str((index*100.0)/14000000.0)+"%")

                #try: 
                add_values = "INSERT INTO "+str(table_to_make)+" (Frequency,mean_intensity,max_intensity,min_intensity,median_intensity,low_percentile_intensity,high_percentile_intensity) VALUES (\""+f"{cached_frequency:.6f}"+"\",\""+str(average_intensity)+"\",\""+str(max_intensity)+"\",\""+str(min_intensity)+"\",\""+str(median_intensity)+"\",\""+str(low_percentile_intensity)+"\",\""+str(high_percentile_intensity)+"\")"
        
                    

                #creating SQL table of RFI_Avgs
                cursor.execute(add_values)

                cached_intensity = np.array([])
                cached_frequency = frequency
                number_of_repeat_frequencies = 0

                cached_intensity = np.append(cached_intensity,intensity)
                number_of_repeat_frequencies += 1

	

if __name__ == "__main__":
    calculate_avgs_load_into_database



