###_________________________________________________________###

#  Code Name: RFI_input_for_SQL.py

#  Code Purpose: To calculate the total energy of the frequency range desired using the regular SQL database as well as the SQL_avgs database

#  For any questions please contact Joy Nicole Skipper at jskipper@nrao.edu

###_________________________________________________________###
################################################################################################################################################################################################################################


print("running total energy calculator")
print("importing values...")
import numpy as np
import math
import fxns_output_process
import pymysql
import random
import csv
import sys


def total_NRG_calc(full_data_table,avgs_data_table):
    total_intensity = []
    total_frequency = []
    mean_intensity = []
    median_intensity = []
    avg_frequency = []

    with open("Ryans_RFI_table_f_i_mjd.csv") as f:

        reader=csv.reader(f)
        for index,row in enumerate(reader):
            total_frequency.append(float(row[1])*1000.0) #converting to Hz
            total_intensity.append(float(row[2]))	
            print("progress: "+str((index*100.0)/14000000.0)+"%")

        f.close()


    with open("RFI_Avgs.csv") as f:

        reader=csv.reader(f)
        for index,row in enumerate(reader):
            avg_frequency.append(float(row[0])*1000.0) # Converting to Hz
            mean_intensity.append(float(row[1]))	
            median_intensity.append(float(row[4]))
            print("progress: "+str((index*100.0)/780278.0)+"%")

        f.close()


    #print(str(len(np.diff(frequency))))
    #print(str(len(mean_intensity[:-1])))  
    print("calculating mean flux times delta nu")
    mean_flux_times_delta_nu = [a*b for a,b in zip(mean_intensity[:-1],np.diff(avg_frequency))]  
    print("calculating median flux times delta nu")
    median_flux_times_delta_nu = [a*b for a,b in zip(median_intensity[:-1],np.diff(avg_frequency))]  
    print("calculating total flux times delta nu")
    total_flux_times_delta_nu = [a*b for a,b in zip(total_intensity[:-1],np.diff(total_frequency))]
    #print(mean_flux_times_delta_nu)
    #input("stop")
    total_NRG_mean = sum(mean_flux_times_delta_nu)*0.70*7853.98*math.pow(10,-26)
    total_NRG_median = sum(median_flux_times_delta_nu)*0.70*7853.98*math.pow(10,-26)
    total_NRG = sum(total_flux_times_delta_nu)*0.70*7853.98*math.pow(10,-26)
    print("total mean energy: "+str(total_NRG_mean))
    print("total median energy: "+str(total_NRG_median))
    print("total energy: "+str(total_NRG))
    

    #cnx.close()


if __name__ == "__main__":
    full_data_table = sys.argv[1]
    avgs_data_table = sys.argv[2]
    print("starting main function of total energy calculator")
    total_NRG_calc(full_data_table,avgs_data_table)