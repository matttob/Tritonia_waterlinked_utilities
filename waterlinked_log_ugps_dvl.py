"""
Get position from Water Linked Underwater GPS
"""


import argparse
from calendar import c
import csv

import json
import socket
import threading
import time
import requests
import threading
import datetime
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



# create splash screen for .exe opening
try:
    import pyi_splash
    pyi_splash.update_text('UI Loaded ...')
    pyi_splash.close()
except:
    pass


## UGPS FUNCTIONS
def log_file_name(extension):
    """
    Create a file name in the logfiles directory, based on current data and time
    Requires the computer to have an RTC or synched clock
    """
    now = datetime.datetime.now()
    # Linux
    file_name = '%0.4d%0.2d%0.2d-%0.2d%0.2d%0.2d' % (now.year, now.month, now.day, now.hour, now.minute, now.second)
    return file_name + extension


def get_logging_data_dir():
    global logging_data_dir
    logging_data_dir = filedialog.askdirectory(title='Select the Parent Directory')
    # test for api response 
    global base_url
    # base_url = 'http://192.168.2.94'
    base_url = ' http://dempreo.waterlinked.com'
    start_button.config(state='normal')

    

def get_data(url):
    try:
        r = requests.get(url)
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


def get_imu(base_url):
    return get_data("{}/api/v1/imu/calibrate".format(base_url))


## DVL FUNCTIONS

class _CSVWriter:
    def __init__(self, csv_file, message_type):
        self.csv_file = csv_file
        self.csv_writer = self._csv_writer(csv_file, message_type)

    @classmethod
    def _csv_field_names(cls, message_type):
        if message_type == "velocity":
            return [
                "log_time",
                "time_of_validity",
                "time_of_transmission",
                "time",
                "vx",
                "vy",
                "vz",
                "fom",
                "altitude",
                "velocity_valid",
                "status" ]
        return [
            "log_time",
            "ts",
            "x",
            "y",
            "z",
            "std",
            "status" ]

    @classmethod
    def _csv_writer(cls, csv_file, message_type):
        csv_writer = csv.DictWriter(
            csv_file,
            fieldnames = cls._csv_field_names(message_type),
            extrasaction = "ignore",
            delimiter = ',')
        csv_writer.writeheader()
        return csv_writer

    def writerow(self, row):
        self.csv_writer.writerow(row)

    def flush(self):
        self.csv_file.flush()

def _start_dvl_socket(dvl_ip):
    dvl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dvl_socket.connect((dvl_ip, 16171))
    return dvl_socket



def _format_timestamp(timestamp, time_format):
    return datetime.datetime.strftime(
        datetime.datetime.fromtimestamp(timestamp),
        time_format)

def _format_timestamps(message_type, message, time_format):
    message["log_time"] = _format_timestamp(
        message["log_time"] / 1e6,
        time_format)
    if message_type == "velocity":
        try:
            message["time_of_validity"] = _format_timestamp(
                message["time_of_validity"] / 1e6,
                time_format)
            message["time_of_transmission"] = _format_timestamp(
                message["time_of_transmission"] / 1e6,
                time_format)
        except KeyError:
            pass
    else:
        message["ts"] = _format_timestamp(message["ts"], time_format)

def _handle(message_type, message, time_format, csv_writer):
    if not message:
        return
    try:
        report = json.loads(message)
    except json.decoder.JSONDecodeError:
        print("Could not parse to JSON: " + message)
        return
    if report["type"] != message_type:
        return
    report["log_time"] = int(datetime.datetime.utcnow().timestamp() * 1e6)
    if time_format:
        _format_timestamps(message_type, report, time_format)
    # print(json.dumps(report))
    if csv_writer is not None:
        csv_writer.writerow(report)
        csv_writer.flush()

def _process_messages(dvl_socket, message_type, time_format, csv_writer = None):
    buffer_size = 4096
    message = ""
    while True:
        if stop == 0:
            buffer = dvl_socket.recv(buffer_size).decode()
            if not buffer:
                continue
            message_parts = buffer.split("\r\n")
            if len(message_parts) == 1:
                message += message_parts[0]
                continue
            for message_part in message_parts[:-1]:
                message = message + message_part
                _handle(message_type, message, time_format, csv_writer)
                message = ""
            if message_parts[-1]:
                message = message_parts[-1]


def dvl_velocity_log_main():
        global csv_file_velocity
        # arguments = arguments_parser().parse_args()
        dvl_ip = "dvl.demo.waterlinked.com"
        csv_file_path_velocity = logging_data_dir + '/'+ 'DVL_VELOCITIES_' + log_file_name('.csv')
        message_type = "velocity"
        time_format = ""
        with open(csv_file_path_velocity, "w") as csv_file_velocity:
            _process_messages(
                _start_dvl_socket(dvl_ip),
                message_type,
                time_format,
                _CSVWriter(csv_file_velocity, message_type))

def dvl_position_log_main():
        global csv_file_position
        # arguments = arguments_parser().parse_args()
        dvl_ip = "dvl.demo.waterlinked.com"
        # dvl_ip = "192.168.2.95"
        
        csv_file_path_position = logging_data_dir + '/'+ 'DVL_DEAD_RECKON_POSITIONS_' + log_file_name('.csv')
        message_type = "position_local"
        time_format = ""
        with open(csv_file_path_position, "w") as csv_file_position:
            _process_messages(
                _start_dvl_socket(dvl_ip),
                message_type,
                time_format,
                _CSVWriter(csv_file_position, message_type))                

