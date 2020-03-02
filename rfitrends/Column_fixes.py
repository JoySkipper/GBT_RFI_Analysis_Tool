"""
.. module:: Column_fixes.py
    :synopsis: streamlines multiple formats of GBT RFI data into one, consistent format
.. moduleauthor:: Joy Skipper <jskipper@nrao.edu>
Code Origin: https://github.com/JoySkipper/GBT_RFI_Analysis_Tool
"""

# Various column names we can get, streamlining to one format
Column_name_corrections = {
    "Frequency(MHz)": "Frequency_MHz",
    "Frequency (MHz)": "Frequency_MHz",
    "Frequency(GHz)": "Frequency_MHz",
    "Frequency GHz)": "Frequency_MHz",
    "Intensity(Jy)": "Intensity_Jy",
    "Intensity (Jy)":"Intensity_Jy",
    "Window": "Window",
    "IFWindow":"Window",
    "Channel":"Channel"
}

