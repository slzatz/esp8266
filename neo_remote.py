'''
This uses the homemade Feather Wing doubler: one of the top boards is the
Feather Wing SSD1306 OLED and the other is a homemade board that has a
play/pause button and a potentiometer.
This micropython script displays songs that are being scrobbled to the mqtt broker
running in AWS EC2 or locally (most recently locally)
On Huzzah ESP8266 Feather, buttons A, B & C connect to 0, 16, 2 respectively
The buttons on OLED are also used:
    - Button A (GPIO 0): play wnyc since that is such a frequent thing that I want to do
    - Button B (GPIO 16): some boards this is redirected to another pin because 16 is not a normal
      pin but might work (needs a physical pull-up since there isn't a builtin pullup)
    - Button C (GPIO 2): plays any songs in the queue
Note that this script sends mqtt messages and a script on the raspberry pi named esp_check_mqtt.py,
which looks for the messages and then issues sonos commands

There is a separate button that is connected to GPIO 14 that is on the board that has the
volume potentiometer and that button play_pauses.

On some setups, I have rewired GPIO 16 on the OLED to GPIO 13, which is a normal pin
The script also pings the broker to keep it alive
'''

import gc
from time import sleep, time
import json
import network
from config import hosts, ssid, pw 
from ssd1306_min import SSD1306 as SSD
from umqtt_client import MQTTClient
from machine import Pin, I2C, ADC

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

host = hosts['other']

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)

d = SSD(i2c)
d.init_display()
d.draw_text(0, 0, "HELLO NEO")
d.display()

umc = MQTTClient(mqtt_id, host, 1883)

b = bytearray(1)
# mtpPublish is a class method that produces a bytes object that is used in
# the callback where we can't allocate any memory on the heap
rgb1 = umc.mtpPublish('neo', '{"rgb":1}')
rgb2 = umc.mtpPublish('neo', '{"rgb":2}')
rgb3 = umc.mtpPublish('neo', '{"rgb":3}')

#callbacks
# note that b[0] is set to 0 in the while loop
def send_rgb1(p):
  if b[0]:
    print("debounced", p, b[0])
    return
  b[0] = umc.sock.send(rgb1)
  print("change pin", p, b[0])

def send_rgb2(p):
  if b[0]:
    print("debounced", p, b[0])
    return
  b[0] = umc.sock.send(rgb2)
  print("change pin", p, b[0])

def send_rgb3(p):
  if b[0]:
    print("debounced", p, b[0])
    return
  b[0] = umc.sock.send(rgb3)
  print("change pin", p, b[0])

p0 = Pin(0, Pin.IN, Pin.PULL_UP) #button A on FeatherWing OLED
p2 = Pin(2, Pin.IN, Pin.PULL_UP)  #button C on FeatherWing OLED
p13 = Pin(13, Pin.IN, Pin.PULL_UP) #some boards redirected pin 16 to pin 13 on FeatherWing OLED
p14 = Pin(14, Pin.IN, Pin.PULL_UP) #button on homemade volume play/pause board
p0.irq(trigger=Pin.IRQ_RISING, handler=send_rgb1) 
p2.irq(trigger=Pin.IRQ_RISING, handler=send_rgb3)
p13.irq(trigger=Pin.IRQ_RISING, handler=send_rgb2)
p14.irq(trigger=Pin.IRQ_FALLING, handler=send_rgb2)

adc = ADC(0)

def run():
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
  sleep(2) 

  cur_time = time()
  bb = True
  level = 300

  while 1:
    new_level = 1000-adc.read() # since current wiring has clockwise decreasing voltage
    if abs(new_level-level) > 10:
      try:
        umc.publish('neo', json.dumps({"brightness":new_level/100}))
      except Exception as e:
        print(e)
        umc.sock.close()
        umc.connect()
      level = new_level
      print("new level =", level)

    z = umc.check_msg()
    if z:
      print(z)
      if isinstance(z, int):
        print("returned an integer")
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
      d.draw_text(0, 0, 'rgb: ' + str(zz.get('rgb', 0))) 

      brightness = str(zz.get('brightness', -1.0))
      d.draw_text(0, 12, 'brightness: ' + brightness)
      d.display()

    t = time()
    if t > cur_time + 30:
        umc.ping()
        cur_time = t
    gc.collect()
    #print(gc.mem_free())
    b[0] = 0 # for debouncing
    sleep(1)

#run()
