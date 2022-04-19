"""
Get position from Water Linked Underwater GPS
"""
import threading
from time import sleep
import requests
import threading
# import argparse
# import json
from datetime import datetime
from csv import DictWriter
import tkinter as tk
from tkinter import filedialog
from tkinter import Canvas
from tkinter import Label
# from tkinter import Text
# from tkinter import Entry
from threading import Thread
from gpx_converter import Converter
import platform
import subprocess

# Enable flash screen on loading when python module is converted into .exe
try:
    import pyi_splash
    pyi_splash.update_text('UI Loaded ...')
    pyi_splash.close()
except:
    pass

def get_data(base_url):
    try:
        r = requests.get(base_url)
    except requests.exceptions.RequestException as exc:
        print("Exception occured {}".format(exc))
        return None
    if r.status_code != requests.codes.ok:
        print("Got error {}: {}".format(r.status_code, r.text))
        return None
    return r.json()


def get_acoustic_position(base_url):
    return get_data("{}/api/v1/position/acoustic/filtered".format(base_url))


def get_global_position(base_url):
    return get_data("{}/api/v1/position/global".format(base_url))


def get_master_position(base_url):
    return get_data("{}/api/v1/position/master".format(base_url))


def test_for_connection_set_start_button_status():
     # test for api response 
    global base_url
    base_url = user_input_url.get()
    filtered_acoutistic_position = get_acoustic_position(base_url)
    if filtered_acoutistic_position:   
        start_button.config(state='normal')
        canvas.itemconfig(log_light, fill='lawn green')
    else:
        start_button.config(state='disable')
        canvas.itemconfig(log_light, fill='red')  

def get_logging_data_dir():
    global logging_data_dir
    logging_data_dir = filedialog.askdirectory(title='Select the Parent Directory')


def file_dialog_box_handler():
    get_logging_data_dir()
    test_for_connection_set_start_button_status()

# Create a file name in the logfiles directory
def log_file_name(extension,time_now):
    file_name = '%0.4d%0.2d%0.2d-%0.2d%0.2d%0.2d' % (time_now.year, time_now.month, time_now.day, time_now.hour, time_now.minute, time_now.second)
    return file_name + extension

def start_thread():
    # Assign global variable and initialize value
    global stop
    stop = 0
    # Create and launch a thread 
    t = Thread (target = main)
    t.start()
    stop_button.config(state='normal')
    start_button.config(state='disabled')

def stop_thread():
    # Assign global variable and set value to stop
    global stop
    stop = 1
    start_button.config(state='normal')
    stop_button.config(state='disabled')
      

def create_gpx(global_position_log_file_name,master_position_log_file_name):
    # create gpx files
    Converter(input_file=global_position_log_file_name).csv_to_gpx(lats_colname='latitude',
                                                longs_colname='longitude',
                                                times_colname='time',
                                                alts_colname='altitude',
                                                output_file=global_position_log_file_name[0:-3]+'gpx')

    Converter(input_file=master_position_log_file_name).csv_to_gpx(lats_colname='latitude',
                                                longs_colname='longitude',
                                                times_colname='time',
                                                output_file=master_position_log_file_name[0:-3]+'gpx')

def cronstruct_log_files():
        # filtered Log file
    filtered_log_file_name =logging_data_dir + '/'+ 'WL_filtered_positions_' + log_file_name('.csv',datetime.now)
    # Open the file for append
    filtered_output_file = open(filtered_log_file_name, 'w', newline='')   
    filtered_position_headers = ['Time', 'X Position','Y Position', 'Z Position']
    writer = DictWriter(filtered_output_file, delimiter=',', lineterminator='\n',fieldnames=filtered_position_headers)
    writer.writeheader()
    filtered_output_file.close()

    # global position Log File
    global_position_log_file_name = logging_data_dir +'/'+ 'WL_global_positions_' + log_file_name('.csv',datetime.now)
    # Open the file for append
    global_position_output_file = open(global_position_log_file_name, 'w', newline='')   
    global_position_headers = ['time', 'longitude','latitude','altitude']
    writer = DictWriter(global_position_output_file, delimiter=',', lineterminator='\n',fieldnames=global_position_headers)
    writer.writeheader()
    global_position_output_file.close()

    # master Log 
    master_position_log_file_name = logging_data_dir + '/'+ 'WL_master_positions_' + log_file_name('.csv',datetime.now)
    # Open the file for append
    master_output_file = open(master_position_log_file_name, 'w', newline='') 
    master_position_headers = ['time', 'longitude','latitude']
    writer = DictWriter(master_output_file, delimiter=',', lineterminator='\n',fieldnames=master_position_headers)
    writer.writeheader()
    master_output_file.close()                                                


