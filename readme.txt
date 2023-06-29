## Stim protocol for Eye Link

The code automatically executes the stimulation protocol for a 
Eye Link experiment. It automatically conects and starts the recording.
It also sends events to Emotibit and eye link and LSL to record the timstamp in which each event 
was presented.  Is also automaticall sends the .edf data from the host pc to the display pc
and transfors it to ascii file.

To install the environment just execute:

conda env create -f eye_link.yaml

Once with the environment installed drop the fotos in .tif format you want
for the screen stimulation in OBJECTS.

To run the code:
python stim_final3.py <dir>

Where dir is the directory to save the stimulation images.

For help type

python stim_final3 -h

Run the program and follow the instruction in the console.


## De code is under development. Any contributions and suggestions are welcome. To 
commit a pull request refer to the Xscape proyect corresponding author: 
arturo-jose.valino@incipit.csic.es

                                            Xscape Project (CSIC-INCIPIT) 02/03/2023
                                            
## Coments from eye link:

This program will also write the data using EyeLinks native EDF format. A good way to control this (in Windows) is to make a shortcut, right click and open the properties dialogue. For the target, specify the full path to python 2.6, then the path to the program to which your shortcut is linked, eg:

C:\Python26\python.exe C:\Users\ces\Desktop\EyeLink\eyelink.py

then in the Start in field, specify the directory into which you would like your EDF written. The file will be called TRIAL.edf, so you will have to move/rename it after each trial. Obviously, this system can be improved with more code, perhaps a GUI.