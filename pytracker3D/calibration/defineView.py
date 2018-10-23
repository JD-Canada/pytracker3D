# -*- coding: utf-8 -*-
"""
Created on Thu Apr  5 15:12:09 2018

@author: dugj2403
"""

import sys
sys.path.append('..')


import os
import cv2

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import cv2

class calibration3D:
    
    def __init__(self,imagePath):
        print("You are now working on a new image. If you make errors selecting a marker with select_marker(), just rerun this line of code to get a fresh start.")
        self.point=1
        self.imagePath=imagePath

    def loadCalView(self):
        if self.view1_rb.isChecked()==True:
            view="1"
        if self.view1_rb.isChecked()==False:
            view="2"
            
        try:
            self.calView = QFileDialog.getOpenFileNames(self,"Image file", self.path,filter="Image Files(*.jpeg *.jpg)")[0][0]
        except IndexError:
            return
        image = cv2.imread(self.calView,0)

        cv2.namedWindow('Calibration view %s' % view, cv2.WINDOW_NORMAL)
        cv2.imshow('Calibration view %s' % view, image)

    def loadCalBackgroundView(self):
        
        if self.view1_rb.isChecked()==True:
            view="1"
        if self.view1_rb.isChecked()==False:
            view="2"
            
        try:
            self.calView = QFileDialog.getOpenFileNames(self,"Image file", self.path,filter="Image Files(*.jpeg *.jpg)")[0][0]
        except IndexError:
            return
        image = cv2.imread(self.calView,0)

        cv2.namedWindow('Background view %s' % view, cv2.WINDOW_NORMAL)
        cv2.imshow('Background view %s' % view, image)
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
        
        
        
        
        