'''
This script runs on @loboris fork of MicroPython for the ESP32
The fork runs MicroPython as an RTOS process and wraps interesting display and mqtt modules.
This script displays mqtt messages to the TFT Featherwing using @loboris display module
This takes advantage of a C implementation of MQTT that reuns in the background as a separate freeRTOS task.
The MQTT broker is running on an EC2 instance. 
Note that multiple mqtt clients can be created.
The mqtt topic is in a separate file called topic 
'''

import network, utime
import display
from machine import Pin, I2C, RTC, random
import json
from config import ssid, pw, mqtt_aws_host

with open('mqtt_id', 'r') as f:
    mqtt_id = f.read().strip()

with open('topic', 'r') as f:
    topic = f.read().strip()

print("mqtt_id =", mqtt_id)
print("host =", mqtt_aws_host)
print("topic =", topic)

tft = display.TFT()
tft.init(tft.ILI9341, width=240, height=320, miso=19, mosi=18, clk=5, cs=15, dc=33, bgr=True)
tft.text(10, 10, "Hello Steve", random(0xFFFFFF))

#pin15 = Pin(15, Pin.OUT) #will need to find another pin since this is cs pin

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
  #msg = zz.get('message', '')
  t = "{}".format(utime.strftime("%c", utime.localtime()))

  tft.clear()
  tft.text(0, 0, msg[1], random(0xFFFFFF))
  tft.text(0, 12, t, random(0xFFFFFF))
  #tft.text(0, 24, msg, 0x00FF00))

  y = 24
  for line in zz.get('text', ["No text"]):
    lines = wrap(line, 26)
    for l in lines:
      y+=15 
      tft.text(0, y, l, 0x00FF00))

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
