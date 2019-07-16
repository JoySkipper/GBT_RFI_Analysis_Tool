# Origin: 
The current version of this code lives on Joy Skipper's Github: 
https://github.com/JoySkipper/GBT_RFI_Analysis_Tool


# How to run the GBT RFI Analysis Tool

The GBT RFI Analysis tool is meant, at least at the moment, to be run specifically on GBT RFI through the jskipper database on the colossus machine at the Green Bank Observatory. Therefore, the credentials for jskipper and a connection to the GBO machines is needed for the code to work. The hope is to eventually have this code be more generalized, such that an SQL database can be made and used in any setting from any machine. This documentation will be updated accordingly when this occurs. 

## RFI_input_for_SQL.py

other scripts used: 
GBT_receiver_specs.py, 
fxns_output_process.py
LST_calculator.py 

Run as: 
```console
RFI_input_for_SQL.py <main_table_name> <dirty_table_name> <filepath_to_RFI_scans>
```

Where main_table_name is the name of the table to which you want to put all of your clean data. This should already exist in the jskipper database with all of the column names already filled for the script to work. 

Dirty_table_name is the name of the table to which you want to put any flagged data or data that doesn't fit into any of our known receivers. The same requirements are necessary as those for the main_table_name.

Filepath_to_RFI_scans is the path to the RFI scans that you wish to use to load into the database. These should be in the following format: 

  ```
  ################ HEADER #################
  # projid: TRFI_141109_X1
  # date: 2014-11-09
  # utc (hrs):        11.989722
  # mjd:        56970.500
  # lst (hrs):        9.9072678
  # scan_numbers:        1
  # frontend: Rcvr8_10
  # feed:            1
  # polarization: I
  # backend: Spectrometer
  # number_IF_Windows:        4
  # exposure (sec):        354.27933
  # tsys (K):       24.6196
  # frequency_type: TOPO
  # frequency_resolution (MHz):       0.82164538
  # source: rfiscan2
  # azimuth (deg):        182.49776
  # elevation (deg):        44.516684
  # units: Jy
  ################   Data  ################
  # Window   Channel Frequency(MHz)  Intensity(Jy)
          1         2       7.630781            NaN
          1         3       7.631172            NaN
          1         4       7.631563            NaN
          1         5       7.631953            NaN
          1         6       7.632344            NaN
          1         7       7.632734            NaN
          1         8       7.633125            NaN
          1         9       7.633516            NaN
  ```
Where Intensity can be either a NaN or a float.

You will be prompted for the username and password of the user on the colossus machine that holds these tables. It will then load the appropriate information into the tables. 

Once these are loaded, you'll need to export this database to a .txt file via phpMyAdmin before continuing. 

## RFI_avgs_loader.py 

other scripts used:  
fxns_output_process.py

This script reads a text file that was exported from an SQL database made by RFI_input_for_SQL.py. It then calculates various statistics (mean, median, 97th percentile, 2.75th percentile) and then reloads them into a new table in the same SQL database. 

Run as: 
```console
RFI_avgs_loader.py <table_to_read> <table_to_make> 
```
Where table_to_read is the .txt file of the exported database from which to calculate averages, and table_to_make is the name of the table in the SQL database meant to have the statistics. This table must exist in the database and also have the column names populated. 

## RFI_process_graph_avgs.py

other scripts used:  
fxns_output_process.py

This script takes data from the table made from RFI_avgs_loader.py and creates several graphs to show the nature of the RFI data. 

Run as: 
```console
RFI_process_graph_avgs.py <avgs_table_to_read>
```

Where avgs_table_to_read is the table from the database made from RFI_avgs_loader.py that contains the statistical information from the RFI data. 

## Total_energy_calculator.py 

other scripts used:  
fxns_output_process.py

This script calculates the total energy of the frequency range of the RFI data from the table specified. 

Run as: 
```console
total_energy_calculatory.py <full_data_table> <avgs_data_table>
```

Where "full_data_table" is the primary RFI table made in RFI_input_for_SQL.py and "avgs_data_table" is the RFI table with statistical information made from RFI_avgs_loader.py. 

This script returns a number, simply the total energy. 


