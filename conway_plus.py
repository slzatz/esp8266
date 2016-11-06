'''
This code implements Conways Game of Life using micropython on an ESP8266
It creates the color of a new life form based on the color of the three "parents"
Some code borrow from a video Lady Ada did
'''

from machine import Pin  #freq
import neopixel
import utime
import uos

# at one point thought I had to increase freq for pixels to always fire correctly
#freq(160000000)

PIXEL_WIDTH = const(8)
PIXEL_HEIGHT = const(8)
MAX_BRIGHT = const(10)

pixels = neopixel.NeoPixel(Pin(13, Pin.OUT), PIXEL_WIDTH*PIXEL_HEIGHT)

def conway_step():
  global board
  global color_board
  new_board = board[:]
  new_color_board = color_board[:]
  changed = False
  for x in range(PIXEL_HEIGHT):
    for y in range(PIXEL_WIDTH):
      num_neighbors = board[x-1][y-1] + board[x][y-1] + board[x+1][y-1] + board[x-1][y] \
                      + board[x+1][y] + board[x+1][y+1] + board[x][y+1] + board[x-1][y+1]

      if board[x][y] and not (2 <= num_neighbors <=3):
        new_board[x][y] = 0
        new_color_board[x][y] = (0,0,0) 
        changed = True
      elif not board[x][y] and num_neighbors == 3:
        new_board[x][y] = 1
        #color_board[x][y] = color() 

        # to add multiple same length tuples: tuple(map(sum, zip(a,b,...)))
        # note that only three of the below should be nonzero - (0,0,0,)
        color = tuple(map(sum, zip(color_board[x-1][y-1], color_board[x][y-1], color_board[x+1][y-1], color_board[x-1][y], 
                                                   color_board[x+1][y], color_board[x+1][y+1], color_board[x][y+1], color_board[x-1][y+1])))

        new_color_board[x][y] = (color[0]//3, color[1]//3, color[2]//3)
        print(new_color_board[x][y])
        changed = True
  
  board = new_board[:]
  color_board = new_color_board[:]
  return changed

def conway_rand():
  global board
  global color_board

  pixels.fill((0,0,0))
  pixels.write()
  utime.sleep(2)

  # note that the + 1 below means that the board[X][-1] pulls in zero from a position beyond the grid
  board = [[0 for j in range(PIXEL_WIDTH + 1)] for i in range(PIXEL_HEIGHT + 1)]
  color_board = [[(0,0,0) for j in range(PIXEL_WIDTH + 1)] for i in range(PIXEL_HEIGHT + 1)]
  for x in range(PIXEL_HEIGHT):
    for y in range(PIXEL_WIDTH):
      board[x][y] = uos.urandom(1)[0]//128
      if board[x][y]:
        color_board[x][y] = color()
      else:
        color_board[x][y] = (0,0,0)

  print("--------------------------------------------")
  for x in range(PIXEL_HEIGHT):
    print(board[x][0:PIXEL_WIDTH])
    for y in range(PIXEL_WIDTH):
        pixels[x * PIXEL_HEIGHT + y] = color_board[x][y]
  print("--------------------------------------------")

  pixels.write()
  utime.sleep(3)

def random():
  return MAX_BRIGHT*(uos.urandom(1)[0]//128)
  
def color():
  return (random(), random(), random())

conway_rand()

while True:
  if not conway_step():
    utime.sleep(5)
    conway_rand()

  print("--------------------------------------------")
  for x in range(PIXEL_HEIGHT):
    print(board[x][0:PIXEL_WIDTH])
    for y in range(PIXEL_WIDTH):
        pixels[x * PIXEL_HEIGHT + y] = color_board[x][y]
  print("--------------------------------------------")

  pixels.write()
  utime.sleep(0.1)

