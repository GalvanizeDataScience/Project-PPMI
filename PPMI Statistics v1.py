# PPMI Statistics Module
# Christian Bracher, July 2014

# (This is only a first draft - reads pickled data object, 
# understands data selection commands.  All output functionality is still hard-wired.)

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
    		print 'Unknown cohort:'

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
                selections.append([ev, tt])
                
    return cohorts, selections