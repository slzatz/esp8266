# The MIT License (MIT)
# 
# Based on Kenneth Henderick's Micropython drivers: https://github.com/khenderick/micropython-drivers
# and Vladimir Iakovlev's addition of font handling:  https://github.com/nvbn/micropython-drivers/tree/master/ssd1306
# Copyright (c) 2014 Kenneth Henderick
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#from machine import Pin, I2C
import font

# Constants
DISPLAYOFF          = const(0xAE)
SETCONTRAST         = const(0x81)
DISPLAYALLON_RESUME = const(0xA4)
NORMALDISPLAY       = const(0xA6)
INVERTDISPLAY       = const(0xA7)
DISPLAYON           = const(0xAF)
SETDISPLAYOFFSET    = const(0xD3)
SETCOMPINS          = const(0xDA)
SETVCOMDETECT       = const(0xDB)
SETDISPLAYCLOCKDIV  = const(0xD5)
SETPRECHARGE        = const(0xD9)
SETMULTIPLEX        = const(0xA8)
SETSTARTLINE        = const(0x40)
MEMORYMODE          = const(0x20)
COLUMNADDR          = const(0x21)
PAGEADDR            = const(0x22)
COMSCANDEC          = const(0xC8)
SEGREMAP            = const(0xA0)
CHARGEPUMP          = const(0x8D)

class SSD1306:

  def __init__(self, i2c):
    # assumes height=32, pages=4, columns=128, internal vcc

    self.cbuffer = bytearray(2)
    self.cbuffer[0] = 0x80

    #self.i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000) 
    self.i2c = i2c

  def clear(self):
    self.buffer = bytearray(513)
    self.buffer[0] = 0x40

  def write_command(self, command_byte):
    self.cbuffer[1] = command_byte
    self.i2c.writeto(0x3c, self.cbuffer)

  def invert_display(self, invert):
    self.write_command(INVERTDISPLAY if invert else NORMALDISPLAY)

  def display(self):
    self.write_command(COLUMNADDR)
    self.write_command(0)
    self.write_command(127) #(self.columns - 1)
    self.write_command(PAGEADDR)
    self.write_command(0)
    self.write_command(3) #(self.pages - 1)
    self.i2c.writeto(0x3c, self.buffer)

  def set_pixel(self, x, y, state):
    # each byte of buffer covers 8 pixels and index gets you the position in the buffer
    index = x + (int(y / 8) * 128)
    if state:
      self.buffer[1 + index] |= (1 << (y & 7))
    else:
      self.buffer[1 + index] &= ~(1 << (y & 7))

  def init_display(self):
    data = [DISPLAYOFF,
            SETDISPLAYCLOCKDIV, 0x80,
            SETMULTIPLEX, 0x1f,
            SETDISPLAYOFFSET, 0x00,
            SETSTARTLINE | 0x00,
            CHARGEPUMP, 0x14,
            MEMORYMODE, 0x00,
            SEGREMAP | 0x10,
            COMSCANDEC,
            SETCOMPINS, 0x02,
            SETCONTRAST, 0xff,
            SETPRECHARGE, 0xf1,
            SETVCOMDETECT, 0x40,
            DISPLAYALLON_RESUME,
            NORMALDISPLAY,
            DISPLAYON]
    for item in data:
      self.write_command(item)
    self.clear()
    self.display()

  def poweron(self):
    pass

  def poweroff(self):
    self.write_command(DISPLAYOFF)

  def contrast(self, contrast):
    self.write_command(SETCONTRAST)
    self.write_command(contrast)

  def draw_text(self, x, y, string): #, size=1, space=1):
    def pixel_x(char_number, char_column):
      char_offset = x + char_number * font.cols + char_number
      pixel_offset = char_offset + char_column + 1
      return 128 - pixel_offset

    def pixel_y(char_row):
      char_offset = y + char_row 
      return char_offset 

    def pixel_mask(char, char_column, char_row):
      # To save space, eliminated first 32 non-printing chars
      char_index_offset = (ord(char)-32) * font.cols
      return font.bytes_[char_index_offset + char_column] >> char_row & 0x1

    pixels = (
             (pixel_x(char_number, char_column),
              pixel_y(char_row),
              pixel_mask(char, char_column, char_row))
              for char_number, char in enumerate(string)
              for char_column in range(font.cols)
              for char_row in range(font.rows)
              )

    for pixel in pixels:
      self.set_pixel(*pixel)
