'''
This script is designed to run on Loboris' fork of MicroPython running on an ESP32
Loboris has made a number of additions including things like hardware I2C, which this uses.
The ssd1306 driver is an adafruit driver written for hardware I2C.  On this date 9/9/2017, the
official MicroPython ssd1306 driver did not work but a forum mentioned the adafruit driver at
github.com/adafruit/micropython-adafruit-ssd1306
The basic setup here is to have an Adafruit Feather HUZZAH ESP8266 or ESP32 plus a Featherwing OLED SSD1306
This is a non-specific script that writes the MQTT message to the OLED display.
The MQTT broker is running on an EC2 instance. 
This takes advantage of a C implementation of MQTT that runs in the background as a separate freeRTOS tas.
Note that multiple clients can be created.
The mqtt topic is in a separate file called topic 
'''

import machine
import network
import json
from ssd1306 import SSD1306_I2C
import utime
from bme280 import BME280
from config import ssid, pw, mqtt_aws_host
from settings import mqtt_id, pos, pub_topic, period, location

print("mqtt_id =", mqtt_id)
print("host =", mqtt_aws_host)
print("pub topic =", pub_topic)

sda = machine.Pin(23)
scl = machine.Pin(22)
#i2c = machine.I2C(scl=scl, sda=sda, speed=400000)
i2c = machine.I2C(scl=scl, sda=sda)
bme = BME280(i2c=i2c, address=0x77)
ssd = SSD1306_I2C(128, 32, i2c)

ssd.fill(0)
ssd.text("Hello Steve", 0, 0)
ssd.show()

#mqtt callbacks ################################################################

def conncb(task):
  print("[{}] Connected".format(task))

def disconncb(task):
  print("[{}] Disconnected".format(task))

def subscb(task):
  print("[{}] Subscribed".format(task))

def pubcb(pub):
  print("[{}] Published: {}".format(pub[0], pub[1]))

#def datacb(msg):
#  print("[{}] Data arrived - topic: {}, message:{}".format(msg[0], msg[1], msg[2]))
#  try:
#    zz = json.loads(msg[2])
#  except:
#    zz = {}
#  msg = zz.get('message', '')
#  t = zz.get('time', "{}".format(utime.strftime("%c", utime.localtime())))
#
#  if msg == 'on':
#    pin15.value(1)
#  elif msg == 'off':
#    pin15.value(0)
#  else:
#    pass
#
#  d.fill(0)
#  d.show()
#  d.text(topic, 0, 0) 
#  d.text(t, 0, 12) 
#  d.text(msg, 0, 24) 
#  d.show()

#end mqtt callbacks ################################################################

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
  print('connecting to network...')
  wlan.connect(ssid, pw)
  while not wlan.isconnected():
    pass
print('network config:', wlan.ifconfig())     
utime.sleep(5)

rtc = machine.RTC()
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

mqttc = network.mqtt(mqtt_id, mqtt_aws_host, connected_cb=conncb, clientid=mqtt_id)
utime.sleep(1)
#mqttc.config(subscribed_cb=subscb, data_cb=datacb)
#mqttc.subscribe(topic)

cur_time = utime.time()

while 1:
  t = utime.strftime("%x %X", utime.localtime())
  z = bme.read_compensated_data()
  temp = 32 +9*z[0]/500
  humidity = z[2]/1024
  #print(temp)
  #print(humidity)
  ssd.fill(0)
  ssd.text(t, 0, 0)
  ssd.text("T: {:.2f}".format(temp), 0, 12)
  ssd.text("H: {:.0f}%".format(humidity), 0, 24)
  ssd.show()
  
  mqttc.publish(pub_topic, json.dumps({"header":"340 CCR: {}".format(location), "text":["{}".format(t), "temperature: {:.1f}".format(temp), "humidity: {:.0f}%".format(humidity)], "pos":pos}))
  utime.sleep(period)
    

