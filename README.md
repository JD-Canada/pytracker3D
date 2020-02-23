# pytracker3D
Python GUI for 3D tracking of fish (or any object for that matter) using 2 simultaneous views of the fish in a properly calibrated object space (i.e. tracking domain). 

Stay tuned. I plan on uploading a explanatory video to YouTube in a short while. 

To launch pytracker3D:

1.) Make sure you have a properly configured Python 3.6 installation (I recommended the Anaconda distribution)
2.) From the termina, (command prompt, conda prompt, etc.), install the opencv package for python: pip install opencv-python
3.) Navigate to the directory you downloaded the code to
4.) Type: python pytracker3D.py in the command line
5.) After a few seconds a window will pop up and you can begin the tracking process.

To track in 3D you will need:

1.) Two simultaneous views (videos) of your object moving in the object space.The views can be obtained using two independant cameras or, with one camera with the frame sharing a 'top' view of the object space and a mirrored 'side' view of the object space (e.g. one (direct) view looks straight down at the object and the other (mirrored) view reflects a side view of the object back to the camera).

2.) A minimum of eight calibration points that are simultaneously visible in both views and that occupy the extents of the object space (i.e. the eight points should cover the spatial extents of the entire object space). You must know the 3D object space coordinates of each of the eight points beforehand. 

You can either provide the eight calibration points in (A) a single set of two images (one image per view), or (B) you can use multiple images of a target at different positions within the object space to obtain 8 unique calibration points. 

The former (A) is the suggested method (because it is easiest) and can be done by constructing a calibration target that fits within the object space and provides an unobstructed line of sight of each of the eight calibration points in both views. An example of such a 3D calibration target can be imagined as a cube constructed from an atomic structure kit (like the ones from high-school chemistry class), where each of the eight corners serves as a distinctly colored calibration point and the rods joining them are a completely different color (ideally the atoms would be white and the rods would be black to improve the detection of the atoms (i.e. targets) in the software). During the calibration, both views of the calibration target are loaded into the calibration module.

The latter (b): if for whatever reason you can't do A, then you can place an easily detectable target (a small ball with a strong shade contrast to its surrounding) at eight distinct points within the object space and obtain your two views of the target at each of the positions. I leave it to your imagination as to how you could do this. It can be done relatively easily, but I warned you A was easier.

3.) Separate videos of the object to track. Each video is a view of the moving object in the 3D object space. If you used two simultaneous cameras, then great, those two videos will be used in the tracking process. If you have two views on one video (i.e. top and side views), then you will need to split the video frame into two parts, one for the top view and one for the side view. I recommend using the ffmpeg package to do this. If you do use ffmpeg, install it first, then try: ffmpeg -i yourVideoNameIn.mp4 -filter:v "crop=out_w:out_h:x:y" yourVideoNameOut.mp4 from the command line, where 'out_w' is the width of the output rectangle, 'out_h' is the height of the output rectangle and 'x' and 'y' specify the top left corner of the output rectangle.

