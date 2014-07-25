# PPMI Statistics Module
# Christian Bracher, July 2014

# (This is only a first draft - reads pickled data object, 
# understands data selection commands.  Output functionality no yet implemented here.)

# ******** METHODS:

# 
# Unpickle the PPMI data object:
# Restore subject list and conditions, event and test lists;
# return data as pandas Panel object:
#
#   First (item) coordinate:  Event
#   Second (major) coordnate:  Subject
#   Third (minor) coordinate:  Test 
# 
# Parameter:  File name & path for pickled data object
# Returns:
# subject_list - a list of all subject IDs
# subject_condition - a dictionary that lists the cohort (condition) by subject ID
# event_list - a list of all events (timeline of study)
# test_list - a list of all study tests stored in the data object (clear text)
# test_dict - a dictionary PPMI test code : clear text descriptor
# data_panel - three-dimensional pandas data object.

import pandas as pd
import numpy as np
import json as js
import pickle

def Unpickle_PPMI_data(filename = 'PPMI_data.pkl'):

	# Recover the pickled data:

	datafile = open(filename, 'rb')
	subject_list, subject_condition, event_list, test_list, test_dict, PPMI_array = pickle.load(datafile)
	datafile.close()

	# Create pandas Panel object:

	data_panel = pd.Panel(data = PPMI_array, items = event_list, major_axis = subject_list, minor_axis = test_list)

	return subject_list, subject_condition, event_list, test_list, test_dict, data_panel

# Create lists that indicate membership of study subjects to the three 'cohorts':
# 'HC' (healthy control), 'PD' (Parkinson's Disease), 'SWEDD' (scan w/o evidence of dopaminergic deficiency)
#
# Parameter:  subject ID list, Subject:Condition dictionary
# Returns:  Dictionary containing membership lists for HC, PD, SWEDD cohorts

def Create_cohort_filters(subject_list, subject_condition):
	
	# Membership templates:

	HC_filter = []
	PD_filter = []
	SWEDD_filter = []

	# Examine membership of individual subjects

	for subject in subject_list:
		if (subject_condition[subject] == 'HC'):
		 	HC_filter.append(True)
			PD_filter.append(False)
			SWEDD_filter.append(False)
		elif (subject_condition[subject] == 'PD'):
			HC_filter.append(False)
			PD_filter.append(True)
			SWEDD_filter.append(False)
		elif (subject_condition[subject] == 'SWEDD'):
			HC_filter.append(False)
			PD_filter.append(False)
			SWEDD_filter.append(True)
	
	# 'Zip' this information into a membership dictionary

	filter_dict = {'HC':HC_filter, 'PD':PD_filter, 'SWEDD':SWEDD_filter}

	return filter_dict

# Read instructions for test/subject/event selection from file (json format)
# (see separate instructions for format)
#
# Parameter:  File path & name
# Returns:
# cohorts - a list of the cohorts requested (some combination of 'HC', 'PD', 'SWEDD')
# selections - a list of the individual combinations of event and test requested,
#              in the form [[event1, test1], [event2, test2], ...]

def Extract_Information(fileinfo = '../PPMI Analysis/employdata.json'):
    
    # Open information file
    
    overview = open(fileinfo, 'r')
    contents = js.load(overview)['employdata']
    overview.close()
    
    # Read in cohort information stored in 'cohort' key, then remove
    
    cohorts = contents.pop('cohort', [])
   
    # Check validity:
    if (cohorts == []):
		print "ERROR:  No cohorts specified for analysis"
		raise ValueError

    for group in cohorts:
    	if not (group in ['HC', 'PD', 'SWEDD']):
    		print 'ERROR:  Unknown cohort ', group
    		raise ValueError

    # Build placeholder for selections from dataset
    
    selections = []
        
    # Read in information for each dataset - events and tests desired
    # Extract every combination of event and test
    # (Note:  Combinations formed separately for each entry in the information file)
    
    datasets = contents.keys()

    for entry in datasets:
        events = contents[entry]['events']
        tests =  contents[entry]['tests']
        
        for ev in events:
            for tt in tests:
            	selections.append((ev, tt))

    # Render selections unique:
    
    selections = list(set(selections))

    return cohorts, selections

# Extract desired data from general data storage object
# 
# Parameters:
# data_panel - the 3D storage object for PPMI data
# cohorts - list of subject cohorts to be included
# selections - list of event-test combinations to be included
# subject_list - list of all subject IDs
# subject_condition - dictionary of subject cohort membership
#
# Returns:
# subj_cond - series object containing condition (data) for each subject in table (index)
# data_table - dataframe containing test results in selection
#
# Requires:
# filter_dict - library of cohort membership filters
#

def Build_data_table(data_panel, cohorts, selections, subject_list, subject_condition):
	
	# Template for data table

	data_table = pd.DataFrame()

	# Populate data table with desired test/event combinations

	for group in selections:
		
		# Make sure test/event really exists:

		try:
			event_data = data_panel[group[0]][group[1]]
		except:
			print 'ERROR:  Unknown event or test ', group
			raise ValueError

		# Invent column name for combination:

		event_name = group[1] + ' [' + group[0] + ']'

		# Store data as column in table

		data_table[event_name] = event_data

	# Create a filter for cohorts - select all subjects in any of the cohorts listed
	    
	cohort_filter = [False for subject in subject_list]    
	
	# Read in global filter information:

	filter_dict = Create_cohort_filters(subject_list, subject_condition)

	# Determine union of membership lists

	for group in cohorts:
		cohort_filter = [i|j for i,j in zip(cohort_filter, filter_dict[group])]

	# Apply subject filter    
	    
	data_table = data_table[cohort_filter]    

	# Clean out subjects that have incomplete information for any test:

	subjects_complete = (data_table.notnull().all(axis = 1))
	data_table = data_table[subjects_complete]

	# Warn user if selection is empty:

	if (len(data_table) == 0):
		print 'WARNING:  No subjects available'

	# Retrieve list of subjects in this set, their condition:

	subjects_in_selection = data_table.index
	conditions_in_selection = [subject_condition[subj] for subj in subjects_in_selection]

	# Create a subject-condition dictionary in the form of a pandas Series object:

	subj_cond = pd.Series(conditions_in_selection, index = subjects_in_selection)

	return subj_cond, data_table