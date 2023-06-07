
import pylsl,socket
import msvcrt
from pylink import * 


if __name__ == '__main__':

    outlet = None 
    SR = 500
    edfFileName = "TRIAL.edf"
    try:
        #info = pylsl.stream_info("EyeLink","Gaze",9,500,pylsl.cf_float32,"eyelink-" + socket.gethostname());
        info = pylsl.stream_info("EyeLink","Gaze",10,SR,pylsl.cf_double64,"eyelink-" + socket.gethostname());
        channels = info.desc().append_child("channels")

        channels.append_child("channel") \
            .append_child_value("label", "leftEyeX") \
            .append_child_value("type", "eyetracking")
        channels.append_child("channel") \
            .append_child_value("label", "leftEyeY") \
            .append_child_value("type", "eyetracking")

        channels.append_child("channel") \
            .append_child_value("label", "rightEyeX") \
            .append_child_value("type", "eyetracking") 
        channels.append_child("channel") \
            .append_child_value("label", "rightEyeY") \
            .append_child_value("type", "eyetracking")
        channels.append_child("channel") \
            .append_child_value("label", "leftPupilArea") \
            .append_child_value("type", "eyetracking")
        channels.append_child("channel") \
            .append_child_value("label", "rightPupilArea") \
            .append_child_value("type", "eyetracking")
        # channels.append_child("channel") \
        #     .append_child_value("label", "pixelsPerDegreeX") \
        #     .append_child_value("type", "eyetracking")
        # channels.append_child("channel") \
        #     .append_child_value("label", "pixelsPerDegreeY") \
        #     .append_child_value("type", "eyetracking")
        channels.append_child("channel") \
            .append_child_value("label", "eyelink_timestamp") \
            .append_child_value("type", "eyetracking")
        channels.append_child("channel") \
            .append_child_value("label", "LSL_timestamp") \
            .append_child_value("type", "eyetracking")



            
        outlet = pylsl.stream_outlet(info)
        print ("Established LSL outlet.")
    except:
        print ("Could not create LSL outlet.")



    tracker = EyeLink("100.1.1.1")
    print ("Established a primary connection with the eye tracker.")
    beginRealTimeMode(100)
    getEYELINK().openDataFile(edfFileName)	
    getEYELINK().startRecording(1, 1, 1, 1)                
    print ("Now reading samples...")
    print ("Press \'Esc\' to quit")
