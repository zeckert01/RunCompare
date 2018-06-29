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

    from ROOT import TH2D,TCanvas,gROOT,TFile
    gROOT.SetBatch()
    # Definitions
    #ranges = [0,1,2,3]
    #shunts = [1,1.5,2,3,4,5,6,7,8,9,10,11,11.5]
    #plotBoundaries_slope = [0.28,0.33]
    plotBoundaries_offset = [1,16,100,800]
    plotBoundaries_slope = [5,-5]
    #plotBoundaries_offset = [0,0,0,0]
    

    # Histogram lists
    histOffset = []
    histSlope = []
    histShuntFactor = []
    
    # Canvas list
    c = []

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

    # Get Ranges
    ranges = cursor.execute("SELECT DISTINCT range FROM qieshuntparams").fetchall()

    # Get shunts
    shunts = cursor.execute("SELECT DISTINCT shunt FROM qieshuntparams").fetchall()

    # Loop over each uniqueID
    for nameList in idList:
        name = nameList[0]
        
        # Create output directory for images if not exist
        if not os.path.exists("%s%sImages"%(options.outDir,name)):
            os.makedirs("%s%sImages"%(options.outDir,name))

        # open root file for storing output histograms
        rootOut = TFile("%s/comparison_%s.root"%(options.outDir,name),"recreate")
        for ra in ranges:
            r = ra[0]
            for shu in shunts:
                sh = shu[0]
                if (r == 2 or r == 3) and (sh != 1):
                    continue
                
                # Fetch values of slope for each run
                slopes = cursor.execute("SELECT runDirectory,slope,\
                        (SELECT runDirectory FROM qieshuntparams\
                            WHERE id = p.id and range = p.range and shunt = p.shunt and capID = p.capID and runDirectory != p.runDirectory), \
                        (SELECT slope FROM qieshuntparams\
                            WHERE id = p.id and range = p.range and shunt = p.shunt and capID = p.capID and RunDirectory != p.RunDirectory)\
                        FROM qieshuntparams as p WHERE id = '%s' and shunt = %.1f and range = %d"%(name,sh,r)).fetchall()

                # Fetch values of offset for each run
                offsets = cursor.execute("SELECT runDirectory,offset,\
                        (SELECT runDirectory FROM qieshuntparams\
                            WHERE id = p.id and range = p.range and shunt = p.shunt and capID = p.capID and runDirectory != p.runDirectory),\
                        (SELECT offset FROM qieshuntparams\
                            WHERE id = p.id and range = p.range and shunt = p.shunt and capID = p.capID and RunDirectory != p.RunDirectory)\
                        FROM qieshuntparams as p WHERE id = '%s' and shunt = %.1f and range = %d"%(name,sh,r)).fetchall()

                shuntFactors = cursor.execute("SELECT runDirectory, \
                        (SELECT slope FROM qieshuntparams WHERE qie = p.qie and capID = p.capID and range = p.range and id = p.id and shunt = 1)/slope,\
                        (SELECT runDirectory FROM qieshuntparams\
                            WHERE id = p.id and range = p.range and shunt = p.shunt and capID = p.capID and runDirectory != p.runDirectory),\
                        (SELECT slope FROM qieshuntparams\
                            WHERE id = p.id and qie = p.qie and range = p.range and shunt = 1 and capID = p.capID and runDirectory != p.runDirectory)/\
                                (SELECT slope FROM qieshuntparams\
                                WHERE id = p.id and qie = p.qie and range = p.range and shunt = p.shunt and capID = p.capID and runDirectory != p.runDirectory)\
                        FROM qieshuntparams AS p WHERE id = '%s' and shunt = %.1f and range = %d"%(name,sh,r)).fetchall()

                # Fetch Max and minimum values for slope of shunt
                maxmin = cursor.execute("select max(slope),min(slope) from qieshuntparams where range=%i and shunt = %.1f and id = '%s';" % (r, sh,name)).fetchall()
                maximum, minimum = maxmin[0]
                maximumS = max(plotBoundaries_slope[1]/sh, maximum+0.01)
                minimumS = min(plotBoundaries_slope[0]/sh, minimum-0.01)

                # Create canvas for each shunt and range (TH2D)
                c.append(TCanvas("Card%sShunt%sRange%d"%(name,str(sh).replace(".",""),r),"hist"))
                c[-1].Divide(1,3)

                # Create histogram for the slopes
                histSlope.append(TH2D("Slope_sh:%s_r:%d"%(str(sh).replace(".",""),r),"%s Slope Shunt %.1f Range %i"%(name,sh,r),100,minimumS,maximumS,100,minimumS,maximumS))

                # Create histograms for offsets
                maxmin = cursor.execute("SELECT MAX(offset),MIN(offset) FROM qieshuntparams WHERE range = %i and shunt = %.1f and id = '%s';"%(r,sh,name)).fetchall()

                maximum,minimum = maxmin[0]
                maximumo = max(plotBoundaries_offset[r],maximum)
                minimumo = min(-1*plotBoundaries_offset[r],minimum)

                c[-1].cd(2)
                histOffset.append(TH2D("Offset_Sh%s_R%d"%(str(sh).replace(".",""),r),"%s Offset Shunt %.1f Range %d"%(name,sh,r),40,minimumo,maximumo,40,minimumo,maximumo))

                # Create Shunt Factor Histogram
                c[-1].cd(3)
                histShuntFactor.append(TH2D("ShuntFactor_Sh%s_R%d"%(str(sh).replace(".",""),r),"%s Shunt Factor Shunt %.1f Range %d"%(name,sh,r),40,sh-0.5,sh+0.5,40,sh-0.5,sh+0.5))

                # Fill histograms
                for valS in slopes:
                    runDir1,slope1,runDir2,slope2 = valS
                    histSlope[-1].GetXaxis().SetTitle(runDir1)
                    histSlope[-1].GetYaxis().SetTitle(runDir2)
                    histSlope[-1].Fill(slope1,slope2)
                    
                for valO in offsets:
                    runDir1,off1,runDir2,off2 = valO
                    histOffset[-1].GetXaxis().SetTitle(runDir1)
                    histOffset[-1].GetYaxis().SetTitle(runDir2)
                    histOffset[-1].Fill(off1,off2)

                for valF in shuntFactors:
                    runDir1, sf1, runDir2, sf2 = valF
                    histShuntFactor[-1].GetXaxis().SetTitle(runDir1)
                    histShuntFactor[-1].GetYaxis().SetTitle(runDir2)
                    histShuntFactor[-1].Fill(sf1,sf2)

                #c[-1].cd(1)
                #histSlope[-1].Draw("colz")
                histSlope[-1].Write()
                #c[-1].cd(2)
                #histOffset[-1].Draw("colz")
                histOffset[-1].Write()
                #c[-1].cd(3)
                #histShuntFactor[-1].Draw("colz")
                histShuntFactor[-1].Write()

                #c[-1].Write()
                #c[-1].Print("%s%sImages/%s_Shunt%s_Range%d"%(options.outDir,name,name,str(sh).replace(".",""),r))

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description = "Create comparison plots to compare calibrations of cards between runs")
    parser.add_argument('-d','--date', required=True, action="append", dest="date", help = "Enter date in the format MM-DD-YYYY (required)")
    parser.add_argument('-r','--run', required=True, action="append", dest="run", type=int, help="Enter run number. Ex: -r 1 -r 2 will compare run 1 and run 2")
    parser.add_argument('-o','--outDirectory',action="store", dest="outDir", default = "./", help = "Output directory. Default: current directory")
    parser.add_argument('-u','--uniqueID', action="append", dest = 'uid', help  = "NOT IMPLEMENTED Creates Summary Plots for a  file(s) based on Unique IDs list with -u [UniqueID] -u [UniqueID] -u [UniqueID] (format uniqueID as '0xXXXXXXXX_0xXXXXXXXX')")
    parser.add_argument('-a','--all', action="store_true", default = True, help = "SET BY DEFAULT Run over all cards in each run")

    options = parser.parse_args()
    runCompare(options)
