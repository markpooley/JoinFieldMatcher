# !/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Name          : Join Field Matcher
# Author  		: Mark Pooley (mark-pooley@uiowa.edu)
# Link    		: http://www.ppc.uiowa.edu
# Date    		: 2015-04-14 15:18:14
# Version		: $1.0$
# Description	: Takes non matching Name fields and creates a new field to join the table to the
# fc with.
#-------------------------------------------------------------------------------------------------

###################################################################################################
#Import python modules
###################################################################################################}
import os
import arcpy
from arcpy import env
from fuzzywuzzy import fuzz,process

###################################################################################################
#Input Variable loading and environment declaration
###################################################################################################
FC = arcpy.GetParameterAsText(0)
FC_Field = arcpy.GetParameterAsText(1)
table = arcpy.GetParameterAsText(2)
table_Field = arcpy.GetParameterAsText(3)
###################################################################################################
# Add necessary fields for the process.
###################################################################################################
arcpy.SetProgressor('step','Adding "JoinName" to {0}...'.format(table),0,1,1)
arcpy.AddField_management(table,'JoinName',"TEXT")
arcpy.AddField_management(table,'JoinCity',"TEXT")
arcpy.AddField_management(table,'JoinMatchScore',"SHORT")

###################################################################################################
#Build a list of the MSA Names from the FC data
###################################################################################################
MSAs = []
featureCount = int(arcpy.GetCount_management(FC).getOutput(0))
arcpy.SetProgressor('step','building list of MSAs from {0}...'.format(FC),0,featureCount,1)
with arcpy.da.SearchCursor(FC,FC_Field) as cursor:
	for row in cursor:
		MSAs.append(row[0])
		arcpy.SetProgressorPosition()
arcpy.AddMessage('{0} MSAs found in {1}'.format(len(MSAs),FC))

###################################################################################################
#Match the best options found in the FC data to the TAble data
###################################################################################################
featureCount = int(arcpy.GetCount_management(table).getOutput(0))
arcpy.SetProgressor('step','Finding MSAs for {0}...'.format(table),0,featureCount,1)
unMatched = 0
with arcpy.da.UpdateCursor(table,[table_Field,'JoinName','JoinMatchScore']) as cursor:
	for row in cursor:

		#Extract best options for current entry
		loc = process.extractOne(row[0].lower(),MSAs)

		#check that accuracy/macth score is suitable and update rows
		if loc[1] >= 90:
			row[1] = loc[0]
			row[2] = loc[1]

			arcpy.SetProgressorLabel('Match found for {0}'.format(row[0]))
			cursor.updateRow(row)

		else:
			arcpy.SetProgressorLabel('Match score too low for {0}...'.format(row[0]))
			pass

		arcpy.SetProgressorPosition()

###################################################################################################
#Find the stragglers that couldn't be matched one way
###################################################################################################
query = "JoinMatchScore IS NULL"
arcpy.SetProgressor('step','Attempting to find best fit for unMatched',0,unMatched,1)
with arcpy.da.UpdateCursor(table,[table_Field,'JoinName','JoinMatchScore'],query) as cursor:
	for row in cursor:

		#find index of the comma to separate out the city and state
		n = row[0].find(',')
		cit = row[0][:n]
		st = row[0][n:]

		#Extract the best options
		opts = process.extract(cit,MSAs)

		#Iterate through the options to hopefully find a suitable match
		#---------------------------------------------------------------------------
		for j in opts:

			#splice J at comma to separate city and state
			cit1 = j[0][:j[0].find(',')]
			st1 = j[0][j[0].find(','):]

			#check that both are in the current option
			if cit in cit1 and st in st1:

				#update rows
				row[1] = j[0]
				row[2] = 100
				cursor.updateRow(row)
				arcpy.SetProgressorPosition()
			else:
				pass

####################################################################################################
#process complete
####################################################################################################
arcpy.AddMessage("Process complete!")
