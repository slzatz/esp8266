from machine import Pin, freq
import neopixel
import utime
import uos

freq(160000000)

PIXEL_WIDTH = const(8)
PIXEL_HEIGHT = const(8)
MAX_BRIGHT = const(2)

pixels = neopixel.NeoPixel(Pin(13, Pin.OUT), PIXEL_WIDTH*PIXEL_HEIGHT)

def conway_step():
  global board
  global color_board
  new_board = board[:]
  changed = False
  for x in range(PIXEL_HEIGHT):
    for y in range(PIXEL_WIDTH):
      num_neighbors = board[x-1][y-1] + board[x][y-1] + board[x+1][y-1] + board[x-1][y] \
                      + board[x+1][y] + board[x+1][y+1] + board[x][y+1] + board[x-1][y+1]

      if board[x][y] and not (2 <= num_neighbors <=3):
        new_board[x][y] = 0
        color_board[x][y] = (0,0,0) 
        changed = True
      elif not board[x][y] and num_neighbors == 3:
        new_board[x][y] = 1
        color_board[x][y] = color() 
        changed = True
  
  board = new_board[:]
  return changed

def conway_rand():
  global board
  global color_board

  pixels.fill((0,0,0))
  pixels.write()
  utime.sleep(2)

  # note that the + 1 below means that the board[X][-1] pulls in zero from a position beyond the grid
  board = [[0 for j in range(PIXEL_WIDTH + 1)] for i in range(PIXEL_HEIGHT + 1)]
  color_board = [[(0,0,0) for j in range(PIXEL_WIDTH)] for i in range(PIXEL_HEIGHT)]
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
  return (random(), random(), 2)

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

