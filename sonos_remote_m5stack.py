'''
Based on the @loboris ESP32 MicroPython port
Uses the m5stack dev board with wrover with 4mb psram
left button lowers volume, right raises, middle is play_pause
Also displays track information that is being published by local raspi
sonos-companion script esp_check_mqtt.py to AWS EC2 mqtt broker

Buttons and volume are publish to the topic: sonos/ct or sonos/nyc
The topic that is subscribed to for track info is sonos/{loc}/track
'''
#import gc # not sure if needed
import network
from time import sleep, sleep_ms, strftime, localtime #time
from machine import RTC #Pin, I2C
import json
from config import mqtt_aws_host
from settings import ssid, pw, mqtt_id, location as loc
import m5stack # from tuupola @ https://github.com/tuupola/micropython-m5stack

topic = 'sonos/{}/track'.format(loc)

print("mqtt_id =", mqtt_id)
print("host =", mqtt_aws_host)
print("topic =", topic)

#i2c = I2C(scl=Pin(22), sda=Pin(23)) #speed=100000 is the default

tft = m5stack.Display()
tft.font(tft.FONT_DejaVu18, fixedwidth=False)
tft.clear()
tft.text(tft.CENTER, 20, "Hello Steve \n")

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

  tft.clear()
  ##################################################################
  artist = zz.get('artist', '')
  if artist:
    try:
      tft.image(0,0,'/sd/{}.jpg'.format(artist.lower()))
    except:
      pass
  ##################################################################
  #tft.text(5, 5, zz.get('artist', '')+"\n") 
  tft.text(5, 5, artist+"\n") 

  title = wrap(zz.get('title', ''), 28) # 28 seems right for DejaVu18
  for line in title:
    tft.text(5, tft.LASTY, line+"\n")

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

#cur_time = time()
level = 300
# increase the volume
def button_hander_a(pin, pressed):
  if pressed:
    try:
      mqttc.publish('sonos/'+loc, json.dumps({"action":"quieter"}))
    except Exception as e:
      print(e)
    m5stack.tone(1800, duration=10, volume=1)

# play/pause
def button_hander_b(pin, pressed):
  if pressed:
    try:
      mqttc.publish('sonos/'+loc, json.dumps({"action":"play_pause"}))
    except Exception as e:
      print(e)
    m5stack.tone(1800, duration=10, volume=1)

# increase the volume
def button_hander_c(pin, pressed):
  if pressed:
    try:
      mqttc.publish('sonos/'+loc, json.dumps({"action":"louder"}))
    except Exception as e:
      print(e)
    m5stack.tone(1800, duration=10, volume=1)

a = m5stack.ButtonA(callback=button_hander_a)
b = m5stack.ButtonB(callback=button_hander_b)
c = m5stack.ButtonC(callback=button_hander_c)

while 1:
  #t = time()
  #if t > cur_time + 600:
   # print(strftime("%c", localtime()))
   # cur_time = t
  #gc.collect()
  sleep(.5)
