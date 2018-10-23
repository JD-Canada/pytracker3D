# -*- coding: utf-8 -*-
"""
Created on Sun Jul 29 03:52:54 2018

@author: Jason
"""

import numpy as np
import cv2

# Load an color image in grayscale
img1 = cv2.imread('before.jpg',0) #READ BGR

img2 = cv2.imread('after.jpg',0) #READ AS ALPHA
cv2.imshow('test',img2)
#kernel = np.ones((2,2), np.uint8) #Create Kernel for the depth
#img2 = cv2.erode(img2, kernel, iterations=2) #Erode using Kernel
#
#width, height, depth = img1.shape
#combinedImage = cv2.merge((img1, img2))
#
#cv2.imshow('test',combinedImage)

