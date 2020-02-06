"""
..module:: manage_missing_cols.py
    :synopsis: Takes in a dictionary containing the data for a single line of RFI data, and fills in NaN for any columns missing data. 
..moduleauthor:: JoySkipper <jskipper@nrao.edu>
Code Origin: https://github.com/JoySkipper/GBT_RFI_Analysis_Tool
"""

class manage_missing_cols: 
    # Takes in data_entry, a dictionary containing the data for a single line of RFI data
    
    def __init__(self, data_entry):
        self.data_entry = data_entry
        self.setcolumn("Window")
        self.setcolumn("Channel")

    def setcolumn(self,column_name):
        if column_name not in self.data_entry: 
            self.data_entry[column_name] = "NaN"

    def getdata_entry(self):
        return self.data_entry
        