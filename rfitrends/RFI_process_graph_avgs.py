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

print("starting script...")


print("connecting to database...")
username = input("Please enter SQL database username... ")
password = input("Please enter SQL database password... ")
cnx = pymysql.connect(user=username, password=password,
                              host='192.33.116.22',
                              database='jskipper')
#cnx is connecting to the sql database
cursor = cnx.cursor()

print("fetching data...")
query = (" SELECT * FROM RFI_Avgs_expanded; ")
#query1 =(" SELECT Frequency,mean_intensity FROM RFI_Avgs; ") 
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
	
	


print("starting graphs...")

"""
print("frequency: "+str(frequency[0:10]))
print("mean intensity: "+str(mean_intensity[0:10]))
print("max intensity: "+str(max_intensity[0:10]))
print("min_intensity: "+str(min_intensity[0:10]))
print("median intensity: "+str(median_intensity[0:10]))
print("low percentile: "+str(low_percentile_intensity[0:10]))
print("high percentile: "+str(high_percentile_intensity[0:10]))
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
plt.show()

plt.clf()


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

plt.show()



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
plt.yscale('log')
plt.xlim(600.00,700.0)
plt.show()

plt.clf()



