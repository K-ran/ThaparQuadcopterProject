#!/usr/bin/env python
from __future__ import print_function

from firebase import firebase
from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command
import time, os
import math
from pymavlink import mavutil
import requests

current_dir = os.path.dirname(os.path.realpath(__file__))

# Change according to your firebase database. 
firebase = firebase.FirebaseApplication('https://capstone-f2b6f.firebaseio.com/')

def get_location():
    locations=firebase.get('area',None)
    return locations

def get_status():
    status=firebase.get('status',None)
    return status



def set_status(status):
    status=firebase.put('/','status',status)
    return status

# write status to file
def write_status(status):
    try:
        with open(current_dir+'/status.txt', 'w') as file:
            file.write(status)
    except: 
        print_log("Error sending location")


#Set up option parsing to get connection string
import argparse  

parser = argparse.ArgumentParser(description='Demonstrates basic mission operations.')
parser.add_argument('--connect', 
                   help="vehicle connection target string. If not specified, SITL automatically started and used.")
args = parser.parse_args()

# function to print logs on the file
def print_log(string):
    try:
        with open(current_dir+'/logs.txt', 'a') as file:
             file.write(string+'\n')
    except:
        print("Error writing logs")

# Clear the file
try:
    with open(current_dir+'/logs.txt', 'w') as file:
        pass
except:
    print("Error writing logs")

# Connect to the Quadcopter
print_log('Connecting to vehicle on: %s' % connection_string)
vehicle = connect(connection_string, wait_ready=True)


# Put the quad on standby mode
write_status("standby")


# Create a mission on the 
def create_mission(altitude, coordinates):
    cmds = vehicle.commands
    # Clear any existiong commands
    cmds.clear() 
    
    # Create New commands     
    #Add MAV_CMD_NAV_TAKEOFF command. This is ignored if the vehicle is already in the air.
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 0, altitude))

    for i in range(len(coordinates)):
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, coordinates[i]['latitude'], coordinates[i]['longitude'], altitude))

    # add current position as last waypoint
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, vehicle.location.global_frame.lat, vehicle.location.global_frame.lon, altitude))

    #add a few dummy waypoints (lets us know when have reached destination)
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, vehicle.location.global_frame.lat, vehicle.location.global_frame.lon, altitude))   
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, vehicle.location.global_frame.lat, vehicle.location.global_frame.lon, altitude))   
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, vehicle.location.global_frame.lat, vehicle.location.global_frame.lon, altitude))   

    print(" Upload new commands to vehicle")
    cmds.upload()


def arm_and_takeoff(aTargetAltitude):
    print_log("Basic pre-arm checks")

    #This code is commented because this was not working and its kinf of optional.
    #If possible, get this working.  
    # Don't let the user try to arm until autopilot is ready
#    while not vehicle.is_armable:
#       print_log(" Waiting for vehicle to initialise...")
#        time.sleep(1)

        
    print_log("Arming motors")
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:      
        print_log(" Waiting for arming...")
        time.sleep(1)

    print_log("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command 
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print_log(" Altitude: "+ str(vehicle.location.global_relative_frame.alt))      
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95: #Trigger just below target alt.
            print_log("Reached target altitude")
            break
        time.sleep(1)

while True:
    write_status("standby")	
    status = get_status();
    # just s safety measure
    while status!="standby":
	time.sleep(1);
	write_status("standby")
	status= get_status();
	
    while status=='standby':
        print_log('Waiting for instructions.')
        try:
            with open(current_dir+'/coordinates.txt', 'w') as file:
                file.write(str(vehicle.location.global_frame.lat)+','+str(vehicle.location.global_frame.lon))
        except:
                print("Error sending location")  
        time.sleep(1)
        status = get_status();
        
    print_log('Waiting for new waypoint')

    data = None
    while(data==None):
        data = get_location()

    # data = [{u'latitude': 30.352446922204905, u'longitude': 76.35800365358591}, {u'latitude': 30.354363365436974, u'longitude': 76.36379018425941}, {u'latitude': 30.353681736245733, u'longitude': 76.36066339910029}, {u'latitude': 30.351726510376686, u'longitude': 76.36398900300264}]

    print_log("Got way points\n "+str(data))


    try:
            with open(current_dir+'/coordinates.txt', 'w') as file:
                 file.write(str(vehicle.location.global_frame.lat)+','+str(vehicle.location.global_frame.lon))
    except:
            print("Error sending location")

    #exit()


    break_point = len(data)+2 #additional 2 ecause of one dummy and one initial coordinated

    altitude=15

    create_mission(altitude,data)

    # From Copter 3.3 you will be able to take off using a mission item. Plane must take off using a mission item (currently).
    arm_and_takeoff(altitude)

    print_log("Starting mission")
    # Reset mission set to first (0) waypoint
    vehicle.commands.next=0

    # Set mode to AUTO to start mission
    vehicle.mode = VehicleMode("AUTO")

    print_log('Mission Started')

    seconds=0
    try:
        r = requests.get("http://127.0.0.1:5000/reset")
    except Exception as e:
        raise e

    while True:
        seconds+=1;    
        nextwaypoint=vehicle.commands.next
        lat = str(vehicle.location.global_frame.lat)
        lon = str(vehicle.location.global_frame.lon)    

        # capture images 
        if seconds%2==0:
             try:
                 r = requests.get("http://127.0.0.1:5000/capture/"+lat+"/"+lon)
             except Exception as e:
                 raise e

        try:
            with open(current_dir+'/coordinates.txt', 'w') as file:
                 file.write(lat+','+lon)
        except: 
            print_log("Error sending location")
            
        if nextwaypoint>=break_point: #Dummy waypoint - as soon as we reach waypoint 4 this is true and we exit.
            print_log("Mission over, eading back home")
            break;
        time.sleep(1)

    print_log('Landing....')
    vehicle.mode = VehicleMode("LAND")

    while vehicle.system_status.state!="STANDBY":
	print_log('Altitude: '+str(vehicle.location.global_relative_frame.alt))
        time.sleep(1)
	pass;
    print_log('Quadcopter Landed!')  
    write_status("standby")  

    # Shut down simulator if it was started.
    if sitl is not None:
        sitl.stop()

vehicle.close()
