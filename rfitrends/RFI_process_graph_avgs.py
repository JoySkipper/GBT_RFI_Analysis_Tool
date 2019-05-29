###_________________________________________________________###

#  Code Name: RFI_process_graph_avgs.py

#  Code Purpose: To take the data from the SQL-Avgs database and make appropriate graphs for display

#  For any questions please contact Joy Nicole Skipper at jskipper@nrao.edu

###_________________________________________________________###
################################################################################################################################################################################################################################


print("Importing packages...")
import pymysql
import numpy as np
import matplotlib.pyplot as plt
import fxns_output_process



def load_data():
    """
    Loads data from the RFI_Avgs_expanded table in the SQL database for RFI
    returns: frequency: list of frequencies
    returns: mean_intensity: list of mean intensities
    returns: max_intensity: list of max intensities
    returns: min_intensity: list of min intensities
    returns: median intensity: list of median intensities
    returns: low_percentile_intensity: list of 2nd percentile intensities
    returns: high_percentile_intensity: list of 97th percentile intensities
    """
    cursor,cnx = fxns_output_process.connect_to_database()

    print("fetching data...")
    query = (" SELECT * FROM RFI_Avgs_expanded; ")
    cursor.execute(query)

    frequency = []
    mean_intensity = []
    max_intensity = []
    min_intensity = []
    median_intensity = []
    low_percentile_intensity = []
    high_percentile_intensity = []

    print("processing data...")
    result = cursor.fetchall() #getting each row
    

    for row in result:
        
        frequency.append(float(row[0]))
        mean_intensity.append(row[1])
        max_intensity.append(row[2])
        min_intensity.append(row[3])
        median_intensity.append(row[4])
        low_percentile_intensity.append(row[5])
        high_percentile_intensity.append(row[6])
    
    return frequency,mean_intensity,max_intensity,min_intensity,median_intensity,low_percentile_intensity,high_percentile_intensity
	
	



def log_y_axis_graph(frequency,mean_intensity,max_intensity,min_intensity,median_intensity,low_percentile_intensity,high_percentile_intensity):
    """
    Graphs intensity vs frequency with the y-axis in log-scale
    param: frequency: list of frequencies
    param: mean_intensity: list of mean intensities
    param: max_intensity: list of max intensities
    param: min_intensity: list of min intensities
    param: median intensity: list of median intensities
    param: low_percentile_intensity: list of 2nd percentile intensities
    param: high_percentile_intensity: list of 97th percentile intensities
    """
    print("Making graph with log y-axis...")
    plt.plot(frequency,max_intensity, color="red",label='max or min')
    plt.plot(frequency,min_intensity, color="red")
    # These next two lines will plot the 2.75 and 97.5 percentiles, i.e. showing us the range that encompasses 95% of the data
    plt.plot(frequency,low_percentile_intensity, color="magenta",label='high or low percentiles (2.75 or 97.5)')
    plt.plot(frequency,high_percentile_intensity, color="magenta")
    plt.plot(frequency,mean_intensity, color="blue",label='mean')
    # since these are Gaussian random variables the mean and median will be nearly equal
    plt.plot(frequency,median_intensity, color="green",label='median')
    plt.legend(loc='upper right')
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("log(Intensity) (Jy)")
    plt.yscale('log')
    plt.title("Frequency vs. Intensity (Log Version)")
    plt.show()
    plt.clf()

def lin_y_axis_graph(frequency,mean_intensity,max_intensity,min_intensity,median_intensity,low_percentile_intensity,high_percentile_intensity):
    """
    Graphs intensity vs frequency with the y-axis in linear scale
    param: frequency: list of frequencies
    param: mean_intensity: list of mean intensities
    param: max_intensity: list of max intensities
    param: min_intensity: list of min intensities
    param: median intensity: list of median intensities
    param: low_percentile_intensity: list of 2nd percentile intensities
    param: high_percentile_intensity: list of 97th percentile intensities
    """
    print("Making graph with linear y-axis...")
    plt.plot(frequency,max_intensity, color="red",label='max or min')
    plt.plot(frequency,min_intensity, color="red")
    # These next two lines will plot the 2.75 and 97.5 percentiles, i.e. showing us the range that encompasses 95% of the data
    plt.plot(frequency,low_percentile_intensity, color="magenta",label='high or low percentiles (2.75 or 97.5)')
    plt.plot(frequency,high_percentile_intensity, color="magenta")
    plt.plot(frequency,mean_intensity, color="blue",label='mean')
    # since these are Gaussian random variables the mean and median will be nearly equal
    plt.plot(frequency,median_intensity, color="green",label='median')
    plt.legend(loc='upper right')
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Intensity (Jy)")
    plt.title("Frequency vs. Intensity (Linear Version)")
    plt.show()
    plt.clf()


def log_y_axis_lim_graph(frequency,mean_intensity,max_intensity,min_intensity,median_intensity,low_percentile_intensity,high_percentile_intensity):
    """
    Graphs intensity vs frequency with the y-axis in log-scale, and the frequency range only from 600-700 MHz
    param: frequency: list of frequencies
    param: mean_intensity: list of mean intensities
    param: max_intensity: list of max intensities
    param: min_intensity: list of min intensities
    param: median intensity: list of median intensities
    param: low_percentile_intensity: list of 2nd percentile intensities
    param: high_percentile_intensity: list of 97th percentile intensities
    """
    print("Making graph with log y-axis 600-700 MHz...")
    plt.plot(frequency,max_intensity, color="red",label='max or min')
    plt.plot(frequency,min_intensity, color="red")
    # These next two lines will plot the 2.75 and 97.5 percentiles, i.e. showing us the range that encompasses 95% of the data
    plt.plot(frequency,low_percentile_intensity, color="magenta",label='high or low percentiles (2.75 or 97.5)')
    plt.plot(frequency,high_percentile_intensity, color="magenta")
    plt.plot(frequency,mean_intensity, color="blue",label='mean')
    # since these are Gaussian random variables the mean and median will be nearly equal
    plt.plot(frequency,median_intensity, color="green",label='median')
    plt.legend(loc='upper right')
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("log(Intensity) (Jy)")
    plt.title("Frequency vs Intensity (Log, 600-700 MHz only)")
    plt.yscale('log')
    plt.xlim(600.00,700.0)
    plt.show()
    plt.clf()



if __name__ == "__main__":
    print("starting script...")
    frequency,mean_intensity,max_intensity,min_intensity,median_intensity,low_percentile_intensity,high_percentile_intensity = load_data()
    print("starting graphs...")
    log_y_axis_graph(frequency,mean_intensity,max_intensity,min_intensity,median_intensity,low_percentile_intensity,high_percentile_intensity)
    lin_y_axis_graph(frequency,mean_intensity,max_intensity,min_intensity,median_intensity,low_percentile_intensity,high_percentile_intensity)
    log_y_axis_lim_graph(frequency,mean_intensity,max_intensity,min_intensity,median_intensity,low_percentile_intensity,high_percentile_intensity)