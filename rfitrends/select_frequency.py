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
query = (" SELECT Frequency FROM Ryans_RFI_table; ")

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

print("fetching data...")


frequency = gather_list(cursor,query)
print(max(frequency))
print(min(frequency))

print("data fetched")

#frequency_float = np.array(frequency, dtype=np.float32)
print("sorting list...")
#sorted_f_float = frequency.sort
sorted_array = np.array(frequency)
print(sorted_array) 

#filtered_array = np.array(filter(lambda x:x>3000.0 and x<4000.0, sorted_array))
#print(filtered_array)

value_previous = 2900.0
for value in (np.sort(sorted_array)):
    if value < 2900.0: 
        continue
    if abs(value - value_previous) > 100.0:
        print(value_previous)
        print(value)
    value_previous = value


	