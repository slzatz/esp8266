'''
This script runs on @loboris port of MicroPython for the ESP32
The port runs MicroPython as an RTOS process and wraps useful modules like display and mqtt.
This script displays mqtt messages to the TFT Featherwing or wrover-kit TFT using @loboris display module
This takes advantage of a C implementation of MQTT that reuns in the background as a separate freeRTOS task.
The MQTT broker is running on an AWS EC2 instance. 
Note that multiple mqtt clients can be created.
MQTT messages are json in the form of:
{"text":["The rain in spain {RED} falls mainly on the {GREEN} plain", "Now is the time for all good {BLUE}men {WHITE}to come to the aid of their country"]}
Note you have to explicity unsubscribe - it retains subscriptions through power down somehow
'''

import network
import utime
import gc
import display
from machine import Pin, I2C, RTC, random
import json
import ure as re
from config import ssid, pw, mqtt_aws_host
from settings import width, height, font, display_type, mqtt_id, sub_topic

print("mqtt_id =", mqtt_id)
print("host =", mqtt_aws_host)
print("subscription topic =", sub_topic)

tft = display.TFT()

if display_type == 'WROVER':
    # ST7789V used by v3 esp-wrover kit (I think default is 240 x 320)
    tft.init(tft.ST7789, rst_pin=18, backl_pin=5, miso=25, mosi=23, clk=19, cs=22, dc=21)
else:
    # ILI9341
    tft.init(tft.ILI9341, width=width, height=height, miso=19, mosi=18, clk=5, cs=15, dc=33, bgr=True)

font_num = getattr(tft, font)
tft.font(font_num)
#utime.sleep(1)
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
  lines = []
  pos = 0 
  line = []
  last_tag = None
  for word in text.split():
    ln = len(word)
    z = regex.search(word)
    if z:
      last_tag = z.group(0)
      ln-= len(last_tag)
    if pos+ln < lim+1:
      line.append(word)
      pos+= ln+1 
    else:
      lines.append(' '.join(line))
      if last_tag and word[0]!='{':
        line = [last_tag+word]
      else:
        line=[word]
      pos = ln

  lines.append(' '.join(line))
  return lines

line_height = tft.fontSize()[1]
# note for below -- average width seems to be about 1/2 of font size
max_chars_line = int(1.8*width/tft.fontSize()[0]) # 30; note that there is hidden markup that are treated like words

def conncb(task):
  print("[{}] Connected".format(task))

def disconncb(task):
  print("[{}] Disconnected".format(task))

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

  #n = line_height #20
  n = 0
  for item in zz.get('text',['No text']): 
    if not item.strip():
      #n+=line_height
      continue
    #font.set_bold(False)
    n+=4 if bullets else 2 # makes multi-line bullets more separated from prev and next bullet

    if n+line_height > height:
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
      # a line could be blank and right now display_text doesn't like that
      if line.strip():
        display_text(line, n)
        n+=line_height

  if zz.get('header')=='Weather':
    tft.circle(120, 150, 30, tft.YELLOW, tft.YELLOW)

  gc.collect()
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

mqttc = network.mqtt(mqtt_id, mqtt_aws_host, connected_cb=conncb, clientid=mqtt_id)
utime.sleep(1)
mqttc.config(subscribed_cb=subscb, disconnected_cb=disconncb, data_cb=datacb)
mqttc.subscribe(sub_topic)

cur_time = utime.time()

while 1:
  t = utime.time()
  if t > cur_time + 600:
    print(utime.strftime("%X", utime.localtime()))
    cur_time = t
  utime.sleep(1)
