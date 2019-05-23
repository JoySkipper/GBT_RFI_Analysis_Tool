"""
param frontend_aliases: used as a reference for various names given to our receivers, and changing them to a standardized set of names
param GBT_receiver_ranges: using the standardized set of receiver names, this contains the range of values for each receiver
"""

frontend_aliases = {
    'P1': 'Prime Focus 1',
    'RcvrPF_1': 'Prime Focus 1',
    'RcvrPF_': 'Prime Focus All',
    'Rcvr_342':'Rcvr_342',
    'Rcvr_450':'Rcvr_450',
    'Rcvr_600':'Rcvr_600',
    'Rcvr_800':'Rcvr_800',
    'Rcvr_1070':'Prime Focus 2',
    'RcvrPF_2':'Prime Focus 2',
    'P2':'Prime Focus 2',
    'RcvrArr': 'Array All',
    'RcvrArray1_2':'RcvrArray1_2',
    'Rcvr1_2': 'Rcvr1_2',
    'L1': 'Rcvr1_2',
    'Rcvr2_3': 'Rcvr2_3',
    'S1': 'Rcvr2_3',
    'Rcvr4_6': 'Rcvr4_8',
    'Rcvr4_8':'Rcvr4_8',
    'C1':'Rcvr4_8',
    'Rcvr8_1': 'Rcvr8_10',
    'Rcvr8_10':'Rcvr8_10',
    'X1': 'Rcvr8_10',
    'K1':'Kband All',
    'Rcvr12_': 'Rcvr12_18',
    'Rcvr12_18':'Rcvr12_18',
    'KU1': 'Rcvr12_18',
    'Ku1': 'Rcvr12_18',
    'RcvrArray18_26':'RcvrArray19_26',
    'RcvrArray19_26':'RcvrArray19_26',
    'Rcvr26_40':'Rcvr26_40',
    'Rcvr40_': 'Rcvr40_52',
    'Rcvr40_52':'Rcvr40_52',
    'Rcvr68_92':'Rcvr68_92',
    'Rcvr_MBA1_2':'Rcvr_MBA1_2',
    'RcvrArray75_115':'Rcvr75_115',
    '82':'Unknown',
    '83':'Unknown', 
    'L2':'Unknown'




}

GBT_receiver_ranges = { 
    'Rcvr_342':{'freq_min': 290.0,'freq_max': 395.0},
    'Rcvr_450':{'freq_min': 385.0,'freq_max': 520.0},
    'Rcvr_600':{'freq_min': 510.0,'freq_max': 690.0},
    'Rcvr_800':{'freq_min': 680.0,'freq_max': 920.0},
    'Prime Focus 1': {'freq_min': 290.0, 'freq_max': 920.0},
    'Prime Focus 2': {'freq_min': 910.0, 'freq_max': 1230.0},
    'Prime Focus All': {'freq_min': 290.0, 'freq_max': 1230.0},
    'Array All': {'freq_min':1200.0, 'freq_max':115300.0},
    'RcvrArray1_2':{'freq_min':1200.0,'freq_max':1600.0},
    'Rcvr1_2':{'freq_min':1150.0, 'freq_max':1730.0},
    'Rcvr2_3':{'freq_min':1730.0,'freq_max':2600.0},
    'Rcvr4_8':{'freq_min':3950.0, 'freq_max': 7800.0},
    'Rcvr8_10':{'freq_min':8000.0,'freq_max':11600.0},
    'Kband All':{'freq_min':12000.0,'freq_max':40000.0},
    'Rcvr12_18':{'freq_min':12000.0,'freq_max':15400.0},
    'RcvrArray19_26':{'freq_min':18000.0,'freq_max':27500.0},
    'Rcvr26_40':{'freq_min':26000.0,'freq_max':39500.0},
    'Rcvr40_52':{'freq_min':38200.0,'freq_max':49800.0},
    'Rcvr68_92':{'freq_min':67000.0,'freq_max':93300.0},
    'RcvrMBA1_2':{'freq_min':80000.0,'freq_max':100000.0},
    'RcvrArray75_115':{'freq_min':80000.0,'freq_max':115300.0},
    'Unknown':{'freq_min':290.0,'freq_max':115300.0}
}

