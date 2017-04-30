from bmp180 import BMP180
from machine import I2C, Pin
from time import sleep
from umqtt_client_official import MQTTClient as umc 
import json 
import network 
from config import mqtt_aws_host, ssid, pw 

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
bmp180 = BMP180(i2c)
bmp180.oversample_sett = 2
bmp180.baseline = 101325

c = umc("04112017a", mqtt_aws_host, 1883) 
c.connect() 

#def run():
#  wlan = network.WLAN(network.STA_IF)
#  wlan.active(True)
#  if not wlan.isconnected():
#    print('connecting to network...')
#    wlan.connect(ssid, pw)
#    while not wlan.isconnected():
#      pass
#  print('network config:', wlan.ifconfig())     

while 1:

  temp = round(32 + 1.8*bmp180.temperature, 1)
  print(temp)

  try:
    c.publish("esp_tft", json.dumps({"header":"Temperature", "text":["nyc apt: "+str(temp)], "pos":0, "dest":(1,1)}))
  except Exception as e:
    print(e)
    c.sock.close()
    c.connect()

  sleep(60)

