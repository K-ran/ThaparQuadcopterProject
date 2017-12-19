import picamera
# from time import sleep
from flask import Flask
from subprocess import call
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
fileList = os.listdir(current_dir+"/images/")
for fileName in fileList:
 os.remove(current_dir+"/images/"+fileName)

app = Flask(__name__)

camera = picamera.PiCamera()

i=0

@app.route('/reset')
def reset():
    global i
    i=0

@app.route('/capture/<lat>/<lon>')
def capture(lat,lon):
    global i
    lat = str(lat)
    lon = str(lon)
    print 'Image captures at lat:%s lon%s'%(lat,lon)
    try:
        with open(current_dir+'/images/image'+str(i), 'w') as file:
             file.write(lat+','+lon)
    except: 
        return "Error writing location location" 
    camera.capture( current_dir+'/images/image'+str(i)+'.jpg')
    i+=1
    return 'Done!'

app.run(host='0.0.0.0',port=5000)
