'''
This relies on font2.py, rgb_text2.py and ili9341_text2.py to display info on the TFT FeatherWing
Uses umqtt_client_official.py
The mqtt topic is:  'esp_tft'
The format of the mqtt messages is:
{"header":"Weather", "text":"Some text goes here", "pos":2}
The position is whether it is the first, second, third etc item on the screen going top to bottom
The script running on raspberry pis that generates the mqtt messages is ...
Note you must transfer config, mqtt_id and location to the esp8266 (e.g., using ampy)
'''

import machine
import gc
from time import sleep, time
import json
import network
from config import ssid, pw
from config import mqtt_aws_host as host
import ili9341_text2 as ili
from umqtt_client_official import MQTTClient as umc

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

print("mqtt_id =", mqtt_id)
print("host =", host)

spi = machine.SPI(1, baudrate=32000000)
d = ili.ILI9341(spi, cs=machine.Pin(0), dc=machine.Pin(15))

d.fill(0)
d.draw_text(0, 0, "Hello Steve", ili.color565(255,255,255))

c = umc(mqtt_id, host, 1883)

def wrap(text,lim):
  lines = []
  pos = 0 
  line = []
  for word in text.split():
    if pos + len(word) < lim + 1:
      line.append(word)
      pos+= len(word) + 1 
    else:
      lines.append(' '.join(line))
      line = [word] 
      pos = len(word)

  lines.append(' '.join(line))
  return lines

def run():
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  if not wlan.isconnected():
    print('connecting to network...')
    wlan.connect(ssid, pw)
    while not wlan.isconnected():
      pass
  print('network config:', wlan.ifconfig())     

  # weather can be so long not much room for anything else
  #positions = [0, 260, 320, 320, 320] 
  positions = [0, 0, 0, 0, 0] 

  def callback(topic,msg):
    zz = json.loads(msg.decode('utf-8'))
    pos = zz.get('pos', 0)
    y = positions[pos]
    if y > 305: 
      return    
    # blank out section of display where you are writing the text;draw_text signature is (self,x,y,width,height,color)
    #d.fill_rectangle(0, y, 240, positions[pos+1], 0)
    d.fill_rectangle(0, y, 240, 320, 0) # idea is to always erase from first line of info ast pos 0,1,2 etc. to the end of the screen - does require writing in order of position
    d.draw_text(0, y, zz.get('header', "No header"), ili.color565(0,255,0))

    for line in zz.get('text', ["No text"]):
      lines = wrap(line, 26)
      for line in lines:
        y+=15 
        d.draw_text(0, y, line, ili.color565(255,255,255))

    positions[pos+1] = y+15 if y < 305 else 320 

  r = c.connect()
  print("connect:",r)

  c.set_callback(callback)
  r = c.subscribe('esp_tft')
  print("subscribe:",r)

  sleep(5) 

  cur_time = time()

  while 1:

    c.check_msg()
    
    t = time()
    if t > cur_time + 30:
        c.ping()
        cur_time = t
    gc.collect()
    sleep(1)

run()
