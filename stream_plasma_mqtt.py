'''
Tony DiCola's video and references are at https://www.youtube.com/watch?v=QcyuYvyvOEI
The formulas are at http://www.bidouille.org/prog/plasma
The mqtt topic is "neo" and the server is located on my aws ec2 instance
'''

from machine import Pin, Timer
import math
import neopixel
import time
from micropython import const
from umqtt_client import MQTTClient
from config import hosts 

PIXEL_WIDTH = const(8)
PIXEL_HEIGHT = const(8)
MAX_BRIGHT = 20.0
FACTOR_ONE = 1.0 
host = hosts['other']

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

tim = Timer(-1)

def callback(t):
  global MAX_BRIGHT
  b = umc.check_msg()
  print("b =",b)
  if b:
    np.fill((0,0,0))
    np[0] = (100,0,0)
    np.write()

    try:
      MAX_BRIGHT = float(b[1].decode('ascii'))
    except ValueError as e:
      print("Value couldn't be converted to float")

    time.sleep(2)

tim.init(period=10000, mode=Timer.PERIODIC, callback=callback)
np = neopixel.NeoPixel(Pin(13, Pin.OUT), PIXEL_WIDTH*PIXEL_HEIGHT)

umc = MQTTClient(mqtt_id, host, 1883)

umc.connect()
umc.subscribe('neo')

# Clear all the pixels and turn them off.
np.fill((0,0,0))
np.write()

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

      # simpler option for the color (adding 1 since can't be negative)
      b = 1 + math.sin(v*math.pi)
      r = 1 + math.cos(v*math.pi)
      g = 0

      # option below is more complicated formula for colors
      #r = 1 + math.sin(v*math.pi)
      #g = 1 + math.sin(v*math.pi+2.0*math.pi/3.0)
      #b = 1 + math.sin(v*math.pi+4.0*math.pi/3.0)

      #print(r,g,b)

      np[y*PIXEL_WIDTH+x] = (int(MAX_BRIGHT*r),int(MAX_BRIGHT*g),int(MAX_BRIGHT*b))

  np.write()
