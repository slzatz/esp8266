'''
This script is for periodically sampling temperature and humidity from a bme280
sensor attached to an ESP32 and is designed to run on Loboris' fork of MicroPython
for the ESP32 located at https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo
Loboris has made a number of additions including, most importantly, the ability to
utilize the psRAM (4MB) that is included on the esp32 wrover chip. 
Loboris' port also includes hardware I2C, an FTP server and a telnet server.
This script is intended to run on the esp32 wrover dev kit which uses the ST7789V to drive a 240 x 320 LCD
The MQTT broker is running on my AWS EC2 instance. 
This takes advantage of a C implementation of MQTT that runs in the background as a separate freeRTOS task.
Note that multiple MQTT clients can be created.
'''

from machine import Pin, I2C, RTC, random
import network
import json
import utime
import display 
from bme280 import BME280
from config import mqtt_aws_host, font
from settings import ssid, pw, mqtt_id, pos, pub_topic, period, location, display_type

print("mqtt_id =", mqtt_id)
print("host =", mqtt_aws_host)
print("pub topic =", pub_topic)

sda = Pin(13, Pin.PULL_UP) #23 #sdi on the bme280
scl = Pin(12, Pin.PULL_UP) #22 #sck on the bme280
i2c = I2C(scl=scl, sda=sda)
bme = BME280(i2c=i2c, address=0x77)

tft = display.TFT()

if display_type == 'WROVER':
    # ST7789V used by v3 esp-wrover kit (I think default is 240 x 320)
    tft.init(tft.ST7789, rst_pin=18, backl_pin=5, miso=25, mosi=23, clk=19, cs=22, dc=21)
else:
    # ILI9341
    tft.init(tft.ILI9341, width=width, height=height, miso=19, mosi=18, clk=5, cs=15, dc=33, bgr=True)

font_num = getattr(tft, font)
tft.font(font_num)
tft.clear()
tft.text(10, 10, "Hello Steve", random(0xFFFFFF))

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
  print(temp)
  print(humidity)
  tft.clear()
  tft.text(10, 10, t, random(0xFFFFFF))
  tft.text(10, 30, "Temp: {:.2f}".format(temp), random(0xFFFFFF))
  tft.text(10, 50, "Hum: {:.0f}%".format(humidity), random(0xFFFFFF))
  
  mqttc.publish(pub_topic, json.dumps({"header":"340 CCR: {}".format(location), "text":["{}".format(t), "temperature: {:.1f}".format(temp), "humidity: {:.0f}%".format(humidity)], "pos":pos}))
  utime.sleep(period)
    

