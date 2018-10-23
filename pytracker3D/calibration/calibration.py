# -*- coding: utf-8 -*-
"""
Created on Thu Apr  5 16:27:48 2018

@author: dugj2403
"""

import sys
sys.path.append('..')

import os

import numpy as np
import pandas as pd


def find_x_coords(knownPositions,centroids):
    
    """ Uses the equation of plane defined by three points on the plane to 
		determine the x coordinate for each of the markers on the calibration plate
		
        -centroid filename must follow this format:
            LatLong_14375_112_thresh, with the plate position from the start of 
            the flume as the third element (ie, '112' in centimeters)
            
        - Warning, this function is very application specific to calibration plate
 		  at the Université de Sherbrooke
    
    Args:
    knownPositions   (dataframe): ['Point','y','z']
    centroids        (list): list of .csv paths containing columns Point, cx,cy
    
    Returns:
	 pixelPointsList  (list): list of dataframes containing x,y,z of the detected points
    """
    
    pixelPointsList=[]
    for i in range(len(centroids)):
        df=pd.read_csv(centroids[i])
        name=os.path.basename(centroids[i])
        name=os.path.splitext(name)
        name=name[0].split("_")
        print(name)
        xPosition=int(name[2])*10
        view=name[0]
        df['xPlate']=xPosition
        df['view']=view
        df=df.merge(knownPositions,on=['Point'])
        
        #points of calibration plate
        P=[int(xPosition),150,0]          #corner used to position plate
        Q=[int(xPosition)+150,0,0]        #leading corner
        R=[int(xPosition)-127+150,0,86.5] #corner downstream but higher in z of leading corner
    
        v1=np.subtract(Q,P)
        v2=np.subtract(R,P)
        n=np.cross(v1,v2)
    
        def calculate_x(row):
            ##n[0](x-P[0])+n[1](y-P[1])+n[2](z-P[2])=0
            return ((-n[1]*(row['y']-P[1])-n[2]*(row['z']-P[2]))/n[0])+P[0]
        
        df['x'] = df.apply(calculate_x, axis=1)
        pixelPointsList.append(df)
        
    return pixelPointsList

def find_intersection_of_points(pixelPointsList):
    
    """Returns a dataframe of the common points detected in both views
    
    Args:
    pixelPointsList   (list of dataframes): 
    
    Returns:
    joinedPoints  (dataframe): ['Point','cx_dorsal','cy_dorsal', 'xPlate','cx_profile', 'cy_profile', 'y','z','x'] 
    """
    
    together=pd.concat(pixelPointsList)
    dorsal = together.ix[together['view']=="LatLong"]
    dorsal=dorsal.drop(['view','x','y','z'], axis=1)
    dorsal.columns=['Point','cx_dorsal','cy_dorsal','xPlate']
    profile=together.ix[together['view']=="Vert"]
    profile.columns=['Point','cx_profile','cy_profile','xPlate','view','y','z','x']
    
    joinedPoints=pd.merge(dorsal,profile,how='inner',on=['xPlate','Point'])
    joinedPoints=joinedPoints.drop(['view'], axis=1)
    return joinedPoints

        
