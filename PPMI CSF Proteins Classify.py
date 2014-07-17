# Machine Learning with PPMI Data
# (last Tuesday - this is just a proof of concept, to be extended & improved)
#
# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# <codecell>

fileinfo = 'Desktop/PPMI Data/Biospecimen_Analysis/Biospecimen_Analysis_Results.csv'
biodata_raw = pd.io.parsers.read_table(fileinfo, sep =',', header = 0, index_col = False)
biodata_columns = biodata_raw.columns.values.tolist()

# <codecell>

fileinfo = 'Desktop/PPMI Data/Biospecimen_Analysis/Pilot_Biospecimen_Analysis_Results_Projects_101_and_103.csv'
biodata2_raw = pd.io.parsers.read_table(fileinfo, sep =',', header = 0, index_col = False)
biodata2_columns = biodata2_raw.columns.values.tolist()

# <codecell>

biodata  = biodata_raw[biodata_columns[0:9]]
biodata2 = biodata2_raw[biodata2_columns[0:9]]

# <codecell>

allbiodata = pd.concat([biodata, biodata2])

# <codecell>

def Discard_obsolete_data(database):
    
    # This method eliminates obsolete database entries for laboratory tests that have been redone.
    
    testlist = database.sort(['PATNO', 'CLINICAL_EVENT', 'TYPE', 'TESTNAME', 'RUNDATE'], ascending = False) 
    
    comparelist = testlist[['PATNO', 'CLINICAL_EVENT', 'TYPE', 'TESTNAME']]
    
    test_size = len(testlist)
    row_keep = []
    last_entry = []
    
    for row in range(0, test_size):
        entry = comparelist.iloc[row].tolist()
                
        if (entry != last_entry):
            row_keep.append(row)
        
        last_entry = entry
        
    testlist = testlist.take(row_keep, axis = 0)
    
    return testlist.sort(['PATNO', 'CLINICAL_EVENT', 'TYPE', 'TESTNAME', 'RUNDATE'], ascending = True)

cleanbiodata = Discard_obsolete_data(allbiodata)

# <codecell>

biodata_baseline = cleanbiodata[(cleanbiodata['CLINICAL_EVENT'] == 'Baseline Collection')]

# <codecell>

def extract_test(database, testname):
    aux = database[['PATNO', 'DIAGNOSIS', 'TESTVALUE']][(biodata_baseline['TESTNAME'] == testname)]
    
    return aux.rename(columns = {'TESTVALUE' : testname})
    
biodata_baseline_asyn = extract_test(biodata_baseline, 'CSF Alpha-synuclein')
biodata_baseline_beta = extract_test(biodata_baseline, 'Abeta 42')
biodata_baseline_ptau = extract_test(biodata_baseline, 'p-Tau181P')
biodata_baseline_ttau = extract_test(biodata_baseline, 'Total tau')

# <codecell>

def merge_tests(database_list):
    aux = database_list[0]
    
    for i in range(1, len(database_list)):
        aux = pd.merge(aux, database_list[i], on = ['PATNO', 'DIAGNOSIS'], how = 'inner')
    
    return aux

biodata_baseline_csf = merge_tests([biodata_baseline_asyn, biodata_baseline_beta, biodata_baseline_ptau, biodata_baseline_ttau])

# <codecell>

# Let's write a copy of this to disk!

biodata_baseline_csf.to_csv('Desktop/PPMI Data/Biospecimen_Analysis/CSF_proteins_baseline.csv', index = False)

# <codecell>

def mean_and_std(database, column):
    aux_series = database[column].astype(float)
    return aux_series.mean(), aux_series.std()

# <codecell>

def standardize_table(database):
    
    # Take a table of test results and express it in units of std deviations from the mean
    
    data_columns = database.columns.tolist()[2:]
    dbase = database.copy()
    
    for col in data_columns:
        avg, stddev = mean_and_std(database, col)
        dbase[col] = dbase[col].apply(lambda x : (float(x) - avg) / stddev)
    
    return dbase

csfdata_norm = standardize_table(biodata_baseline_csf)

# <codecell>

def condition_to_number(database, binary = True):
    
    # Replace 'Condition' by numerical code:  0 = healthy control, 1 = Parkinson's, 2 = SWEDD
    # If binary == True, then return only two outcomes: 0 = healthy, 1 = symptomatic
    
    condition_dict = {'Control' : 0, 'PD' : 1, 'SWEDD' : 2}
    
    # Lump together PD and SWEDD patients, if desired: 
    
    if (binary == True):
        condition_dict['SWEDD'] = 1
    
    dbase = database.copy()
    dbase['DIAGNOSIS'] = dbase['DIAGNOSIS'].apply(lambda x : condition_dict[x])
    
    return dbase

normalizedcsfdata = condition_to_number(csfdata_norm, True)

# <codecell>

# Let's check visually for some correlation between pairs of proteins in the CSF:

protein_list =  normalizedcsfdata.columns.tolist()[2:]
protein_count = len(protein_list)

for p1 in range(0, protein_count):
    for p2 in range(p1 + 1, protein_count):
        
        plt.xlim(-2,2)
        plt.ylim(-2,2)
        plt.title(protein_list[p1] + ' vs. ' + protein_list[p2])
        plt.scatter(normalizedcsfdata[protein_list[p1]], normalizedcsfdata[protein_list[p2]], c = normalizedcsfdata['DIAGNOSIS'], alpha = 0.5)
        plt.show()

# <codecell>

# Let's get started classifying ...

from sklearn.linear_model import LogisticRegression
from sklearn.cross_validation import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_curve, auc
from sklearn.neighbors import KNeighborsClassifier

# Create Matrix (protein data) and Vector (health status) for Statistical Tests

def Create_Matrix_and_Vector(data):
    test_columns = data.columns.tolist()[2:]
    cond_labels = data['DIAGNOSIS'].as_matrix()
    test_results = data.as_matrix(test_columns)

    return test_results, cond_labels

# Random Forest Classifier

def RFClass(features, labels, estimators = 100):
    X_train, X_test, y_train, y_test = train_test_split(features, labels)
    
    rf = RandomForestClassifier(n_estimators = estimators, max_features = None)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    
    print rf.score(X_test, y_test)
    print confusion_matrix(y_test, rf_pred)
    print rf.feature_importances_
    
    probs = rf.predict_proba(X_test)
        
    fpr, tpr, thresholds = roc_curve(y_test, probs[:,1])
    roc_auc = auc(fpr, tpr)
    
    plt.figure()
    plt.plot(fpr, tpr, label='ROC curve (area = %0.2f)' % roc_auc)
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver operating characteristic')
    plt.legend(loc="lower right")
    plt.show()
    
    return rf

features, labels = Create_Matrix_and_Vector(normalizedcsfdata)
RFClass(features, labels)

# <codecell>

# Try nearest neighbors classifier (with 5 neighbors, euclidean distance):

X_train, X_test, y_train, y_test = train_test_split(features, labels, train_size =.9)

kNN = KNeighborsClassifier(n_neighbors = 5)
kNN.fit(X_train, y_train)
kNN_pred = kNN.predict(X_test)

print kNN.score(X_test, y_test)
print confusion_matrix(y_test, kNN_pred)

probs = kNN.predict_proba(X_test)
    
fpr, tpr, thresholds = roc_curve(y_test, probs[:,1])
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr, label='ROC curve (area = %0.2f)' % roc_auc)
plt.plot([0, 1], [0, 1], 'k--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver operating characteristic')
plt.legend(loc="lower right")
plt.show()