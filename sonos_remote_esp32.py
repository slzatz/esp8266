'''
Based on the @loboris ESP32 MicroPython port
Uses Adafruit Feather ESP32 and Adafruit Featherwing SSD1306 OLED
Uses the frozen ssd1306 module that @loboris port provides
play/pause button and a potentiometer.
Also displays track information that is being published by local raspi
sonos-companion script esp_check_mqtt.py to AWS EC2 mqtt broker
On Huzzah ESP8266 Feather, buttons A, B & C connect to 0, 16, 2 respectively
The buttons on OLED are also used:
    - Button A (GPIO 0): play wnyc since that is such a frequent thing that I want to do
    - Button B (GPIO 16): some boards this is redirected to another pin because 16 is not a normal
      pin but might work (needs a physical pull-up since there isn't a builtin pullup)
    - Button C (GPIO 2): plays any songs in the queue
Note that this script sends mqtt messages and a script on the raspberry pi named esp_check_mqtt.py
which looks for the messages and then issues sonos commands

There is a separate button that is connected to GPIO 14 that is on the board that has the
volume potentiometer and that button play_pauses.

Buttons and volume are publish to the topic: sonos/ct or sonos/nyc
The topic that is subscribed to for track info is sonos/{loc}/track
'''
import gc
import network
from time import sleep, sleep_ms, time, strftime, localtime
from machine import Pin, I2C, ADC, RTC
import json
from config import ssid, pw, mqtt_aws_host
from ssd1306 import SSD1306_I2C as SSD #the driver is included in the port's frozen modules

with open('mqtt_id', 'r') as f:
  mqtt_id = f.read().strip()

#with open('topic', 'r') as f:
#  topic = f.read().strip()

with open('location', 'r') as f:
  loc = f.read().strip()

topic = 'sonos/{}/track'.format(loc)

print("mqtt_id =", mqtt_id)
print("host =", mqtt_aws_host)
print("topic =", topic)

adc = ADC(Pin(36))

i2c = I2C(scl=Pin(22), sda=Pin(23)) #speed=100000 is the default

d = SSD(width=128, height=32, i2c=i2c, external_vcc=False)
d.init_display()
d.text("Hello Steve", 0, 0)
d.show()

print("version plays wnyc")
print("mqtt_id =", mqtt_id)
print("location =", loc)
print("mqtt_aws_host =", mqtt_aws_host)

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

# for some reason this callback seems to cause a Guru Meditation Error
#def pubcb(pub):
#  print("[{}] Published: {}".format(pub[0], pub[1]))

def datacb(msg):
  #zz = json.loads(msg.decode('utf-8'))
  print("[{}] Data arrived - topic: {}, message:{}".format(msg[0], msg[1], msg[2]))

  try:
    zz = json.loads(msg[2])
  except Exception as e:
    print(e)
    zz = {}

  d.fill(0)
  d.show()

  d.text(zz.get('artist', '')[:17], 0, 0) 

  title = wrap(zz.get('title', ''), 17)
  d.text(title[0], 0, 12)
  if len(title) > 1:
    d.text(title[1], 0, 24)

  d.show()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
  print('connecting to network...')
  wlan.connect(ssid, pw)
  while not wlan.isconnected():
    pass
print('network config:', wlan.ifconfig())     
sleep(5)

rtc = RTC()
print("synchronize time with NTP server ...")
# limit the time waiting since sometimes never connects
rtc.ntp_sync(server="pool.ntp.org")
for n in range(10):
  if rtc.synced():
    break
  sleep_ms(100)
else:
    print("Could not synchronize with ntp")
print("Time set to: {}".format(strftime("%c", localtime())))

mqttc = network.mqtt(mqtt_id, mqtt_aws_host, connected_cb=conncb, clientid=mqtt_id)
sleep(1)
# note got Guru Meditation Error with the published callback
#mqttc.config(subscribed_cb=subscb, published_cb=pubcb, data_cb=datacb)
mqttc.config(subscribed_cb=subscb, data_cb=datacb)
mqttc.subscribe(topic)

cur_time = time()
level = 300

while 1:
  t = time()
  if t > cur_time + 600:
    print(strftime("%c", localtime()))
    cur_time = t

  new_level = 1000-adc.read() # since current wiring has clockwise decreasing voltage
  if abs(new_level-level) > 10:

    try:
      mqttc.publish('sonos/'+loc, json.dumps({"action":"volume", "level":new_level}))
    except Exception as e:
      print(e)

    level = new_level
    print("new level =", level)

  gc.collect()
  sleep(1)
