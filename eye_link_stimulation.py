import sys
import os
import keyboard
from time import sleep
from psychopy import visual, core, event, monitors, gui
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
from string import ascii_letters, digits
from pathlib import Path
import random
import commons as cm
import time
import argparse
import logging
import pylink
import platform
from pylsl import StreamInfo, StreamOutlet
from PIL import Image  # for preparing the Host backdrop image
import subprocess


# Show only critical log message in the PsychoPy console
from psychopy import logging
logging.console.setLevel(logging.CRITICAL)

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
    MON_DISTANCE = 60  # Distance between subject's eyes and monitor
    MON_WIDTH = 50  # Width of your monitor in cm
    MON_SIZE = [1920, 1080]  # Pixel-dimensions of your monitor
    MON_HZ=60.01 #Monitor frame rate in Hz 
    FIX_HEIGHT = 100  # Text height of fixation cross
    stimulus_duration=6  #in seconds
    insterstimulus_duration=2
    hello_window_duration=10
    goodbye_window_duration=10
    STIMULUS_FRAMES=round(MON_HZ*stimulus_duration)
    INTERSTIMULUS_FRAMES=round(MON_HZ*insterstimulus_duration)

    # Set up LabStreamingLayer stream.
    info = StreamInfo(name='DataSyncMarker', type='Tags', channel_count=1,
                      channel_format='string', source_id='1234')
    outlet = StreamOutlet(info)  # Broadcast the stream.

    # Switch to the script folder
    script_path = os.path.dirname(sys.argv[0])
    if len(script_path) != 0:
        os.chdir(script_path)

    # Set this variable to True if you use the built-in retina screen as your
    # primary display device on macOS. If have an external monitor, set this
    # variable True if you choose to "Optimize for Built-in Retina Display"
    # in the Displays preference settings.
    use_retina = False

    # Set this variable to True to run the script in "Dummy Mode"
    dummy_mode = False

    # Set this variable to True to run the task in full screen mode
    # It is easier to debug the script in non-fullscreen mode
    full_screen = True

    # Set up EDF data file name and local data folder
    #
    # The EDF data filename should not exceed 8 alphanumeric characters
    # use ONLY number 0-9, letters, & _ (underscore) in the filename
    edf_fname = '001'

    # Prompt user to specify an EDF data filename
    # before we open a fullscreen window
    # dlg_title = 'Enter EDF File Name'
    # dlg_prompt = 'Please enter a file name with 8 or fewer characters\n' + \
    #             '[letters, numbers, and underscore].'

    # # loop until we get a valid filename
    # while True:
    #     dlg = gui.Dlg(dlg_title)
    #     dlg.addText(dlg_prompt)
    #     dlg.addField('File Name:', edf_fname)
    #     # show dialog and wait for OK or Cancel
    #     ok_data = dlg.show()
    #     if dlg.OK:  # if ok_data is not None
    #         print('EDF data filename: {}'.format(ok_data[0]))
    #     else:
    #         print('user cancelled')
    #         core.quit()
    #         sys.exit()

    #     # get the string entered by the experimenter
    #     tmp_str = dlg.data[0]
    #     # strip trailing characters, ignore the ".edf" extension
    #     edf_fname = tmp_str.rstrip().split('.')[0]

        # check if the filename is valid (length <= 8 & no special char)
        # allowed_char = ascii_letters + digits + '_'
        # if not all([c in allowed_char for c in edf_fname]):
        #     print('ERROR: Invalid EDF filename')
        # elif len(edf_fname) > 8:
        #     print('ERROR: EDF filename should not exceed 8 characters')
        # else:
        #     break

    # Set up a folder to store the EDF data files and the associated resources
    # e.g., files defining the interest areas used in each trial
    results_folder = 'results'
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    # We download EDF data file from the EyeLink Host PC to the local hard
    # drive at the end of each testing session, here we rename the EDF to
    # include session start date/time
    time_str = time.strftime("_%Y_%m_%d_%H_%M", time.localtime())
    session_identifier = edf_fname + time_str

    # create a folder for the current testing session in the "results" folder
    session_folder = os.path.join(results_folder, session_identifier)
    if not os.path.exists(session_folder):
        os.makedirs(session_folder)  

    #  Step 1: Connect to the EyeLink Host PC
    #
    # The Host IP address, by default, is "100.1.1.1".
    # the "el_tracker" objected created here can be accessed through the Pylink
    # Set the Host PC address to "None" (without quotes) to run the script
    # in "Dummy Mode"
    if dummy_mode:
        el_tracker = pylink.EyeLink(None)
    else:
        try:
            el_tracker = pylink.EyeLink("100.1.1.1")
        except RuntimeError as error:
            print('ERROR:', error)
            core.quit()
            sys.exit()

    # Step 2: Open an EDF data file on the Host PC
    edf_file = edf_fname + ".EDF"
    try:
        el_tracker.openDataFile(edf_file)
    except RuntimeError as err:
        print('ERROR:', err)
        # close the link if we have one open
        if el_tracker.isConnected():
            el_tracker.close()
        core.quit()
        sys.exit()

    # Add a header text to the EDF file to identify the current experiment name
    # This is OPTIONAL. If your text starts with "RECORDED BY " it will be
    # available in DataViewer's Inspector window by clicking
    # the EDF session node in the top panel and looking for the "Recorded By:"
    # field in the bottom panel of the Inspector.
    preamble_text = 'RECORDED BY %s' % os.path.basename(__file__)
    el_tracker.sendCommand("add_file_preamble_text '%s'" % preamble_text)

    # Step 3: Configure the tracker
    #
    # Put the tracker in offline mode before we change tracking parameters
    el_tracker.setOfflineMode()

    # Get the software version:  1-EyeLink I, 2-EyeLink II, 3/4-EyeLink 1000,
    # 5-EyeLink 1000 Plus, 6-Portable DUO
    eyelink_ver = 5  # set version to 0, in case running in Dummy mode
    if not dummy_mode:
        vstr = el_tracker.getTrackerVersionString()
        eyelink_ver = int(vstr.split()[-1].split('.')[0])
        # print out some version info in the shell
        print('Running experiment on %s, version %d' % (vstr, eyelink_ver))

    # File and Link data control
    # what eye events to save in the EDF file, include everything by default
    file_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
    # what eye events to make available over the link, include everything by default
    link_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
    # what sample data to save in the EDF data file and to make available
    # over the link, include the 'HTARGET' flag to save head target sticker
    # data for supported eye trackers
    if eyelink_ver > 3:
        file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
        link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
    else:
        file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,GAZERES,BUTTON,STATUS,INPUT'
        link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT'
    el_tracker.sendCommand("file_event_filter = %s" % file_event_flags)
    el_tracker.sendCommand("file_sample_data = %s" % file_sample_flags)
    el_tracker.sendCommand("link_event_filter = %s" % link_event_flags)
    el_tracker.sendCommand("link_sample_data = %s" % link_sample_flags)

    # Optional tracking parameters
    # Sample rate, 250, 500, 1000, or 2000, check your tracker specification
    if eyelink_ver > 2:
        el_tracker.sendCommand("sample_rate 500")
    # Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
    el_tracker.sendCommand("calibration_type = HV9")
    # Set a gamepad button to accept calibration/drift check target
    # You need a supported gamepad/button box that is connected to the Host PC
    el_tracker.sendCommand("button_function 5 'accept_target_fixation'")

    # Step 4: set up a graphics environment for calibration
    #
    # Open a window, be sure to specify monitor parameters
    mon = monitors.Monitor('myMonitor', width=63.0, distance=58.0)
    win = visual.Window(fullscr=full_screen,
                        monitor=mon,
                        screen=0,
                        size=MON_SIZE,
                        allowGUI=True,
                        color=(110,110,110),
                        colorSpace='rgb255',
                        units='pix')
    # win = visual.Window(fullscr=full_screen,
    #                     monitor=mon,
    #                     winType='pyglet',
    #                     units='pix')


    # get the native screen resolution used by PsychoPy
    scn_width, scn_height = win.size
    # scn_width, scn_height=MON_SIZE

    # Pass the display pixel coordinates (left, top, right, bottom) to the tracker
    # see the EyeLink Installation Guide, "Customizing Screen Settings"
    el_coords = "screen_pixel_coords = 0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendCommand(el_coords)

    # Write a DISPLAY_COORDS message to the EDF file
    # Data Viewer needs this piece of info for proper visualization, see Data
    # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
    dv_coords = "DISPLAY_COORDS  0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendMessage(dv_coords)

    # Configure a graphics environment (genv) for tracker calibration
    genv = EyeLinkCoreGraphicsPsychoPy(el_tracker, win)
    print(genv)  # print out the version number of the CoreGraphics library
 
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

    def clear_screen(win):
        """ clear up the PsychoPy window"""

        win.fillColor = genv.getBackgroundColor()
        win.flip()

    def show_msg(win, text, wait_for_keypress=True):
        """ Show task instructions on screen"""

        msg = visual.TextStim(win, text,
                            color=genv.getForegroundColor(),
                            wrapWidth=scn_width/2)
        clear_screen(win)
        msg.draw()
        win.flip()

    def terminate_task():
        """ Terminate the task gracefully and retrieve the EDF data file

        file_to_retrieve: The EDF on the Host that we would like to download
        win: the current window used by the experimental script
        """

        el_tracker = pylink.getEYELINK()

        if el_tracker.isConnected():
            # Terminate the current trial first if the task terminated prematurely
            error = el_tracker.isRecording()
            if error == pylink.TRIAL_OK:
                abort_trial()

            # Put tracker in Offline mode
            el_tracker.setOfflineMode()

            # Clear the Host PC screen and wait for 500 ms
            el_tracker.sendCommand('clear_screen 0')
            pylink.msecDelay(500)

            # Close the edf data file on the Host
            el_tracker.closeDataFile()

            # Show a file transfer message on the screen
            print('EDF data is transferring from EyeLink Host PC...')

            # Download the EDF data file from the Host PC to a local data folder
            # parameters: source_file_on_the_host, destination_file_on_local_drive
            local_edf = os.path.join(session_folder, session_identifier + '.EDF')
        
            try:
                el_tracker.receiveDataFile(edf_file, local_edf)
            except RuntimeError as error:
                print('ERROR:', error)

            # Close the link to the tracker.
            el_tracker.close()
            # transform to ascii file
            subprocess.call(['C:\\Program Files (x86)\\SR Research\\EyeLink\\bin\\64\\edf2asc64.exe',
                    local_edf])
            
            # Save stimulation images
            print('Saving stimulation images...')
            win.saveMovieFrames(target_dir.joinpath(' .tif'))

            # Save assets order images
            print('Saving assets order list...')
            save_list_to_txt(images_list,target_dir.joinpath('assets.txt'))
                     
            #Rename saved images
            for asset, saved_stim_images in zip(images_list,os.listdir(target_dir)):
                stimulus_order,_=os.path.splitext(saved_stim_images)
                previous_name=target_dir.joinpath(saved_stim_images)
                asset_number,t_=asset.split('.')
                final_name=asset_number+'_'+stimulus_order.strip() + '.tif'
                previous_name.rename(target_dir / final_name)
           
            finish_input='finish'
            final_test=True
            while final_test:
                user_input=input('Do a Test before you end. Type "finish" to finish the experiment": \n')
                if finish_input==user_input:
                    print('Ending experiment...')
                    final_test=False
                elif finish_input!=user_input:
                    print('Wrong input. Press control+c to skip program')
                else:
                    raise ValueError("You have to input a string")   

            for frame in range(round(goodbye_window_duration*MON_HZ)):
                goodbye_image.draw()
                win.flip()

        # close the PsychoPy window
        win.close()

        # quit PsychoPy
        core.quit()
        sys.exit()
    def abort_trial():
        """Ends recording """

        el_tracker = pylink.getEYELINK()

        # Stop recording
        if el_tracker.isRecording():
            # add 100 ms to catch final trial events
            pylink.pumpDelay(100)
            el_tracker.stopRecording()

        # clear the screen
        clear_screen(win)
        # Send a message to clear the Data Viewer screen
        bgcolor_RGB = (116, 116, 116)
        el_tracker.sendMessage('!V CLEAR %d %d %d' % bgcolor_RGB)

        # send a message to mark trial end
        el_tracker.sendMessage('TRIAL_RESULT %d' % pylink.TRIAL_ERROR)

        return pylink.TRIAL_ERROR
    # Set background and foreground colors for the calibration target
    # in PsychoPy, (-1, -1, -1)=black, (1, 1, 1)=white, (0, 0, 0)=mid-gray
    foreground_color = (-1, -1, -1)
    background_color = win.color
    genv.setCalibrationColors(foreground_color, background_color)

    # The target could be a "circle" (default), a "picture", a "movie" clip,
    # or a rotating "spiral".
    genv.setTargetType('circle')

    genv.setTargetSize(24)
    # Beeps to play during calibration, validation and drift correction
    # parameters: target, good, error
    #     target -- sound to play when target moves
    #     good -- sound to play on successful operation
    #     error -- sound to play on failure or interruption
    # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
    # genv.setCalibrationSounds('', '', '')

    genv.setup_cal_display()
    # Request Pylink to use the PsychoPy window we opened above for calibration
    pylink.openGraphicsEx(genv)

    # Step 5: Set up the camera and calibrate the tracker
    
    # print('Press "Enter" to start the calibration')
    if not dummy_mode:
        try:
            print('Enter: Show/Hide camera image\n' + \
                            'Left/Right: Switch camera view\n' + \
                            'C: Calibration\n' + \
                            'V: Validation\n' + \
                            'O: Start Recording\n' + \
                            '+=/-: CR threshold\n' + \
                            'Up/Down: Pupil threshold\n' + \
                            'Alt+arrows: Search limit')
            el_tracker.doTrackerSetup()
  
        except RuntimeError as err:
            print('ERROR:', err)
        el_tracker.exitCalibration()


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
    # Generate stimulus objects
    drift_point = visual.Circle(win=win,
                                    units="pix",
                                    radius=15,
                                    fillColor=[-1]*3,
                                    lineColor=[-1]*3,
                                    edges=128
                                    )
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

    # Start stimulation
    start_input='start'
    stim=True
    while stim:
        user_input=input('Type "start" to begin stimulation: \n')
        if start_input==user_input:
            print('Starting stimulation...')
            sleep(2)
            stim=False
        elif start_input!=user_input:
            print('Wrong input. Press control+c to skip program')
        else:
            raise ValueError("You have to input a string") 

    for im_number, image_stim in enumerate(image_stim_vec):

        # # get a reference to the currently active EyeLink connection
        el_tracker = pylink.getEYELINK()

        # # put the tracker in the offline mode first
        el_tracker.setOfflineMode()

        # # clear the host screen before we draw the backdrop
        el_tracker.sendCommand('clear_screen 0')
        # Use the code commented below to convert the image and send the backdrop
        im = Image.open(images[im_number])  # read image with PIL
        im = im.resize((scn_width, scn_height))
        img_pixels = im.load()  # access the pixel data of the image
        pixels = [[img_pixels[i, j] for i in range(scn_width)]
                for j in range(scn_height)]
        el_tracker.bitmapBackdrop(scn_width, scn_height, pixels,
                                0, 0, scn_width, scn_height,
                                0, 0, pylink.BX_MAXCONTRAST)        
        
        # send a "TRIALID" message to mark the start of a trial, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        el_tracker.sendMessage('TRIALID %d' % im_number)

        # record_status_message : show some info on the Host PC
        # here we show how many trial has been tested
        status_msg = 'TRIAL number %d' % im_number
        el_tracker.sendCommand("record_status_message '%s'" % status_msg)


        # drift check
        # we recommend drift-check at the beginning of each trial
        # the doDriftCorrect() function requires target position in integers
        # the last two arguments:
        # draw_target (1-default, 0-draw the target then call doDriftCorrect)
        # allow_setup (1-press ESCAPE to recalibrate, 0-not allowed)
        #
        # # # Skip drift-check if running the script in Dummy Mode
        while not dummy_mode:
            # terminate the task if no longer connected to the tracker or
            # user pressed Ctrl-C to terminate the task
            if (not el_tracker.isConnected()) or el_tracker.breakPressed():
                terminate_task()
                return pylink.ABORT_EXPT

            # drift-check and re-do camera setup if ESCAPE is pressed
            try:
                error = el_tracker.doDriftCorrect(int(scn_width/2.0),
                                                int(scn_height/2.0), 1, 1)
                # break following a success drift-check
                if error is not pylink.ESC_KEY:
                    break
            except:
                pass
    
        # put tracker in idle/offline mode before recording
        el_tracker.setOfflineMode()


        # Start recording
        # arguments: sample_to_file, events_to_file, sample_over_link,
        # event_over_link (1-yes, 0-no)
        try:
            el_tracker.startRecording(1, 1, 1, 1)
        except RuntimeError as error:
            print("ERROR:", error)
            abort_trial()
            return pylink.TRIAL_ERROR
        
        # # Allocate some time for the tracker to cache some samples
        pylink.pumpDelay(100)

        #Stimulus
        cm.tic()
        image_stim.draw()
        win.flip()
        el_tracker.sendMessage(images[im_number].name)
        el_tracker.sendMessage('image_onset')
        outlet.push_sample([markers['event'][im_number].name])

        img_onset_time = core.getTime()  # record the image onset time

        # Send a message to clear the Data Viewer screen, get it ready for
        # drawing the pictures during visualization
        bgcolor_RGB = (116, 116, 116)
        el_tracker.sendMessage('!V CLEAR %d %d %d' % bgcolor_RGB)

        # send over a message to specify where the image is stored relative
        # to the EDF data file, see Data Viewer User Manual, "Protocol for
        # EyeLink Data to Viewer Integration"
        bg_image ='../../'+images[im_number].as_posix()
        # imgload_msg = '!V IMGLOAD CENTER %s %d %d %d %d' % (bg_image,
        #                                                     int(scn_width/2.0),
        #                                                     int(scn_height/2.0),
        #                                                     int(scn_width),
        #                                                     int(scn_height))

        imgload_msg = '!V IMGLOAD FILL {}'.format(bg_image)

        el_tracker.sendMessage(imgload_msg)
        RT = -1  # keep track of the response time

        for frame in range(STIMULUS_FRAMES-1):
            image_stim.draw()
            win.flip()
        win.getMovieFrame()        
        print('stimulus time:')
        cm.toc()
        el_tracker.sendMessage('image_offset')

        # get response time in ms, PsychoPy report time in sec
        RT = int((core.getTime() - img_onset_time)*1000)

        # clear the screen
        clear_screen(win)
        el_tracker.sendMessage('blank_screen')
        # send a message to clear the Data Viewer screen as well
        # el_tracker.sendMessage('!V CLEAR 128 128 128')

        # stop recording; add 100 msec to catch final events before stopping
        pylink.pumpDelay(100)
        el_tracker.stopRecording()

        # record trial variables to the EDF data file, for details, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        el_tracker.sendMessage('!V TRIAL_VAR condition %s' % im_number)
        el_tracker.sendMessage('!V TRIAL_VAR image %s' % images[im_number].name)
        el_tracker.sendMessage('!V TRIAL_VAR RT %d' % RT)

        # send a 'TRIAL_RESULT' message to mark the end of trial, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        el_tracker.sendMessage('TRIAL_RESULT %d' % pylink.TRIAL_OK)

        # Step 7: disconnect, download the EDF file, then terminate the task
    el_tracker.sendMessage('EndOfExperiment')    
    outlet.push_sample(['EndOfExperiment'])
    terminate_task()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Killed by user')
        sys.exit(0)


        # If want yo add some interstimulus
        # cm.tic()
        # win.flip()
        # el_tracker.sendMessage('blank_{}'.format(im_number))
        # outlet.push_sample(['blank_{}'.format(im_number)])

        # #Interstimulus
        # for frame in range(INTERSTIMULUS_FRAMES-1):
        #     win.flip()
        # print('interstimulus time blank:')  
        # cm.toc()

        # cm.tic()
        # drift_point.draw()
        # win.flip()
        # el_tracker.sendMessage('drift_point_{}'.format(im_number))
        # outlet.push_sample(['drift_point_{}'.format(im_number)])

        # for frame in range(INTERSTIMULUS_FRAMES-1):
        #     drift_point.draw()
        #     win.flip()
        # print('interstimulus time drift correction:')
        # cm.toc()
