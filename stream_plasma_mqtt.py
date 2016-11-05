'''
Tony DiCola's video and references are at https://www.youtube.com/watch?v=QcyuYvyvOEI
The formulas are at http://www.bidouille.org/prog/plasma
The mqtt topic is "neo" and the server is located on my aws ec2 instance
Right now the program is expecting an MQTT message of the form:
{"brightness":2.0, "rgb":1, "factor":2.0}
Still working on how best to handle a WiFi hiccough -- right now trying to reboot
This version does not allocate memory in the timer callback
'''

from machine import Pin, Timer, reset
import network
import json
import math
import neopixel
import time
#from micropython import const
from umqtt_client import MQTTClient
from config import hosts, ssid, pw, pixel_width, pixel_height 

PIXEL_WIDTH = pixel_width #const(8)
PIXEL_HEIGHT = pixel_height #const(8)
MAX_BRIGHT = 2.0
FACTOR_ONE = 1.0 
host = hosts['other']

flag = bytearray(1)

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

tim = Timer(-1)

def rgb1(v):
  r = 1 + math.cos(v*math.pi)
  g = 0
  b = 1 + math.sin(v*math.pi)
  return (int(MAX_BRIGHT*r),int(MAX_BRIGHT*g),int(MAX_BRIGHT*b))

def rgb2(v):
  r = 1 + math.sin(v*math.pi)
  g = 1 + math.cos(v*math.pi)
  b = 0
  return (int(MAX_BRIGHT*r),int(MAX_BRIGHT*g),int(MAX_BRIGHT*b))

def rgb3(v):
  r = 0
  g = 1 + math.cos(v*math.pi)
  b = 1 + math.sin(v*math.pi)
  return (int(MAX_BRIGHT*r),int(MAX_BRIGHT*g),int(MAX_BRIGHT*b))

RGB_OPTIONS = {1:rgb1, 2:rgb2, 3:rgb3}
RGB = rgb2

def callback(t):
  flag[0] = 1

def check_mqtt():
  global MAX_BRIGHT 
  global RGB
  global FACTOR_ONE

  try:
    b = umc.check_msg()
  except OSError as e:
    print("check_msg:",e)
    # note that when you reset it still gets to the lines below
    # so need to set the value of b (although in the end it resets anyway)
    b = None
    reset()

  print("b =",b)

  if b is None:
    print("ping")
    umc.ping()
    time.sleep(1)
    return

  elif isinstance(b, int):
    time.sleep(1)
    return

  np.fill((0,50,0))
  np.write()

  try:
    zz = json.loads(b[1].decode('utf-8'))
    option = zz.get('rgb', 0)
    RGB = RGB_OPTIONS.get(option, rgb1)
    MAX_BRIGHT = zz.get('brightness', MAX_BRIGHT)
    FACTOR_ONE = zz.get('factor', FACTOR_ONE)
  except Exception as e:
    print(e)

tim.init(period=10000, mode=Timer.PERIODIC, callback=callback)

np = neopixel.NeoPixel(Pin(13, Pin.OUT), PIXEL_WIDTH*PIXEL_HEIGHT)
np.fill((50,0,0))
np.write()

umc = MQTTClient(mqtt_id, host, 1883)

# connect does not have to be a function if it's not going to be called in error handler
def connect():
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  if not wlan.isconnected():
    print('connecting to network...')
    wlan.connect(ssid, pw)
    while not wlan.isconnected():
      pass
  print('network config:', wlan.ifconfig())     

  umc.connect()
  umc.subscribe('neo')

connect()

while True:
  np.fill((0,0,0))
  current = time.ticks_ms() / 1000.0
  for x in range(PIXEL_WIDTH):
    for y in range(PIXEL_HEIGHT):
      v = 0.0
      v += math.sin(x+current)
      v += math.sin(1.0*(x*math.sin(current/0.5)+y*math.cos(current/0.25))+current)
      cx = x + FACTOR_ONE*math.sin(current/5.0)
      cy = y + FACTOR_ONE*math.cos(current/3.0)
      v += math.sin(math.sqrt((math.pow(cx, 2.0)+math.pow(cy, 2.0))+1.0)+current)
      v = (v+3.0)/6.0

      # option below is more complicated formula for colors
      #r = 1 + math.sin(v*math.pi)
      #g = 1 + math.sin(v*math.pi+2.0*math.pi/3.0)
      #b = 1 + math.sin(v*math.pi+4.0*math.pi/3.0)

      #print(r,g,b)

      #np[y*PIXEL_WIDTH+x] = (int(MAX_BRIGHT*r),int(MAX_BRIGHT*g),int(MAX_BRIGHT*b)) ####################################
      np[y*PIXEL_WIDTH+x] = RGB(v)
  np.write()

  if flag[0]:
    check_mqtt()
    flag[0] = 0