def start_thread():
    # Assign global variable and initialize value
    global stop
    global t_dvl
    stop = 0
    # Create and launch a thread 
    t = Thread (target = main)
    t.start()
    stop_button.config(state='normal')
    start_button.config(state='disabled')
    if DVL_Check_velocity.get() == 1:
        t_dvl_velocity = Thread (target = dvl_velocity_log_main)
        t_dvl_velocity.start()

    if DVL_Check_position.get() == 1:
        t_dvl_position = Thread (target = dvl_position_log_main)
        t_dvl_position.start()

def stop_thread():
    # Assign global variable and set value to stop
    global stop
    stop = 1
    start_button.config(state='normal')
    stop_button.config(state='disabled')
    # # close DVL log files
    # if DVL_Check_velocity.get() == 1:
    #     csv_file_velocity.close()
    #     csv_file_position.close()

def create_gpx():
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


def get_and_store_values():    
    now = datetime.datetime.now()
    time_iter = '%0.4d%0.2d%0.2d-%0.2d%0.2d%0.2d' % (now.year, now.month, now.day, now.hour, now.minute, now.second)

    filtered_acoutistic_position = get_acoustic_position(base_url)
    if filtered_acoutistic_position:
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
    master_imu = get_imu(base_url)
    if master_position:
        master_position_data_dict = {'time' : time_iter, 'longitude' :master_position["lon"],'latitude' :master_position["lat"],
        'heading' : master_position["orientation"], 'pitch' : master_imu["pitch"], 'progress' : master_imu["progress"], 
        'roll' : master_imu["roll"], 'state' : master_imu["state"], 'yaw' : master_imu["yaw"]}
        with open(master_position_log_file_name, mode='a')  as f_master:
            dictwriter_object = DictWriter(f_master, fieldnames=master_position_headers)
            dictwriter_object.writerow(master_position_data_dict)
            # Close the file object
            f_master.close()
    time.sleep(1)        
    
def main():
    # filtered Log file
    global filtered_log_file_name 
    filtered_log_file_name = logging_data_dir + '/'+ 'WL_filtered_positions_' + log_file_name('.csv')
    # Open the file for append
    global filtered_output_file
    filtered_output_file = open(filtered_log_file_name, 'w', newline='')   
    global filtered_position_headers
    filtered_position_headers = ['Time', 'X Position','Y Position', 'Z Position']
    writer = DictWriter(filtered_output_file, delimiter=',', lineterminator='\n',fieldnames=filtered_position_headers)
    writer.writeheader()
    filtered_output_file.close()

    # global position Log File
    global  global_position_log_file_name
    global_position_log_file_name = logging_data_dir +'/'+ 'WL_global_positions_' + log_file_name('.csv')
    # Open the file for append
    global global_position_output_file
    global_position_output_file = open(global_position_log_file_name, 'w', newline='')   
    global global_position_headers
    global_position_headers = ['time', 'longitude','latitude','altitude']
    writer = DictWriter(global_position_output_file, delimiter=',', lineterminator='\n',fieldnames=global_position_headers)
    writer.writeheader()
    global_position_output_file.close()

    # master Log 
    global master_position_log_file_name 
    master_position_log_file_name = logging_data_dir + '/'+ 'WL_master_positions_' + log_file_name('.csv')
    # Open the file for append
    global master_output_file
    master_output_file = open(master_position_log_file_name, 'w', newline='')   
    global master_position_headers
    master_position_headers = ['time', 'longitude','latitude','heading','pitch','progress','roll','state','yaw']
    writer = DictWriter(master_output_file, delimiter=',', lineterminator='\n',fieldnames=master_position_headers)
    writer.writeheader()
    master_output_file.close()


    
    while True:
        get_and_store_values() 
        if stop == 1:   
            thread = threading.Thread(target=get_and_store_values)
            thread.start()
            thread.join()
            

            break   #Break while loop when stop = 1


    create_gpx()


app = tk.Tk()
app.title("TRITONIA WATERLINKED DATA LOGGING")
app.geometry("250x200")

directory_choose_button = tk.Button(app, text="Choose data storage folder",command=get_logging_data_dir)
directory_choose_button.grid(row=1,columnspan=2)


start_button = tk.Button(app, text="Start Logging",command=start_thread,state='disabled')
start_button.grid(row=2,columnspan=2)

stop_button = tk.Button(app, text="Stop Logging",command=stop_thread,state='disabled')
stop_button.grid(row=3,columnspan=2)

UGPS_Check = tk.IntVar()
UGPS_record_check_box = tk.Checkbutton(app, text = "UGPS Logging", variable = UGPS_Check, \
                 onvalue = 1, offvalue = 0, height=1, \
                 width = 20)
UGPS_record_check_box.grid(row=4,column=0)

DVL_Check_velocity = tk.IntVar()
DVL_velocity_record_check_box = tk.Checkbutton(app, text = "DVL Velocity Logging", variable = DVL_Check_velocity, \
                 onvalue = 1, offvalue = 0, height=1, \
                 width = 20)
DVL_velocity_record_check_box.grid(row=5,column=0)

DVL_Check_position = tk.IntVar()
DVL_position_record_check_box = tk.Checkbutton(app, text = "DVL Position Logging", variable = DVL_Check_position, \
                 onvalue = 1, offvalue = 0, height=1, \
                 width = 20)
DVL_position_record_check_box.grid(row=6,column=0)

L2 = tk.Label(app, text="Logging Status : ")
L2.grid(row=7,column=0,sticky=tk.W)

canvas = Canvas(app, width = 13, height = 13)  
canvas.grid(row=7,column=1,sticky=tk.W)

log_light=canvas.create_oval(3, 3,13, 13, fill='white')



app.mainloop()
