import pygame as pg
from collections import deque
import pytmx
# define some colors (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGREY = (40, 40, 40)
LIGHTGREY = (100, 100, 100)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# game settings
WIDTH = 1024   # 16 * 64 or 32 * 32 or 64 * 16
HEIGHT = 768  # 16 * 48 or 32 * 24 or 64 * 12
FPS = 60
TITLE = "quantum freeze block"
BGCOLOR = DARKGREY

TILESIZE = 64
GRIDWIDTH = WIDTH / TILESIZE
GRIDHEIGHT = HEIGHT / TILESIZE

class Circuit(object):

    def __init__(self):
        self.qubit_operation=[0,0,0] # used to build up the circuit


class TiledMap:
    def __init__(self, filename):
        tm = pytmx.load_pygame(filename, pixelalpha=True)
        self.width = tm.width * tm.tilewidth
        self.height = tm.height * tm.tileheight
        self.tmxdata = tm

    def render(self, surface):
        ti = self.tmxdata.get_tile_image_by_gid
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid, in layer:
                    tile = ti(gid)
                    if tile:
                        surface.blit(tile, (x * self.tmxdata.tilewidth,
                                            y * self.tmxdata.tileheight))

    def make_map(self):
        temp_surface = pg.Surface((self.width, self.height))
        self.render(temp_surface)
        return temp_surface


class Player(pg.sprite.Sprite):
    # sprite for play button and penguin
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.players

        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.image.load('resources/penguin.png')
        self.image = pg.transform.scale(self.image, (TILESIZE, TILESIZE))

        self.rect = self.image.get_rect()

        self.x = x
        self.dx = 0
        self.y = y
        self.dy = 0

        self.xorj, self.yorj = x, y
        self.last_update = pg.time.get_ticks()
        self.off_lake = 0 # controls is on lake= 0 if yes?
        self.win = False
        self.moving = False # used by the update loop to know what objects to move?
        self.position_targets = deque()
        self.load = False
        self.dots = 0


    def update(self):
        self.x += self.dx
        self.y += self.dy

        self.rect.x = self.x * TILESIZE
        self.rect.y = self.y * TILESIZE

    def add_target(self, x, y):
        self.position_targets.append((x+self.xorj, y+self.yorj))

    def add_target_walk(self, targets):
        for target in targets:
            self.add_target(*target)

    def kill(self):
        pg.sprite.Sprite.kill(self)

class Play_button(pg.sprite.Sprite):
    # sprite for play button and penguin
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.image.load('resources/play_but.png')
        half_size= int(1.5*TILESIZE)
        self.image = pg.transform.scale(self.image,(half_size,half_size))
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y

    def update(self):
        self.rect.x = self.x * TILESIZE
        self.rect.y = self.y * TILESIZE

    def kill(self):
        pg.sprite.Sprite.kill(self)

class Gaps(pg.sprite.Sprite):
    def __init__(self,game,x,y,id):
            self.groups = game.all_sprites, game.gaps_group
            pg.sprite.Sprite.__init__(self, self.groups)

            self.image = pg.image.load('resources/gap_gate.png')

            self.image = pg.transform.scale(self.image, ( TILESIZE, TILESIZE))
            self.rect = self.image.get_rect()
            self.x = x
            self.y = y
            self.clicked = False # controls if clicked
            self.game = game
            self.id = id

    def update(self):
        self.rect.x = self.x * TILESIZE
        self.rect.y = self.y * TILESIZE
    def kill(self):
        pg.sprite.Sprite.kill(self)



class Gates(pg.sprite.Sprite):
    # sprite for the gates
    def __init__(self,game,type,x,y):

        # load gates according to their type
        if type=="I":
            self.groups = game.all_sprites, game.Igroup, game.gate_group
            pg.sprite.Sprite.__init__(self, self.groups)

            self.image = pg.image.load('resources/Igate.png')

            self.image = pg.transform.scale(self.image, ( TILESIZE, TILESIZE))
            self.rect = self.image.get_rect()
            self.type = "I"


        elif type=="X":
            self.groups = game.all_sprites, game.Xgroup, game.gate_group
            pg.sprite.Sprite.__init__(self, self.groups)
            self.image = pg.image.load('resources/X_gate.png')
            self.image = pg.transform.scale(self.image, ( TILESIZE, TILESIZE))

            self.rect = self.image.get_rect()
            self.type = "X"
        elif type=="H":
            self.groups = game.all_sprites, game.Hgroup, game.gate_group
            pg.sprite.Sprite.__init__(self, self.groups)
            self.image = pg.image.load('resources/H_gate.png')
            self.image = pg.transform.scale(self.image, (TILESIZE, TILESIZE))
            self.rect = self.image.get_rect()
            self.type = "H"
        elif type=="K":
            self.groups = game.all_sprites, game.Hgroup, game.gate_group
            pg.sprite.Sprite.__init__(self, self.groups)
            self.image = pg.image.load('resources/CX_gate.png')
            self.image = pg.transform.scale(self.image, (TILESIZE, TILESIZE))
            self.rect = self.image.get_rect()
            self.type = "K"

        self.clicked = False
        self.click_time = 0
        self.game = game
        self.x = x
        self.y = y
        self.rect.x = self.x * TILESIZE
        self.rect.y = self.y * TILESIZE
        def update(self): # controls movement along wire
            if self.clicked == True:
                #print("hello")
                self.image = pg.Surface((TILESIZE, TILESIZE ))
                self.image.fill(WHITE)


