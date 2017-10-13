'''
This script runs on @loboris fork of MicroPython for the ESP32
The fork runs MicroPython as an RTOS process and wraps interesting display and mqtt modules.
This script displays mqtt messages to the TFT Featherwing using @loboris display module
This takes advantage of a C implementation of MQTT that reuns in the background as a separate freeRTOS task.
The MQTT broker is running on an EC2 instance. 
Note that multiple mqtt clients can be created.
The mqtt topic is in a separate file called topic 
MQTT messages are json in the form of:
{"text":["The rain in spain {RED} falls mainly on the {GREEN} plain", "Now is the time for all good {BLUE}men {WHITE}to come to the aid of their country"]}
Note you have to explicity unsubscribe - it retains subscriptions through power down somehow
'''

import network, utime
import display
from machine import Pin, I2C, RTC, random
import json
import ure as re
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
utime.sleep(1)
tft.clear()
tft.text(10, 10, "Hello Steve", random(0xFFFFFF))

#pin15 = Pin(15, Pin.OUT) #will need to find another pin since this is cs pin

regex= re.compile('{(.*?)}')
#s = "jkdsfl{RED}fkjsdflds{GREEN}jlklfjsl{PINK}lkdsjflkdsjfl"
def display_text(s, n, tag=None, h=0):

  # the following two things can only happen the first time a string is processed
  if s and s[0] != '{': # deal with strings with no pos 0 tag (they may be tags elsewhere in the string)
    s = '{WHITE}' + s
  if tag is None: 
    z = regex.search(s)
    tag = z.group(0)
  
  col = tag[1:-1].upper()
  col = col if col else 'WHITE' # {} was used for white, which produces col = '', so need to do this check
  if col == '':
    col = 'WHITE'
  if col == 'GREY':
    col = 'LIGHTGREY'
  s = s[len(tag):]
  z = regex.search(s)
  if z is None:
    print("No more tags")
    print("col=",col)
    print("text=",s)
    tft.text(h, n, s, getattr(tft, col))
    return
  tag2 = z.group(0)
  pos = s.find(tag2) # will be non-zero
  print("col=",col)
  print("text=",s[:pos])
  tft.text(h, n, s[:pos], getattr(tft, col))
  h+=tft.textWidth(s[:pos])
  return display_text(s[pos:], n, tag2, h)

def wrap(text,lim):
  # a little tricky to deal with {RED} since can be at beginning or end of a regular word
  # z = regex.search(word)
  #if z: inc = len(word) - len(z.group(0)) else len(word)
  lines = []
  pos = 0 
  line = []
  for word in text.split():
    z = regex.search(word)
    ln = len(word)-len(z.group(0)) if z else len(word)
    if pos+ln < lim+1:
      line.append(word)
      pos+= ln+1 
    else:
      lines.append(' '.join(line))
      line = [word] 
      pos = ln

  lines.append(' '.join(line))
  return lines

line_height = tft.fontSize()[1]
MAX_HEIGHT = 320
max_chars_line = 30 #240/tft.fontSize()[0] # note that there is hidden markup that are treated like words

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
  bullets = zz.get('bullets', True)

  tft.clear()

  n = line_height #20
  for item in zz.get('text',['No text']): 
    if not item.strip():
      n+=line_height
      continue
    #font.set_bold(False)
    n+=4 if bullets else 0 # makes multi-line bullets more separated from prev and next bullet

    if n+line_height > MAX_HEIGHT:
      break

    if item[0] == '#':
      item=item[1:]
      #font.set_bold(True)

    if item[0] == '*': 
      item=item[1:]
      #foo.blit(star, (2,n+7))
    elif bullets:
      #foo.blit(bullet_surface, (7,n+13)) #(4,n+13)
      pass
    # neither a star in front of item or a bullet
    else:
      #max_chars_line+= 1 
      pass

    print("item=",item)
    lines = wrap(item, max_chars_line) # if line is just whitespace it returns []
    print("lines=",lines)

    for line in lines:
      display_text(line, n)
      n+=line_height
#############################

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
for k in range(10):
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
