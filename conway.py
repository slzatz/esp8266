from machine import Pin
import neopixel
import utime
import uos

PIXEL_WIDTH = const(8)
PIXEL_HEIGHT = const(8)
MAX_BRIGHT = const(2)

# note that the + 1 below means that the board[X][-1] pulls in zero from a position beyond the grid
board = [[0 for j in range(PIXEL_WIDTH + 1)] for i in range(PIXEL_HEIGHT + 1)]
new_board = [[0 for j in range(PIXEL_WIDTH + 1)] for i in range(PIXEL_HEIGHT + 1)]

pixels = neopixel.NeoPixel(Pin(13, Pin.OUT), PIXEL_WIDTH*PIXEL_HEIGHT)

def conway_step():
  global board
  global new_board
  changed = False
  for x in range(PIXEL_HEIGHT):
    for y in range(PIXEL_WIDTH):
      num_neighbors = board[x-1][y-1] + board[x][y-1] + board[x+1][y-1] + board[x-1][y] \
                      + board[x+1][y] + board[x+1][y+1] + board[x][y+1] + board[x-1][y+1]

      if board[x][y] and not (2 <= num_neighbors <=3):
        new_board[x][y] = 0
        changed = True
      elif not board[x][y] and num_neighbors == 3:
        new_board[x][y] = 1
        changed = True
  
  board = new_board[:]
  return changed

def conway_rand():
  for x in range(PIXEL_HEIGHT):
    for y in range(PIXEL_WIDTH):
      board[x][y] = uos.urandom(1)[0]//128

pixels.fill((0,0,0))
pixels.write()

def random():
  return MAX_BRIGHT*(uos.urandom(1)[0]//128)
  
def color():
  return (random(), random(), 2)

while True:
  if not conway_step():
    utime.sleep(10)
    conway_rand()

  print("--------------------------------------------")
  for x in range(PIXEL_HEIGHT):
    print(board[x][0:PIXEL_WIDTH])
    for y in range(PIXEL_WIDTH):
      if board[x][y]:
        pixels[x * PIXEL_HEIGHT + y] = color()
      else:
        pixels[x * PIXEL_HEIGHT + y] = (0,0,0)

  print("--------------------------------------------")
  pixels.write()
  utime.sleep(0.1)

