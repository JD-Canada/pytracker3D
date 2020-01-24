import cv2
import numpy as np
import pandas as pd
import os
from PyQt5.QtWidgets import QMessageBox, QFileDialog




class VideoTracking():

    def __init__(self,MainWindow):
        self.MainWindow=MainWindow
        
        self.path, self.basename=os.path.split(os.path.abspath(self.MainWindow.video))
        self.filename=os.path.splitext(self.basename)[0]

        cap = cv2.VideoCapture(self.MainWindow.video)
        self.start=0
        self.stop = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.MainWindow.stop_sb.setValue(self.stop)
 
    def blockRegion(self,img):
        if self.MainWindow.blockOutRegions_cb.isChecked()==True: 
            for key in self.MainWindow.blockOutRegions: 
                
                if key in self.MainWindow.disabledBlockOutRegions.keys():
                    continue

                topx=self.MainWindow.blockOutRegions[key].topx            
                topy=self.MainWindow.blockOutRegions[key].topy            
                bottomx=self.MainWindow.blockOutRegions[key].bottomx            
                bottomy=self.MainWindow.blockOutRegions[key].bottomy            
                img=cv2.rectangle(img, (topx,topy),(bottomx,bottomy), 100,-1)
        return img

    def preview(self):

        cap = cv2.VideoCapture(self.MainWindow.video)
        self.MainWindow.track_TE.append("Playing preview. Click video window and press 'q' or click 'Stop' button to cancel")
        
        while(True):
            (grabbed, frame) = cap.read()
            
            if not grabbed:
                break                 
            currentframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = currentframe.shape[:2]
            cv2.namedWindow("Preview", cv2.WINDOW_NORMAL) 
            cv2.imshow("Preview",currentframe)  
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break  
        cap.release()
        cv2.destroyAllWindows()  

    def selectVideoBounds(self):

        cap = cv2.VideoCapture(self.MainWindow.video)
        length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        def onChange(trackbarValue):
            cap.set(cv2.CAP_PROP_POS_FRAMES,trackbarValue)
            err,img = cap.read()
            cv2.imshow("Select", img)
            pass

        self.start=self.MainWindow.start_sb.value()
        self.stop=self.MainWindow.stop_sb.value()

        cv2.namedWindow('Select')
        cv2.createTrackbar( 'Start', 'Select', self.start, length, onChange )
        cv2.createTrackbar( 'Stop'  , 'Select', self.stop, length, onChange )
        cap.set(cv2.CAP_PROP_POS_FRAMES,cv2.getTrackbarPos('Start','Select'))
        err,img = cap.read()
        cv2.imshow("Select", img)
        
        self.MainWindow.statusBar().showMessage("Press any key once frame limits have been chosen to exit.")

        onChange(0)
        cv2.waitKey()
         
        self.start = cv2.getTrackbarPos('Start','Select')
        self.stop   = cv2.getTrackbarPos('Stop','Select')
        cap.release()
        cv2.destroyAllWindows()   
        
        self.MainWindow.start_sb.setValue(self.start)
        self.MainWindow.stop_sb.setValue(self.stop)

        self.MainWindow.statusBar().showMessage("") 

    def trackVideo(self):

        self.MainWindow.track_TE.clear()

        self.cap = cv2.VideoCapture(self.MainWindow.video)
        self.background = None
        self.fgbg = cv2.createBackgroundSubtractorMOG2()

        count = 1
        xcoord=[]
        ycoord=[]
        frame=[]
        cx=0
        cy=0

        try:
            self.highPassThresh=int(self.MainWindow.highPass_le.text())
            self.lowPassThresh=int(self.MainWindow.lowPass_le.text())
        except AttributeError:
            pass

        while(True):
            if count==0:
                self.MainWindow.statusBar().showMessage("Tracking. Click video window and press 'q' or click 'Stop' button to cancel.")
                
            if self.MainWindow.trkTrack_B.isChecked()== False:
                self.MainWindow.trkTrack_B.setText('Track')
                self.MainWindow.statusBar().showMessage("")
                break
            else:
                self.MainWindow.trkTrack_B.setText('Stop')
                
            (self.grabbed, self.frame) = self.cap.read()

            if not self.grabbed:
                self.MainWindow.trkTrack_B.setChecked(False)
                self.MainWindow.trkTrack_B.setText('Track')
                self.MainWindow.track_TE.append("Tracking complete!")        
                break
            
            rows,cols,ch = self.frame.shape
        

            self.trackingFrame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            self.trackingFrame=self.blockRegion(self.trackingFrame)
            
            if self.MainWindow.specifyBackground_rb.isChecked()==True:
                ret=self.useSelectedFrameBackground()
                if ret == False:
                    self.MainWindow.trkTrack_B.setText('Track')
                    break
            elif self.MainWindow.mog_rb.isChecked()==True:
                self.mog2Subtraction()
            elif self.MainWindow.firstFrame_rb.isChecked()==True:
                self.useFirstFrameBackground()
            
            self.filters()

            try:
                cnts, hierachy = cv2.findContours(self.trackingFrame.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            except ValueError:
                ret, cnts, hierachy = cv2.findContours(self.trackingFrame.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)   

            cntarea=[0]
            xcntcoord=[0]
            ycntcoord=[0]
            
            for c in cnts:
                if self.MainWindow.lowPass_cb.isChecked():
                    if cv2.contourArea(c) > self.lowPassThresh:
                        continue
                if self.MainWindow.highPass_cb.isChecked():
                    if cv2.contourArea(c) < self.highPassThresh:
                        continue
                    
                cntarea.append(cv2.contourArea(c))
                (x, y, w, h) = cv2.boundingRect(c)
        
                M = cv2.moments(c)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                
                xcntcoord.append(cx)
                ycntcoord.append(cy)

            self.MainWindow.track_TE.append("|------------------|")
            if cntarea[-1]==0:
                self.MainWindow.track_TE.append("Frame %d: No valid contours detected" % count)
            else:
                self.MainWindow.track_TE.append("Valid detections on frame: %d" % count)
                for c in cntarea:
                    c=int(c)
                    if c == 0:
                        continue
                    else:
                        self.MainWindow.track_TE.append("Frame %i coutour area: %i" % (count,c))

            self.start=self.MainWindow.start_sb.value()    
            self.stop=self.MainWindow.stop_sb.value()    
            
            if count > self.stop or count < self.start:
                self.MainWindow.track_TE.append("Not within frame number bounds.")  
            else:
                biggestcontour=cntarea.index(max(cntarea))
                xcoord.append(xcntcoord[biggestcontour])
                ycoord.append(ycntcoord[biggestcontour])
                frame.append(count)
                self.objectCoords=np.array((frame,xcoord,ycoord),dtype=float) 

            for i in range(len(xcoord)):
                if xcoord[i]==0: 
                    pass
                else:
                    cv2.circle(self.frame, (xcoord[i], ycoord[i]),6, (0, 0, 255),thickness=-1)
                  
            self.frame=self.blockRegion(self.frame)

            cv2.namedWindow("Background removed", cv2.WINDOW_NORMAL) 
            cv2.imshow("Background removed",self.trackingFrame)   

            cv2.namedWindow("Tracking", cv2.WINDOW_NORMAL)
            cv2.imshow("Tracking",self.frame)  

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.MainWindow.trkTrack_B.setChecked(False)
                self.MainWindow.trkTrack_B.setText('Track')
                self.MainWindow.statusBar().showMessage("")
                break
            count = count +1
            
        self.cap.release()
        cv2.destroyAllWindows()
        self.MainWindow.statusBar().showMessage("")
        
    def saveTrack(self):

        try:
            path = QFileDialog.getSaveFileName(None, 'Save File', self.MainWindow.path, 'CSV(*.csv)')[0]

            self.objectCoords=np.transpose(self.objectCoords)
            self.objectCoords=pd.DataFrame(self.objectCoords)
            self.objectCoords.index = np.arange(1, len(self.objectCoords) + 1)
            self.objectCoords.to_csv(path, header=False,index=False)
            self.MainWindow.track_TE.append("Raw pixel coordinates saved to:")    
            self.MainWindow.track_TE.append(path)    
        except AttributeError:
            self.errMessage="No track yet to save. Make a track, then try again."
            self.errorTitle="No track available!"
            self.errorMsg()
            return None   

    def mog2Subtraction(self):

        self.frameDelta = self.fgbg.apply(self.trackingFrame)
        self.trackingFrame = cv2.threshold(self.frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

    def useFirstFrameBackground(self):

        if self.background is None:
            self.background = self.trackingFrame
    
        self.background=self.blockRegion(self.background)
        self.frameDelta = cv2.absdiff(self.background, self.trackingFrame)
        self.trackingFrame = cv2.threshold(self.frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

    def useSelectedFrameBackground(self):
 
        self.background = self.MainWindow.background
        self.background=self.blockRegion(self.background)
        try:
            self.frameDelta = cv2.absdiff(self.background, self.trackingFrame)
            self.trackingFrame = cv2.threshold(self.frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
            return True
        except:
            self.errMessage="Seems like your chosen background frame and the video are not of the same dimensions, or you have not chosen a background frame at all. Verify your choice of background frame and try again."
            self.errorTitle="Error with background frame!"
            self.errorMsg()
            return False
                   
    def filters(self):

        self.medianFiltersize=int(self.MainWindow.medianSlider.value())

        if self.medianFiltersize % 2 == 0:
                self.medianFiltersize=self.medianFiltersize + 1
        
        if self.MainWindow.medianFilterCheckbox.isChecked() == True:
            self.trackingFrame = cv2.medianBlur(self.trackingFrame,self.medianFiltersize)
            
        if self.MainWindow.gaussCheckBox.isChecked() == True:
            self.gauss=int(self.MainWindow.gaussSlider.value())
            if self.gauss % 2 == 0:
                self.gauss=self.gauss + 1
            self.trackingFrame = cv2.GaussianBlur(self.trackingFrame, (self.gauss,self.gauss), 0)

    def errorMsg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(self.errMessage)
        msg.setWindowTitle(self.errorTitle)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = msg.exec_()       