def get_and_store_values(filtered_log_file_name, filtered_position_headers, global_position_log_file_name, global_position_headers, master_position_log_file_name, master_position_headers):    
    
    now = datetime.now()
    time_iter = '%0.4d%0.2d%0.2d-%0.2d%0.2d%0.2d' % (now.year, now.month, now.day, now.hour, now.minute, now.second)
    print(time_iter)

    filtered_acoutistic_position = get_acoustic_position(base_url)
    if filtered_acoutistic_position:
        # flash logging 'light' on succesful recpeipt of data
        if canvas.itemcget(log_light, "fill") == 'lawn green':
            canvas.itemconfig(log_light, fill='white') 
        else:
            canvas.itemconfig(log_light, fill='lawn green')
        filtered_position_data_dict = {'Time' : time_iter, 'X Position' :filtered_acoutistic_position["x"],'Y Position' :filtered_acoutistic_position["y"],'Z Position':filtered_acoutistic_position["z"]}
        with open(filtered_log_file_name, mode='a')  as f_filtered:
            dictwriter_object = DictWriter(f_filtered, fieldnames=filtered_position_headers)
            dictwriter_object.writerow(filtered_position_data_dict)
            # Close the file object
            f_filtered.close()
    
    global_position = get_global_position(base_url)
    if global_position:
        global_position_data_dict = {'time' : time_iter, 'longitude' :global_position["lon"],'latitude' :global_position["lat"],'altitude':filtered_acoutistic_position["z"]}
        with open(global_position_log_file_name, mode='a')  as f_global:
            dictwriter_object = DictWriter(f_global, fieldnames=global_position_headers)
            dictwriter_object.writerow(global_position_data_dict)
            # Close the file object
            f_global.close()

    master_position = get_master_position(base_url)
    if master_position:
        master_position_data_dict = {'time' : time_iter, 'longitude' :master_position["lon"],'latitude' :master_position["lat"]}
        with open(master_position_log_file_name, mode='a')  as f_master:
            dictwriter_object = DictWriter(f_master, fieldnames=master_position_headers)
            dictwriter_object.writerow(master_position_data_dict)
            # Close the file object
            f_master.close()


    
def main(filtered_log_file_name, global_position_log_file_name, global_position_headers, master_position_log_file_name, master_position_headers):
    
    cronstruct_log_files()
    
    while True:
        get_and_store_values(filtered_log_file_name, global_position_log_file_name, global_position_headers, master_position_log_file_name, master_position_headers)
        if stop == 1:   
            thread = threading.Thread(target=get_and_store_values)
            thread.start()
            thread.join()
            break   #Break while loop when stop = 1

    create_gpx(global_position_log_file_name,master_position_log_file_name)


## Create GUI
app = tk.Tk()
app.title("TRITONIA WATERLINKED DATA LOGGING")
app.geometry("250x150")

# TextBox Creation for URL of data source
app.update_idletasks()
L1 = tk.Label(app, text="IP of Topside :")
L1.grid(row=0,column=0,sticky=tk.W)
user_input_url = tk.Entry(app)
# user_input_url.insert(0, "http://192.168.2.94")
user_input_url.insert(0, "http://demo.waterlinked.com")
user_input_url.grid(row=0,column=1,sticky=tk.E)

directory_choose_button = tk.Button(app, text="Choose data storage folder",command=file_dialog_box_handler())
directory_choose_button.grid(row=1,columnspan=2)

start_button = tk.Button(app, text="Start Logging Positions",command=start_thread,state='disabled')
start_button.grid(row=2,columnspan=2)

stop_button = tk.Button(app, text="Stop Logging Positions",command=stop_thread,state='disabled')
stop_button.grid(row=3,columnspan=2)

L2 = tk.Label(app, text="Logging Status :     ")
L2.grid(row=4,column=0,sticky=tk.E)

canvas = Canvas(app, width = 13, height = 13)  
canvas.grid(row=4,column=0,sticky=tk.E)

log_light=canvas.create_oval(3, 3,13, 13, fill='white')

app.mainloop()