class Qubits(pg.sprite.Sprite):
    # Sprite for the moving qubit
    def __init__(self,game,number,x,y):
        self.groups = game.all_sprites, game.all_qubits
        pg.sprite.Sprite.__init__(self, self.groups)
        self.image = pg.image.load('resources/tesseract.png')
        self.image = pg.transform.scale(self.image, (TILESIZE, TILESIZE))
        #self.image = pg.transform.rotate(self.image,45)
        self.rect = self.image.get_rect()

        self.speedx = 0
        self.number = number
        self.x = x
        self.y = y
        self.rect.x = self.x * TILESIZE
        self.rect.y = self.y * TILESIZE
        self.end= False
        self.step=0

    def update(self): # controls movement along wire
        self.rect.x += self.speedx
        if self.rect.left>WIDTH-128:
            self.speedx = 0
            self.end = True


class circ(pg.sprite.Sprite): #wires along which qubits move
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.image.load('resources/circuit background.png')
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y

        self.rect.bottomright = (WIDTH,HEIGHT)

class Wire(pg.sprite.Sprite): #wires along which qubits move
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.wires
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.image.load('resources/wire.png')
        wire_width = int(TILESIZE/8)
        self.image = pg.transform.scale(self.image,(TILESIZE,wire_width))

        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE+28

class Background2(pg.sprite.Sprite): #background tiles for frozen lake
    def __init__(self, game, x, y):
                self.groups = game.all_sprites, game.backgrounds
                pg.sprite.Sprite.__init__(self, self.groups)
                self.game = game
                self.image = pg.image.load('resources/ice_tile.png')
                self.image = pg.transform.scale(self.image, (2*TILESIZE, 2*TILESIZE))
                self.rect = self.image.get_rect()
                #self.image = pg.Surface((TILESIZE, TILESIZE ))
                #self.image.fill(WHITE)
                self.rect = self.image.get_rect()
                self.x = x
                self.y = y
                self.rect.x = x * TILESIZE
                self.rect.y = y * TILESIZE


class Background(pg.sprite.Sprite): #background tiles for frozen lake
    def __init__(self, game, x, y, w, h):
                self.groups = game.all_sprites, game.backgrounds
                pg.sprite.Sprite.__init__(self, self.groups)
                self.game = game
                self.rect = pg.Rect(x,y,w,h)
                self.image = pg.image.load('resources/ice_tile.png')

                #self.image = pg.Surface((TILESIZE, TILESIZE ))
                #self.image.fill(WHITE)
                self.rect = self.image.get_rect()
                self.x = x
                self.y = y
                self.rect.x = x
                self.rect.y = y


class Hole(pg.sprite.Sprite):  # background tiles for frozen lake
    def __init__(self, game, x, y):
            self.groups =  game.holes
            pg.sprite.Sprite.__init__(self, self.groups)
            self.game = game
            self.image = pg.image.load('resources/icy hole.png')
            self.image = pg.transform.scale(self.image, (2 * TILESIZE, 2 * TILESIZE))
            self.rect = self.image.get_rect()
            # self.image = pg.Surface((TILESIZE, TILESIZE ))
            # self.image.fill(WHITE)
            self.rect = self.image.get_rect()
            self.x = x
            self.y = y
            self.rect.x = x * TILESIZE - TILESIZE
            self.rect.y = y * TILESIZE
            self.hit = False

class Igloo(pg.sprite.Sprite): # victory endpoints
    def __init__(self, game, x, y):
                self.groups = game.all_sprites, game.backgrounds, game.igloos
                pg.sprite.Sprite.__init__(self, self.groups)
                self.game = game
                self.image = pg.image.load('resources/igloo.png')
                height_img = int(1.5*TILESIZE)
                self.image = pg.transform.scale(self.image, (2*TILESIZE-16, height_img))
                self.rect = self.image.get_rect()
                self.x = x
                self.y = y
                self.rect.x = x * TILESIZE
                self.rect.y = y * TILESIZE
                self.win = False
