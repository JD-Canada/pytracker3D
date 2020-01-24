import sys
import os
import csv
import cv2
import PyQt5

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from glob import glob
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from gui import tracker_ui
from gui import calibration_ui
from tracking import videoTracking

class MainWindow(PyQt5.QtWidgets.QMainWindow, tracker_ui.Ui_MainWindow):

    """Main graphical user interface for pyTracker3D

    Interactive GUI for 2D and 3D tracking and calibration. 
    """
    
    def __init__(self, parent=None):
        """Sets up GUI

        Creates empty dicts and connects GUI elements to the various class methods. 
        """
        super(MainWindow, self).__init__(parent)
        
        #setup GUI 
        self.setupUi(self)
        self.setWindowIcon(PyQt5.QtGui.QIcon(os.path.dirname(os.path.abspath(__file__))+'/misc/dice.png'))
        self.setWindowTitle("Tracker3D")
        self.setGeometry(300, 200, 700, 500)
        self.path=os.path.dirname(os.path.realpath(__file__))
        
        """
        Init empty dictionaries to hold instances of various classes. The key to access each class is a user specified name (i.e., name of a blocked out region) or the loaded file name without extension.
        """
        ## Dictionary containing instances of TrackProcessing()
        self.tracksDict={}
        ## Dictionary containing instances of BlockOutRegion()
        self.blockOutRegions= {}
        ## Dictionary containing deactivated instances of BlockOutRegion() 
        self.disabledBlockOutRegions= {}


        """Tracking event handlers"""

        #buttons
        self.chooseProjectPath_b.clicked.connect(self.get_project_path)
        self.choose_background_b.clicked.connect(self.selectBackgroundImage)
        self.selBackgroundVid_b.clicked.connect(self.scrollSelectBackgroundImage)
        self.trkTrack_B.clicked.connect(self.trackVideo)
        self.trkLoad_B.clicked.connect(self.videoOpen)
        self.trkPreview_B.clicked.connect(self.previewVideo)
        self.selectStartStop_b.clicked.connect(self.selectVideoBounds)
        self.addBlock_b.clicked.connect(self.addBlockOutRegion)
        self.deleteBlock_b.clicked.connect(self.deleteBlockOutRegion)
        self.disableBlock_b.clicked.connect(self.disableBlockOutRegion)
        self.enableBlock_b.clicked.connect(self.enableBlockOutRegion)
        self.saveTrack_b.clicked.connect(self.saveTrack)
        self.saveTrackEdits_b.clicked.connect(self.saveTrackEdits)
        self.loadBlock_b.clicked.connect(self.loadBlock)
        self.saveBlock_b.clicked.connect(self.saveBlock)

        #sliders
        self.gaussSlider.valueChanged.connect(self.gaussSliderChange)
        self.medianSlider.valueChanged.connect(self.medianSliderChange)
        

        """Processing event handlers"""

        #buttons
        self.loadTracks_b.clicked.connect(self.loadTracks)
        self.delAllTracks_b.clicked.connect(self.clean_CSV_tracks)
        self.deleteTrack_b.clicked.connect(self.deleteTrack)
        self.tracks_lw.setDragDropMode(PyQt5.QtWidgets.QAbstractItemView.InternalMove)
        self.reorder_b.clicked.connect(self.orderTracks)
        self.tracks_lw.doubleClicked.connect(self.doubleClickTrack)
        self.tracks_lw.clicked.connect(self.selectTrack)

        self.ppBlank_B.clicked.connect(self.blankRows)
        self.ppUndo_B.clicked.connect(self.changesUndo)
        self.interpolate_b.clicked.connect(self.interpolateBlanks)

        self.newCalibration_b.clicked.connect(self.init_Calibration)
        self.loadCal_b.clicked.connect(self.loadCalibration)
        self.showCal_b.clicked.connect(self.showCalibration)

        self.reconstruct_3D_b.clicked.connect(self.reconstruct_3D)
        self.plot3D_b.clicked.connect(self.plot3D)
        self.save3DTrack_b.clicked.connect(self.save3DTrack)
        self.show3Dcoords_b.clicked.connect(self.show3Dcoords)

        self.groupBox_8.setVisible(False)


    def init_Calibration(self):
        """Instantiates CalibrationWindow()

        Shows the calibration module window.
        """
        
        ## Instance of CalibrationWindow()
        self.window = CalibrationWindow()
        self.window.show()     

    def showCalibration(self):
        """Shows loaded calibration in self.pp_TV tableView
        """

        try:
            self.calib.populateTable()
            self.tableItem_l.setText('Showing loaded calibration file')
        except AttributeError:
            self.errMessage="Please load a calibration to load."
            self.errorTitle="No calibration loaded!"
            self.errorMsg()
            return None

    def loadCalibration(self):
        """Called when user loads a calibration file

        1 - Prompts user for file name
        2 - sets self.calib to an instance of Calibration()
        3 - Populates self.pp_TV with calibration table data
        """

        pointFilePath=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,"Load calibration file", self.path, filter="Text files( *.txt *.csv)")

        if pointFilePath[0] != '':

            ### Coefficients of currently loaded calibration
            self.calib=Calibration(pointFilePath[0],self)

            self.calib.populateTable()
            self.calStyleSheet = "::section{Background-color:rgb(190,1,1);border-radius:14px;}"
            self.pp_TV.horizontalHeader().setStyleSheet(self.calStyleSheet)
            self.tableItem_l.setText('Showing loaded calibration file')

    def orderTracks(self):

        """Sets viewNumber of tracks to position in self.tracks_lw

        1 - Gets trackNames loaded into self.tracks_lw
        2 - Each track's value of viewNumber is updated to reflect the position
            in self.tracks_lw
        3 - Instantiates or reinstantiates Processing3D() with the updated
            viewNumber positions
        4 - Calls self.selectTrack() which shows a 2D plot of the track and
            updates the currently selected track label.
        """

        trackNames =  [str(self.tracks_lw.item(i).text()) for i in range(self.tracks_lw.count())]

        for position, trackName in enumerate(trackNames):
            for key in self.tracksDict.keys():
                if trackName == key:
                    self.tracksDict[key].viewNumber=position+1

        ##Instance of Processing3D()
        self.reconGroup=Processing3D(self)
        self.selectTrack()

    def setup3Dgroup(self):
        """ Convienience function to reinstantiate self.reconGroup
        """

        self.reconGroup=Processing3D(self)

    def loadBlock(self):
        """ Loads block out region data from file. 

        To define a block, write 'Block' in a text file followed by a space and then the block's 'name'. On each line below, write an integer value for the top x pixel coordinate of the block, an integer value for the top y pixel coordinate, an integer value for the bottom x pixel coordinate, an integer value for the bottom y pixel coordinate. 

        1 - prompt's user to load file
        2 - reads each line looking for 'Block'
        3 - once found, read in the values on the next four lines 
        """

        self.savedBlocksPath=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,
        "Load blockout region file",filter="Text Files( *.csv *.txt)")

        if self.savedBlocksPath[0]!='':

            with open(self.savedBlocksPath[0]) as fp:
                line = fp.readline()
                
                while line:
                    try:
                        if 'Block' in line:
                            blockID=line.split()
                            
                            if blockID[1] in self.blockOutRegions.keys():
                                self.errMessage="There is already a block out region named %s!" % self.blockOutRegions[blockID[1]].ID
                                self.errorTitle="Region already exists!"
                                self.errorMsg()
                                break 

                            self.blockOutRegions[blockID[1]]=BlockOutRegion(self,True)
                            self.blockOutRegions[blockID[1]].ID=blockID[1]

                            self.blockRegions_lw.addItem(blockID[1])
                            entry='topx'
                            line = fp.readline()
                            continue
                        if entry=='topx':
                            self.blockOutRegions[blockID[1]].topx=int(line)
                            entry='topy'
                            line = fp.readline()
                            continue
                        if entry=='topy':
                            self.blockOutRegions[blockID[1]].topy=int(line)
                            entry='bottomx'
                            line = fp.readline()
                            continue
                        if entry=='bottomx':
                            self.blockOutRegions[blockID[1]].bottomx=int(line)
                            entry='bottomy'
                            line = fp.readline()
                            continue
                        if entry=='bottomy':
                            self.blockOutRegions[blockID[1]].bottomy=int(line)
                            line = fp.readline()
                            continue
                    except UnboundLocalError:
                        self.errMessage="This file is not the right format. Have a look inside the file to see if it follows the correct format."
                        self.errorTitle="Incorrect file format!"
                        self.errorMsg()
                        return None                       
                
    def saveBlock(self):

        """Saves the selected blocks to file.

        1 - Prompts user for file name
        2 - Saves data in self.blockOutRegions[key].top* or self.blockOutRegions[key].bottom* to file
        """

        path = PyQt5.QtWidgets.QFileDialog.getSaveFileName(
                self, 'Save File', self.path, 'CSV(*.txt)')[0]

        if path != '':
            outF = open(path, "w")

            for count, key in enumerate(self.blockOutRegions.keys()):
                outF.write("Block %s \n" %str(self.blockOutRegions[key].ID))
                outF.write(str(self.blockOutRegions[key].topx)+"\n")
                outF.write(str(self.blockOutRegions[key].topy)+"\n")
                outF.write(str(self.blockOutRegions[key].bottomx)+"\n")
                outF.write(str(self.blockOutRegions[key].bottomy)+"\n")
            outF.close()

    def saveTrack(self):
        """Calls TrackProcessing.saveTrack() to save the current track to file.
        """

        try:
            self.tracking.saveTrack()
        except AttributeError:
            self.errMessage="No track yet to save. Make a track, then try again."
            self.errorTitle="No track available!"
            self.errorMsg()
            return None

    def saveTrackEdits(self):
        """Saves edits on current track to file by calling TrackProcessing.saveTrack().
        """
        try:
            self.selectedItemText=self.tracks_lw.currentItem().text()
            self.tracksDict[self.selectedItemText].saveTrack()
        except AttributeError:
            self.errMessage="Please click on a track to save."
            self.errorTitle="No track selected"
            self.errorMsg()
            return None

    def selectBackgroundImage(self):
        """Prompts user to select the image used for background subtraction.

        1 - Prompts user for image path
        2 - Loads and shows the image for confirmation
        """

        ## Path to background image
        self.backgroundPath=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,
        "Load image view",filter="Image Files( *.png *.jpg)")

        if self.backgroundPath[0]!='':

            ## OpenCV version of background image
            self.background=cv2.imread(self.backgroundPath[0])
            self.background = cv2.cvtColor(self.background, cv2.COLOR_BGR2GRAY)
            print(self.background.shape[:2])
            cv2.namedWindow("Tracking", cv2.WINDOW_NORMAL)
            cv2.imshow("Tracking",self.background)

    def scrollSelectBackgroundImage(self):

        """Opens and OpenCV window to allow user to scroll to the desired video frame to use for background selection.

        Writes the selected frame to file calling it 'firstFrame.jpg' in the current working directory. 
        """

        try:
            cap = cv2.VideoCapture(self.video)
            length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        except AttributeError:
            self.errMessage="Please select a video to extract frame from then try again."
            self.errorTitle="No video selected!"
            self.errorMsg()
            return None

        def onChange(trackbarValue):
            cap.set(cv2.CAP_PROP_POS_FRAMES,trackbarValue)
            err,img = cap.read()
            cv2.imshow("Select", img)
            pass

        self.start=self.start_sb.value()

        cv2.namedWindow('Select')
        cv2.createTrackbar( 'Frame #', 'Select', self.start, length, onChange )
        cap.set(cv2.CAP_PROP_POS_FRAMES,cv2.getTrackbarPos('Frame #','Select'))
        err,self.background = cap.read()
        self.background = cv2.cvtColor(self.background, cv2.COLOR_BGR2GRAY)

        cv2.imwrite('firstFrame.jpg',self.background)
        cv2.imshow("Select", self.background)
        
        self.statusBar().showMessage("Press any key once background frame has been chosen to exit.")

        onChange(0)
        cv2.waitKey()
         
        cap.release()
        cv2.destroyAllWindows()   
        
        self.statusBar().showMessage("") 

    def addBlockOutRegion(self):
            self.newBlockRegion=BlockOutRegion(self,False)

            if self.newBlockRegion.ID in self.blockOutRegions.keys():
                self.errMessage="There is already a block out region named %s!" % self.newBlockRegion.ID
                self.errorTitle="Region already exists!"
                self.errorMsg()
                return None  

            if self.newBlockRegion.valid == True:
                self.blockOutRegions[self.newBlockRegion.ID]=self.newBlockRegion

    def deleteBlockOutRegion(self):
        try:
            self.selectedItemText=self.blockRegions_lw.currentItem().text()
            self.blockOutRegions.pop(self.selectedItemText)
            self.blockRegions_lw.takeItem(self.blockRegions_lw.currentRow())

            if self.selectedItemText in self.disabledBlockOutRegions.keys():
                self.disabledBlockOutRegions.pop(self.selectedItemText)
        except AttributeError:
            self.errMessage="Please click on region to remove."
            self.errorTitle="No region selected"
            self.errorMsg()
            return None

    def disableBlockOutRegion(self):
        try:
            self.selectedItemText=self.blockRegions_lw.currentItem().text()
        except AttributeError:
            self.errMessage="Please click on region to disable."
            self.errorTitle="No region selected"
            self.errorMsg()
            return None
        self.disabledBlockOutRegions[self.selectedItemText]=self.selectedItemText
        item=self.blockRegions_lw.currentItem()
        item.setBackground(PyQt5.QtGui.QColor('red'))

    def enableBlockOutRegion(self):

        try:
            self.selectedItemText=self.blockRegions_lw.currentItem().text()
        except AttributeError:
            self.errMessage="Please click on region to enable."
            self.errorTitle="No region selected"
            self.errorMsg()
            return None

        try:
            self.disabledBlockOutRegions.pop(self.selectedItemText)
        except KeyError:
            return None
        item=self.blockRegions_lw.currentItem()
        item.setBackground(PyQt5.QtGui.QColor('white'))

    def gaussSliderChange(self):
        self.gaussValueLabel.setText(str(self.gaussSlider.value()))

    def medianSliderChange(self):
        self.medianValueLabel.setText(str(self.medianSlider.value()))

    def get_project_path(self):
        """
        GUI workflow is organized by first specifying a project directory. This
        approach allows the program to know where to place a number of folders
        that are created during a tracking project used to hold treated data in
        .csv files (e.g. calibration files and tracks).
        """
        self.newPath=PyQt5.QtWidgets.QFileDialog.getExistingDirectory(self,"Choose project folder", "C:\\Users\\tempo\\Desktop\\Trial_1")

        if self.newPath != '':
            self.path=self.newPath
            self.active_path_label.setText(self.path)
        
    def promptVideoDelete(self):

        if hasattr(self, 'video'):

            reply = PyQt5.QtWidgets.QMessageBox.question(self, 'Continue?', 
                    'Loading a new video will delete the track made on the current video, accept?', PyQt5.QtWidgets.QMessageBox.Yes, PyQt5.QtWidgets.QMessageBox.No)
            if reply == PyQt5.QtWidgets.QMessageBox.Yes:
                return True
            else:
                return False

    def videoOpen(self): 
        """
        Opens a PyQt5.QtWidgets.QFileDialog allowing user to choose a video file for tracking.
        Currently, only .mp4 and .h264 files will appear in dialog, we might 
        need to change this.
        
        The path to the video is saved as self.video. An important part of this 
        method is to create an instance of the videoTracking class which
        contains all the necessary methods to track the animal. The attributes 
        of the MainWindow class are passed to VideoTracking with the 'self' in 
        the last line of the try block below. This allows VideoTracking to access
        the video path chosen by the user immediately in the VideoTracking
        class's __init__ function. 
        """
        ret=self.promptVideoDelete()

        if ret == False:
            return None

        try:
            fileobj=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,"Video file", self.path,filter="Video Files( *.mp4 *.h264)")
            if fileobj[0]=="":
                return None

            self.pathLabel.setText(str(fileobj[0]))
            self.video=fileobj[0]

            self.tracking=videoTracking.VideoTracking(self)
            
        except AttributeError:
            self.errMessage="Project path not specified."
            self.errorTitle="Please specify a project path ..."
            self.errorMsg()  
        
    def previewVideo(self):
        """
        Accesses the VideoTracking method "preview" for the current self.tracking 
        instance. There is likely a cleaner way to do this without defining a function.
        This also needs to have a try except statement in case there isn't a current
        VideoTracking instance.
        """
        try:
            self.tracking.preview()
        except AttributeError:
            self.errMessage="Please select a video to preview, then try again."
            self.errorTitle="No video selected!"
            self.errorMsg()
        
    def selectVideoBounds(self):
        """
        Accesses the VideoTracking method selectVideoBounds which allows the user
        to move the sliders to choose when in the video to start and stop tracking.
        The name of selectVideoBounds might be better named timeBounds? Again there 
        might be a way to define this without requiring a new method and again it 
        should have error catching.
        """
        self.tracking.selectVideoBounds()

    def trackVideo(self):
        """
        Runs the trackVideo method of VideoTracking for the instance stored in 
        self.tracking. trackVideo is where the animal gets tracked. Its tracked
        coordinates get stored in a folder called 2DTracks which, if it doesn't 
        already exist, will be created in the root of the project directory.
        """
        try:
            self.tracking.trackVideo()
        except AttributeError:
            self.errMessage="Please select a video to track on, then try again."
            self.errorTitle="No video selected!"
            self.errorMsg()

    def loadTracks(self):

        self.trackPaths = PyQt5.QtWidgets.QFileDialog.getOpenFileNames(self,"CSV files", self.path, filter="Text Files (*.csv)")[0]
        print(self.trackPaths)

        if not self.trackPaths:
            print("there were no tracks loaded")
            return None
        else:
            for count, path in enumerate(self.trackPaths):

                try:

                    self.currentTrack=TrackProcessing(path,self)
                    self.tracksDict[self.currentTrack.trackID]=self.currentTrack    
                    self.tracks_lw.addItem(self.currentTrack.trackID)  

                except ValueError:

                    self.errMessage="You are trying to load a incorrect file format for a track (it should only have 3 columns, one for the frame number, one for the x pixel coordinate and one for the y pixel coordinate). Try a correctly formatted file."
                    self.errorTitle="Incorrect file format!"
                    self.errorMsg()
                    return None            
            self.orderTracks()
        
    def interpolateBlanks(self):
        self.selectedItemText=self.tracks_lw.currentItem().text()
        self.tracksDict[self.selectedItemText].interpolateBlanks()       

    def blankRows(self):
        """
        Calls postProcessing2D method to remove selected rows in the table from
        the track. This might be a useful feature when there are persistent 
        abberant points that show up during tracking. Ideally the row indices of 
        the points removed should also be automatically removed from the second 
        view to make sure the tracks are the same length.
        """
        try:

            self.selectedItemText=self.tracks_lw.currentItem().text()
            self.tracksDict[self.selectedItemText].blankRows()
        except AttributeError:
            self.errMessage="Please click on track to edit."
            self.errorTitle="No track selected"
            self.errorMsg()
            return None            
    def changesUndo(self):
        """
        Undos blank row changes
        """
        self.selectedItemText=self.tracks_lw.currentItem().text()
        self.tracksDict[self.selectedItemText].reinitializeCoords()

    def clean_CSV_tracks(self):
        """
        Empties the self.tracksDict, GUI table and listwidgets.
        """
        self.tracksDict={}
        self.tracks_lw.clear()
        self.dummy_df=pd.DataFrame()
        self.pp_TV.setModel(PandasModel(self.dummy_df))

    def deleteTrack(self):
        try:
            self.selectedItemText=self.tracks_lw.currentItem().text()
        except AttributeError:
            self.errMessage="Please click on track to remove."
            self.errorTitle="No track selected"
            self.errorMsg()
            return None
        self.tracksDict.pop(self.selectedItemText)
        self.tracks_lw.takeItem(self.tracks_lw.currentRow())

        self.orderTracks()
        self.setup3Dgroup()

    def doubleClickTrack(self):
        """
        Method called when user doubleclicks a track in the "Please select track
        to edit" listwidget. This in turn calls the plot_pixel_coordinates() 
        method of the postProcessing2D class to make a 2D plot of the coordinates
        appear. The plot needs some matplotlib love and ideally should be embedded in the
        GUI.
        """
        try:
            self.selectedItemText=self.tracks_lw.currentItem().text()
            
            for count, track in enumerate(self.tracksDict):
                
                if track in self.selectedItemText:
                    
                    self.tracksDict[track].plotNoConditions()
                    self.tableItem_l.setText('Track name : %s   View number: %s' %(track,str(self.tracksDict[track].viewNumber)))
        except AttributeError:
            pass

    def selectTrack(self):

        try:
            self.selectedItemText=self.tracks_lw.currentItem().text()
            
            for count, track in enumerate(self.tracksDict):
                
                if track in self.selectedItemText:
                    
                    self.tracksDict[track].plot_pixel_coordinates()
                    self.tableItem_l.setText('Track name : %s   View number: %s' %(track,str(self.tracksDict[track].viewNumber)))

        except AttributeError:
            pass

    def plot3D(self):
        try:
            self.reconGroup.xyz  
        except AttributeError:
            self.errMessage="No 3D track available to plot. Please perform a 3D reconstruction and try again."
            self.errorTitle="No 3D track available to plot!"
            self.errorMsg()
            return None
              
        self.reconGroup.plot3DPoints()

    def save3DTrack(self):

        try:
            self.reconGroup.xyz  
            path = PyQt5.QtWidgets.QFileDialog.getSaveFileName(
                    self, 'Save File', '', 'CSV(*.csv)')[0]
            
            if path:
                self.reconGroup.xyz.to_csv(path,sep=',',index=False)
                self.errorTitle="3D track Successfully saved!"
                self.errMessage="Saved successfully to: %s" % path
                self.errorMsg()
        except AttributeError:
            self.errMessage="No 3D track available to save. Please perform a 3D reconstruction and try again."
            self.errorTitle="No 3D track available to save!"
            self.errorMsg()
            return None

    def show3Dcoords(self):
        
        try:
            self.reconGroup.xyz  
        except AttributeError:
            self.errMessage="No 3D track available to plot. Please perform a 3D reconstruction and try again."
            self.errorTitle="No 3D track available to plot!"
            self.errorMsg()
            return None
              
        self.reconGroup.populate_table()       

    def reconstruct_3D(self):
        """
        """
        try:
            if not self.tracksDict:
                raise AttributeError()
        except AttributeError:
            self.errMessage="No tracks have been loaded. Load at least two tracks and try again."
            self.errorTitle="No tracks loaded!"
            self.errorMsg()
            return None

        try:
            self.calib.coefficients
        except AttributeError:
            self.errMessage="No calibration file loaded. Please load a calibration file and then try again."
            self.errorTitle="No calibration loaded!"
            self.errorMsg()
            return None

        self.reconGroup.find3DCoordinates()
            
    def errorMsg(self):
        msg = PyQt5.QtWidgets.QMessageBox()
        msg.setIcon(PyQt5.QtWidgets.QMessageBox.Information)
        msg.setWindowIcon(PyQt5.QtGui.QIcon('misc/dice.png'))
        msg.setText(self.errMessage)
        msg.setWindowTitle(self.errorTitle)
        msg.setStandardButtons(PyQt5.QtWidgets.QMessageBox.Ok | PyQt5.QtWidgets.QMessageBox.Cancel)
        retval = msg.exec_()        
 
