'''
The basic setup here is to have an Adafruit Feather HUZZAH ESP8266 plus a Featherwing OLED SSD1306
This is a non-specific script that writes the MQTT message to the OLED display.
The MQTT broker is running on an EC2 instance. 
The esp8266+OLED that subscribes to the topic can be used to turn  on and off a Data Loggers IoT Control Relay.
Uses umqtt_client_official.py - my renamed version of the official simple mqtt script
The mqtt topic is in a separate file called topic 
Pressing the AWS IoT switch triggers an AWS Lambda function that sends the MQTT message to the EC2 MQTT broker
with topic "switch" and the jsonified info that the AWS IoT Button generates, which is:

{"batteryVoltage": "1705mV", "serialNumber": "G030MD0371271BB1", "clickType": "SINGLE"}

Note the clickType can be SINGLE, DOUBLE or LONG.

I am using SINGLE to turn the relay swith on and DOUBLE to shut it off.
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

pin15 = Pin(15, Pin.OUT)

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
    t = zz.get('time', '')

    if msg == 'on':
      pin15.value(1)  
    elif msg == 'off':
      pin15.value(0)  
    else:
      pass

    d.clear()
    d.display()
    d.draw_text(0, 0, "topic: "+topic.decode('utf-8')) 
    d.draw_text(0, 12, "time: "+t) 
    d.draw_text(0, 24, "message: "+msg) 
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
