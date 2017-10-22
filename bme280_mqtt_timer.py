'''
Based on driver at https://github.com/catdog2/mpy_bme280_esp8266
Created on 4-15-2017
'''
from bme280 import BME280
from machine import I2C, Pin, Timer
from time import sleep
from umqtt_client_official import MQTTClient as umc 
import json 
from config import mqtt_aws_host, pos

i2c = I2C(scl=Pin(5), sda=Pin(4))
bme = BME280(i2c=i2c, address=0x77) #0x77

flag = bytearray(1)
flag[0] = 0

sleep(20)

c = umc("10222017z", mqtt_aws_host, 1883) 
c.connect() 

def callback(t):
  flag[0] = 1

tim = Timer(-1)
tim.init(period=150000, mode=Timer.PERIODIC, callback=callback)

while 1:

  if flag[0]:
    z = bme.read_compensated_data()
    temp = 32 + 9*z[0]/500
    humidity = z[2]/1024

    try:
      c.publish("esp_tft", json.dumps({"header":"CT Temp/Humidity", "text":["temperature: {:.1f}".format(temp), "humidity: {:.0f}%".format(humidity)], "pos":pos}))
    except Exception as e:
      print(e)
      c.sock.close()
      c.connect()

    flag[0] = 0

  sleep(1)