class BlockOutRegion(PyQt5.QtWidgets.QWidget):

    def __init__(self,MainWindow,load):
        super().__init__()
        self.MainWindow=MainWindow
        self.valid=True

        if load == False:

            self.ID, okPressed = PyQt5.QtWidgets.QInputDialog.getText(self, "Name region","Specify region's name:", PyQt5.QtWidgets.QLineEdit.Normal, "")

            if not self.checkInput(okPressed,self.ID):
                self.valid=False
                return None

            self.topx, okPressed = PyQt5.QtWidgets.QInputDialog.getInt(self, "Top x coordinate:","Enter an interger for the top x pixel coordinate of the region:", 0, 0, 10000, 1)
            
            if not self.checkInput(okPressed,self.topx):
                self.valid=False
                return None

            self.topy, okPressed = PyQt5.QtWidgets.QInputDialog.getInt(self, "Top y coordinate:","Enter an interger for the top y pixel coordinate of the region:", 0, 0, 10000, 1)

            if not self.checkInput(okPressed,self.topy):
                self.valid=False
                return None

            self.bottomx, okPressed = PyQt5.QtWidgets.QInputDialog.getInt(self, "Bottom x coordinate:","Enter an interger for the bottom x pixel coordinate of the region:", 0, 0, 10000, 1)

            if not self.checkInput(okPressed,self.bottomx):
                self.valid=False
                return None

            self.bottomy, okPressed = PyQt5.QtWidgets.QInputDialog.getInt(self, "Bottom y coordinate:","Enter an interger for the bottom y pixel coordinate of the region:", 0, 0, 10000, 1)

            if not self.checkInput(okPressed,self.bottomx):
                self.valid=False
                return None

            if self.valid==True:
                self.MainWindow.blockRegions_lw.addItem(self.ID)
    
        elif load==True:
            self.ID='placeholder'
            self.topx=1
            self.topy=1
            self.bottomx=1
            self.bottomy=1

    def checkInput(self, okPressed, input):
        if okPressed:
            return True
        else:
            return False
 
