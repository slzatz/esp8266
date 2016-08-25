'''
This micropython script is for use with the hacked FeatherWing doubler.  It displays songs that
are being scrobbled to the mqtt broker running in AWS EC2 or locally and also the top bottom (A)
increases the volume, the bottom button (C) decreases the volume and middle (B) play_pauses
The separate button on GPIO 14 also play_pauses.
The script also pings the broker to keep it alive
One board is the FeatherWing SSD1306 OLED and the other has a play/pause button and potentiometer
'''

import gc
from time import sleep, time
import json
import network
from config import hosts, ssid, pw 
from ssd1306_min import SSD1306 as SSD
from umqtt_client import MQTTClient as umc
from machine import Pin, I2C, ADC

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

with open('location', 'r') as f:
    loc = f.read().strip()

host = hosts[loc]

print("mqtt_id =", mqtt_id)
print("location =", loc)
print("host =", host)

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)

d = SSD(i2c)
d.init_display()
d.draw_text(0, 0, "HELLO STEVE")
d.display()

c = umc(mqtt_id, host, 1883)

b = bytearray(1)
# mtpPublish is a class method that produces a bytes object that is used in
# the callback where we can't allocate any memory on the heap
quieter = umc.mtpPublish('sonos/'+loc, '{"action":"quieter"}')
louder = umc.mtpPublish('sonos/'+loc, '{"action":"louder"}')
play_pause = umc.mtpPublish('sonos/'+loc, '{"action":"play_pause"}')

def callback_louder(p):
  if b[0]:
    print("debounced", p, b[0])
    return
  b[0] = c.sock.send(louder)
  print("change pin", p, b[0])
 
def callback_quieter(p):
  if b[0]:
    print("debounced", p, b[0])
    return
  b[0] = c.sock.send(quieter)
  print("change pin", p, b[0])

def callback_play_pause(p):
  if b[0]:
    print("debounced", p, b[0])
    return
  b[0] = c.sock.send(play_pause)
  print("change pin", p, b[0])

p0 = Pin(0, Pin.IN, Pin.PULL_UP)
p2 = Pin(2, Pin.IN, Pin.PULL_UP)
p13 = Pin(13, Pin.IN, Pin.PULL_UP)
p14 = Pin(14, Pin.IN, Pin.PULL_UP)
p0.irq(trigger=Pin.IRQ_RISING, handler=callback_louder)
p2.irq(trigger=Pin.IRQ_RISING, handler=callback_quieter)
p13.irq(trigger=Pin.IRQ_RISING, handler=callback_play_pause)
p14.irq(trigger=Pin.IRQ_FALLING, handler=callback_play_pause)

adc = ADC(0)

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

  c.connect()
  c.subscribe('sonos/{}/current_track'.format(loc))
  sleep(2) 

  cur_time = time()
  bb = True
  level = 300

  while 1:
    new_level = adc.read()
    if abs(new_level-level) > 20:
      try:
        c.publish('sonos/'+loc, json.dumps({"action":"volume", "level":new_level}))
      except Exception as e:
        print(e)
        c.sock.close()
        c.connect()
      level = new_level
      print(level)

    z = c.check_msg()
    if z:
      print(z)
      if isinstance(z, int):
        print("returned a integer")
        d.draw_text(123, 24, ' ')
        if bb:
          d.draw_text(123, 24, '|') 
        else:
          d.draw_text(123, 24, '-') 
        bb = not bb
        d.display()
        continue

      topic, msg = z
      zz = json.loads(msg.decode('utf-8'))
      print("assuming a tuple")
      d.clear()
      d.display()
      d.draw_text(0, 0, zz.get('artist', '')[:20]) 

      title = wrap(zz.get('title', ''), 20)
      d.draw_text(0, 12, title[0])
      if len(title) > 1:
        d.draw_text(0, 24, title[1])
      d.display()

    t = time()
    if t > cur_time + 30:
        c.ping()
        cur_time = t
    gc.collect()
    #print(gc.mem_free())
    b[0] = 0 # for debouncing
    sleep(1)

run()
