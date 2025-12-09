import PySimpleGUI as sg
import json
import numpy as np
import time as timing
import os, struct, scipy, warnings
from numba import jit
import matplotlib.pyplot as plt 
import TimeTagger as tt
warnings.filterwarnings('ignore')
from array import array
import numba
from time import sleep, time
from ctypes import *
from NanodriveControl import createScanPoints, startScanningWithoutWaveform
import multiprocessing as mp
import sys
import clr
#from PVTMovementFunctions import mover , collect_data
#from NanodriveControl import  move_positive_x, move_negative_x, move_positive_y, move_negative_y, move_positive_z, move_negative_z, wait_for_key_input
import keyboard
from pathlib import Path
import time as timing

if __name__ == '__main__':
    nanoWaveForms = ['Square Raster', 'Sawtooth Raster']

    tagger_layout = [
        [sg.Text('Select directory:'), sg.InputText(size=(100,1), key='-DIRECTORY-', ), sg.FolderBrowse()],
        [
            sg.Text('Presets:'), 
            sg.Input(size=(30,1), key='-PRESETS-', ),
            sg.Text('Channels:'), 
            sg.Input(size=(10,1), key='-CHANNELS-', ),
            sg.Text('Run Name:'), 
            sg.Input(size=(30,1), key='-NAME-',)
        ],
        [
            sg.Text('Trigger Voltage:'), 
            sg.Input(size=(7,1), key='-VOLTAGE-',),
            sg.Text('Integration Time(s):'), 
            sg.Input(size=(5,1), key='-TIME-',),
            sg.Text('Test(y/n):'), 
            sg.Input(size=(5,1), key='-TEST-',)
        ],
        [ sg.Text('Z Pos'), 
            sg.Input(size=(7,1), key='-ZPOS-',),
            sg.Text('X Pos'), 
            sg.Input(size=(7,1), key='-XPOS-',),
            sg.Text('Y Pos'), 
            sg.Input(size=(7,1), key='-YPOS-',),
            sg.Text('Step size'), 
            sg.Input(size=(7,1), key='-STEPSIZE-',),],
            

        [ sg.Button('Z up',size=(7,1) ), sg.Button('Y up', pad = (10,0),size=(7,1)), sg.Button('Z down', pad = (10,0),size=(7,1)), ],
        [ sg.Button('X down',size=(7,1)), sg.Button('X up', pad = (90,0),size=(7,1)),],
        [ sg.Button('Y down', pad = (85,0),size=(7,1)), ],
        [sg.Text('Bin Width in ms'),sg.Input(size = (7,1), key='-BINWIDTH-'),sg.Text('Number of Bins'),sg.Input(size = (7,1), key='-BINNUM-'),
         sg.Text('Y max'),sg.Input(size = (7,1), key='-YMAX-'), sg.Text('Y min'),sg.Input(size = (7,1), key='-YMIN-')],
        [sg.Button('Collect Data'),sg.Button('Start Plotting'),sg.Button('Stop Plotting')]
    ]

    nano_stage_layout = [
        [sg.Text('Select directory:'), sg.InputText(size=(100,1), key='-DIRECTORY3-'), sg.FolderBrowse(),
          sg.Text('Run Name:'), 
            sg.Input(size=(30,1), key='-NAME2-')],
        [sg.Text('Absolute Move'),
        sg.InputText(size=(5,1), key='-ABSOLUTEMOVE-'),
        sg.Text('Absolute Move Z'),
        sg.InputText(size=(5,1), key='-ABSOLUTEMOVEZ-'),
        sg.Text('Motion Pattern'),
        sg.DropDown(nanoWaveForms, key='-NANOWAVEFORMS-')],
        
        [sg.Text('Start X Coord'),
        sg.InputText(size=(5,1), key='-STARTXCOORD-'),
        sg.Text('End X Coord'),
        sg.InputText(size=(5,1), key='-ENDXCOORD-'),
        sg.Text('Start Y Coord'),
        sg.InputText(size=(5,1), key='-STARTYCOORD-'),
        sg.Text('End Y Coord'),
        sg.InputText(size=(5,1), key='-ENDYCOORD-'),
        sg.Text('# X of Points'),
        sg.InputText(size=(5,1), key='-XPOINTS-'),
        sg.Text('# Y of Points'),
        sg.InputText(size=(5,1), key='-YPOINTS-'),
        sg.Text('Pixel Dwell Time (set to zero for fast FOV)'),
        sg.InputText(size=(10,1), key='-PIXELDWELLTIME-'),
        sg.Text('Iterations (0 for infinite)'),
        sg.InputText(size=(5,1), key='-ITERATIONS-'),
         ],

        [sg.Text('Select a Scale Range:')],

        [sg.Text('Max Pixel Value'),
        sg.InputText(size=(5,1), key='-MAXPIXEL-')],

        [sg.Text('Min Pixel Value'),
        sg.InputText(size=(5,1), key='-MINPIXEL-')],
        
        [sg.Button('Move to Abs Position'),
         sg.Button('Move to Abs Z Position'),
         sg.Button('Move Z up'),
         sg.Button('Move Z down'),
        sg.Button('Start Scan'),
        sg.Button('Stop Scanning'),
        sg.Checkbox('Integration Mode', key = '-INTEGRATIONMODE-'),
        sg.Button('Move Stage')],
        
        
    ]

    pvtlayout = [
    [sg.Text('Position (comma separated numbers):'), sg.Input(key='-POSITION-')],
    [sg.Text('Directory:'), sg.Input(key='-DIRECTORY2-'), sg.FolderBrowse()],
    [sg.Text('Channels (comma separated numbers):'), sg.Input(key='-CHANNELS2-')],
    [sg.Text('Voltage:'), sg.Input(key='-VOLTAGE2-')],
    [sg.Text('PVT File'), sg.Input(key = '-PVTFILE-'), sg.FileBrowse()],
    [sg.Button('Get Data')],
    ]

    layout = [[sg.TabGroup([[sg.Tab('Tagger', tagger_layout),
                            sg.Tab('Nano Drive Stage', nano_stage_layout),sg.Tab('PVT',pvtlayout)]])]]
    
    window = sg.Window("Basic PySimpleGUI Window",layout)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break
        '''
        ====================================
        Events on tab 1
        ====================================
        '''
        if event == 'Collect Data':
            voltage = float(values['-VOLTAGE-'])
            time = int(values['-TIME-'])
            presets = str(values['-PRESETS-'])
            directory = str(values['-DIRECTORY-'])
            name = str(values['-NAME-'])
            channels = [int(x) for x in values['-CHANNELS-'].split(',')]
            test = values['-TEST-']
            tagger = tt.createTimeTagger()

            if test == 'y':
                tagger.setTestSignal(channels, False )
                tagger.setInputDelay(1,2000)

            
            for i in range(len(channels)):
                tagger.setTriggerLevel(channel=channels[i] ,voltage=voltage )
            

            synchronized = tt.SynchronizedMeasurements(tagger)

            filewriter = tt.FileWriter(synchronized.getTagger(),  directory + os.sep + name, channels)

            synchronized.startFor(1e12*int(time))
            
            synchronized.waitUntilFinished()
            
            del filewriter
            del synchronized
        

            tt.freeTimeTagger(tagger)
            
        
        if event == 'Start Plotting':
            bin_number = int(values['-BINNUM-'])
            bin_width = float(values['-BINWIDTH-'])
           # max_value = int(values["-YMAX-"])
           # min_value = int(values["-YMIN-"])
            

           
            tagger = tt.createTimeTagger()
            tagger.setTestSignal(1, False)
            tagger.setTestSignal(2, False)
            tagger.setTriggerLevel(1,.5)
            counter = tt.Counter(tagger, [1] , bin_width*1e9, bin_number,  )
            fig, ax =  plt.subplots(1, 1,figsize = (15,5) )
            while 1:
                
                x = np.linspace(0,bin_number*int(bin_width),int(bin_number))
            
                counts = np.squeeze(np.array(counter.getData(rolling = True)))
               
               
                ax.plot(x,counts, color = 'blue')
                ax.set_ylabel(f'Counts per {bin_width}ms')
                ax.set_xlabel('Bins')
                #plt.ylim(min_value,max_value )
                plt.pause(.5)
                ax.cla()
                event, values = window.read(timeout = 100)
                if event == sg.WINDOW_CLOSED or event == 'Exit':
                    break
                if event == 'Stop Plotting':
                    break
                if event == 'Z up':
                    step_size = float(values['-STEPSIZE-'])
                    new_pos = str(float(values['-ZPOS-']) +float(step_size))
                    window['-ZPOS-'].update(new_pos)
                    zpos = float(new_pos)
                    mcldll = CDLL(r"C:/Program Files/Mad City Labs/NanoDrive/Madlib.dll")

                    # The correct return types for the functions used must be set.
                    mcldll.MCL_ReleaseHandle.restype = None
                    mcldll.MCL_SingleReadN.restype = c_double

                    # Acquire a device handle
                    handle = mcldll.MCL_InitHandle()
                    print("Handle = ", handle)

                    # Choose axis to move and new position in micrometers
                    axis_z = c_uint(3)
                    pos_z = c_double(zpos)

                    # Move to a new position
                    error = mcldll.MCL_SingleWriteN(pos_z, axis_z, handle)
                    print("Error = ", error)

                    # Wait for nanopositioner to settle
                    sleep(0.1)

                    # Read the new position
                    positionZ = mcldll.MCL_SingleReadN(axis_z, handle)
                    print("PositionZ = ", positionZ)
            

                    # Release the device handle
                    mcldll.MCL_ReleaseHandle(handle)
                if event == 'Z down':
                    step_size = float(values['-STEPSIZE-'])
                    new_pos = str(float(values['-ZPOS-']) -float(step_size))
                    window['-ZPOS-'].update(new_pos)
                    zpos = float(new_pos)
                    mcldll = CDLL(r"C:/Program Files/Mad City Labs/NanoDrive/Madlib.dll")

                    # The correct return types for the functions used must be set.
                    mcldll.MCL_ReleaseHandle.restype = None
                    mcldll.MCL_SingleReadN.restype = c_double

                    # Acquire a device handle
                    handle = mcldll.MCL_InitHandle()
                    print("Handle = ", handle)

                    # Choose axis to move and new position in micrometers
                    axis_z = c_uint(3)
                    pos_z = c_double(zpos)

                    # Move to a new position
                    error = mcldll.MCL_SingleWriteN(pos_z, axis_z, handle)
                    print("Error = ", error)

                    # Wait for nanopositioner to settle
                    sleep(0.1)

                    # Read the new position
                    positionZ = mcldll.MCL_SingleReadN(axis_z, handle)
                    print("PositionZ = ", positionZ)
            

                    # Release the device handle
                    mcldll.MCL_ReleaseHandle(handle)
                if event == 'X up':
                    step_size = float(values['-STEPSIZE-'])
                    new_pos = str(float(values['-XPOS-']) +float(step_size))
                    window['-XPOS-'].update(new_pos)
                    xpos = float(new_pos)
                    mcldll = CDLL(r"C:/Program Files/Mad City Labs/NanoDrive/Madlib.dll")

                    # The correct return types for the functions used must be set.
                    mcldll.MCL_ReleaseHandle.restype = None
                    mcldll.MCL_SingleReadN.restype = c_double

                    # Acquire a device handle
                    handle = mcldll.MCL_InitHandle()
                    print("Handle = ", handle)

                    # Choose axis to move and new position in micrometers
                    axis_x = c_uint(1)
                    pos_x = c_double(xpos)

                    # Move to a new position
                    error = mcldll.MCL_SingleWriteN(pos_x, axis_x, handle)
                    print("Error = ", error)

                    # Wait for nanopositioner to settle
                    sleep(0.1)

                    # Read the new position
                    positionX = mcldll.MCL_SingleReadN(axis_x, handle)
                    print("PositionX = ", positionX)
            

                    # Release the device handle
                    mcldll.MCL_ReleaseHandle(handle)
                if event == 'X down':
                    step_size = float(values['-STEPSIZE-'])
                    new_pos = str(float(values['-XPOS-']) -float(step_size))
                    window['-XPOS-'].update(new_pos)
                    xpos = float(new_pos)
                    mcldll = CDLL(r"C:/Program Files/Mad City Labs/NanoDrive/Madlib.dll")

                    # The correct return types for the functions used must be set.
                    mcldll.MCL_ReleaseHandle.restype = None
                    mcldll.MCL_SingleReadN.restype = c_double

                    # Acquire a device handle
                    handle = mcldll.MCL_InitHandle()
                    print("Handle = ", handle)

                    # Choose axis to move and new position in micrometers
                    axis_x = c_uint(3)
                    pos_x = c_double(xpos)

                    # Move to a new position
                    error = mcldll.MCL_SingleWriteN(pos_x, axis_x, handle)
                    print("Error = ", error)

                    # Wait for nanopositioner to settle
                    sleep(0.1)

                    # Read the new position
                    positionX = mcldll.MCL_SingleReadN(axis_x, handle)
                    print("PositionX = ", positionX)
            

                    # Release the device handle
                    mcldll.MCL_ReleaseHandle(handle)
                
                if event == 'Y up':
                    step_size = float(values['-STEPSIZE-'])
                    new_pos = str(float(values['-YPOS-']) +float(step_size))
                    window['-YPOS-'].update(new_pos)
                    ypos = float(new_pos)
                    mcldll = CDLL(r"C:/Program Files/Mad City Labs/NanoDrive/Madlib.dll")

                    # The correct return types for the functions used must be set.
                    mcldll.MCL_ReleaseHandle.restype = None
                    mcldll.MCL_SingleReadN.restype = c_double

                    # Acquire a device handle
                    handle = mcldll.MCL_InitHandle()
                    print("Handle = ", handle)

                    # Choose axis to move and new position in micrometers
                    axis_y = c_uint(1)
                    pos_y = c_double(ypos)

                    # Move to a new position
                    error = mcldll.MCL_SingleWriteN(pos_y, axis_y, handle)
                    print("Error = ", error)

                    # Wait for nanopositioner to settle
                    sleep(0.1)

                    # Read the new position
                    positionY = mcldll.MCL_SingleReadN(axis_y, handle)
                    print("PositionY = ", positionY)
            

                    # Release the device handle
                    mcldll.MCL_ReleaseHandle(handle)
                
                if event == 'Y down':
                    step_size = float(values['-STEPSIZE-'])
                    new_pos = str(float(values['-YPOS-']) -float(step_size))
                    window['-YPOS-'].update(new_pos)
                    ypos = float(new_pos)
                    mcldll = CDLL(r"C:/Program Files/Mad City Labs/NanoDrive/Madlib.dll")

                    # The correct return types for the functions used must be set.
                    mcldll.MCL_ReleaseHandle.restype = None
                    mcldll.MCL_SingleReadN.restype = c_double

                    # Acquire a device handle
                    handle = mcldll.MCL_InitHandle()
                    print("Handle = ", handle)

                    # Choose axis to move and new position in micrometers
                    axis_y = c_uint(1)
                    pos_y = c_double(ypos)

                    # Move to a new position
                    error = mcldll.MCL_SingleWriteN(pos_y, axis_y, handle)
                    print("Error = ", error)

                    # Wait for nanopositioner to settle
                    sleep(0.1)

                    # Read the new position
                    positionY = mcldll.MCL_SingleReadN(axis_y, handle)
                    print("PositionY = ", positionY)
            

                    # Release the device handle
                    mcldll.MCL_ReleaseHandle(handle)
                
            tt.freeTimeTagger(tagger) 

        '''
        ====================================
        Events on Tab 2
        ====================================
        '''
        if event == 'Move to Abs Position':

            position = [float(x) for x in values['-ABSOLUTEMOVE-'].split(',')]
            print( position)
            # change the path to match your system.
            mcldll = CDLL(r"C:/Program Files/Mad City Labs/NanoDrive/Madlib.dll")

            # The correct return types for the functions used must be set.
            mcldll.MCL_ReleaseHandle.restype = None
            mcldll.MCL_SingleReadN.restype = c_double

            # Acquire a device handle
            handle = mcldll.MCL_InitHandle()
            print("Handle = ", handle)

            # Choose axis to move and new position in micrometers
            axis_x = c_uint(1)
            pos_x = c_double(position[0])

            axis_y = c_uint(2)
            pos_y = c_double(position[1])

            # Move to a new position
            error = mcldll.MCL_SingleWriteN(pos_x, axis_x, handle)
            print("Error = ", error)

            error = mcldll.MCL_SingleWriteN(pos_y, axis_y, handle)
            print("Error = ", error)


            # Wait for nanopositioner to settle
            sleep(0.1)

            # Read the new position
            positionX = mcldll.MCL_SingleReadN(axis_x, handle)
            print("PositionX = ", positionX)
            positionY = mcldll.MCL_SingleReadN(axis_y, handle)
            print("PositionY = ", positionY)

            # Release the device handle
            mcldll.MCL_ReleaseHandle(handle)

        if event == 'Start Scan' :
            global_plot_control = True
            x_start = float(values['-STARTXCOORD-'])
            y_start = float(values['-STARTYCOORD-'])
            y_end = float(values['-ENDYCOORD-'])
            x_end = float(values['-ENDXCOORD-'])
            nx_pix = int(values['-XPOINTS-'])
            ny_pix = int(values['-YPOINTS-'])
            dwell_time = int(values['-PIXELDWELLTIME-'])
            if dwell_time<100000:
                dwell_time = 100000
            iterations = int(values['-ITERATIONS-'])
            max_value = int(values["-MAXPIXEL-"])
            min_value = int(values["-MINPIXEL-"])
            directory = values['-DIRECTORY3-']
            name = values['-NAME2-']
            if iterations == 0:
                iterations = 100000000000000000000
            if values['-NANOWAVEFORMS-'] == 'Square Raster':
                square_raster = True
            else:
                square_raster = False
            
            if values['-INTEGRATIONMODE-']:
                
                if plt.get_fignums():
                    plt.close()

                createScanPoints(x_start = x_start, y_start = y_start, nx_pix = nx_pix, ny_pix = ny_pix, x_end = x_end, y_end =  y_end, file_name = 'path', square_raster = square_raster)
            
                tagger = tt.createTimeTagger()
                tagger.setTestSignal(1, False)
                tagger.setTestSignal(2, False)
                tagger.setTriggerLevel(1,.5)
                int_img = np.zeros((ny_pix, nx_pix))
                
                plt.imshow(int_img, extent=[x_start, x_end, y_end, y_start],  vmin = min_value, vmax = max_value)
                
                cbar = plt.colorbar()
                
                for i in range(iterations):
                    
                    delay_signal = tt.DelayedChannel(tagger, 3, dwell_time * 1e6)
                    delay_ch = delay_signal.getChannel()

                    cbm = tt.CountBetweenMarkers(tagger, 4, 3, delay_ch, nx_pix*ny_pix )
                    p1 = mp.Process(target = startScanningWithoutWaveform, args = ('pathX.txt' , 'pathY.txt', None, dwell_time, 1))#the args are (input pos for x, input pos for y, input pos for z, dwell time , iteratoins)
                    
                    p1.start()
                    p1.join()

                    counts = cbm.getData()
                    current_img =  np.reshape(counts, (ny_pix, nx_pix))
                    int_img+=current_img
                    

                    cbar.remove()
                    plt.imshow(int_img, extent=[x_start, x_end, y_end, y_start], vmin = min_value, vmax = max_value)
                    plt.xticks(np.arange(x_start, x_end, (x_end-x_start)/10))
                    plt.yticks(np.arange(y_start, y_end, (y_end-y_start)/10))
                    plt.ylabel('μm')
                    plt.xlabel('μm')
                    cbar = plt.colorbar()
                    cbar.set_label('Counts')
                    plt.pause(1)

                    event, values = window.read(timeout = 100)
                    if event == sg.WINDOW_CLOSED or event == 'Exit':
                        break
                    if event == 'Stop Scanning':
                        break

                cbar.remove()    
                plt.colorbar()
                plt.show()
                
                tt.freeTimeTagger(tagger) 


            else:
                if plt.get_fignums():
                    plt.close()
                       
                createScanPoints(x_start = x_start, y_start = y_start, nx_pix = nx_pix, ny_pix = ny_pix, x_end = x_end, y_end =  y_end, file_name = 'path', square_raster = square_raster)
               
                tagger = tt.createTimeTagger()
                tagger.setTestSignal(1, False)
                tagger.setTestSignal(2, False)
                tagger.setTriggerLevel(1,.5)

                
                img = np.zeros((ny_pix, nx_pix))
                plt.imshow(img, extent=[x_start, x_end, y_end, y_start],  vmin = min_value, vmax = max_value)
                cbar = plt.colorbar()
                
                plt.tight_layout()
                for i in range(iterations):
                  
                    delay_signal = tt.DelayedChannel(tagger, 3, dwell_time * 1e6)
                    delay_ch = delay_signal.getChannel()
                    
                    cbm = tt.CountBetweenMarkers(tagger, 1, 3, delay_ch, nx_pix*ny_pix )
                    p1 = mp.Process(target = startScanningWithoutWaveform, args = (r'C:\Users\ccobbbruno\Documents\Utzat Lab Code\src\pathX.txt' , r'C:\Users\ccobbbruno\Documents\Utzat Lab Code\src\pathY.txt', None, dwell_time, 1))#the args are (input pos for x, input pos for y, input pos for z, dwell time , iteratoins)
                    
                    p1.start()
                    
                    while 1:
                        counts = cbm.getData()
                        
                        current_img = np.reshape(counts, (ny_pix, nx_pix))
                        
                    
                        if square_raster:
                            for i in range(ny_pix):
                                if i%2 == 1:
                                    current_img[i,:] = current_img[i,::-1]

                        mask = current_img !=0
                        img[mask]=current_img[mask]
                        
                        cbar.remove()
                        plt.imshow(img, extent=[x_start, x_end, y_end, y_start],  vmin = min_value, vmax = max_value)
                        plt.tight_layout()
                        plt.xticks(np.arange(x_start, x_end, (x_end-x_start)/(10)))
                        plt.yticks(np.arange(y_start, y_end, (y_end-y_start)/(10)))
                        plt.ylabel('μm')
                        plt.xlabel('μm')
                        cbar = plt.colorbar()
                        
                        cbar.set_label('Counts')
                        
                        plt.pause(.5)

                        event, values = window.read(timeout = 100)
                        if event  == 'Stop Scanning':
                            p1.terminate()
                        elif p1.is_alive()==False:
                            sleep(.5)
                            break
                        
                    p1.join()
                   
                    
                np.savetxt(directory + os.sep+ name + '.txt',img)
                tt.freeTimeTagger(tagger) 
        
        if event == 'Move to Abs Z Position':

            zpos = float(values['-ABSOLUTEMOVEZ-'])

            mcldll = CDLL(r"C:/Program Files/Mad City Labs/NanoDrive/Madlib.dll")

            # The correct return types for the functions used must be set.
            mcldll.MCL_ReleaseHandle.restype = None
            mcldll.MCL_SingleReadN.restype = c_double

            # Acquire a device handle
            handle = mcldll.MCL_InitHandle()
            print("Handle = ", handle)

            # Choose axis to move and new position in micrometers
            axis_z = c_uint(3)
            pos_z = c_double(zpos)

            # Move to a new position
            error = mcldll.MCL_SingleWriteN(pos_z, axis_z, handle)
            print("Error = ", error)

            # Wait for nanopositioner to settle
            sleep(0.1)

            # Read the new position
            positionZ = mcldll.MCL_SingleReadN(axis_z, handle)
            print("PositionZ = ", positionZ)
       

            # Release the device handle
            mcldll.MCL_ReleaseHandle(handle)
        
        if event == 'Move Z up':
            new_pos = str(float(values['-ABSOLUTEMOVEZ-']) +.05)
            window['-ABSOLUTEMOVEZ-'].update(new_pos)
            zpos = float(values['-ABSOLUTEMOVEZ-']) 
            mcldll = CDLL(r"C:/Program Files/Mad City Labs/NanoDrive/Madlib.dll")

            # The correct return types for the functions used must be set.
            mcldll.MCL_ReleaseHandle.restype = None
            mcldll.MCL_SingleReadN.restype = c_double

            # Acquire a device handle
            handle = mcldll.MCL_InitHandle()
            print("Handle = ", handle)

            # Choose axis to move and new position in micrometers
            axis_z = c_uint(3)
            pos_z = c_double(zpos)

            # Move to a new position
            error = mcldll.MCL_SingleWriteN(pos_z, axis_z, handle)
            print("Error = ", error)

            # Wait for nanopositioner to settle
            sleep(0.1)

            # Read the new position
            positionZ = mcldll.MCL_SingleReadN(axis_z, handle)
            print("PositionZ = ", positionZ)
       

            # Release the device handle
            mcldll.MCL_ReleaseHandle(handle)

        if event == 'Move Z down':
            new_pos = str(float(values['-ABSOLUTEMOVEZ-']) -.05)
            window['-ABSOLUTEMOVEZ-'].update(new_pos)
            zpos = float(values['-ABSOLUTEMOVEZ-']) 
            mcldll = CDLL(r"C:/Program Files/Mad City Labs/NanoDrive/Madlib.dll")

            # The correct return types for the functions used must be set.
            mcldll.MCL_ReleaseHandle.restype = None
            mcldll.MCL_SingleReadN.restype = c_double

            # Acquire a device handle
            handle = mcldll.MCL_InitHandle()
            print("Handle = ", handle)

            # Choose axis to move and new position in micrometers
            axis_z = c_uint(3)
            pos_z = c_double(zpos)

            # Move to a new position
            error = mcldll.MCL_SingleWriteN(pos_z, axis_z, handle)
            print("Error = ", error)

            # Wait for nanopositioner to settle
            sleep(0.1)

            # Read the new position
            positionZ = mcldll.MCL_SingleReadN(axis_z, handle)
            print("PositionZ = ", positionZ)
       

            # Release the device handle
            mcldll.MCL_ReleaseHandle(handle)
        '''
        =====================================
        Events on Tab 3
        =====================================
        '''
        if event == 'Get Data':

            tagger = tt.createTimeTagger()
            # Retrieve input values from GUI
            
            positions  = [float(x) for x in values['-POSITION-'].split(',')]
            PVT_file = values['-PVTFILE-']
            directory = values['-DIRECTORY2-']
            
            channels = [float(x) for x in values['-CHANNELS2-'].split(',')]
            voltage = float(values['-VOLTAGE2-'])
            names = []


            with open(directory + os.sep + 'positions.pos', "w") as file:
                for pos in positions:
                    file.write(str(pos) + "\n")


            for i in range(len(positions)):
                names.append('pos' + str(int(1e6*positions[i])))

            '''
            i = -1
            for name in names:
                path = Path(directory + os.sep + name + '.ttbin')
                if path.is_file():
                    i +=1
                    if directory + os.sep + name :
                        names[i] = name + '_1'
                '''
            print(names)
            
            with open(PVT_file, 'r') as file:
                lines = file.readlines()
                time = 0
                for line in lines:
                    elements = line.strip().split(', ')
                    number = float(elements[0])
                    time += number

            print(time)
            #set test signal
            tagger.setTestSignal(2, False)
            assemblypath = r"C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.XPS.CommandInterface\v4.0_2.3.0.0__9a267756cf640dcf\Newport.XPS.CommandInterface.dll"
               
            clr.AddReference(assemblypath)
        
            from CommandInterfaceXPS import *
        
            xps = XPS()
        
            xps.OpenInstrument('192.168.254.254', 5001,1000000)
        
            err_groupkill = xps.GroupKill('Multiple1')
            err_groupinit = xps.GroupInitialize('Multiple1')
            err_grouphome = xps.GroupHomeSearch('Multiple1')
            
            for i in range(len(positions)):
                
                name = names[i]
                position = positions[i]
                # Call the collect_data function with the provided inputs
                synchronized = tt.SynchronizedMeasurements(tagger)
                print(directory + os.sep + name)
                filewriter = tt.FileWriter(synchronized.getTagger(),  directory + os.sep + name, channels)
                
           
                
                
                pvtname = PVT_file.rsplit('/', 1)[-1]
                sleep(.2)
                filename = pvtname.rsplit('/', 1)[-1]
                xps.GroupMoveAbsolute('Multiple1', [position], 1)
                
                synchronized.startFor(1e12*int(np.ceil(time)))
                
                err_exec = xps.MultipleAxesPVTExecution('Multiple1', filename, 1)
                print(err_exec)
              
                synchronized.waitUntilFinished()
                del filewriter
                del synchronized
            
            tt.freeTimeTagger(tagger)
            print('Measurement Over')

    window.close()
