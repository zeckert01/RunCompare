#!/usr/bin/env python
####################################
# runCompare.py
# Create comparison plots to compare 
# calibrations of cards between runs
#
# Author: Zach Eckert
# Created 06-28-2018
####################################
import sqlite3
import pprint
import glob
import os
import sys
import sys
import argparse
from MergeDatabases import MergeDatabases


def runCompare(options):

    from ROOT import *
    gROOT.SetBatch()
    # Definitions
    ranges = [0,1,2,3]
    shunts = [1,1.5,2,3,4,5,6,7,8,9,10,11,11.5]

    # Histogram lists
    histOffset = []
    histSlope = []
    histShuntFactor = []

    # determine which cards to compare
    files = []
    for date in options.date:
        for run in options.run:
            files.extend(glob.glob("data/%s/Run_%d/qieCalibrationParameters*.db"%(date,run)))

    # Merge databases for ease of analysis
    if not os.path.exists(options.outDir):
        os.makedirs(options.outDir)
    MergeDatabases(files,options.outDir,"compareRunsMerged.db")

    # Connect to database
    database = sqlite3.connect("%scompareRunsMerged.db"%options.outDir)
    cursor = database.cursor()

    # Get list of uniqueID's
    idList = cursor.execute("SELECT DISTINCT id FROM qieshuntparams").fetchall()

    # Loop over each uniqueID
    for nameList in idList:
        name = nameList[0]
        
        # Create output directory for images if not exist
        if not os.path.exists("%s%sImages"%(options.outDir,name)):
            os.makedirs("%s%sImages"%(options.outDir,name))

        # open root file for storing output histograms
        rootOut = TFile("%s/comparison_%s.root"%(options.outDir,name))
        for r in ranges:
            for sh in shunts:
                if (r == 2 or r == 3) and (sh != 1):
                    continue
                
                # Fetch values of slope for each run
                slopes = cursor.execute("SELECT slope, (SELECT slope FROM qieshuntparams WHERE id = p.id and range = p.range and shunt = p.shunt and capID = p.capID and RunDirectory != p.RunDirectory) FROM qieshuntparams as p WHERE id = '%s' and shunt = %.1f and range = %d"%(name,sh,r)).fetchall()

                # Fetch values of offset for each run
                offsets = cursor.execute("SELECT offset, (SELECT offset FROM qieshuntparams WHERE id = p.id and range = p.range and shunt = p.shunt and capID = p.capID and RunDirectory != p.RunDirectory) FROM qieshuntparams as p WHERE id = '%s' and shunt = %.1f and range = %d"%(name,sh,r)).fetchall()



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description = "Create comparison plots to compare calibrations of cards between runs")
    parser.add_argument('-d','--date', required=True, action="append", dest="date", help = "Enter date in the format MM-DD-YYYY (required)")
    parser.add_argument('-r','--run', required=True, action="append", dest="run", type=int, help="Enter run number. Ex: -r 1 -r 2 will compare run 1 and run 2")
    parser.add_argument('-o','--outDirectory',action="store", dest="outDir", default = "./", help = "Output directory. Default: current directory")
    parser.add_argument('-u','--uniqueID', action="append", dest = 'uid', help  = "NOT IMPLEMENTED Creates Summary Plots for a  file(s) based on Unique IDs list with -u [UniqueID] -u [UniqueID] -u [UniqueID] (format uniqueID as '0xXXXXXXXX_0xXXXXXXXX')")
    parser.add_argument('-a','--all', action="store_true", default = True, help = "SET BY DEFAULT Run over all cards in each run")

    options = parser.parse_args()
    runCompare(options)