class PandasModel(PyQt5.QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """
    def __init__(self, data, parent=None):
        PyQt5.QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=PyQt5.QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == PyQt5.QtCore.Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == PyQt5.QtCore.Qt.Horizontal and role == PyQt5.QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        return None

class Image(PyQt5.QtWidgets.QGraphicsPixmapItem):
    """ create Pixmap image for each scene"""
    
    def __init__(self,path):
        super().__init__()
        
        self.setPixmap(PyQt5.QtGui.QPixmap(path))

class Scene(PyQt5.QtWidgets.QGraphicsScene):
    entered = PyQt5.QtCore.pyqtSignal([PyQt5.QtWidgets.QGraphicsItem],[PyQt5.QtWidgets.QGraphicsEllipseItem])
    leave = PyQt5.QtCore.pyqtSignal([PyQt5.QtWidgets.QGraphicsItem],[PyQt5.QtWidgets.QGraphicsEllipseItem])
    move = PyQt5.QtCore.pyqtSignal([PyQt5.QtWidgets.QGraphicsItem],[PyQt5.QtWidgets.QGraphicsEllipseItem])
    # press = PyQt5.QtCore.pyqtSignal([PyQt5.QtWidgets.QGraphicsItem],[PyQt5.QtWidgets.QGraphicsEllipseItem])
    """Each instance holds all image and ellipse data"""
    def __init__(self,MainWindow,**keywords):
        # executes PyQt5.QtWidgets.QGraphicsScene.__init__()
        super().__init__()
        
        # self.sceneCount=self.counter
        self.MainWindow=MainWindow
        self.keywords=keywords
        self.threshold=self.MainWindow.binary_sb.value()
        self.populated=False
        self.sceneID=''
        self.headx_px=''
        self.heady_px=''


        if 'path' in self.keywords.keys():
            self.getPathData(self.keywords['path'])
            self.binarize_image()
            self.findContours()
            self.image = Image(self.path)   
            self.addItem(self.image)

        if 'headers' in self.keywords.keys():
            self.headx_px = self.keywords['headers'][0]
            self.heady_px = self.keywords['headers'][1]
            xheader = self.headx_px.split("_")
            yheader = self.heady_px.split("_")
            self.sceneID = list(set(xheader).intersection(set(yheader)))[0]

            
        self.dotCoords={}
        if 'coords' in self.keywords.keys():
            self.pointCount=len(self.keywords['coords'][0])
            self.dotCoords['x_px']= self.keywords['coords'][0]
            self.dotCoords['y_px']= self.keywords['coords'][1]
        else:
            self.pointCount=0

            self.dotCoords['x_px']=[None]*len(self.MainWindow.pointData.index)
            self.dotCoords['y_px']=[None]*len(self.MainWindow.pointData.index)

        if self.sceneID in self.MainWindow.scenes:
            self.sceneID="%s_copy" %(self.sceneID)
        

    def populateLW(self):
        self.MainWindow.view_lw.addItem(self.sceneID)

    def changeImage(self,path):

        self.getPathData(path)
        self.binarize_image()
        self.findContours()
        self.remove_image()
        self.image = Image(self.path)   
        self.addItem(self.image)

    def setThreshold(self):
        self.threshold=self.MainWindow.binary_sb.value()
        
    def populateDotsOnLink(self):
        
        self.pointCount=0
        for i in range(len(self.MainWindow.pointData.index)):
            self.circle=Ellipse(0,0, 10, 10,self.pointCount)
            self.circle.setPos(self.dotCoords['x_px'][i]-5,self.dotCoords['y_px'][i]-5)
            self.circle.moved=True
            self.circle.setBrush(PyQt5.QtGui.QColor('green'))

            self.addItem(self.circle)
            self.pointCount += 1
        self.populated=True

    def linkView(self,path):

        if path[0]!='':

            self.getPathData(path[0])
            
            
            self.clear()
            
            self.image = Image(self.path)   
            self.addItem(self.image)
            self.binarize_image()
            self.findContours()

            self.populateDotsOnLink()

    def getPathData(self,path):
        self.path=path
        self.filename_w_ext = os.path.basename(path)
        self.filename, file_extension = os.path.splitext(self.filename_w_ext)
        self.root=os.path.dirname(os.path.abspath(path))

    def remove_image(self):
        self.removeItem(self.image)
    
    def refresh_image(self,path):
        self.image = Image(self.path)        
        self.addItem(self.image)

    def binarize_image(self):
        
        self.orig_image = cv2.imread(self.path)
        self.cnts_image=self.orig_image
        imageGray = cv2.cvtColor(self.orig_image,cv2.COLOR_BGR2GRAY)
        
        ret,self.cvBinaryImage = cv2.threshold(imageGray,self.threshold,255,cv2.THRESH_BINARY_INV)

        self.binaryImagePath=self.root+"\\" + self.filename+'_binary.jpg'
        cv2.imwrite(self.binaryImagePath, self.cvBinaryImage)
        
        # self.binarySceneName='%s_binary' % str(self.sceneID)
        self.binaryImage = Image(self.binaryImagePath)  
        
    def findContours(self):

        #Prevents a fatal crash due to version conflict in cv2.findContours
        try:
            
            self.cnts, hierachy = cv2.findContours(self.cvBinaryImage, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        except ValueError:
            ret, self.cnts, hierachy = cv2.findContours(self.cvBinaryImage, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)           
    
        self.good_cnts=[]
        for c in self.cnts:
            
            if self.MainWindow.lowCnt_sb.value() <= cv2.contourArea(c) <= self.MainWindow.highCnt_sb.value():
                self.good_cnts.append(c)
                cv2.drawContours(self.cnts_image, [c], -5, (255, 0, 0), 1)
                
                (xstart, ystart, w, h) = cv2.boundingRect(c)
                M = cv2.moments(c)
                try:
                    cx = int(M['m10']/M['m00'])
                    cy = int(M['m01']/M['m00'])
                    cv2.circle(self.cnts_image,(cx,cy),2,(0,0,255),-1)
                except ZeroDivisionError:
                    continue
        
        self.cntsImagePath=self.root+"\\" + self.filename+'_cnts.jpg'
        cv2.imwrite(self.cntsImagePath, self.cnts_image)
        self.contourImage=Image(self.cntsImagePath)

    def clearView(self):
        self.removeItem(self.image)
        self.removeItem(self.binaryImage)
        self.removeItem(self.contourImage)

    def showBinaryImage(self):
        self.clearView()
        self.addItem(self.binaryImage)

    def showContourImage(self):
        self.clearView()
        self.addItem(self.contourImage)

    def showOriginalImage(self):
        self.clearView()
        self.addItem(self.image)

    def correct_centers(self):
        
        self.findContours()

        for idx, i in enumerate(self.items()):
            
            if isinstance(i, Ellipse):
                if i.moved==True:
                    continue
                # if i.brush.color() == PyQt5.QtGui.QColor('green'):
                #     print("The color is green!")
                # if i.brush == PyQt5.QtGui.QColor('red'):
                #     print("The color is red!")

                for c in self.good_cnts:
                    (xstart, ystart, w, h) = cv2.boundingRect(c)

                    x=i.pos().toPoint().x()+5
                    y=i.pos().toPoint().y()+5
                    
                    if xstart <= x <= xstart+w and ystart <= y <= ystart+h:
                        M = cv2.moments(c)
                        try:
                            cx = int(M['m10']/M['m00'])
                            cy = int(M['m01']/M['m00'])

                            i.setX(cx-5)
                            i.setY(cy-5)
                            self.MainWindow.ellipseMove(i)
                            i.setBrush(PyQt5.QtGui.QColor('green'))
                            i.moved=True
                            
                        except ZeroDivisionError:
                            continue

    def showCoords(self, event):
        try:
            self.removeItem(self.text)
            self.removeItem(self.dot)
        except AttributeError:
            pass
        p=self.MainWindow.View.mapToScene(event.x(),event.y())
        self.dot=PyQt5.QtWidgets.QGraphicsEllipseItem(int(p.x())-3,int(p.y())-3, 6, 6)
        self.dot.setBrush(PyQt5.QtCore.Qt.blue)
        self.addItem(self.dot)
        self.text=PyQt5.QtWidgets.QGraphicsSimpleTextItem("x%s_y%s" % (str(int(p.x())+5),str(int(p.y())+5)))
        self.text.setBrush(PyQt5.QtCore.Qt.red)
        self.text.setPos(p.x(), p.y())
        self.addItem(self.text)
        # self.removeItem(self.text)

    def removeInfo(self, item):
        self.current_scene.removeItem(self.text)

    def add_point(self, event):
        
        try:
            self.path
        except AttributeError:
            self.MainWindow.errMessage="Please link calibration point data with a calibration view"
            self.MainWindow.errorTitle="Calibration view not linked"
            self.MainWindow.errorMsg()
            return None             

        if self.pointCount == self.MainWindow.num_points:
            self.MainWindow.errMessage="You have placed all the points listed in the calibration point file. If you wish to add more points, add more rows to the point file and start over."
            self.MainWindow.errorTitle="Cannot place any more points!"
            self.MainWindow.errorMsg()
            return None

        p=self.MainWindow.View.mapToScene(event.x(),event.y())
        self.circle=Ellipse(0,0, 10, 10,self.pointCount)
        self.circle.setPos(p.x()-5,p.y()-5)
        self.addItem(self.circle)
        self.dotCoords['x_px'][self.pointCount]=int(p.x())
        self.dotCoords['y_px'][self.pointCount]=int(p.y())
        self.MainWindow.refreshTableData()
        self.pointCount += 1

    def updateTableOnEllipseMove(self,x,y,item):
        
        self.dotCoords['x_px'][item.count]=int(x)
        self.dotCoords['y_px'][item.count]=int(y)
        self.MainWindow.refreshTableData()

class Ellipse(PyQt5.QtWidgets.QGraphicsEllipseItem):
    """creates circles placed in scene"""
    moved = PyQt5.QtCore.pyqtSignal(int,int)
    def __init__(self, x, y, w, h,count):
        super().__init__(x, y, w, h)

        self.count=count
        self.setBrush(PyQt5.QtGui.QColor('red'))
        self.setPen(PyQt5.QtGui.QColor('black'))
        self.setFlag(PyQt5.QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(PyQt5.QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(PyQt5.QtCore.Qt.SizeAllCursor)
        self.setZValue(100)
        self.moved=False

    def hoverEnterEvent(self, event) :
        super().hoverEnterEvent(event)
        self.scene().entered.emit(self)
        self.update()
        
    def hoverLeaveEvent(self, event):
        super().hoverEnterEvent(event)
        self.scene().leave.emit(self)
        self.update()
      
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.scene().move.emit(self)
        self.update()

class DLT:

    def __init__(self,nd,nc):
        
        self.nd=nd
        self.nc=nc

    def DLTcalib(self, nd, xyz, uv):
        """
        Camera calibration by DLT using known object points and their image points.

        This code performs 2D or 3D DLT camera calibration with any number of views (cameras).
        For 3D DLT, at least two views (cameras) are necessary.
        Inputs:
        nd is the number of dimensions of the object space: 3 for 3D DLT and 2 for 2D DLT.
        xyz are the coordinates in the object 3D or 2D space of the calibration points.
        uv are the coordinates in the image 2D space of these calibration points.
        The coordinates (x,y,z and u,v) are given as columns and the different points as rows.
        For the 2D DLT (object planar space), only the first 2 columns (x and y) are used.
        There must be at least 6 calibration points for the 3D DLT and 4 for the 2D DLT.
        Outputs:
        L: array of the 8 or 11 parameters of the calibration matrix
        err: error of the DLT (mean residual of the DLT transformation in units of camera coordinates).
        """
        #Convert all variables to numpy array:
        xyz = np.asarray(xyz)
        uv = np.asarray(uv)
        #number of points:
        np = xyz.shape[0]
        #Check the parameters:
        if uv.shape[0] != np:
            raise ValueError('xyz (%d points) and uv (%d points) have different number of points.' %(np, uv.shape[0]))
        if (nd == 2 and xyz.shape[1] != 2) or (nd == 3 and xyz.shape[1] != 3):
            raise ValueError('Incorrect number of coordinates (%d) for %dD DLT (it should be %d).' %(xyz.shape[1],nd,nd))
        if nd == 3 and np < 6 or nd == 2 and np < 4:
            raise ValueError('%dD DLT requires at least %d calibration points. Only %d points were entered.' %(nd, 2*nd, np))
            
        #Normalize the data to improve the DLT quality (DLT is dependent of the system of coordinates).
        #This is relevant when there is a considerable perspective distortionp.
        #Normalization: mean position at origin and mean distance equals to 1 at each directionp.
        Txyz, xyzn = self.Normalization(nd, xyz)
        Tuv, uvn = self.Normalization(2, uv)

        A = []
        if nd == 2: #2D DLT
            for i in range(np):
                x,y = xyzn[i,0], xyzn[i,1]
                u,v = uvn[i,0], uvn[i,1]
                A.append( [x, y, 1, 0, 0, 0, -u*x, -u*y, -u] )
                A.append( [0, 0, 0, x, y, 1, -v*x, -v*y, -v] )
        elif nd == 3: #3D DLT
            for i in range(np):
                x,y,z = xyzn[i,0], xyzn[i,1], xyzn[i,2]
                u,v = uvn[i,0], uvn[i,1]
                A.append( [x, y, z, 1, 0, 0, 0, 0, -u*x, -u*y, -u*z, -u] )
                A.append( [0, 0, 0, 0, x, y, z, 1, -v*x, -v*y, -v*z, -v] )

        #convert A to array
        A = np.asarray(A) 
        #Find the 11 (or 8 for 2D DLT) parameters:
        U, S, Vh = np.linalg.svd(A)
        #The parameters are in the last line of Vh and normalize them:
        L = Vh[-1,:] / Vh[-1,-1]
        #Camera projection matrix:
        H = L.reshape(3,nd+1)
        #Denormalization:
        H = np.dot( np.dot( np.linalg.pinv(Tuv), H ), Txyz );
        H = H / H[-1,-1]
        self.L = H.flatten(0)
        #Mean error of the DLT (mean residual of the DLT transformation in units of camera coordinates):
        uv2 = np.dot( H, np.concatenate( (xyz.T, np.ones((1,xyz.shape[0]))) ) ) 
        uv2 = uv2/uv2[2,:] 
        #mean distance:
        self.err = np.sqrt( np.mean(np.sum( (uv2[0:2,:].T - uv)**2,1 )) ) 

        return self.L, self.err

    def Normalization(self,nd,x):
        '''
        Normalization of coordinates (centroid to the origin and mean distance of sqrt(2 or 3).

        Inputs:
            nd: number of dimensions (2 for 2D; 3 for 3D)
            x: the data to be normalized (directions at different columns and points at rows)
        Outputs:
            Tr: the transformation matrix (translation plus scaling)
            x: the transformed data
        '''

        x = np.asarray(x)
        m, s = np.mean(x,0), np.std(x)
        if nd==2:
            Tr = np.array([[s, 0, m[0]], [0, s, m[1]], [0, 0, 1]])
        else:
            Tr = np.array([[s, 0, 0, m[0]], [0, s, 0, m[1]], [0, 0, s, m[2]], [0, 0, 0, 1]])
            
        Tr = np.linalg.inv(Tr)
        x = np.dot( Tr, np.concatenate( (x.T, np.ones((1,x.shape[0]))) ) )
        x = x[0:nd,:].T

        return Tr, x

    def DLTrecon(self,nd, nc, Ls, uvs):
        '''
        Reconstruction of object point from image point(s) based on the DLT parameters.

        This code performs 2D or 3D DLT point reconstruction with any number of views (cameras).
        For 3D DLT, at least two views (cameras) are necessary.
        Inputs:
        nd is the number of dimensions of the object space: 3 for 3D DLT and 2 for 2D DLT.
        nc is the number of cameras (views) used.
        Ls (array type) are the camera calibration parameters of each camera 
        (is the output of DLTcalib function). The Ls parameters are given as columns
        and the Ls for different cameras as rows.
        uvs are the coordinates of the point in the image 2D space of each camera.
        The coordinates of the point are given as columns and the different views as rows.
        Outputs:
        xyz: point coordinates in space
        '''
        
        #Convert Ls to array:
        Ls = np.asarray(Ls) 
        #Check the parameters:
        if Ls.ndim ==1 and nc != 1:
            self.errMessage="Number of views (%d) and number of sets of camera calibration parameters (%d) are different. Either add/remove views or load the correct calibration file." % (nc, len(Ls))
            self.errorTitle="Wrong # of views!"
            self.errorMsg()
            return None,False  

            # raise ValueError('Number of views (%d) and number of sets of camera calibration parameters (1) are different.' %(nc))    
        if Ls.ndim > 1 and nc != Ls.shape[0]:

            self.errMessage="Number of views (%d) and number of sets of camera calibration parameters (%d) are different. Either add/remove views or load the correct calibration file." % (nc, len(Ls))
            self.errorTitle="Wrong # of views!"
            self.errorMsg()
            return None,False  

            # raise ValueError('Number of views (%d) and number of sets of camera calibration parameters (%d) are different.' %(nc, Ls.shape[0]))
        if nd == 3 and Ls.ndim == 1:
            self.errMessage='At least two sets of camera calibration parameters are needed for 3D point reconstruction.'
            self.errorTitle="No enough views!"
            self.errorMsg()
            return None,False
            # raise ValueError('At least two sets of camera calibration parameters are needed for 3D point reconstruction.')

        if nc == 1: #2D and 1 camera (view), the simplest (and fastest) case
            #One could calculate inv(H) and input that to the code to speed up things if needed.
            #(If there is only 1 camera, this transformation is all Floatcanvas2 might need)
            Hinv = np.linalg.inv( Ls.reshape(3,3) )
            #Point coordinates in space:
            xyz = np.dot( Hinv,[uvs[0],uvs[1],1] ) 
            xyz = xyz[0:2]/xyz[2]       
        else:
            M = []
            for i in range(nc):
                L = Ls[i,:]
                u,v = uvs[i][0], uvs[i][1] #this indexing works for both list and numpy array
                if nd == 2:      
                    M.append( [L[0]-u*L[6], L[1]-u*L[7], L[2]-u*L[8]] )
                    M.append( [L[3]-v*L[6], L[4]-v*L[7], L[5]-v*L[8]] )
                elif nd == 3:  
                    M.append( [L[0]-u*L[8], L[1]-u*L[9], L[2]-u*L[10], L[3]-u*L[11]] )
                    M.append( [L[4]-v*L[8], L[5]-v*L[9], L[6]-v*L[10], L[7]-v*L[11]] )
            
            #Find the xyz coordinates:
            U, S, Vh = np.linalg.svd(np.asarray(M))
            #Point coordinates in space:
            xyz = Vh[-1,0:-1] / Vh[-1,-1]
        
            
        return xyz, True

    def errorMsg(self):
        msg = PyQt5.QtWidgets.QMessageBox()
        msg.setWindowIcon(PyQt5.QtGui.QIcon('dice.png'))
        msg.setIcon(PyQt5.QtWidgets.QMessageBox.Information)
        msg.setText(self.errMessage)
        msg.setWindowTitle(self.errorTitle)
        msg.setStandardButtons(PyQt5.QtWidgets.QMessageBox.Ok | PyQt5.QtWidgets.QMessageBox.Cancel)
        retval = msg.exec_() 

class CalibrationWindow(PyQt5.QtWidgets.QMainWindow, calibration_ui.Ui_CalibrationWindow):

    """main user interface """
    def __init__(self, parent=None):
        
        super(CalibrationWindow, self).__init__(parent)

        self.setupUi(self)
        self.setWindowTitle("Calibrate 3D")

        self.setWindowIcon(PyQt5.QtGui.QIcon(os.path.dirname(os.path.abspath(__file__))+'/misc/dice.png'))
        
        self.scenes={}
        self.calibrate=DLT(3,2)
        self.tableCreated=False
        self.calStyleSheet = "::section{Background-color:rgb(190,1,1);border-radius:14px;}"
        # self.tableWidget.horizontalHeader().setStyleSheet(calStyleSheet)

        self.initUI()

    def initUI(self):   
        
        #button connects
        self.addPointFile_b.clicked.connect(self.newGetCalibrationPoints)
        self.loadFilledTable_b.clicked.connect(self.readInTable)
        self.loadCal_b.clicked.connect(self.loadCalibration)
        self.newView_b.clicked.connect(self.new_add_scene)
        self.link_b.clicked.connect(self.linkView)
        self.correct_b.clicked.connect(self.button_correct_centers)
        self.binary_sb.valueChanged.connect(self.redo_binarization)
        self.saveTable_b.clicked.connect(self.saveTable)
        self.calibrate_b.clicked.connect(self.calibrate3D)
        self.loadTest_b.clicked.connect(self.loadTestTableData)
        self.testCal_b.clicked.connect(self.test3DCalibration)
        self.delete_b.clicked.connect(self.deleteView)
        self.saveTest_b.clicked.connect(self.saveTestData)
        self.saveCalibration_b.clicked.connect(self.saveCalibration)
        
        #list widget connects
        # self.view_lw.clicked.connect(self.change_scene)
        self.view_lw.currentRowChanged.connect(self.change_scene)
        self.original_rb.toggled.connect(self.change_scene)
        self.binary_rb.toggled.connect(self.change_scene)
        self.contour_rb.toggled.connect(self.change_scene)
        
        #other
        self.View.mouseDoubleClickEvent= self.add_point
        self.slider.setRange(1, 500)
        self.slider.setValue(100)
        self.slider.valueChanged[int].connect(self.onZoom)
        self.lowCnt_sb.valueChanged.connect(self.redo_binarization)
        self.highCnt_sb.valueChanged.connect(self.redo_binarization)
        self.groupBox_8.setVisible(False)
        self.link_b.setVisible(False)
        self.radioButton_2.toggled['bool'].connect(self.link_b.setVisible)

        self.changeImage_b.clicked.connect(self.changeImage)

    def changeImage(self):

        if not hasattr(self, 'current_scene'):

            self.errMessage="Please first load a view with an associated calibration image and try again."
            self.errorTitle="No view yet loaded!"
            self.errorMsg()
            return None     
        

        imagePath=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,"Load calibration file", self.current_scene.path, filter="Text files( *.jpg *.png)")

        if imagePath[0] != '':       
            self.current_scene.changeImage(imagePath[0])

    def linkView(self):

        if self.view_lw.count() == 0:
            self.errMessage="No views available for linking."
            self.errorTitle="Cannot link view"
            self.errorMsg()
            return None            

        self.selectedItemText=self.view_lw.currentItem().text()
        self.current_scene=self.scenes[self.selectedItemText]

        path=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,
        "Load image view",filter="Image Files( *.png *.jpg)")

        self.scenes[self.selectedItemText].linkView(path)
        self.change_scene()
        self.View.setScene(self.current_scene)

    def deleteView(self):
        
        try:
            self.selectedItemText=self.view_lw.currentItem().text()
        except AttributeError:
            self.errMessage="Please click on the view to remove."
            self.errorTitle="No view selected"
            self.errorMsg()
            return None
        xCol=str(self.scenes[self.selectedItemText].headx_px)
        yCol=str(self.scenes[self.selectedItemText].heady_px)
        self.pointData.drop(columns=[xCol, yCol],inplace =True)
        self.scenes.pop(self.selectedItemText)
        self.view_lw.takeItem(self.view_lw.currentRow())

        try:
            self.firstSceneKey=list(self.scenes.keys())[0]
            self.current_scene=self.scenes[self.firstSceneKey]
            self.current_scene.showOriginalImage()
            item=self.view_lw.findItems(self.current_scene.sceneID,PyQt5.QtCore.Qt.MatchExactly)[0]
            item.setSelected(True)
            self.view_lw.setCurrentItem(item)
            self.View.setScene(self.current_scene)
        except IndexError:
            self.current_scene.clear()
        except AttributeError:
            pass
        
        self.tableWidget.setModel(PandasModel(self.pointData))
        self.tableWidget.horizontalHeader().setStyleSheet(self.calStyleSheet)

    """
    Table loading and manipulation methods
    """
    def newGetCalibrationPoints(self):

        self.promptSceneDelete()
        pointFilePath=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,"Load point data file",filter="Text files( *.txt *.csv)")

        if pointFilePath[0]!='':

            self.pointData=pd.read_csv(pointFilePath[0])
            self.num_points=len(self.pointData.index)
            self.nmbViews=(len(self.pointData.columns)-3)/2
            if self.nmbViews > 0:
                self.errMessage="Please load a file containing colums for only the point coordinates."
                self.errorTitle="File contains view data!"
                self.errorMsg()
                return None  
            self.tableWidget.setModel(PandasModel(self.pointData))
            self.tableWidget.horizontalHeader().setStyleSheet(self.calStyleSheet)

            self.tabWidget.setCurrentIndex(1)
            self.pointFile_l.setText(pointFilePath[0])         
    
    def refreshTableData(self):

        for key in self.scenes:

            for inner_key in self.scenes[key].dotCoords:
                if inner_key == 'x_px':
                    self.pointData[self.scenes[key].headx_px]=self.scenes[key].dotCoords[inner_key]
                if inner_key == 'y_px':
                    self.pointData[self.scenes[key].heady_px]=self.scenes[key].dotCoords[inner_key]

        self.tableWidget.setModel(PandasModel(self.pointData))
        self.tableWidget.horizontalHeader().setStyleSheet(self.calStyleSheet)
        
    def promptSceneDelete(self):

        if self.view_lw.count() > 0:

            reply = PyQt5.QtWidgets.QMessageBox.question(self, 'Continue?', 
                    'Loading a new calibration table will delete existing views, accept?', PyQt5.QtWidgets.QMessageBox.Yes, PyQt5.QtWidgets.QMessageBox.No)
            if reply == PyQt5.QtWidgets.QMessageBox.Yes:
                self.scenes={}
                self.view_lw.clear()
            else:
                return None
            
    def readInTable(self):

        self.promptSceneDelete()
        pointFilePath=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,"Load populated point data file",filter="Text files( *.txt *.csv)")

        if pointFilePath[0]!='':
            self.pointData=pd.read_csv(pointFilePath[0])
            self.num_points=len(self.pointData.index)
            self.nmbViews=int((len(self.pointData.columns)-3)/2)
            self.headers=list(self.pointData.columns) 

            if self.nmbViews < 2:
                self.errMessage="File does not contain data sufficient for at least two views"
                self.errorTitle="Not enough views in file"
                self.errorMsg()
                return None 

            col=3
            for i in range(self.nmbViews):
                colNames=[]
                colNames.append(self.headers[col])
                colNames.append(self.headers[col+1])
                
                coords=[]
                coords.append(self.pointData[self.headers[col]])
                coords.append(self.pointData[self.headers[col+1]])

                
                self.current_scene=Scene(self,coords=coords,headers=colNames)
                
                self.current_scene.entered.connect(self.displayInfo)
                self.current_scene.leave.connect(self.removeInfo)
                self.current_scene.move.connect(self.ellipseMove)
                
                self.scenes[self.current_scene.sceneID]=self.current_scene
                self.current_scene.populateLW()
                # self.View.setScene(self.current_scene)
                item=self.view_lw.findItems(self.current_scene.sceneID,PyQt5.QtCore.Qt.MatchExactly)[0]
                item.setSelected(True)
                self.view_lw.setCurrentItem(item)
                # self.newView_b.setText("Add view")
                
                col+=2

            self.pointFile_l.setText(pointFilePath[0])
            self.tableWidget.setModel(PandasModel(self.pointData))
            self.tableWidget.horizontalHeader().setStyleSheet(self.calStyleSheet)

            self.tabWidget.setCurrentIndex(1)
            
    def saveTable(self):

        path = PyQt5.QtWidgets.QFileDialog.getSaveFileName(
                self, 'Save File', '', 'CSV(*.csv)')[0]
        self.pointData.to_csv(path,index=False)
        

    """
    View and Scene related methods
    """

    def new_add_scene(self):

        if not hasattr(self, 'pointData'):

            self.errMessage="Please load a point file or a populate calibration file and then try again."
            self.errorTitle="Cannot add view!"
            self.errorMsg()
            return None       

        sceneID, okPressed = PyQt5.QtWidgets.QInputDialog.getText(self, "Name view","Specify View's ID:", PyQt5.QtWidgets.QLineEdit.Normal, "")

        if not okPressed:
            sceneID="Please specify correctly"

        if sceneID =='':
            sceneID="Please specify correctly"

        viewPath=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,
        "Load image view",filter="Image Files( *.png *.jpg)")

        if viewPath[0]!='':

            self.current_scene=Scene(self,path=viewPath[0])
            self.current_scene.entered.connect(self.displayInfo)
            self.current_scene.leave.connect(self.removeInfo)
            self.current_scene.move.connect(self.ellipseMove)
            self.current_scene.headx_px="%s_x" %sceneID
            self.current_scene.heady_px="%s_y" %sceneID
            self.current_scene.sceneID=sceneID
            self.current_scene.populateLW()
            self.scenes[self.current_scene.sceneID]=self.current_scene
            self.View.setScene(self.current_scene)
            item=self.view_lw.findItems(self.current_scene.sceneID,PyQt5.QtCore.Qt.MatchExactly)[0]
            item.setSelected(True)
            self.view_lw.setCurrentItem(item)
            self.newView_b.setText("Add view")

            self.pointData[self.current_scene.headx_px]=np.nan
            self.pointData[self.current_scene.heady_px]=np.nan
            self.tableWidget.setModel(PandasModel(self.pointData))
            self.tableWidget.horizontalHeader().setStyleSheet(self.calStyleSheet)
            self.tabWidget.setCurrentIndex(1)

    def my_decorator(self):
        
        for count, scene in enumerate(self.scenes):
            
            if scene in self.selectedItemText:
                
                self.current_scene=self.scenes[scene]
                
    def change_scene(self):
        self.tabWidget.setCurrentIndex(0)
        try:
            self.selectedItemText=self.view_lw.currentItem().text()
           
            self.my_decorator()

            if not hasattr(self.current_scene, 'path'):
                emptyScene=PyQt5.QtWidgets.QGraphicsScene()
                self.View.setScene(emptyScene)
                return None
                
            self.binary_sb.setValue(self.current_scene.threshold)
            
            if self.original_rb.isChecked()==True:
                self.current_scene.showOriginalImage()
            elif self.binary_rb.isChecked()==True:
                self.current_scene.showBinaryImage()
            elif self.contour_rb.isChecked()==True:
                self.current_scene.showContourImage()
            self.View.setScene(self.current_scene)
        except AttributeError:
            pass

    def redo_binarization(self):

        if not hasattr(self, 'pointData'):
                self.errMessage="Please select a view then try again."
                self.errorTitle="No view selected!"
                self.errorMsg()
                return None    

        try:
            self.selectedItemText=self.view_lw.currentItem().text()
            
        except IndexError:
            self.errMessage="Please click on a view to work with."
            self.errorTitle="No view selected"
            self.errorMsg()
            return None
        except AttributeError:
            self.errMessage="Please click on a view to work with."
            self.errorTitle="No view selected"
            self.errorMsg()
            return None      

        try:
            self.my_decorator()
            self.current_scene.setThreshold()
            self.current_scene.findContours()
            self.current_scene.binarize_image()
            self.change_scene()
        except AttributeError:
            pass

    def onZoom(self, value):
        val = value / 100    
        self.View.resetTransform()
        self.View.scale(val, val)    

    """
    Calibration marker methods
    """
    def add_point(self, event):
        self.current_scene.add_point(event)

    def showCoords(self, event):
        self.current_scene.showCoords(event)

    def button_correct_centers(self):
        try:
            self.current_scene.correct_centers()
            self.change_scene()
        except AttributeError:
            pass

    def displayInfo(self, item):
        self.text=PyQt5.QtWidgets.QGraphicsSimpleTextItem("P%s_x%s_y%s" % (str(item.count+1),str(item.pos().toPoint().x()+5),str(item.pos().toPoint().y()+5)))
        self.text.setBrush(PyQt5.QtCore.Qt.red)
        self.text.setPos(item.pos().toPoint().x()+10, item.pos().toPoint().y()+10)
        self.current_scene.addItem(self.text)

    def removeInfo(self, item):
        self.current_scene.removeItem(self.text)

    def ellipseMove(self, item):
        item.setBrush(PyQt5.QtGui.QColor('red'))
        item.moved=False
        self.current_scene.removeItem(self.text)
        x=str(item.pos().toPoint().x()+5)
        y=str(item.pos().toPoint().y()+5)  

        self.current_scene.updateTableOnEllipseMove(x,y,item)         

    """
    Calibration and testing methods
    """
    def calibrate3D(self):

        try:
            x=list(self.pointData['x'])
            y=list(self.pointData['y'])
            z=list(self.pointData['z'])

        except AttributeError:
            self.errMessage="Fully populate the calibration table to continue."
            self.errorTitle="Calibration table not correctly populated!"
            self.errorMsg()
            return None   

        #set up xyz coords list
        xyz=[]

        for i in range(len(x)):
                point=[]
                point.append(x[i])
                point.append(y[i])
                point.append(z[i])
                print(point)
                xyz.append(point)
 
        px_coords=[]
        for key in self.scenes:
            view_coords=[]
            x_px=list(self.pointData[self.scenes[key].headx_px])
            y_px=list(self.pointData[self.scenes[key].heady_px])
            view_coords.append(x_px)
            view_coords.append(y_px)
            px_coords.append(view_coords)
        
        self.nmbDim=3
        self.coefficients=[]
        errors=[]
        
        self.nmbCam=self.nmbViews
    
        #get parameters for each view
        for view in px_coords:
            uv=[]
            for i in range(len(view[0])):
                
                pair=[]
                pair.append(view[0][i])
                pair.append(view[1][i])
                uv.append(pair)
            L, err = self.calibrate.DLTcalib(self.nmbDim, xyz, uv)
            
            self.coefficients.append(L)
            errors.append(err)
        

    def loadTestTableData(self):

        pointFilePath=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,"Load populated test table",filter="Text files( *.txt *.csv)")

        if pointFilePath[0]!='':
            self.testData=pd.read_csv(pointFilePath[0])
            self.numTestPoints=len(self.testData.index)
            self.numTestViews=int((len(self.testData.columns)-3)/2)
            self.testHeaders=list(self.testData.columns) 

            if self.numTestViews < 2:
                self.errMessage="File contains less than two views"
                self.errorTitle="Not enough views in file"
                self.errorMsg()
                return None 

        self.tableWidget.setModel(PandasModel(self.testData))
        self.tableWidget.horizontalHeader().setStyleSheet(self.calStyleSheet)
        self.tabWidget.setCurrentIndex(1)

    def saveCalibration(self):

        try:
            test=self.coefficients

        except AttributeError:
            self.errMessage="Perform a calibration and then try again."
            self.errorTitle="No calibration available!"
            self.errorMsg()
            return None   

        path = PyQt5.QtWidgets.QFileDialog.getSaveFileName(
                self, 'Save File', '', 'CSV(*.csv)')[0]
        if path:
            
            self.coefficients_df=pd.DataFrame(self.coefficients)
            self.coefficients_df.to_csv(path,sep=',',index=False,header=False)
            self.errorTitle="Successfully saved!"
            self.errMessage="Saved successfully to: %s" % path
            self.errorMsg()

    def loadCalibration(self):
        pointFilePath=PyQt5.QtWidgets.QFileDialog.getOpenFileName(self,"Load calibration file",filter="Text files( *.txt *.csv)")
        self.coefficients=[]
    
        if pointFilePath[0]!='':
            self.dfCoefficients=pd.read_csv(pointFilePath[0],header=None)
        
            for index, row in self.dfCoefficients.iterrows():
                self.coefficients.append(np.asarray(list(row)))
        print(self.coefficients)
        self.tabWidget.setCurrentIndex(1)

    def test3DCalibration(self):            

            x=list(self.testData[self.testHeaders[0]])
            y=list(self.testData[self.testHeaders[1]])
            z=list(self.testData[self.testHeaders[2]])

            self.testXYZ=[]
            for i in range(self.numTestPoints):
                testCoord=[]
                testCoord.append(x[i])
                testCoord.append(y[i])
                testCoord.append(z[i])
                self.testXYZ.append(testCoord)
            
            testPxCoords=[]
            col=3
            for i in range(self.numTestViews):
                colNames=[]

                colNames.append(self.testHeaders[col])
                colNames.append(self.testHeaders[col+1])
                x_px=list(self.testData[self.testHeaders[col]])
                y_px=list(self.testData[self.testHeaders[col+1]])
            
                coords=[]
                for i in range(len(x_px)):
                    pair=[]
                    pair.append(x_px[i])
                    pair.append(y_px[i])
                    coords.append(pair)

                testPxCoords.append(coords)
                col+=2


            xyz1234 = np.zeros((len(self.testXYZ),3))
            
            #use parameters to reconstruct input points 
            for i in range(len(testPxCoords[0])):
                print(self.numTestViews)
                i_px_coords=[]
                for view in testPxCoords:
                    i_px_coords.append(view[i])
                try:
                    xyz1234[i,:], ret = self.calibrate.DLTrecon(3,self.numTestViews,self.coefficients,i_px_coords)
                except AttributeError:
                    self.errMessage="No calibration available"
                    self.errorTitle="Perform a calibration, then try again."
                    self.errorMsg()
                    return None   
                except ValueError:
                    self.errMessage="Ensure you have loaded a valid calibration file and a valid marker test point file. The calibration file should have 12 columns and as many rows as were used to perform the calibration. The test point file should have 2x the number of views used to obtain the calibration plus 3 more columns for the object-space coordinates."
                    self.errorTitle="Calibration and test point files are incompatabile!"
                    self.errorMsg()
                    return None                                       


            rec_xyz=pd.DataFrame(xyz1234,columns=['rec_x','rec_y','rec_z'])
            xyz=pd.DataFrame(self.testXYZ,columns=['x','y','z'])
            self.results=pd.concat([xyz,rec_xyz], axis=1)
            self.results['x_e']=self.results['x']-self.results['rec_x']
            self.results['y_e']=self.results['y']-self.results['rec_y']
            self.results['z_e']=self.results['z']-self.results['rec_z']

            self.x_std=self.results['x_e'].abs().std()
            self.y_std=self.results['y_e'].abs().std()
            self.z_std=self.results['z_e'].abs().std()

            self.xmean_l.setText("%.4f" % ((self.results.x - self.results.rec_x)**2).mean()**.5)
            self.ymean_l.setText("%.4f" % ((self.results.y - self.results.rec_y)**2).mean()**.5)
            self.zmean_l.setText("%.4f" % ((self.results.z - self.results.rec_z)**2).mean()**.5)

            self.xstd_l.setText("%.4f" % self.x_std)
            self.ystd_l.setText("%.4f" % self.y_std)
            self.zstd_l.setText("%.4f" % self.z_std)

            self.pointsTested_l.setText(str(self.numTestPoints))

            self.errorTitle="Calibration test successful!"
            self.errMessage="The test completed with success. If desired, consult the simple statistics below or save the test's results and postprocess with a third party application."
            self.errorMsg()
            # print(self.results)

            # print(np.mean(np.sqrt(np.sum((np.array(xyz1234)-np.array(xyz))**2,1))))

    def saveTestData(self):
        path = PyQt5.QtWidgets.QFileDialog.getSaveFileName(
                self, 'Save File', '', 'CSV(*.csv)')[0]
        if path:
            self.results.to_csv(path,sep=',',index=False)
            self.errorTitle="Successfully saved!"
            self.errMessage="Saved successfully to: %s" % path
            self.errorMsg()

    """
    Utility functions
    """
    def errorMsg(self):
        msg = PyQt5.QtWidgets.QMessageBox()
        msg.setWindowIcon(PyQt5.QtGui.QIcon('misc/dice.png'))
        msg.setIcon(PyQt5.QtWidgets.QMessageBox.Information)
        msg.setText(self.errMessage)
        msg.setWindowTitle(self.errorTitle)
        msg.setStandardButtons(PyQt5.QtWidgets.QMessageBox.Ok | PyQt5.QtWidgets.QMessageBox.Cancel)
        retval = msg.exec_() 

class Processing3D:

    """For 3D processing of two or more 2D tracks, contains functions to view and save 3D tracks.

    TODO: Add functionality for more than 2 cameras.
    """
    
    def __init__(self,MainWindow):

        ## Instance of MainWindow
        self.MainWindow = MainWindow

        ## Dict of tracks available in self.MainWindow.tracksDict
        self.tracksDict=self.MainWindow.tracksDict

        ## Instance of DLT
        self.DLT=DLT(3,2)

        for key in self.tracksDict.keys():
            self.tracksDict[key].getMatrix()

        ## Number of dimensions to track in
        self.nd=3
        ## Number of views (or cameras) used
        self.nc=len(self.tracksDict.keys())

        ## List of numpy arrays containing x_px and y_px locations
        ## for each track.
        self.matrices=[None]*self.nc
        self.organizeViews()

    def organizeViews(self):
        """Organizes matrices in the order of their associated track's viewNumber.

        Currently supports up to 4 views, however more can be added if ever
        necessary.
        """
        for key in self.tracksDict.keys():
            if self.tracksDict[key].viewNumber == 1:
                self.matrices[0]=self.tracksDict[key].matrix
                
            elif self.tracksDict[key].viewNumber == 2:
                self.matrices[1]=self.tracksDict[key].matrix
                     
            elif self.tracksDict[key].viewNumber == 3:
                self.matrices[2]=self.tracksDict[key].matrix
                       
            elif self.tracksDict[key].viewNumber == 4:
                self.matrices[3]=self.tracksDict[key].matrix
                       
    def find3DCoordinates(self):

        """Uses DLT.DLTrecon() to determine 3D location of tracked object

        TODO: Add functionality to handle self.nc>2      

        1 - Gets calibration coefficients
        2 - Creates self.xys array full of zeros
        3 - Reconstructs the xyz coordinate frame by frame
                - places pixel coordinates for each view in i_px_coords
                - sends i_px_coords to get reconstructed
                - breaks if there is an error in the loop
                - will print error statement in DLT()
        4 - sets self.xyz as a pandas dataframe
        5 - populates self.pp_TV and sets label text  
        """
        
        ## calibration coefficients 
        self.coefficients=self.MainWindow.calib.coefficients

        if self.nc==2:
            ## Array (or pd.DataFrame) containing 3D reconstructed points
            self.xyz = np.zeros((len(self.matrices[0]), 3))

            for i in range(len(self.matrices[0])):
                i_px_coords=[]
                for view in self.matrices:
                    i_px_coords.append(view[i])
                self.xyz[i,:], ret = self.DLT.DLTrecon(self.nd, self.nc, self.coefficients, i_px_coords) 
                if ret == False:
                    break     

            if ret == True:
                self.xyz = pd.DataFrame(self.xyz, columns=['x', 'y', 'z'])
        
                self.populate_table()
                self.MainWindow.tableItem_l.setText('Showing 3D coordinates of reconstructed track')

        # Add additional camera functionality here
        if self.nc==3:
            pass
        if self.nc==4:
            pass


    def plot3DPoints(self):

        """Plots a 3D scatter plot of reconstructed track.
        """
        ## matPlotLib axis
        self.ax = plt.figure().gca(projection='3d')
        self.ax.scatter(self.xyz.x, self.xyz.y, self.xyz.z)
        self.ax.set_xlabel('x (calibration units)')
        self.ax.set_ylabel('y (calibration units)')
        self.ax.set_zlabel('z (calibration units)')

        try:
            self.ax.set_xlim(int(self.MainWindow.xmax_le.text()), int(self.MainWindow.xmin_le.text()))
            self.ax.set_ylim(int(self.MainWindow.ymax_le.text()), int(self.MainWindow.ymin_le.text()))
            self.ax.set_zlim(int(self.MainWindow.zmax_le.text()), int(self.MainWindow.zmin_le.text()))
        except ValueError:
            pass

        plt.show()

    def populate_table(self):
        """Populates self.MainWindow.pp_TV with self.xyz.
        """
        self.MainWindow.pp_TV.setModel(PandasModel(self.xyz))

class Calibration:

    def __init__(self,fileobj,MainWindow):

        self.MainWindow=MainWindow
        self.fileobj=fileobj
        
        self.path, self.basename=os.path.split(os.path.abspath(self.fileobj))
        self.calID=os.path.splitext(self.basename)[0]
        
        self.coefficients=[]

        self.dfCoefficients=pd.read_csv(fileobj,header=None)
        
        for index, row in self.dfCoefficients.iterrows():
            self.coefficients.append(np.asarray(list(row)))

        self.calNumber=None

    def populateTable(self):

        self.calTable_orig=pd.read_csv(self.fileobj,header=None)
        self.calTable_orig.columns= ['L1','L2','L3','L4','L5','L6','L7','L8','L9','L10','L11','L12']
           
        self.calTable=self.calTable_orig.copy(deep=True)
        self.MainWindow.pp_TV.setModel(PandasModel(self.calTable))

class TrackProcessing():
    
    def __init__(self,fileobj,MainWindow):
        self.MainWindow=MainWindow
        self.fileobj=fileobj
        
        self.orig_df=pd.read_csv(self.fileobj,header=None)
        self.orig_df.columns= ['Image frame', 'x_px','y_px']
        self.orig_df=self.orig_df.replace(0.0, np.nan)
        self.orig_df=self.orig_df.round(0)
           
        self.df=self.orig_df.copy(deep=True)

        self.path, self.basename=os.path.split(os.path.abspath(self.fileobj))
        self.trackID=os.path.splitext(self.basename)[0]
        
        self.getMatrix()
        self.viewNumber=None

    def saveTrack(self):

        print('this is the right function')
        path = PyQt5.QtWidgets.QFileDialog.getSaveFileName(None, 'Save track as ...', self.MainWindow.path, 'CSV(*.csv)')[0]

        self.df.to_csv(path, header=False,index=False)        

    def plotNoConditions(self):
        
        self.x='x_px'
        self.y='y_px'
        self.color='Red'
        self.label="pixel coordinates"
        ax=self.df.plot(x=self.x,y=self.y,kind='scatter',color=self.color, figsize=[7,2], label=None)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        plt.legend(loc='best',prop={'size':10}, frameon=True, shadow=True, bbox_to_anchor=(1.1, 1.1))
        plt.title('Track for %s' % self.trackID, style='italic')
        fig = ax.get_figure()
        plt.show()

        self.populateTable()

    def plot_pixel_coordinates(self):
        
        if self.MainWindow.show2Dplot_B.isChecked()==True:

            self.x='x_px'
            self.y='y_px'
            self.color='Red'
            self.label="pixel coordinates"
            ax=self.df.plot(x=self.x,y=self.y,kind='scatter',color=self.color, figsize=[7,2], label=None)
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            plt.legend(loc='best',prop={'size':10}, frameon=True, shadow=True, bbox_to_anchor=(1.1, 1.1))
            plt.title('Track for %s' % self.trackID, style='italic')
            fig = ax.get_figure()
            plt.show()

        self.populateTable()

    def reinitializeCoords(self):
        self.df=self.orig_df.copy(deep=True)
        self.plot_pixel_coordinates()

    def populateTable(self):
        self.MainWindow.pp_TV.setModel(PandasModel(self.df))

    def blankRows(self):
        self.rowIndices=self.MainWindow.pp_TV.selectionModel().selectedRows()
        for i in range(len(self.rowIndices)):
            self.df.iloc[self.rowIndices[i].row(),1:10]=None 
        self.populateTable()
        self.plot_pixel_coordinates()
        
    def interpolateBlanks(self):

        self.df=self.df.interpolate(limit_direction='both', limit_area='inside')
        self.df=round(self.df)
        self.populateTable()
        self.plot_pixel_coordinates()

    def getMatrix(self):
        self.matrix = self.df[['x_px','y_px']]
        self.matrix = self.matrix.as_matrix(columns=None)

    def errorMsg(self):
        msg = PyQt5.QtWidgets.QMessageBox()
        msg.setIcon(PyQt5.QtWidgets.QMessageBox.Information)
        msg.setText(self.errMessage)
        msg.setWindowTitle(self.errorTitle)
        msg.setStandardButtons(PyQt5.QtWidgets.QMessageBox.Ok | PyQt5.QtWidgets.QMessageBox.Cancel)
        retval = msg.exec_()        
     

app = PyQt5.QtWidgets.QApplication(sys.argv)
app.aboutToQuit.connect(app.deleteLater)
form = MainWindow()
form.show()
app.exec_()

