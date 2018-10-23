import sys
import os
import time
from glob import glob
import csv

sys.path.append('..')

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import cv2

from pytracker3D.gui import tracker_ui
from pytracker3D.processing import postProcessing2D
from pytracker3D.processing import postProcessing3D
from pytracker3D.util import DLT
from pytracker3D.tracking import videoTracking
from pytracker3D.calibration import calibration3D

class MainWindow(QtWidgets.QMainWindow, tracker_ui.Ui_MainWindow):
    
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('./misc/dice.png'))
        self.setWindowTitle("Tracker3D")
        self.setGeometry(300, 200, 700, 500)
        self.path=os.path.dirname(os.path.realpath(__file__))
        
        self.tracks=[]
        self.cal2DFiles=[]
        self.cal3DFiles=[]
        self.reconstruct3D=[]
        self.tracks2DInsts=[]
        self.trackList=[]
        self.master_calList=[]
        self.three_dee=[]

        self.chooseProjectPath_b.clicked.connect(self.get_project_path)
        self.loadCal3D_b.clicked.connect(self.loadCal3D)
        self.removeCal3D_b.clicked.connect(self.removeCal3D)  
        self.loadCalibrationView_b.clicked.connect(self.loadCalView)
        self.loadCalibrationView_b.clicked.connect(self.loadCalView)
        self.loadBackground_b.clicked.connect(self.loadCalBackgroundView)
        self.backgroundSub_b.clicked.connect(self.backgroundSub_cal)
		
        self.trkTrack_B.clicked.connect(self.trackVideo)
        self.trkLoad_B.clicked.connect(self.videoOpen)
        self.trkPreview_B.clicked.connect(self.previewVideo)
        self.selectStartStop_b.clicked.connect(self.selectVideoBounds)

        self.gaussSlider.valueChanged.connect(self.gaussSliderChange)
        self.medianSlider.valueChanged.connect(self.medianSliderChange)
        self.kernelSlider.valueChanged.connect(self.kernelSliderChange)
        
        self.choose_background_b.clicked.connect(self.select_background_image)

        self.ppFileOpen_B.clicked.connect(self.open_CSV_tracks)
        self.ppClearList_B.clicked.connect(self.clean_CSV_tracks)
        self.ppBlank_B.clicked.connect(self.blankRows)
        self.ppUndo_B.clicked.connect(self.changesUndo)
        
        self.csvList_LW.doubleClicked.connect(self.selectTrack)
        self.tracks3D_LW.doubleClicked.connect(self.select_3D_track)
        self.calView1_3D_select_B.clicked.connect(self.calView1_3D_select)
        self.calView2_3D_select_B.clicked.connect(self.calView2_3D_select)        
        self.addView_3D_b.clicked.connect(self.addTrack3D)
        self.clear_reconst3D_LW_b.clicked.connect(self.clear_reconst3D_LW)
        self.reconstruct_3D_b.clicked.connect(self.reconstruct_3D)
        self.cleartracks3DLW_b.clicked.connect(self.clean_3D_tracks)
        
        self.definedCal=calibration3D.calibration3D(self)

    def loadCalView(self):

        try:
            self.calView = QFileDialog.getOpenFileNames(self,"Image file", self.path,filter="Image Files(*.jpeg *.jpg)")[0][0]
        except IndexError:
            return
        
        image = cv2.imread(self.calView,0)
         
        if self.view1_rb.isChecked()==True:
            view="1"
            self.definedCal.calView1=self.calView          
        if self.view1_rb.isChecked()==False:
            view="2"
            self.definedCal.calView2=self.calView

        cv2.namedWindow('Calibration view %s' % view, cv2.WINDOW_NORMAL)
        cv2.imshow('Calibration view %s' % view, image)      
        
    def loadCalBackgroundView(self):
                  
        try:
            self.backGroundView = QFileDialog.getOpenFileNames(self,"Image file", self.path,filter="Image Files(*.jpeg *.jpg)")[0][0]
        except IndexError:
            return
        
        image = cv2.imread(self.backGroundView,0)
          
        if self.view1_rb.isChecked()==True:
            view="1"
            self.definedCal.backView1=self.backGroundView            
        if self.view1_rb.isChecked()==False:
            view="2"
            self.definedCal.backView2=self.backGroundView

        cv2.namedWindow('Background view %s' % view, cv2.WINDOW_NORMAL)
        cv2.imshow('Background view %s' % view, image) 

    def backgroundSub_cal(self):
        self.definedCal.background_subtraction()
    
    def get_project_path(self):
        self.path=QFileDialog.getExistingDirectory(self,"Choose project folder", "C:\\Users\\tempo\\Desktop\\Trial_1")
        self.active_path_label.setText(self.path)

    def select_background_image(self):
        self.background_video = QFileDialog.getOpenFileNames(self,"Video file", self.path,filter="Video Files( *.mp4 *.h264)")[0][0]

        cap = cv2.VideoCapture(self.background_video)
        length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        def onChange(trackbarValue):
            cap.set(cv2.CAP_PROP_POS_FRAMES,trackbarValue)
            err,self.background_img = cap.read()
            cv2.imshow("mywindow", self.background_img)
            pass

        cv2.namedWindow('mywindow')
        cv2.createTrackbar( 'Choose a good blank background image:', 'mywindow', 0, length, onChange )

        onChange(0)
        cv2.waitKey()
        cap.release()
        cv2.destroyAllWindows() 
         
    def videoOpen(self): 
        try:
            fileobj=QFileDialog.getOpenFileName(self,"Video file", self.path,filter="Video Files( *.mp4 *.h264)")
            self.pathLabel.setText(str(fileobj[0]))
            self.video=fileobj[0]
            self.tracking=videoTracking.VideoTracking(self)
            
        except AttributeError:
            self.errMessage="Project path not specified."
            self.errorTitle="Please specify a project path ..."
            self.errorMsg()            

    def previewVideo(self):
        self.tracking.preview() 
        
    def selectVideoBounds(self):
        self.tracking.selectVideoBounds()

    def trackVideo(self):
        self.tracking.trackVideo()
    
    def loadCal3D(self):
     
        try:
            self.cal3DFilesTemp = QFileDialog.getOpenFileNames(self,"CSV files", self.path, filter="Text Files (*.csv)")[0]
            self.cal3DFiles = self.cal3DFiles+self.cal3DFilesTemp
            self.cal3D_LW1.clear()
            self.cal3D_LW2.clear()
    
            for i in range(len(self.cal3DFiles)):
                print(i)
                self.cal3D_LW1.addItem(os.path.split(os.path.abspath(self.cal3DFiles[i]))[1])
                self.cal3D_LW2.addItem(os.path.split(os.path.abspath(self.cal3DFiles[i]))[1])
                
        except AttributeError:
            self.errMessage="Project path not specified."
            self.errorTitle="Please specify a project path ..."
            self.errorMsg()            
               
    def removeCal3D(self):
        self.cal3DFiles=[]
        self.cal3D_LW1.clear()
        self.cal3D_LW2.clear() 
        
    def calView1_3D_select(self):
        view = 1
        self.tracks2DInsts[self.csvList_LW.currentRow()].define_calibration(view)

    def calView2_3D_select(self):
        view = 2
        self.tracks2DInsts[self.csvList_LW.currentRow()].define_calibration(view)

    def selectTrack(self):
        try:
            self.tracks2DInsts[self.csvList_LW.currentRow()].plot_pixel_coordinates()
        except IndexError:
            pass

    def select_3D_track(self):
        try:
            print("sometime")
        except IndexError:
            pass

    def addTrack3D(self):
        self.reconstruct3D.append(self.tracks2DInsts[self.csvList_LW.currentRow()])
        
        if len(self.reconstruct3D) > 2:
            self.errMessage="Only two views allowed for 3D reconstruction."
            self.errorTitle="Trying to add too many views!"
            self.errorMsg()
            return 
            
        self.reconstruct3D_LW.addItem(self.tracks2DInsts[self.csvList_LW.currentRow()].filename)

    def clear_reconst3D_LW(self):
        self.reconstruct3D_LW.clear()
        self.reconstruct3D=[]

    def reconstruct_3D(self):
        try:
            self.threeDee_temp=postProcessing3D.postProcessing3D(self)
            self.three_dee.append(self.threeDee_temp)
            self.tracks3D_LW.clear()
            
            for i in range(len(self.three_dee)): 
                self.useless_path, self.basename=os.path.split(os.path.abspath(self.three_dee[i].three_dee_name))
                self.filename=os.path.splitext(self.basename)[0]
                self.tracks3D_LW.addItem(self.filename)        
        except AttributeError:
            self.errMessage="One or both files has not been attributed a calibration"
            self.errorTitle="Please specify calibrations ..."
            self.errorMsg()    
            
    def open_CSV_tracks(self):
        self.tempTracks = QFileDialog.getOpenFileNames(self,"CSV files", self.path, filter="Text Files (*.csv)")[0]
        self.tracks=self.tracks+self.tempTracks
        
        if self.tracks2DInsts:
            self.nmb_tracks=len(self.tracks2DInsts)
            self.newTracks2DInsts=[postProcessing2D.postProcessing2D(self.tempTracks[i],self) for i in range(len(self.tempTracks))]
            self.tracks2DInsts=self.tracks2DInsts+self.newTracks2DInsts

            for i in range(len(self.tracks2DInsts)): 
                if i+1 <= self.nmb_tracks:
                    continue
                else:
                    self.useless_path, self.basename=os.path.split(os.path.abspath(self.tracks2DInsts[i].fileobj))
                    self.filename=os.path.splitext(self.basename)[0]
                    self.csvList_LW.addItem(self.filename)
        else:
            self.tracks2DInsts=[postProcessing2D.postProcessing2D(self.tempTracks[i],self) for i in range(len(self.tempTracks))]
            self.nmb_tracks=len(self.tracks2DInsts)
            
            for i in range(len(self.tracks2DInsts)): 
                    self.useless_path, self.basename=os.path.split(os.path.abspath(self.tracks2DInsts[i].fileobj))
                    self.filename=os.path.splitext(self.basename)[0]
                    self.csvList_LW.addItem(self.filename)
            
    def clean_CSV_tracks(self):
        self.tracks=[]
        self.tracks2DInsts=[]
        self.pp_TV.clearSpans()
        self.csvList_LW.clear()
        self.reconstruct3D_LW.clear() 
        self.reconstruct3D=[]         

    def clean_3D_tracks(self):
        self.tracks3D=[]
        self.tracks3D_LW.clear()

    def blankRows(self):
        self.tracks2DInsts[self.csvList_LW.currentRow()].blankRows()
        
    def changesUndo(self):
        self.tracks2DInsts[self.csvList_LW.currentRow()]=postProcessing2D.postProcessing2D(self.tracks[self.csvList_LW.currentRow()],self)
        self.tracks2DInsts[self.csvList_LW.currentRow()].plot_pixel_coordinates()
       
    def gaussSliderChange(self):
        self.gaussValueLabel.setText(str(self.gaussSlider.value()))

    def medianSliderChange(self):
        self.medianValueLabel.setText(str(self.medianSlider.value()))

    def kernelSliderChange(self):
        self.kernelValueLabel.setText(str(self.kernelSlider.value()))

    def errorMsg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(self.errMessage)
        msg.setWindowTitle(self.errorTitle)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = msg.exec_()        
 
app = QtWidgets.QApplication(sys.argv)
app.aboutToQuit.connect(app.deleteLater)
form = MainWindow()
form.show()
app.exec_()
