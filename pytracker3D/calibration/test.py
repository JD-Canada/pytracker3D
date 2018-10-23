# -*- coding: utf-8 -*-
"""
Created on Sun Jul 29 03:52:54 2018

@author: Jason
"""

import numpy as np
import cv2
from skimage.measure import compare_ssim

# Load an color image in grayscale
imageA = cv2.imread('before.jpg') 
imageB = cv2.imread('after.jpg') 

grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
(score, diff) = compare_ssim(grayA, grayB, full=True)
diff = (diff * 255).astype("uint8")
print("SSIM: {}".format(score))

thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
cv2.namedWindow('thresh', cv2.WINDOW_NORMAL)
cv2.imshow('thresh',thresh)