# -*- coding: utf-8 -*-
"""
Created on Thu Mar  1 15:47:38 2018

@author: dugj2403
"""
import os
import numpy as np
from copy import deepcopy
import pandas as pd
from glob import glob
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def find_3D_tracks(path,prefix,extension):
    """Recursively look in subdirectories for 3D track files.
    
    Args:
    path   (str): Path to folder to look in.
    param2 (str): User selected prefix used to identify 3D tracks.
    
    Returns:
    bool: list of file names containing prefix in path.
    """
    tracks=[]
    result = [y for x in os.walk(path) for y in glob(os.path.join(x[0], extension))]
    for i in result:
        if prefix in i:
            tracks.append(i)
    return tracks

def convert_to_dataframes(csvList):
    """Convert list of 3D tracks into pandas dataframes.
    
    Args:
    csvList  (str): list containing 3D tracks to be converted to dataframes
    
    Returns:
    bool: list of pandas dataframes containing 3D tracks.
    """
    dataframes=[]
    for file in csvList:
        dat = pd.read_csv(file, sep=',', engine='python') 
    
        dataframes.append(dat)
    return dataframes


def plot_2D_lines(df,columns,limits):
    """Plot multiple columms of a pandas dataframe on a line graph.
    
    Args:
    df      (dataframe): pandas dataframe to plot, must contain x,y and z for now
    columns      (list): list containing xmin,xmax,ymin,ymax,zmin,zmax
    
    Returns:
    bool: list of pandas dataframes containing 3D tracks.
    """

    if type(columns) is list:
        
        ax = df.plot(y=columns[0],use_index=True)
        for i in range(len(columns)-1):
            df.plot(y=columns[i+1],ax=ax,use_index=True)

def plot_3D_points(df,**keyword_parameters):
    """Convert list of 3D tracks into pandas dataframes.
    
    Args:
    df      (dataframe): pandas dataframe to plot
    limits       (list): list containing xmin,xmax,ymin,ymax,zmin,zmax
    
    Returns:
    bool: list of pandas dataframes containing 3D tracks.
    """

    ax = plt.figure().gca(projection='3d')
    ax.scatter(df.x, df.y, df.z)
    ax.set_xlabel('Distance from start of flume (mm)')
    ax.set_ylabel('Lateral position (mm)')
    ax.set_zlabel('Vertical position (mm)')
    
    if ('limits' in keyword_parameters):
        limits=keyword_parameters['limits']
        ax.set_xlim(limits[0],limits[1])
        ax.set_ylim(limits[2],limits[3])
        ax.set_zlim(limits[4],limits[5])
    plt.show()

def scalar_3D_plotter(x,y,z,scalar,limits,pane_gray,title):
    
    """plot 3D scatter with associated scalar values all within scalar pandas dataframe
    
    Args:
    df               [dataframe]: containing 3D scatter data to plot
    columns                 list: ['x','y','z','scalar_name']
    limits                  list: [xlow,xhigh,ylow,yhigh,zlow,zhigh]
    pane_gray            booelan: makes pane backgrounds gray for better constrast
    title                 string: title of plot

    Returns:
        plot the 3D scatter
    """
    
    fig = plt.figure()
    ax=fig.gca(projection='3d')
    ax.set_aspect('equal')
    
    if pane_gray:
        ax.w_xaxis.set_pane_color((0, 0, 0, 0.2))
        ax.w_yaxis.set_pane_color((0, 0, 0, 0.2))
        ax.w_zaxis.set_pane_color((0, 0, 0, 0.2))  
     
    ax.set_xlim(limits[0],limits[1])
    ax.set_ylim(limits[2],limits[3])
    ax.set_zlim(limits[4],limits[5])
    ax.set_title(title)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    sc=ax.scatter(x, y, z, c=scalar, cmap='jet')
    plt.colorbar(sc)
    plt.show()


	
def smooth(df,columns,names,period,**keyword_parameters):
    """Smooths out spikey data in a 3D trajectory by running a moving average
    over specified columns of input dataframe. Optionally, the smoothed curve
    can be shifted back close to its originally position by including the shift
    optional argument.
    
    Args:
    df      (dataframe): pandas dataframe
    columns      (list): list of dataframe headers to smooth
    names        (list): names of new columns in same order as columns
    
    Returns:
    dataframe: pandas dataframe containing smoothed and/or shifted columns.
    """
    df=deepcopy(df)
    for i in range(len(columns)):
        df[names[i]]=pd.rolling(df[columns[i]],period).mean()
            
    if ('shift' in keyword_parameters):
        shift = keyword_parameters['shift']
    
    if shift:
        shift_names=keyword_parameters['shift_names']
        shift_period=keyword_parameters['shift_period']
        
        for i in range(len(columns)):
            df[shift_names[i]]=df[names[i]].shift(shift_period)   
    return df

def calculate_vel_components(df,columns,names,fps,**keyword_parameters):
    """Add velocity components of 3D track to input dataframe. Optionally adds
    the velocity magnitude ('V').
    
    Args:
    df      (dataframe): pandas dataframe
    columns      (list): list of dataframe headers to smooth
    names        (list): names of new columns in same order as columns
    
    Returns:
    dataframe: pandas dataframe containing velocity component and/or magnitude.
    """

    df=deepcopy(df)
       
    for i in range(len(columns)):
         df[names[i]]=(df[columns[i]].diff())*fps
    
    if ('mag' in keyword_parameters):
         mag = keyword_parameters['mag']
         if mag:
              df['V']=(df[names[0]]**2+df[names[1]]**2+df[names[2]]**2)**0.5
    if ('acceleration' in keyword_parameters):
         acc = keyword_parameters['acceleration']
         if acc:
             for i in range(len(columns)):
                 name=names[i]+'_acc'
                 df[name]=(df[names[i]].diff())*fps
    
    return df

	
	
	
def check_time_in_zones(df):

#    df=deepcopy(df)
#    df=df.groupby(['Zone']).count()
    df=df.join(df.groupby('Zone')['Zone'].count(), on='Zone', rsuffix='_counts')
#    df=df.reset_index()
    
    return df


def check_direction(df,limits,names):
    
    df=deepcopy(df)
    df['direction']=np.nan
    df['direction']=np.where(((df.x.iloc[0] <= limits[0]) & (df.x.iloc[-1] >= limits[1] )),names[0], df.direction)
    df['direction']=np.where(((df.x.iloc[0] >= limits[1]) & (df.x.iloc[-1] <= limits[0] )),names[1], df.direction)
    df['direction']=np.where(((df.x.iloc[0] <= limits[0]) & (df.x.iloc[-1] <= limits[0] )),names[2], df.direction)
    df['direction']=np.where(((df.x.iloc[0] >= limits[1]) & (df.x.iloc[-1] >= limits[1] )),names[3], df.direction)
    
    return df
    