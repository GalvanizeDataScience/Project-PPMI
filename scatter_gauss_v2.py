# A fancy Gaussian display style for 2D maps.

# Provide a colored scatterplot that uses Gaussian profiles 
# to show distribution besides markers.
# Indicate averages for different cohorts if applicable

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Input parameters:
# Pairs of values of data points in form of pandas series objects - x_series, y_series
# Corresponding series object (subject ccondition/cohort) - subj_cond
#
# Return - currently none, although carries matplotlib images implicitly.
# (should add bitmap file option)


def Scatter_Gauss(x_series, y_series, subj_cond):
    
    # This section ideally should be controlled by function parameter keys.
    # For now, these were pretty good values for the PPMI study: 

    # Some parameters

    Gauss_width = 0.2  # Width of the Gaussian marker
    Gauss_depth = 0.1  # Maximum color saturation

    # Displayed Canvas

    x_min = -2.0
    x_max = +2.0

    y_min = -2.0
    y_max = +2.0
    
    # Size per Pixel

    image_resolution_x = 0.005
    image_resolution_y = 0.005
    
    # Number of data points to be displayed
    
    scatter_size = len(x_series)
    
    # Color information - dictionary of rgb values for each color code (saturated)
    # Here only defined for types 0, 1, 2 (HC, PD, SWEDD)
    # (One could extend this for more values & colors, of course.)

    rgb = {'HC':[0.0,0.0,1.0], 'PD':[0.0,1.0,0.0], 'SWEDD':[1.0,0.0,0.0]}
    
    # Create Numerical Grid for Gaussians

    x = np.arange(x_min, x_max, image_resolution_x)
    y = np.arange(y_min, y_max, image_resolution_y)
    X, Y = np.meshgrid(x, y)
    
    # Create grids for color functions.
    # (We'll lave an empty canvas black.)
    
    ImageR = np.zeros((len(x),len(y)))
    ImageG = np.zeros((len(x),len(y)))
    ImageB = np.zeros((len(x),len(y)))
    
    ImageRGB = np.zeros((len(x), len(y), 3))
    
    # Add Gaussian 'penumbra' for each data point
    # (color depends on condition listed)
    
    for subj in subj_cond.index:
        delta_X = X - x_series[subj]
        delta_Y = Y - y_series[subj]
        
        rel_dist = (delta_X * delta_X + delta_Y * delta_Y) / (Gauss_width * Gauss_width)
        
        # An interpolation function would speed up calculation here:

        GaussValues = Gauss_depth * np.exp(-rel_dist)
        
        # Provide color by superposition
        
        ImageR = ImageR + GaussValues * rgb[subj_cond[subj]][0]
        ImageG = ImageG + GaussValues * rgb[subj_cond[subj]][1]
        ImageB = ImageB + GaussValues * rgb[subj_cond[subj]][2]
      
    # Check and correct for saturated colors - RGB values should not exceed unity
        
    ImageR = ImageR / (1.0 + ImageR)
    ImageG = ImageG / (1.0 + ImageG)
    ImageB = ImageB / (1.0 + ImageB)
    
    # Combine into RGB color function
    
    ImageRGB[:,:,0] = ImageR
    ImageRGB[:,:,1] = ImageG
    ImageRGB[:,:,2] = ImageB
    
    # Create figure background - Gaussian distributions
    
    im1 = plt.imshow(ImageRGB, interpolation='bilinear', origin='lower', extent=[x_min,x_max,y_min,y_max])
    
    # Create pinpoints for individual measurements by condition:
    # Healthy controls:

    cond_filter = (subj_cond == 'HC')
    
    x_select = x_series[cond_filter]
    y_select = y_series[cond_filter]
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        y_avg = y_select.mean()
        
        # Plot little blue markers for data points, big stars for cohort average

        im2 = plt.scatter(x_select, y_select, s = 10, c = 'b', alpha = .33)
        im3 = plt.scatter(x_avg, y_avg, s = 125 , c = 'b', marker = '*', label = 'HC')
    
    # Same now for Parkinson's cohort:

    cond_filter = (subj_cond == 'PD')
    
    x_select = x_series[(cond_filter)]
    y_select = y_series[(cond_filter)]
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        y_avg = y_select.mean()

        # Plot little green markers for data points, big stars for cohort average
       
        im4 = plt.scatter(x_select.tolist(), y_select.tolist(), s = 10, c = 'g', alpha = .33)
        im5 = plt.scatter(x_avg, y_avg, s = 125 , c = 'g', marker = '*', label = 'PD')
     
    # And finally, the SWEDD cohort:

    cond_filter = (subj_cond == 'SWEDD')
    
    x_select = x_series[(cond_filter)]
    y_select = y_series[(cond_filter)]
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        y_avg = y_select.mean()

        # Plot little red markers for data points, big stars for cohort average
        
        im6 = plt.scatter(x_select, y_select, s = 10, c = 'r', alpha = .33)
        im7 = plt.scatter(x_avg, y_avg, s = 125 , c = 'r', marker = '*', label = 'SWEDD')    

    # Here, ideally add option to save graph as an image cond_filter.
    # For now, just return 'empty,' but loaded with plt objects to be displayed.