'''
Created on Jul 30, 2015

@author: sxm063

This module is used to export data from a python list (array) to a comma separated value (.csv) file
This module is used in PowerSynth to export performance values of all the generated solutions 
(or layout designs) to a csv file for viewing in excel or notepad.
'''

import os
import csv
import numpy
from PySide import QtGui

# Function to condition data into a list and and export it from python to csv
# Purpose of this function is to export the performance values of all the generated solutions (or layout designs) to a csv file for viewing in excel or notepad.
# This function is called from save_solution_set() in graph_app.py module
def py_csv(data, names_units, tgt_file_name):
    
    # hardcode data if input list is empty (in case solutions were not generated):
    if data:
        sheet_title = "All Generated Solutions"
    else:
        sheet_title = "Dummy Data"
        data = [[0,0,0,0,0],[1,1.1,1.01,1.001,1.001],[2,2.2,2.22,2.222,2.2222]] # dummy data with numbers and words
        names_units = [("lower gate loop inductance","nH"),("upper gate loop inductance","nH"),("max temp","deg C")]
            
    # remove trailing decimal places in data by limiting to two decimal places:
    for i in range(len(data)):
        data[i] = ["%.2f" % item for item in data[i]] # data stored as numbers but decimals removed if zeroes
    
    # convert list to array, transpose, and convert back to list:
    data = numpy.asarray(data).T.tolist()
    
    # append layout ID as the first element in each row (to identify each unique layout):   
    for i in range(len(data)):
        data[i].insert(0,'Layout '+str(i+1))
    
    # format names_units list for aesthetics: 
    for i in range(len(names_units)):
        names_units[i] = names_units[i][0] + ' (' + names_units[i][1] + ')'
    
    # insert blank space as first element of names_units (header) to represent the corner of the table
    names_units.insert(0,'')
    
    # insert column headers (names_units) row above data table: 
    data.insert(0,names_units)
    
    # insert page title above compiled data table: 
    data.insert(0,[sheet_title])
   
    # send final list of lists data to be converted to csv file named tgt_file_name:
    write_matrix_to_csv(data, tgt_file_name)
    
    # delete existing lists so that new ones can be created with the same name
    del data
    del names_units [:] # I don't know how this works; it just does!
    
    # inform user that file export operation is complete:
    if sheet_title != "Dummy Data":
        QtGui.QMessageBox.about(None, "Save as CSV", 
                            "Data export successful. \n"
                            "Location: \n" 
                            + os.path.abspath(tgt_file_name))
    else:
        QtGui.QMessageBox.about(None, "Save as CSV", 
                            "Data export not successful. Dummy data loaded. \n"
                            "Location: \n" 
                            + os.path.abspath(tgt_file_name))

        
# Function to write list elements into rows in a csv file
# Purpose of this function is open a csv file, write the performance values of all the generated solutions (or layout designs), and then close the file
# This function is called from py_csv() in py_csv.py module
def write_matrix_to_csv(data, tgt_file_name):
    
    # for developer (display data on console):
    '''print "Data to be exported:"
    for i in data:
        print i'''
        
    # open file and write rows into csv file; close file: 
    with open(tgt_file_name, 'wb') as csv_file: 
        writer = csv.writer(csv_file)  
        writer.writerows(data) 
    csv_file.close() # Always remember to close the file
    
    # for developer (may be commented):
    print("File closed?", csv_file.closed) 
    print("Location: ", os.path.abspath(tgt_file_name)) 
    print("Export completed") 

    
#if __name__ == "__main__":
#    py_csv([],[],"newdata02.csv", "C:\Users\sxm063\workspace\Sandbox\src\powercad\export")
#    print "main completed"
    
