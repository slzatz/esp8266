'''
This script is for periodically sampling temperature and humidity from a bme280
sensor attached to an ESP32 and is designed to run on Loboris' port of MicroPython
for the ESP32 located at https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo
Loboris has made a number of additions including, most importantly, the ability to
utilize the psRAM (4MB) that is included on the esp32 wrover chip. 
Loboris' port also includes hardware I2C, an FTP server and a telnet server.
This script is intended to run on the esp32 wrover tiny:
https://www.tindie.com/products/kilobyte/tiny-esp32-wrover-psram-board/
The MQTT broker is running on my AWS EC2 instance. 
This takes advantage of a C implementation of MQTT that runs in the background as a separate freeRTOS task.
Note that multiple MQTT clients can be created.
'''

from machine import Pin, I2C
import network
import json
import utime
from bme280 import BME280
from config import mqtt_aws_host
from settings import ssid, pw, mqtt_id, pos, pub_topic, period, location

print("mqtt_id =", mqtt_id)
print("host =", mqtt_aws_host)
print("pub topic =", pub_topic)

sda = Pin(13, Pin.PULL_UP) #23 #sdi on the bme280
scl = Pin(12, Pin.PULL_UP) #22 #sck on the bme280
i2c = I2C(scl=scl, sda=sda)
bme = BME280(i2c=i2c, address=0x77)

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
  #pass

#end mqtt callbacks ################################################################

mqttc = network.mqtt(mqtt_id, "mqtt://"+mqtt_aws_host, connected_cb=conncb, clientid=mqtt_id)
mqttc.start()
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
  
  mqttc.publish(pub_topic, json.dumps({"header":"340 CCR: {}".format(location),
                                       "text":["{}".format(t), "temperature: {:.1f}".format(temp),
                                               "humidity: {:.0f}%".format(humidity)],
                                       "pos":pos}))
  utime.sleep(period)
    

