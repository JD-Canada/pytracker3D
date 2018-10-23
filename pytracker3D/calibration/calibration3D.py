# -*- coding: utf-8 -*-
"""
Created on Thu Apr  5 15:12:09 2018

@author: dugj2403
"""

import sys
sys.path.append('..')


import os
import cv2
import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import cv2

class calibration3D:
    
    def __init__(self,MainWindow):
    
        self.MainWindow=MainWindow
#        self.path, self.basename=os.path.split(os.path.abspath(self.MainWindow.calView))
#        self.filename=os.path.splitext(self.basename)[0]

    def background_subtraction(self):
        
        cal = cv2.imread(self.calView1)
        cal = cv2.cvtColor(cal, cv2.COLOR_BGR2GRAY)
        background = cv2.imread(self.backView1)
        background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)
        background_removed=cal-background

        if self.MainWindow.view1_rb.isChecked()==True:
            view="1"
        if self.MainWindow.view1_rb.isChecked()==False:
            view="2"

#        background_removed[np.where((background_removed > [0,0,0]).all(axis = 2))] = [255,255,255]
#
#        #Add the background and the image
#        final = background_removed + cal
#
#        #To be done – Smoothening the edges….
#
#        cv2.imshow('image', final )


        cv2.namedWindow('Background subtracted %s' % view, cv2.WINDOW_NORMAL)
        cv2.imshow('Background subtracted %s' % view, background_removed)        
        
#    def findContours(self,lowLim,upLim,show):
#        """
#        
#        Args:
#        image     (path): path to image
#        lowLim     (int): lower threshold of contour area for detection
#        upLim      (int): upper threshold of contour area for detection
#        
#        Returns:
#        nothing
#        """
#        
#        inputFilepath = self.imagePath
#        filename_w_ext = os.path.basename(inputFilepath)
#        self.filename, file_extension = os.path.splitext(filename_w_ext)
#       
#    
#        self.image = cv2.imread(self.imagePath)
#        imageGray = cv2.cvtColor(self.image,cv2.COLOR_BGR2GRAY)
#        ret,thresh = cv2.threshold(imageGray,40,255,cv2.THRESH_BINARY_INV)
#    
#        (_, self.cnts, _) = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#    
#        i=0
#        for c in self.cnts:
#            
#            if lowLim <= cv2.contourArea(c) <= upLim:
#                cv2.drawContours(self.image, [c], -5, (0, 255, 0), 1)
#                i=i+1
#                
#        if show == True:
#            cv2.namedWindow('Contours')
#            cv2.imshow("Contours", self.image)
#            cv2.waitKey(0)
#            cv2.destroyAllWindows()
#        
#    def draw_circle(self,event,x,y,flags,param):
#        
#        if event == cv2.EVENT_LBUTTONDOWN:
#    
#            cv2.circle(self.image,(x,y),2,(0,255,0),-1)
#            cv2.circle(self.image,(x,y),10,(255,0,0),1)
#            cv2.circle(self.image,(x,y),15,(255,0,0),1)
#            
#            for c in self.cnts:
#                (xstart, ystart, w, h) = cv2.boundingRect(c)
#                if xstart <= x <= xstart+w and ystart <= y <= ystart+h:
#                    M = cv2.moments(c)
#                    cx = int(M['m10']/M['m00'])
#                    cy = int(M['m01']/M['m00'])
#                    cv2.circle(self.image,(cx,cy),2,(0,0,255),-1)
#    
#                    f = open('%s.csv' % param, 'a+') #allows file to be appended to       
#                    #f.write(a+','+cx+','+cy+'\n')
#                    if self.point ==1:
#                        f.write("Point,cx,cy\n")
#                    f.write("%d,%d,%d\n" %(self.point,cx,cy))
#                    f.close()
#                    print("Centroid at x: %d and y: %d, written to file as point %d" % (cx,cy,self.point))
#                    self.point+=1
#
#    def select_centroids(self):
#        print('Ready to start writting points to file. Select centroids and press "c" anytime to save file and close window ... waiting to select first point:')
#    
#        cv2.namedWindow('Calibration frame')
#        cv2.setMouseCallback('Calibration frame',self.draw_circle,param=self.filename)
#        
#        while True:
#            
#                
#            cv2.imshow('Calibration frame', self.image)
#            key = cv2.waitKey(1) & 0xFF
#                       
#            if key == ord("r"):
#                self.point=input("please write a number:")
#                self.point=int(self.point)
#                print("Ready to start new row starting on point %d" % self.point)
#                
#            elif key == ord("c"):
#                break
#        cv2.destroyAllWindows()
        
        
        
        
        