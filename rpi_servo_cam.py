# Raspberry Pi + MG90S + PiCamera 
# rotating the picamera view using MG90S
# using PWM control of GPIO pin 13
#
from picamera import PiCamera
import RPi.GPIO as GPIO
import numpy as np
import time,os

#####################################
# setup picamera for monitoring
#####################################
#
camera = PiCamera() # start picamera

# camera presets
camera.resolution = (1920,1080)
camera.vflip = True
camera.hflip = True
camera.iso = 100
time.sleep(2)
camera.shutter_speed = camera.exposure_speed
camera.exposure_mode = 'off'
g = camera.awb_gains
camera.awb_mode = 'off'
camera.awb_gains = g
camera.framerate = 30

#####################################
# setup the GPIO pin for the servo
#####################################

servo_pin = 13
GPIO.setmode(GPIO.BCM)
GPIO.setup(servo_pin,GPIO.OUT)
pwm = GPIO.PWM(servo_pin,50) # 50 Hz (20 ms PWM period)

# mapping duty cycle to angle
pwm_range = np.linspace(2.0,12.0)
pwm_span = pwm_range[-1]-pwm_range[0]
ang_range = np.linspace(0.0,180.0)
ang_span = ang_range[-1]-ang_range[0]
def angle_to_duty(ang):
    # rounding to approx 0.01 - the max resolution
    # (based on 10-bits, 2%-12% PWM period)
    print('Duty Cycle: '+str(round((((ang - ang_range[0])/ang_span)*pwm_span)+pwm_range[0],1)))
    return round((((ang - ang_range[0])/ang_span)*pwm_span)+pwm_range[0],1)

# optimizing the delay to reduce jitter
def cust_delay(ang,prev_ang):
    # minimum delay using max speed 0.1s/60 deg
    return (10.0/6.0)*(abs(ang-prev_ang))/1000.0

def change_to_angle(prev_ang,curr_ang):
    pwm.ChangeDutyCycle(angle_to_duty(curr_ang))
    camera.wait_recording(cust_delay(curr_ang,prev_ang))
    pwm.ChangeDutyCycle(0) # reduces jitter
    return

prev_ang = 75 # angle to start
pwm.start(angle_to_duty(prev_ang)) # start servo at 0 degrees

cycles = np.linspace(0.0,180.0,20) # duty cycles vector
cycles = np.append(np.append(0.0,cycles),np.linspace(180.0,0.0,20)) # reverse duty cycles

#####################################
# continual scan 0 -> 180 -> 0 [degrees]
# + recording video to a file
#####################################
#
t0 = time.localtime()
vid_name = '{0}_{1}_{2}_{3}_{4}'.format(t0.tm_year,t0.tm_yday,t0.tm_hour,t0.tm_min,t0.tm_sec)
lib_folder = './picamera_videos/'
if os.path.isdir(lib_folder)==False:
    os.mkdir(lib_folder)

camera.start_preview()
camera.start_recording(lib_folder+vid_name+'.h264')
while True:
    try:
        for ii in range(0,len(cycles)):
            change_to_angle(cycles[ii-1],cycles[ii])
            camera.wait_recording(0.5)
           
    except KeyboardInterrupt:
        camera.stop_preview()
        camera.stop_recording()
        break # if CTRL+C is pressed

#####################################
# cleanup RPi, camera, and servo pin
#####################################
#
pwm.ChangeDutyCycle(0) # this prevents jitter
pwm.stop() # stops the pwm on 13
GPIO.cleanup() # good practice when finished using a pin
