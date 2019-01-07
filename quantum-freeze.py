#!/usr/bin/env python3
import pygame as pg
import os
import numpy
import sys
from collections import defaultdict, OrderedDict
from math import copysign
import pytmx
import time

from sprites import *
from pyquil_requests import QThread
from os import path

DEBUG =  False
LEVELS = 3

# define some colors (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGREY = (40, 40, 40)
LIGHTGREY = (100, 100, 100)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
PURPLE = (160,32,240)

# game settings
WIDTH = 1024   # 16 * 64 or 32 * 32 or 64 * 16
HEIGHT = 768  # 16 * 48 or 32 * 24 or 64 * 12
FPS = 60
TITLE = "quantum freeze block"
BGCOLOR = DARKGREY

#define grid map
TILESIZE = 64
GRIDWIDTH = WIDTH / TILESIZE
GRIDHEIGHT = HEIGHT / TILESIZE


# used for signalling to the event loop that the results are back
QVMRET = pg.event.Event(pg.USEREVENT, {})

#Overall game class
class Game:

    def __init__(self, qthread, level=0):
        pg.init()
        self.qthread = qthread
        # self.qthread.start()
        #Set up screen
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.level = level

        self.load_data()
        self.lose = False
        background_image= pg.image.load('resources/snow_scene.png')


    #Load map file into folder
    def load_data(self):
        game_folder = path.dirname(__file__)
        self.map_data = []
        self.map = TiledMap('resources/game_map{}.tmx'.format(self.level))

        self.map_img = self.map.make_map()
        self.map_rect = self.map_img.get_rect()
        with open(path.join(game_folder, 'resources/map{}.txt'.format(self.level)), 'rt') as f:
            for line in f:
                self.map_data.append(line)


    def game_intro(self):
        intro = True
        if DEBUG: print("loading bg")
        background_image = pg.image.load('resources/snow_scene.png')
        if DEBUG: print("scale bg")
        background_image = pg.transform.scale(background_image, (1200, 774))
        while intro:
            if DEBUG: print("blitting")
            self.screen.blit(background_image, [-5, -5])

            if DEBUG: print("messages")
            self.message_to_screen("The Quantum Freeze",PURPLE,(WIDTH/2),(HEIGHT/2)-100,size="large")
            self.message_to_screen("Press space to play", BLACK, (WIDTH/2),(HEIGHT/2)+80)
            if DEBUG: print("wait for event")
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                if event.type == pg.KEYDOWN:
                    if event.key ==pg.K_SPACE:
                        intro = False

            pg.display.update()
            self.clock.tick(15)
    def game_instructions(self):
        instruct=True
        background_image = pg.image.load('resources/snow_scene.png').convert()
        background_image = pg.transform.scale(background_image, (1200, 774))
        while instruct:

            self.screen.blit(background_image,[-5,-5])
            self.message_to_screen("Instructions",PURPLE,0,10,size="medium",corner="left")
            self.message_to_screen("The objective of the game is to guide your penguins"
                                   , BLACK,0,150,corner="left")
            self.message_to_screen("across the frozen lake to reach the igloos", BLACK,0,190,corner="left")
            self.message_to_screen("Every penguin must reach an igloo", BLACK,0,290,corner="left")
            self.message_to_screen("Every igloo must house at least one penguin", BLACK,0,330,corner="left")
            self.message_to_screen("BEWARE: the lake contains hidden holes!!!", BLACK,0,430,corner="left")
            self.message_to_screen("Press space to continue", BLACK, WIDTH/2,HEIGHT/2+200)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                if event.type == pg.KEYDOWN:
                    if event.key ==pg.K_SPACE:
                        instruct = False

            pg.display.update()
            self.clock.tick(15)



    def message_to_screen(self,msg, color,pos_x,pos_y, size="small",corner = "center"):
        if DEBUG: print("print msg, get text obj")
        textSurf, textRect = self.text_objects(msg, color, size)
        if corner =="left":
            textRect.x = pos_x
            textRect.y = pos_y
        else:
            textRect.center = pos_x,pos_y
        if DEBUG: print("blitting in msg_to_screen")
        self.screen.blit(textSurf, textRect)

    def text_objects(self,text, color, size):
        if DEBUG: print("getting fornts")
        smallerfont = pg.font.Font("resources/Iceland-Regular.ttf", 37)
        smallfont = pg.font.Font("resources/Iceland-Regular.ttf", 50)
        mederfont = pg.font.Font("resources/Iceland-Regular.ttf", 70)
        medfont = pg.font.Font("resources/Iceland-Regular.ttf", 100)
        largefont = pg.font.Font("resources/Iceland-Regular.ttf", 120)
        if size == "smaller":
                textSurface = smallerfont.render(text,True,color)
        elif size == "small":
                textSurface = smallfont.render(text, True, color)
        elif size == "mediumer":
                textSurface = mederfont.render(text, True, color)
        elif size == "medium":
                textSurface = medfont.render(text, True, color)
        elif size == "large":
                textSurface = largefont.render(text, True, color)
        return textSurface, textSurface.get_rect()
    # LOADING BAR DISPLAY FUNCTION
    def computing(self,dots):
            dots_progress = '.'*int(dots)
            self.message_to_screen("Computing"+dots_progress, PURPLE, 8*TILESIZE+16,4*64+32,size="mediumer", corner = "left")


    def new(self):

        # initialize all variables and do all the setup for a new game
        self.all_sprites = pg.sprite.Group()
        #3 distinct gate groups
        self.Igroup = pg.sprite.Group()
        self.Xgroup = pg.sprite.Group()
        self.Hgroup = pg.sprite.Group()
        # overall gate group controls drag and drop behaviour
        self.gate_group = pg.sprite.Group()
        # Gaps can be filled by gates
        self.gaps_group = pg.sprite.Group()
        self.all_qubits = pg.sprite.Group()
        # backgrounds will be tiles the penguin must stabd on
        self.backgrounds = pg.sprite.Group()
        # Penguin player group
        self.players = pg.sprite.Group()
        # igloos are endpoints
        self.igloos = pg.sprite.Group()
        self.wires = pg.sprite.Group()
        self.holes = pg.sprite.Group()

        self.circuit = Circuit()
        self.qubitsended = False
        self.inital_player_loc = None


        # Generate Sprites according to map entry
        itr=0
        for row, tiles in enumerate(self.map_data):
            for col, tile in enumerate(tiles):
                if tile == 'L':
                    Hole(self, col, row)
                if tile == 'B':
                    Background2(self, col, row)
                if tile == 'G':
                    Background2(self,col,row)
                    Igloo(self, col+0.25, row+0.25)
                if tile == 'P':
                    #Background2(self,col,row)
                    self.player_placeholder = Player(self, col+0.5, row-0.25) # move them to center of tile
                    self.inital_player_loc = (col+0.5, row-0.25) # center of tile
                if tile == 'Q':
                    Wire(self, col+0.5, row)
                    qubit = Qubits(self, 1, col,row)

                if tile == 'I':
                    self.Igate = Gates(self,"I",col,row)
                if tile == 'X':
                    self.Xgate = Gates(self,"X",col,row)
                if tile == 'H':
                    self.Hgate = Gates(self,"H",col,row)
                if tile == 'K':
                    self.Hgate = Gates(self,"K",col,row)
                if tile == 'S':
                    self.play_button = Play_button(self,col+0.25,row-0.25)
                if tile == 'W':
                    Wire(self,col,row)
                if tile == 'A':
                    gap = Gaps(self,col,row,itr)
                    itr=itr+1
                if tile == 'C':
                    circ(self,col,row)

        #for tile_object in self.map.tmxdata:
         #   if tile_object.name == 'Lake':
          #      print(tile_object.properties)
           #     Background(self,tile_object.x,tile_object.y,tile_object.width,tile_object.height)




    def run(self):
        # game loop - set self.playing = False to end the game
        self.playing = True
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update()
            self.draw()

    def quit(self):
        pg.quit()
        sys.exit()

    def update(self):
        # update portion of the game loop

        self.all_sprites.update()
        # Kill gate on contact




        for player in self.players: #define win and lose conditions
            hitIG = pg.sprite.spritecollide(player, self.igloos, False)
            onlake = pg.sprite.spritecollide(player, self.backgrounds, False)
            if onlake:
                player.on_lake = 0  # onlake must be 0 else the penguin dies
            else:
                player.off_lake = 1
            if hitIG:
                player.win = True #player wins when all penguins have winPe==1
                for igloo in hitIG:
                    igloo.win = True
            else:
                player.win = False




        if self.qubitsended == False and all([q.end for q in self.all_qubits.sprites()]):
            self.qubitsended = True
            # do win condition detection. Only if all the qubits have just hit the end.
            correctIglos = [pg.sprite.spritecollide(igloo, self.players,False) for igloo in self.igloos]

        # move penguins closer to the destination.
        # move dx, dy each timestep - if pos = dest remove dest from list.
        qubit_list = self.all_qubits.sprites()
        for index, qubit in enumerate(qubit_list):
            if index > 0:
                prev_qubit = qubit_list[index - 1]
                if prev_qubit.end == 1 and qubit.end==0:
                    qubit.speedx = 5

        velocity = 0.1
        step = [0]*len(qubit_list)
        for index,qubit in enumerate(qubit_list):
            hit = pg.sprite.spritecollide(qubit, self.gate_group, True)
            if hit:
                qubit.step +=1
            step[index]=qubit.step
            for i, player in enumerate(self.players.sprites()):
                if player.position_targets: # have a target to aim for
                    if step[index]:
                        # print("mov peng", i, "of", len(self.players.sprites()))
                        (tx, ty) = player.position_targets[index+1]

                        if abs(player.x - tx) > 0.01:
                            player.dx = copysign(velocity, tx - player.x)
                        else:
                            player.dx = 0

                        if abs(player.y - ty) > 0.01:
                            player.dy = copysign(velocity, ty - player.y)
                        else:
                            player.dy = 0


                        if abs(player.x - tx) < 0.01 and abs(player.y - ty) < 0.01:
                            qubit.step== 0





    def draw_grid(self):
        for x in range(0, WIDTH, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (0, y), (WIDTH, y))

    def draw(self):
        self.screen.blit(self.map_img,[0,0])
        self.holes.draw(self.screen)
        self.all_sprites.draw(self.screen)
        self.all_qubits.draw(self.screen)

        self.message_to_screen("LEVEL", PURPLE,190,560, "medium")
        self.message_to_screen("{}".format(self.level),PURPLE,190,648,"large")
        self.message_to_screen("Click to select gate",PURPLE,798,80,"smaller")
        self.message_to_screen("then click gap to move",PURPLE,799,120,"smaller")
        self.message_to_screen("Hit play to run circuit",PURPLE,798,160,"smaller")
        player_list = self.players.sprites()
        igloo_list = self.igloos.sprites()
        qubit_list = self.all_qubits.sprites()

        # LOADING BAR
        if self.player_placeholder.load:
            time_count = 0.3
            self.computing(self.player_placeholder.dots)
            self.player_placeholder.dots += 1
            if self.player_placeholder.dots ==4:
                self.player_placeholder.dots = 1
            time.sleep(time_count)
        for player in self.players:
            hit_hole = pg.sprite.spritecollide(player, self.holes, False)

            if hit_hole:
                # player.kill() eventually.
                for hole in hit_hole:
                    self.wires.add(hole)
                    if hole.hit == False:
                        hole.hitting_time = pg.time.get_ticks()
                    hole.hit= True

                now = pg.time.get_ticks()
                if now - hole.hitting_time>100:
                    self.wires.draw(self.screen)
                if now - hole.hitting_time>950:
                    self.play_again_lose()
                    self.playing = False
                    self.wires.draw(self.screen)
            if player.off_lake ==1:
                 self.play_again_lose()
                 self.lose = True
        if all( player.win is True for player in player_list) and all( igloo.win is True for igloo in igloo_list):
            if all( qubit.end is True for qubit in qubit_list):
                self.screen.fill(WHITE)
                self.play_again_win()
        elif all( qubit.end is True for qubit in qubit_list):
            self.lose = True
            self.play_again_lose()


        now = pg.time.get_ticks()
        if self.lose:
            time_count = 1
            time.sleep(time_count)
            self.playing = False


        pg.display.flip()

    def mesurement_callback(self, msmt_outcomes):
        print("sending event notification")
        print("recv final states", msmt_outcomes)
        self.msmt_outcomes = msmt_outcomes
        pg.event.post(QVMRET)

    def events(self):
        # catch all events here
        for event in pg.event.get():
            #print("got event of type", event.type)
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.MOUSEBUTTONDOWN:
                pos = pg.mouse.get_pos()

                if event.button == 1:

                    # if click play set qubit moving and build up circuit
                    if self.play_button.rect.collidepoint(pos):
                        self.play_button.kill()
                        self.player_placeholder.load +=1

                        # call out to the bg thread to run the circuit
                        #
                        self.qthread.build_circuit(self.circuit.qubit_operation)
                        try:
                            self.qthread.execute(callback=self.mesurement_callback)
                        except Exception as e:
                            print(e)

                    # control placement behaviour of the gates
                    for gate in self.gate_group:
                        now = pg.time.get_ticks()
                        if gate.rect.collidepoint(pos) and gate.clicked==False:
                            gate.clicked = True
                            gate.click_time = now
                            if gate.type == "I":
                                gate.image = pg.image.load('resources/Igate_pressed.png')
                            elif gate.type == "X":
                                gate.image = pg.image.load('resources/Xgate_pressed.png')
                            elif gate.type == "H":
                                gate.image = pg.image.load('resources/Hgate_pressed.png')
                            elif gate.type == "K":
                                gate.image = pg.image.load('resources/CXgate_pressed.png')


                        for gap in self.gaps_group:
                            if gap.rect.collidepoint(pos) and gate.clicked == True:
                                        gate_start_x = gate.rect.x/TILESIZE
                                        gate_start_y = gate.rect.y/TILESIZE
                                        gate.clicked = False
                                        Gates(self,gate.type,gate_start_x,gate_start_y)
                                        gate_x = gap.rect.x/TILESIZE
                                        gate_y = gap.rect.y/TILESIZE
                                        Gates(self,gate.type,gate_x,gate_y)
                                        gate.kill()
                                        self.gate_group.draw(self.screen)


                                        #gate.clicked = False

                                        self.circuit.qubit_operation[gap.id]=gate.type
                                        gap.kill()
                        if now-gate.click_time >10 and gate.clicked==True:
                                gate.clicked=False
                                Gates(self,gate.type,gate.x,gate.y)
                                gate.kill()



            if event.type == QVMRET.type:
                self.player_placeholder.load = False
                """Runs the main game loop - processes the quantum sample list
                from the QVM, and instructs the penguins etc to play out the results.
                """
                self.player_placeholder.kill()
                qubit_list = self.all_qubits.sprites()
                for index,qubit in enumerate(qubit_list):
                    if index == 0:
                        qubit.speedx = 5
                    else:
                        prev_qubit=qubit_list[index-1]
                        if prev_qubit.end==1:
                            qubit.speedx = 5

                print(self.players)
                msmt_outcomes = self.msmt_outcomes # saved by the callback
                msmt_outcomes = [tuple(msmt) for msmt in msmt_outcomes]

                # x=set(x)
                #  the defaultdict holds 0 in all key locations - we then
                # incriment each observed sample so we know the relative
                # amplitude for each penguin. relative final amp. the prefix
                # needs to be the sum of amps at that point.
                x = defaultdict(lambda: 0)
                for sample in msmt_outcomes:
                    x[sample] += (1./len(msmt_outcomes))
                # move penguin according to mmt outcomes.
                #
                # test with only the first msmnt outcome
                self.players.empty()
                for pidx in range(len(x.keys())): # additional players
                    Player(self, *self.inital_player_loc)
                print("no unique paths:", len(self.players.sprites()))

                # need a list of steps.
                # [ [(x, y, weight)], [(x, y, weight), (x, y, weight)] ... ]

                # each element of this list is a map of locations -> amplitude for
                # the penguins after gate i.
                print("walking the penguins")
                paths = [OrderedDict() for _ in range(len(msmt_outcomes[0]))]
                for path in paths:
                    path[(0, 0)] = 1./len(msmt_outcomes)


                for pengidx, (path, weight) in enumerate(x.items()):
                    px, py = 0, 0
                    for step in path:
                        if step == 1:
                            px += 2
                        else:
                            py += 2
                        paths[pengidx][(px, py)] =  paths[pengidx].get((px, py), 0) + weight

                pathlists = [path.keys() for path in paths]
                print("penguin paths", pathlists)
                for penguin, path in zip(self.players.sprites(), pathlists):
                    penguin.add_target_walk(path)


    def show_start_screen(self):
        pass
    # if win display congrats and ask to play again
    def play_again_win(self):
        bigfont = pg.font.SysFont('Iceland', 80)
        text = bigfont.render('Congrats!', 13, PURPLE)
        text2 = bigfont.render('Press space to continue', 13, PURPLE)
        textx = WIDTH / 2 - text.get_width() / 2
        texty = HEIGHT / 2 - text.get_height() / 2
        textx_size = text.get_width()
        texty_size = text.get_height()
        pg.draw.rect(self.screen, (255,255,255), ((textx - 5, texty - 5),(textx_size + 10, texty_size +10)))


        self.screen.blit(text, (WIDTH / 2 - text.get_width() / 2,

                                -64+HEIGHT / 2 - text.get_height() / 2))
        self.screen.blit(text2, (WIDTH / 2 - text2.get_width() / 2,

                                100-64 + HEIGHT / 2 - text2.get_height() / 2))

        for event in pg.event.get():
            if event.type == pg.QUIT:
                    pg.quit()
                    quit()
            if event.type == pg.KEYDOWN:
                pos = pg.mouse.get_pos()
                if event.key ==pg.K_SPACE:
                                g = Game(level=(self.level+1) % LEVELS, qthread=self.qthread)
                                g.show_start_screen()
                                while True:
                                    g.new()
                                    g.run()
                                    g.show_go_screen()
    # if lose repeat as above but display lose
    def play_again_lose(self):
            self.screen.fill(WHITE)
            bigfont = pg.font.SysFont('Iceland', 80)
            text = bigfont.render('You lose!', 13, PURPLE)
            text2 = bigfont.render('Press space to play again', 13, PURPLE)
            textx = WIDTH / 2 - text.get_width() / 2
            texty = HEIGHT / 2 - text.get_height() / 2
            textx_size = text.get_width()
            texty_size = text.get_height()
            pg.draw.rect(self.screen, (255,255,255), ((textx - 5, texty - 5),(textx_size + 10, texty_size +10)))


            self.screen.blit(text, (WIDTH / 2 - text.get_width() / 2,

                                   -64 +HEIGHT / 2 - text.get_height() / 2))

            self.screen.blit(text2, (WIDTH / 2 - text2.get_width() / 2,100 -64 + HEIGHT / 2 - text2.get_height() / 2))

            for event in pg.event.get():
                        for event in pg.event.get():
                            if event.type == pg.QUIT:
                                pg.quit()
                                quit()
                            if event.type == pg.KEYDOWN:
                                pos = pg.mouse.get_pos()
                                if event.key ==pg.K_SPACE:
                                                g = Game(qthread=self.qthread, level=self.level)
                                                g.show_start_screen()
                                                while True:
                                                    g.new()
                                                    g.run()
                                                    g.show_go_screen()




    def show_go_screen(self):
            play_again=True
            while play_again:
                self.screen.fill(WHITE)
                bigfont = pg.font.SysFont('Iceland', 80)
                text = bigfont.render('You lose!', 13, PURPLE)
                text2 = bigfont.render('Press space to play again', 13, PURPLE)
                textx = WIDTH / 2 - text.get_width() / 2
                texty = HEIGHT / 2 - text.get_height() / 2
                textx_size = text.get_width()
                texty_size = text.get_height()
                pg.draw.rect(self.screen, (255,255,255), ((textx - 5, texty - 5),(textx_size + 10, texty_size +10)))


                self.screen.blit(text, (WIDTH / 2 - text.get_width() / 2,

                                        -64+HEIGHT / 2 - text.get_height() / 2))
                self.screen.blit(text2, (WIDTH / 2 - text2.get_width() / 2,100-64 + HEIGHT / 2 - text2.get_height() / 2))

                pg.display.flip()

                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        pg.quit()
                        quit()
                    if event.type == pg.KEYDOWN:
                                        pos = pg.mouse.get_pos()
                                        if event.key ==pg.K_SPACE:
                                                        g = Game(qthread=self.qthread)
                                                        g.show_start_screen()
                                                        while True:
                                                            g.new()
                                                            g.run()
                                                            g.show_go_screen()

import pdb


try:
    level_idx = sys.argv.index("-l")+1
    level = int(sys.argv[level_idx])
except ValueError:
    level = 0
# create the game object
print("created game")
qthread = QThread()
print("startred game")

qthread.start()
g = Game(qthread=qthread, level=level)
print("showing start screen")
g.show_start_screen()
# # Game loop
while True:
    print("intro")
    g.game_intro()
    print("instructions")
    g.game_instructions()
    print("new")
    g.new()
    print("run")
    g.run()
    g.show_go_screen()
