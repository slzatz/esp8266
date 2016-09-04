'''
Displays volume on Adafruit NeoPixel FeatherWing
'''

import gc
from time import sleep, time
import network
from config import hosts, ssid, pw 
from umqtt_client import MQTTClient as umc
from machine import Pin
from neopixel import NeoPixel

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

with open('location', 'r') as f:
    loc = f.read().strip()

host = hosts[loc]

print("NewPixel Volume script")
print("mqtt_id =", mqtt_id)
print("location =", loc)
print("host =", host)

np = NeoPixel(Pin(13, Pin.OUT), 32)

def clear():
    for i in range(32):
        np[i] = (0, 0, 0)
    np.write()

c = umc(mqtt_id, host, 1883)

def run():
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  if not wlan.isconnected():
    print('connecting to network...')
    wlan.connect(ssid, pw)
    while not wlan.isconnected():
      pass
  print('network config:', wlan.ifconfig())     

  c.connect()
  c.subscribe('sonos/{}/volume'.format(loc))
  sleep(2) 

  cur_time = time()
  cur_volume = 0
  bb = True

  while 1:

    z = c.check_msg()
    if z:
      print(z)
      if isinstance(z, int):
        print("returned a integer")
        # what could go below is having one neopixel indicate that we're still connected
        if bb:
          np[31] = (50,50,50)
        else:
          np[31] = (0,0,0)
        bb = not bb
        np.write()
        continue

      topic, volume = z
      print("topic =", topic)
      print("volume =", volume)
      ## this is where you would place the neopixel code
      clear()
      # volume maxes at 100
      n = int(volume)//3 # there are 32 neopixels
      for i in range(n):
        np[i] = (50,0,0)#100
      np.write()

    t = time()
    if t > cur_time + 30:
        c.ping()
        cur_time = t
    gc.collect()
    #print(gc.mem_free())
    sleep(1)

#run()
