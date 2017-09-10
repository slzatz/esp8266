'''
This script is designed to run on Loboris' fork of MicroPython running on an ESP32
Loboris has made a number of additions including things like hardware I2C, which this uses.
The ssd1306 driver is an adafruit driver written for hardware I2C.  On this date 9/9/2017, the
official MicroPython ssd1306 driver did not work but a forum mentioned the adafruit driver at
github.com/adafruit/micropython-adafruit-ssd1306
The basic setup here is to have an Adafruit Feather HUZZAH ESP8266 or ESP32 plus a Featherwing OLED SSD1306
This is a non-specific script that writes the MQTT message to the OLED display.
The MQTT broker is running on an EC2 instance. 
This takes advantage of a C implementation of MQTT that reuns in the background as a separate freeRTOS tas.
Note that multiple clients can be created.
The mqtt topic is in a separate file called topic 
'''

import network, utime
from machine import Pin, I2C, RTC
import json
from config import ssid, pw, mqtt_aws_host
from ssd1306_i2c import SSD1306_I2C as SSD #this is the adafruit driver to use until fixed

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

with open('topic', 'r') as f:
    topic = f.read().strip()

print("mqtt_id =", mqtt_id)
print("host =", mqtt_aws_host)
print("topic =", topic)

i2c = I2C(scl=Pin(22), sda=Pin(23)) #speed=100000 is the default

d = SSD(width=128, height=32, i2c=i2c, external_vcc=False)
d.init_display()
d.text("HELLO STEVE", 0, 0)
d.show()

#pin15 = Pin(15, Pin.OUT)
def conncb(task):
  print("[{}] Connected".format(task))

#def disconncb(task):
#  print("[{}] Disconnected".format(task))

def subscb(task):
  print("[{}] Subscribed".format(task))

#def pubcb(pub):
#  print("[{}] Published: {}".format(pub[0], pub[1]))

def datacb(msg):
  print("[{}] Data arrived - topic: {}, message:{}".format(msg[0], msg[1], msg[2]))
  try:
    zz = json.loads(msg[2])
  except:
    zz = {}
  msg = zz.get('message', '')
  t = zz.get('time', "{}".format(utime.strftime("%c", utime.localtime())))

  if msg == 'on':
    #pin15.value(1)  
    pass
  elif msg == 'off':
    #pin15.value(0)  
    pass
  else:
    pass

  d.fill(0)
  d.show()
  d.text(topic, 0, 0) 
  d.text(t, 0, 12) 
  d.text(msg, 0, 24) 
  d.show()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
  print('connecting to network...')
  wlan.connect(ssid, pw)
  while not wlan.isconnected():
    pass
print('network config:', wlan.ifconfig())     
utime.sleep(5)

rtc = RTC()
print("synchronize time with NTP server ...")
# limit the time waiting since sometimes never connects
rtc.ntp_sync(server="pool.ntp.org")
for n in range(10):
  if rtc.synced():
    break
  utime.sleep_ms(100)
else:
    print("Could not synchronize with ntp")
print("Time set to: {}".format(utime.strftime("%c", utime.localtime())))

mqttc = network.mqtt(mqtt_id, mqtt_aws_host)
utime.sleep(1)
mqttc.config(subscribed_cb=subscb, connected_cb=conncb, data_cb=datacb)
mqttc.subscribe(topic)

cur_time = utime.time()

while 1:
  t = utime.time()
  if t > cur_time + 600:
    print(utime.strftime("%c", utime.localtime()))
    cur_time = t
  utime.sleep(1)
