'''
This relies on font2.py, rgb_text2.py and ili9341_text2.py to display info on the TFT FeatherWing
Uses umqtt_client_official.py
The mqtt topic is determined by the config file but previously was hardcoded as 'esp_tft'
The format of the mqtt messages is:
{"header":"Weather", "text":"Some text goes here", "pos":2}
my thought is to display all messages at the top of the display so the pos(ition) doesn't matter
Note you must transfer config, mqtt_id and location to the esp8266 (e.g., using ampy)
'''

from time import sleep, time
import json
import network
from config import ssid, pw, mqtt_aws_host
from ssd1306_min import SSD1306 as SSD
from umqtt_client_official import MQTTClient as umc
from machine import Pin, I2C

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

with open('topic', 'r') as f:
    topic = f.read().strip()

print("mqtt_id =", mqtt_id)
print("host =", mqtt_aws_host)
print("topic =", topic)

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)

d = SSD(i2c)
d.init_display()
d.draw_text(0, 0, "HELLO STEVE")
d.display()

led = Pin(15, Pin.OUT)

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
    msg = zz.get('message', '')
    bv = zz.get('batteryVoltage', '')
    sn = zz.get('serialNumber', '')
    ct = zz.get('clickType', '')

#    if msg == 'on':
#      led.value(1)  
#    elif msg == 'off':
#      led.value(0)  
#    else:
#      pass

    if ct == 'SINGLE':
      led.value(1)
    elif ct == 'DOUBLE':
      led.value(0)
    else:
      pass

    d.clear()
    d.display()
    d.draw_text(0, 0, "Message: "+msg) 
    d.draw_text(0, 12, "Battery Voltage: "+bv) 
    d.draw_text(0, 24, "Click Type: "+ct) 
    d.display()

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
