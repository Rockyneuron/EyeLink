import sys
import os
import keyboard
from time import sleep
from psychopy import visual, core, event, monitors, gui
# from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
from string import ascii_letters, digits
from pathlib import Path
import random
import commons as cm
import time
import argparse
import logging
import pylink
from pylsl import StreamInfo, StreamOutlet
from PIL import Image  # for preparing the Host backdrop image
import subprocess



# Show only critical log message in the PsychoPy console
from psychopy import logging
logging.console.setLevel(logging.DEBUG)

"""Code for eye link stimulation for the Xscape project.
"""

def main(display_size=(1024,768)):

    #Add arguments to indicate where stimulation images will be saved.
    parser=argparse.ArgumentParser(
        prog='Stimulation Protocol',
        description="""Stimulation protocol for XSCAPE proyect. The program runs an 
        randomised stimulation protocol and then saves the images in the provided Path
        in the comand line.""" ,
        epilog="""Rember to enter the path. To execute the program type in the console: 
        python stimulation.py --path <full path for the saved images>""",
        add_help=True,
    )
    parser.add_argument("path")

    args=parser.parse_args()
    target_dir = Path(args.path)

    if not target_dir.exists():
        raise SystemError("The target directory doesn't exist")
    if len(os.listdir(Path(target_dir)))>0:
        raise SystemError('Target directory for saved images is not empty')
    
    #Experiment parameters
    MON_DISTANCE_TOP = 1130  # Distance between subject's eyes and upper part of monitor (mm)
    MON_DISTANCE_BOTTOM = 1160  # Distance between subject's eyes and bottom part of monitor (mm)
    LINK_DISTANCE=550 #distance from eye to top knob of eye link
    MON_WIDTH = 615  # Width of your display image monitor in mm
    MON_HEIGHT = 340  # height of your display image monitor in mm
    MON_SIZE = [1920, 1080]  # Pixel-dimensions of your monitor
    MON_HZ=60 #Monitor frame rate in Hz 
    FIX_HEIGHT = 100  # Text height of fixation cross
    stimulus_duration=0.1  #in seconds
    insterstimulus_duration=2
    hello_window_duration=0.1
    goodbye_window_duration=10
    STIMULUS_FRAMES=round(MON_HZ*stimulus_duration)
    INTERSTIMULUS_FRAMES=round(MON_HZ*insterstimulus_duration)

    def save_list_to_txt(my_list,list_path):
        """Function to save list to a .txt
            Args:
            my_list (_type_): list to save as .txt
            list_path (_type_): fullpath where to save list </.../.../.txt>
        """
        try:
            with open(list_path, mode='x') as f:
                for item in my_list:
                    f.write(str(item) + '\n')
        except FileExistsError:
            with open(list_path, mode='w') as f:
                for item in my_list:
                    f.write(str(item) + '\n')
        else:
            print('Experiment images saved')            
    counter=0
    while True:
        # Open a window, be sure to specify monitor parameters
        clock = core.Clock()  
        win = visual.Window(
            size=MON_SIZE,
            screen=1,
            units="pix",
            allowGUI=True,
            fullscr=True,
            monitor=None,
            color=(110,110,110),
            colorSpace='rgb255',
        )

        #  Step 6: Run the experimental trials, index all the trials
        # Get list of images.
        images_list=os.listdir(Path('OBJECTS'))   
        images_list=[im for im in images_list if '.tif' in im] 

        # If we are on a windows sistem remove thumbs.db cache file
        if 'Thumbs.db' in images_list:
            images_list.remove('Thumbs.db')

        #list of pseudorandom images
        images_psedorand=os.listdir(Path('OBJECTS/pseudorandom'))
        images_psedorand=[im for im in images_psedorand if '.tif' in im]

        with open(Path('OBJECTS/pseudorandom/order.txt'),'r') as file:
            for line in file:
                order=line.split(',')
        order_pseudorand=list(map(int,order)) 

        random.shuffle(images_list)
        random.shuffle(images_psedorand)

        images=[Path('OBJECTS/' + im) for im in images_list]
        images_psedorand_dir=[Path('OBJECTS/pseudorandom/'+ im) for im in images_psedorand]

        for loc, im_dir, im in zip(order_pseudorand,images_psedorand_dir,images_psedorand):
            images.insert(loc,im_dir)
            images_list.insert(loc,im)

        hello_image=visual.ImageStim(win,image='script_images/Bienvenida_.tiff')
        goodbye_image=visual.ImageStim(win,image='script_images/Final_.tiff')

        # Reallocate all stimuly in an initial list to optimize stimulation.
        image_stim_vec=[visual.ImageStim(win, image=im) for im in images]

        markers = {
            'event': images,
            'test': ['test_event']
        }

        # Let everythng settle and say hello
        for frame in range(round(hello_window_duration*MON_HZ)):
            hello_image.draw()
            win.flip()


        for im_number, image_stim in enumerate(image_stim_vec):
            # # get a reference to the currently active EyeLink connectionç
            #Stimulus
            cm.tic()
            image_stim.draw()
            win.flip()
            for frame in range(STIMULUS_FRAMES-1):
                image_stim.draw()
                win.flip()
            print('stimulus time:')
            cm.toc()
            win.flip()
        counter+=1
        win.getMovieFrame()        
        print(f'experiment: {counter}')
        win.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Killed by user')
        sys.exit(0)
