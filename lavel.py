import pygame
import sys
import random
from pygame.math import Vector2 as vector
from settings import *
from sprites import Animated, Block, Cloud, Coin, Generic, Particle, Player, Shell, Spikes, Tooth


class Level:
    def __init__(self, grid, switch, assetDict):
        self.dipslySurface = pygame.display.get_surface()
        self.switch = switch
        self.grid = grid
        self.assetDict = assetDict

        self.CLOUDTIMER = pygame.USEREVENT + 2
        pygame.time.set_timer(self.CLOUDTIMER, 2000)

        # group
        self.allSprites = CameraGroup()
        self.coinSprites = pygame.sprite.Group()
        self.damageSprites = pygame.sprite.Group()
        self.collisionSprites = pygame.sprite.Group()
        self.shellSprites = pygame.sprite.Group()

        # limits
        self.levelLimits = {
            'left': -WINDOW_WIDTH,
            'right': sorted(list(self.grid['terrain'].keys()), key=lambda pos: pos[0])[-1][0] + 500
        }

        # audio
        self.bgMusic = assetDict['sounds']['music']
        self.bgMusic.set_volume(0.4)
        self.bgMusic.play(loops=-1)

        # coin
        self.coinSound = assetDict['sounds']['coin']
        self.coinSound.set_volume(0.4)

        # hit
        self.hitSound = assetDict['sounds']['hit']
        self.hitSound.set_volume(0.4)

        self.buildGrid(grid, assetDict)
        self.startUpClouds()

    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.switch()
                self.bgMusic.stop()

            self.createCloud(event)

    def createCloud(self, event):
        if event.type == self.CLOUDTIMER:
            randomCloud = random.choice(self.assetDict['clouds'])
            if random.randint(0, 4) < 2:
                pygame.transform.scale2x(randomCloud)
            speed = random.randint(20, 50)
            x = self.levelLimits['right'] + random.randint(100, 300)
            y = self.horizonY - random.randint(-50, 600)
            Cloud((x, y), randomCloud, speed,
                  self.allSprites, self.levelLimits['left'])

    def startUpClouds(self):
        for cloud in range(40):
            randomCloud = random.choice(self.assetDict['clouds'])
            if random.randint(0, 4) < 2:
                pygame.transform.scale2x(randomCloud)
            speed = random.randint(20, 50)
            x = random.randint(
                self.levelLimits['left'], self.levelLimits['right'])
            y = self.horizonY - random.randint(-50, 600)
            Cloud((x, y), randomCloud, speed,
                  self.allSprites, self.levelLimits['left'])

    def buildGrid(self, grid, assetDict):
        for layerName, layer in grid.items():
            for pos, data in layer.items():
                if layerName == 'terrain':
                    Generic(pos, assetDict['lands'][data], [
                            self.allSprites, self.collisionSprites])

                if layerName == 'water':
                    if data == 'top':
                        Animated(pos, assetDict['water']
                                 ['top'], self.allSprites, LEVEL_LAYERS['water'])
                    else:
                        Generic(pos, assetDict['water']
                                ['bottom'], self.allSprites, LEVEL_LAYERS['water'])

                match data:
                    # palyer
                    case 0: self.player = Player(pos, self.allSprites, self.collisionSprites, assetDict['player'], assetDict['sounds']['jump'])

                    # sky
                    case 1:
                        self.horizonY = pos[1]
                        self.allSprites.horizonY = pos[1]

                    # coins
                    case 4: Coin('gold', pos, assetDict['coin']['gold'], [self.allSprites, self.coinSprites])
                    case 5: Coin('silver', pos, assetDict['coin']['silver'], [self.allSprites, self.coinSprites])
                    case 6: Coin('diamond', pos, assetDict['coin']['diamond'], [self.allSprites, self.coinSprites])

                    # enemeis
                    case 7: Spikes(pos, assetDict['enemies']['spikes'], [self.allSprites, self.damageSprites])
                    case 8: Tooth(pos, assetDict['enemies']['tooth'], [self.allSprites, self.damageSprites], self.collisionSprites)
                    case 9:
                        Shell('left', pos, assetDict['enemies']['shell'], [
                              self.allSprites, self.collisionSprites, self.shellSprites], assetDict['pearl'], self.damageSprites)
                    case 10:
                        Shell('right', pos, assetDict['enemies']['shell'], [
                              self.allSprites, self.collisionSprites, self.shellSprites], assetDict['pearl'], self.damageSprites)

                    # palm trees
                    case 11:
                        Animated(pos, assetDict['palm']
                                 ['small_fg'], self.allSprites)
                        Block(pos, (76, 50), self.collisionSprites)
                    case 12:
                        Animated(pos, assetDict['palm']
                                 ['large_fg'], self.allSprites)
                        Block(pos, (76, 50), self.collisionSprites)
                    case 13:
                        Animated(pos, assetDict['palm']
                                 ['left_fg'], self.allSprites)
                        Block(pos, (76, 50), self.collisionSprites)
                    case 14:
                        Animated(pos, assetDict['palm']
                                 ['right_fg'], self.allSprites)
                        Block(pos + vector(50, 0), (76, 50),
                              self.collisionSprites)

                    case 15: Animated(pos, assetDict['palm']['small_bg'], self.allSprites, LEVEL_LAYERS['bg'])
                    case 16: Animated(pos, assetDict['palm']['large_bg'], self.allSprites, LEVEL_LAYERS['bg'])
                    case 17: Animated(pos, assetDict['palm']['left_bg'], self.allSprites, LEVEL_LAYERS['bg'])
                    case 18: Animated(pos, assetDict['palm']['right_bg'], self.allSprites, LEVEL_LAYERS['bg'])

        for sprite in self.shellSprites:
            sprite.player = self.player

    def getDamage(self):
        collisionSprites = pygame.sprite.spritecollide(
            self.player, self.damageSprites, False, pygame.sprite.collide_mask)
        if collisionSprites:
            self.hitSound.play()
            self.player.damage()

    def getCoin(self):
        collidedCoins = pygame.sprite.spritecollide(
            self.player, self.coinSprites, True)
        for sprite in collidedCoins:
            self.coinSound.play()
            Particle(sprite.rect.center,
                     self.assetDict['particle'], self.allSprites)

    def run(self, deltaTime):
        # update
        self.eventLoop()
        self.allSprites.update(deltaTime)
        self.getCoin()
        self.getDamage()

        # draw
        self.dipslySurface.fill(SKY_COLOR)
        self.allSprites.customDraw(self.player)


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.displaySurface = pygame.display.get_surface()
        self.offset = vector()

    def drawHorizon(self):
        horizonPos = self.horizonY - self.offset.y

        if horizonPos < WINDOW_HEIGHT:
            seaRect = pygame.Rect(
                0, horizonPos, WINDOW_WIDTH, WINDOW_HEIGHT - horizonPos)
            pygame.draw.rect(self.displaySurface, SEA_COLOR, seaRect)

        if horizonPos > 0:
            horizonRect = pygame.Rect(0, horizonPos, WINDOW_WIDTH, 3)
            horizonRect1 = pygame.Rect(0, horizonPos - 10, WINDOW_WIDTH, 10)
            horizonRect2 = pygame.Rect(0, horizonPos - 16, WINDOW_WIDTH, 4)
            horizonRect3 = pygame.Rect(0, horizonPos - 20, WINDOW_WIDTH, 2)
            pygame.draw.rect(self.displaySurface, HORIZON_COLOR, horizonRect)
            pygame.draw.rect(self.displaySurface,
                             HORIZON_TOP_COLOR, horizonRect1)
            pygame.draw.rect(self.displaySurface,
                             HORIZON_TOP_COLOR, horizonRect2)
            pygame.draw.rect(self.displaySurface,
                             HORIZON_TOP_COLOR, horizonRect3)

        if horizonPos < 0:
            self.displaySurface.fill(SEA_COLOR)

    def customDraw(self, player):
        self.offset.x = player.rect.centerx - WINDOW_WIDTH/2
        self.offset.y = player.rect.centery - WINDOW_HEIGHT/2

        for sprite in self:
            if sprite.z == LEVEL_LAYERS['clouds']:
                offsetRect = sprite.rect.copy()
                offsetRect.center -= self.offset
                self.displaySurface.blit(sprite.image, offsetRect)

        self.drawHorizon()
        for sprite in self:
            for layer in LEVEL_LAYERS.values():
                if sprite.z == layer and sprite.z != LEVEL_LAYERS['clouds']:
                    offsetRect = sprite.rect.copy()
                    offsetRect.center -= self.offset
                    self.displaySurface.blit(sprite.image, offsetRect)
