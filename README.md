# GBT_RFI_Analysis_Tool
A tool to analyze radio frequency interference data taken from the Green Bank Telescope. Assumes that we do not observe at frequencies below 245 MHz. 

## Installation Requirements:

Python 3.5+

All dependencies are included in the setup.py


## Prerequisites:

You should be in posession of reduced GBT RFI data in .txt format. It can either have a header in the format provided below or no header. Note that there will be less metadata available if the file contains no header. 

<details><summary> GBT RFI format for text files containing RFI data: </summary>



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

</details> 

### Note: 

The main general-use purpose of this code is in step 1, where the GBT RFI data are parsed and loaded into an SQL database. From there one can query the SQL database for whatever they like. Steps 2 onward calculate and graph some general-purpose statistics on the data which might be of use to those trying to characterize the RFI environment of their sample. One could also use SQL to create a subset of your data to then calculate statistics on using Steps 2 onwards.

## Step 1: Load RFI data into the database: 

Run RFI_input_for_SQL.py with the text files that you wish to use in the path. 

Run as: 
```console
RFI_input_for_SQL.py <main_table_name> <dirty_table_name> <filepath_to_RFI_scans> <Database_IP> <Database_name>
```

The required arguments are as follows:

1.) Main_table_name is the name you wish to give for your SQL table containing your primary, clean data. 

2.) Dirty_table_name is the name you wish to give for your SQL table containing any data the uploader finds that has flags or issues.

3.) Filepath_to_RFI_scans is the file path given to the directory containing all the text files of RFI scans you wish to analyze.

4. & 5.) Database_IP and database_name are the IP address location and name of the database to which you want to upload your processed data. Youl will be prompted for the credentials to access this database. 


## Step 2: Load statistical data using RFI_avgs_loader.py

Run this to get mean, median, etc and load it into a new table in the SQL database. 

Run as: 
```console
RFI_avgs_loader.py <table_to_read> <table_to_make> 
```

The required arguments are as follows: 

1.) Table_to_read is the table from which you want to calculate statistics (likely main_table_name from step 1) 

2.) Table_to_make is the table you want to make that will contain the statistics calculated. 


## Step 3: Process_graph_avgs.py

Run this to plot informational graphs on the statistical data calculated from step 2. 

Run as: 
```console
RFI_process_graph_avgs.py <avgs_table_to_read>
```

The required argument is as follows:

1.) Avgs_table_to_read is the table containing statistics from which you want to make plots (likely table_to_make from step 2). 

## Step 4: total_energy_calculator.py

Run this to calculate the total energy of the frequency range given by the text files in step 1. 


Run as: 
```console
total_energy_calculatory.py <full_data_table> <avgs_data_table>
```

The required arguments are as follows: 

1.) Full_data_table is the table containing all RFI data from which you want to calculate the total energy (likely main_table_name from step 1) 

2.) Avgs_data_table is the table containing all the RFI statistics from which you want to calculate the total energy (likely table_to_make from step 2). 


## Acknowledgements:
This uses LST_calculator.py, which is code obtained from another GitHub page and edited for my purposes. Here is the citation:

***************************************************************************************
    Title: SiderealTimeCalculator.py
    Author: Justine Haupt
    Date: 11/23/17
    Code version: v1.0
    Availability: https://github.com/jhaupt/Sidereal-Time-Calculator

***************************************************************************************

