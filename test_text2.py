'''
Can either be used by ampy or placed on esp8266 to test writing to the ili9341 with a larger font:
font2.py.  Also uses ili9341_text2.py and rgb_text2.py
'''

import machine
import ili9341_text2 as ili

spi = machine.SPI(1, baudrate=32000000)

display = ili.ILI9341(spi, cs=machine.Pin(0), dc=machine.Pin(15))
color = ((255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(255,0,0),(0,255,0))
display.fill(0)
for x,y in enumerate(range(0,310,20)):
    display.draw_text(10,y,"Micropython Rocks "+str(y),ili.color565(*color[x]))

