import pygame
from lavel import Level
from settings import *
from editor import Editor
from pygame.image import load as imageLoad
from support import *
from pygame.math import Vector2 as vector
from os import walk


class Main:
    def __init__(self):
        pygame.init()
        self.displaySurface = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.imports()

        self.transition = Transition(self.toggle)
        self.editorActive = True
        self.editor = Editor(self.landTiles, self.switch)

        # cursor
        surf = imageLoad('./graphics/cursors/mouse.png').convert_alpha()
        cursor = pygame.cursors.Cursor((0, 0), surf)
        pygame.mouse.set_cursor(cursor)

    def imports(self):
        # land
        self.landTiles = importFolderDict('./graphics/terrain/land')

        # water
        self.waterTop = importFolder('./graphics/terrain/water/animation')
        self.waterBottom = imageLoad(
            './graphics/terrain/water/water_bottom.png').convert_alpha()

        # coin
        self.diamond = importFolder('./graphics/items/diamond')
        self.gold = importFolder('./graphics/items/gold')
        self.silver = importFolder('./graphics/items/silver')
        self.particle = importFolder('./graphics/items/particle')

        # palm
        self.palm = {folder: importFolder(
            f'./graphics/terrain/palm/{folder}') for folder in list(walk('./graphics/terrain/palm'))[0][1]}

        # enemies
        self.spikes = imageLoad(
            './graphics/enemies/spikes/spikes.png').convert_alpha()
        self.tooth = {folder: importFolder(
            f'./graphics/enemies/tooth/{folder}') for folder in list(walk('./graphics/enemies/tooth'))[0][1]}
        self.shell = {folder: importFolder(
            f'./graphics/enemies/shell_left/{folder}') for folder in list(walk('./graphics/enemies/shell_left'))[0][1]}
        self.pearl = imageLoad('./graphics/enemies/pearl/pearl.png')

        # player
        self.player = {folder: importFolder(
            f'./graphics/player/{folder}') for folder in list(walk('./graphics/player'))[0][1]}

        # clouds
        self.clouds = importFolder('./graphics/clouds')

        # sounds
        self.levelSounds = {
            'coin': pygame.mixer.Sound('./audio/coin.wav'),
            'hit': pygame.mixer.Sound('./audio/hit.wav'),
            'jump': pygame.mixer.Sound('./audio/jump.wav'),
            'music': pygame.mixer.Sound('./audio/SuperHero.ogg')
        }

    def toggle(self):
        self.editorActive = not self.editorActive
        if self.editorActive:
            self.editor.editorMusic.play(loops=-1)

    def switch(self, grid=None):
        self.transition.active = True
        if (grid):
            self.level = Level(grid, self.switch, {
                'lands': self.landTiles,
                'water': {
                    'bottom': self.waterBottom,
                    'top': self.waterTop
                },
                'coin': {
                    'diamond': self.diamond,
                    'gold': self.gold,
                    'silver': self.silver
                },
                'particle': self.particle,
                'palm': self.palm,
                'enemies': {
                    'spikes': self.spikes,
                    'tooth': self.tooth,
                    'shell': self.shell
                },
                'player': self.player,
                'pearl': self.pearl,
                'clouds': self.clouds,
                'sounds': self.levelSounds
            })

    def run(self):
        while True:
            deltaTime = self.clock.tick() / 1000
            if self.editorActive:
                self.editor.run(deltaTime)
            else:
                self.level.run(deltaTime)

            self.transition.display(deltaTime)
            pygame.display.update()


class Transition:
    def __init__(self, toggle):
        self.displaySurface = pygame.display.get_surface()
        self.toggle = toggle
        self.active = False

        self.borderWidth = 0
        self.direction = 1
        self.center = (WINDOW_WIDTH/2, WINDOW_HEIGHT/2)
        self.radius = vector(self.center).magnitude()
        self.threshold = self.radius + 100

    def display(self, deltaTime):
        if self.active:
            self.borderWidth += 1000 * deltaTime * self.direction
            if self.borderWidth >= self.threshold:
                self.direction = -1
                self.toggle()

            if self.borderWidth < 0:
                self.active = False
                self.borderWidth = 0
                self.direction = 1
            pygame.draw.circle(self.displaySurface, 'black',
                               self.center, self.radius, int(self.borderWidth))


if __name__ == '__main__':
    main = Main()
    main.run()
