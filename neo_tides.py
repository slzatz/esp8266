'''
Displays tides Adafruit NeoPixel FeatherWing
'''

import gc
from time import sleep, time
import network
from config import host, ssid, pw 
from umqtt_client import MQTTClient as umc
from machine import Pin
from neopixel import NeoPixel
import json

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

#with open('location', 'r') as f:
#    loc = f.read().strip()

print("neopixel tides script")
print("mqtt_id =", mqtt_id)
#print("location =", loc)
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
  c.subscribe('tides')
  sleep(2) 

  cur_time = time()
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

      if 0:
        topic, msg = z
        print("topic =", topic)
        print("msg =", msg)
        tide_data = json.loads(msg.decode('utf-8'))
        h = tide_data.get('time_delta')
        print("time_delta =", h)
        print("type =", tide_data['type'])
        ## this is where you would place the neopixel code
        if h is not None:
          clear()
          if tide_data['type'] == 'High':
            col = (0,0,50) #high = blue
          else:
            col = (50,50,0) #low = yellow
          for i in range(4):
            np[h+i*8] = col
          np.write()

      if 1:
        topic, msg = z
        print("topic =", topic)
        print("msg =", msg)
        data = json.loads(msg.decode('utf-8'))
        clear()
        for tide_data in data:
          h = tide_data.get('time_delta')
          print("time_delta =", h)
          print("type =", tide_data['type'])
          ## this is where you would place the neopixel code
          if h is not None and h < 8:
            if tide_data['type'] == 'High':
              col = (0,0,50) #high = blue
            else:
              col = (50,50,0) #low = yellow
            for i in range(4):
              np[h+i*8] = col
          np.write()
    #t = time()
    #if t > cur_time + 30:
    #    c.ping()
    #    cur_time = t
    c.ping()
    gc.collect()
    #print(gc.mem_free())
    sleep(60)

run()
