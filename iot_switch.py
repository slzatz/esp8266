'''
This relies on font2.py, rgb_text2.py and ili9341_text2.py to display info on the TFT FeatherWing
Uses umqtt_client_official.py
The mqtt topic is determined by the config file but previously was hardcoded as 'esp_tft'
The format of the mqtt messages is:
{"header":"Weather", "text":"Some text goes here", "pos":2}
my thought is to display all messages at the top of the display so the pos(ition) doesn't matter
Note you must transfer config, mqtt_id and location to the esp8266 (e.g., using ampy)
'''

import machine
from time import sleep, time
import json
import network
from config import ssid, pw, topic, mqtt_aws_host
import ili9341_text2 as ili
from umqtt_client_official import MQTTClient as umc

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

print("mqtt_id =", mqtt_id)
print("host =", mqtt_aws_host)

spi = machine.SPI(1, baudrate=32000000)
d = ili.ILI9341(spi, cs=machine.Pin(0), dc=machine.Pin(15))

d.fill(0)
d.draw_text(0, 0, "Hello Steve", ili.color565(255,255,255))

c = umc(mqtt_id, mqtt_aws_host, 1883)

def run():
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  if not wlan.isconnected():
    print('connecting to network...')
    wlan.connect(ssid, pw)
    while not wlan.isconnected():
      pass
  print('network config:', wlan.ifconfig())     

  def callback(topic, msg):
    zz = json.loads(msg.decode('utf-8'))
    msg = zz.get('msg', 'No message')
    d.fill_rectangle(0, 0, 240, 50, 0) # erase before writing new info
    d.draw_text(0, 0, "message: "+msg, ili.color565(0,255,0))

    if msg == 'on':
      #pin goes high
      pass
    elif msg == 'off':
      #pin goes low
      pass
    else:
      pass

  r = c.connect()
  print("connect:",r)

  c.set_callback(callback)
  r = c.subscribe(topic)
  print("subscribe:",r)

  sleep(5) 

  cur_time = time()

  while 1:

    c.check_msg()
    
    t = time()
    if t > cur_time + 30:
        c.ping()
        cur_time = t
    sleep(1)

run()
