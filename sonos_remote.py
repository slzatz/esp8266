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
Note that this script sends mqtt messages and a script on the raspberry pi named esp_check_mqtt.py
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
from umqtt_client_official import MQTTClient as umc
from machine import Pin, I2C, ADC

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

with open('location', 'r') as f:
    loc = f.read().strip()

host = hosts[loc]

print("version plays wnyc")
print("mqtt_id =", mqtt_id)
print("location =", loc)
print("host =", host)

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)

d = SSD(i2c)
d.init_display()
d.draw_text(0, 0, "HELLO STEVE")
d.display()

c = umc(mqtt_id, host, 1883)

def mtpPublish(topic, msg):
  mtopic = bytes([len(topic) >> 8, len(topic) & 255]) + topic.encode('utf-8')
  return  bytes([0b00110001, len(mtopic) + len(msg)]) + mtopic + msg.encode('utf-8')

play_wnyc_msg = mtpPublish('sonos/'+loc, '{"action":"play_wnyc"}')
play_queue_msg = mtpPublish('sonos/'+loc, '{"action":"play_queue"}')
play_pause_msg = mtpPublish('sonos/'+loc, '{"action":"play_pause"}')

b = bytearray(1)

#callbacks
# note that b[0] is set to 0 in the while loop
def play_wnyc(p):
  if b[0]:
    print("debounced", p, b[0])
    return
  b[0] = c.sock.send(play_wnyc_msg)
  print("change pin", p, b[0])

def play_queue(p):
  if b[0]:
    print("debounced", p, b[0])
    return
  b[0] = c.sock.send(play_queue_msg)
  print("change pin", p, b[0])

def play_pause(p):
  if b[0]:
    print("debounced", p, b[0])
    return
  b[0] = c.sock.send(play_pause_msg)
  print("change pin", p, b[0])

p0 = Pin(0, Pin.IN, Pin.PULL_UP) #button A on FeatherWing OLED
p2 = Pin(2, Pin.IN, Pin.PULL_UP)  #button C on FeatherWing OLED
p13 = Pin(13, Pin.IN, Pin.PULL_UP) #some boards redirected pin 16 to pin 13 on FeatherWing OLED
p14 = Pin(14, Pin.IN, Pin.PULL_UP) #button on homemade volume play/pause board
p0.irq(trigger=Pin.IRQ_RISING, handler=play_wnyc) 
p2.irq(trigger=Pin.IRQ_RISING, handler=play_queue)
p13.irq(trigger=Pin.IRQ_RISING, handler=play_pause)
p14.irq(trigger=Pin.IRQ_FALLING, handler=play_pause)

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

  def callback(topic,msg):
    zz = json.loads(msg.decode('utf-8'))
    d.clear()
    d.display()
    d.draw_text(0, 0, zz.get('artist', '')[:20]) 

    title = wrap(zz.get('title', ''), 20)
    d.draw_text(0, 12, title[0])
    if len(title) > 1:
      d.draw_text(0, 24, title[1])
    d.display()

  r = c.connect()
  print("connect:",r)

  c.set_callback(callback)
  r = c.subscribe('sonos/{}/current_track'.format(loc))
  print("subscribe:",r)

  sleep(5) 

  cur_time = time()
  bb = True
  level = 300

  while 1:
    new_level = 1000-adc.read() # since current wiring has clockwise decreasing voltage
    if abs(new_level-level) > 10:
      try:
        c.publish('sonos/'+loc, json.dumps({"action":"volume", "level":new_level}))
      except Exception as e:
        print(e)
        c.sock.close()
        c.connect()
      level = new_level
      print("new level =", level)

    c.check_msg()

    t = time()
    if t > cur_time + 30:
        c.ping()
        cur_time = t
    gc.collect()
    b[0] = 0 # for debouncing
    sleep(1)

run()
