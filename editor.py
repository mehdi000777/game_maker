import pygame
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouseButtons
from pygame.mouse import get_pos as mousePos
from pygame.image import load as imageLoad
import sys
from settings import *
from menu import Menu
from support import importFolder
from timer import Timer
import random


class Editor:
    def __init__(self, landTiles, switch):
        # setup
        self.displySurface = pygame.display.get_surface()
        self.canvasData = {}
        self.switch = switch

        # imports
        self.landTiles = landTiles
        self.animations = {}
        self.imports()

        # clouds
        self.currentClouds = []
        self.cloudsSurf = importFolder('./graphics/clouds')
        self.cloudTimer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.cloudTimer, 2000)
        self.startClouds()

        # navigation
        self.origin = vector()
        self.panOffset = vector()
        self.panActive = False

        # support lines
        self.supportLineSurface = pygame.Surface(
            (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.supportLineSurface.set_colorkey('green')
        self.supportLineSurface.set_alpha(30)

        # selection
        self.selectionIndex = 2
        self.lastSelectedCell = None

        # menu
        self.menu = Menu()

        # objects
        self.canvasGroup = pygame.sprite.Group()
        self.forground = pygame.sprite.Group()
        self.background = pygame.sprite.Group()
        self.activeDragObject = False
        self.timerObject = Timer(400)

        # player
        CanvasObject((200, WINDOW_HEIGHT/2),
                     self.animations[0]['frames'], 0, self.origin, [self.canvasGroup, self.forground])

        # sky
        self.skyHandle = CanvasObject(
            (WINDOW_WIDTH/2, WINDOW_HEIGHT/2), [self.skyHandleSurface], 1, self.origin, [self.canvasGroup, self.background])

        # music
        self.editorMusic = pygame.mixer.Sound('./audio/Explorer.ogg')
        self.editorMusic.set_volume(0.4)
        self.editorMusic.play(loops=-1)

    # support
    def getCurrentPos(self, obj=None):
        distanceToOrigin = vector(
            mousePos()) - self.origin if not obj else vector(obj.distaceToOrigin) - self.origin

        if distanceToOrigin.x > 0:
            x = int(distanceToOrigin.x / TILE_SIZE)
        else:
            x = int(distanceToOrigin.x / TILE_SIZE) - 1

        if distanceToOrigin.y > 0:
            y = int(distanceToOrigin.y / TILE_SIZE)
        else:
            y = int(distanceToOrigin.y / TILE_SIZE) - 1

        return x, y

    def checkNeighbors(self, cellPos):
        # create a local cluster
        clusterSize = 3
        localCluster = []
        for y in range(clusterSize):
            for x in range(clusterSize):
                tileX = cellPos[0] + x - int(clusterSize/2)
                tileY = cellPos[1] + y - int(clusterSize/2)
                localCluster.append((tileX, tileY))

        # check neighbors
        for cell in localCluster:
            if cell in self.canvasData:
                self.canvasData[cell].terrainNeighbors = []
                self.canvasData[cell].waterOnTop = False
                for name, side in NEIGHBOR_DIRECTIONS.items():
                    neighborCell = (cell[0] + side[0], cell[1] + side[1])

                    if neighborCell in self.canvasData:
                        # terrain neighbors
                        if self.canvasData[neighborCell].hasTerrain:
                            self.canvasData[cell].terrainNeighbors.append(name)

                        # water on top
                        if self.canvasData[neighborCell].hasWater and name == 'A':
                            self.canvasData[cell].waterOnTop = True

    def imports(self):
        self.waterBottom = imageLoad(
            './graphics/terrain/water/water_bottom.png').convert_alpha()
        self.skyHandleSurface = imageLoad(
            './graphics/cursors/handle.png').convert_alpha()

        for key, value in EDITOR_DATA.items():
            if value['graphics']:
                files = importFolder(value['graphics'])
                self.animations[key] = {'frameIndex': 0,
                                        'frames': files, 'length': len(files)}

        self.previewSurf = {key: imageLoad(
            value['preview']).convert_alpha() for key, value in EDITOR_DATA.items() if value['preview']}

    def animationUpdate(self, deltaTime):
        for value in self.animations.values():
            value['frameIndex'] += ANIMATION_SPEED * deltaTime
            if value['frameIndex'] >= value['length']:
                value['frameIndex'] = 0

    def createGrid(self):
        # add objects to tiles
        for tile in self.canvasData.values():
            tile.objects = []
        for obj in self.canvasGroup:
            currentCell = self.getCurrentPos(obj)
            offset = vector(obj.distaceToOrigin) - \
                vector(currentCell) * TILE_SIZE

            if currentCell in self.canvasData:
                self.canvasData[currentCell].addId(obj.tileId, offset)
            else:
                self.canvasData[currentCell] = CanvasTile(obj.tileId, offset)

        # grid offset
        left = sorted(self.canvasData.keys(), key=lambda tile: tile[0])[0][0]
        top = sorted(self.canvasData.keys(), key=lambda tile: tile[1])[0][1]

        # create an empty grid
        layers = {
            'water': {},
            'bg palms': {},
            'terrain': {},
            'enemies': {},
            'coins': {},
            'fg objects': {},
        }

        # fill the grid
        for tilePos, tile in self.canvasData.items():
            rowAdjusted = tilePos[1] - top
            colAdjusted = tilePos[0] - left
            x = colAdjusted * TILE_SIZE
            y = rowAdjusted * TILE_SIZE

            if tile.hasWater:
                layers['water'][(x, y)] = tile.getWater()
            if tile.hasTerrain:
                layers['terrain'][(x, y)] = tile.getTerrain(
                ) if tile.getTerrain() in self.landTiles else 'X'
            if tile.coin:
                layers['coins'][(x + TILE_SIZE//2, y +
                                 TILE_SIZE//2)] = tile.coin
            if tile.enemy:
                layers['enemies'][(x, y)] = tile.enemy
            if tile.objects:
                for obj, offset in tile.objects:
                    if obj in [key for key, value in EDITOR_DATA.items() if value['style'] == 'palm_bg']:
                        layers['bg palms'][(
                            int(x + offset.x), int(y + offset.y))] = obj
                    else:
                        layers['fg objects'][(
                            int(x + offset.x), int(y + offset.y))] = obj

        return layers

    # input
    def eventLoop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.switch(self.createGrid())
                self.editorMusic.stop()

            self.panInput(event)
            self.selectionHotKeys(event)
            self.menuClick(event)
            self.selectObject(event)
            self.canvasAdd()
            self.canvaseRemove()

            self.createClouds(event)

    def canvasAdd(self):
        if mouseButtons()[0] and not self.menu.rect.collidepoint(mousePos()) and not self.activeDragObject:
            currentCell = self.getCurrentPos()
            if EDITOR_DATA[self.selectionIndex]['type'] == 'tile':
                if currentCell != self.lastSelectedCell:
                    if currentCell in self.canvasData:
                        self.canvasData[currentCell].addId(self.selectionIndex)
                    else:
                        self.canvasData[currentCell] = CanvasTile(
                            self.selectionIndex)

                    self.checkNeighbors(currentCell)
                    self.lastSelectedCell = currentCell
            else:
                if not self.timerObject.active:
                    background = [self.canvasGroup, self.background]
                    forground = [self.canvasGroup, self.forground]
                    if EDITOR_DATA[self.selectionIndex]['style'] == 'palm_bg':
                        CanvasObject(mousePos(
                        ), self.animations[self.selectionIndex]['frames'], self.selectionIndex, self.origin, background)
                    else:
                        CanvasObject(mousePos(
                        ), self.animations[self.selectionIndex]['frames'], self.selectionIndex, self.origin, forground)

                    self.timerObject.activat()

    def panInput(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and mouseButtons()[1]:
            self.panActive = True
            self.panOffset = vector(mousePos()) - self.origin

        if not mouseButtons()[1]:
            self.panActive = False

        # mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            if pygame.key.get_pressed()[pygame.K_LCTRL]:
                self.origin.y -= event.y * 20
            else:
                self.origin.x -= event.y * 20
            for sprite in self.canvasGroup:
                sprite.panPos(self.origin)

        # panning update
        if self.panActive:
            self.origin = vector(mousePos()) - self.panOffset

            for sprite in self.canvasGroup:
                sprite.panPos(self.origin)

    def selectionHotKeys(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.selectionIndex += 1
            if event.key == pygame.K_LEFT:
                self.selectionIndex -= 1

            self.selectionIndex = max(2, min(self.selectionIndex, 18))

    def menuClick(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.menu.rect.collidepoint(mousePos()):
            newIndex = self.menu.click(mousePos(), mouseButtons())
            self.selectionIndex = newIndex if newIndex else self.selectionIndex

    def mouseOnObject(self):
        for sprite in self.canvasGroup:
            if sprite.rect.collidepoint(mousePos()):
                return sprite

    def canvaseRemove(self):
        if mouseButtons()[2] and not self.menu.rect.collidepoint(mousePos()):
            # tiles
            if self.canvasData:
                currentPos = self.getCurrentPos()
                if currentPos in self.canvasData:
                    self.canvasData[currentPos].removeId(self.selectionIndex)
                    if self.canvasData[currentPos].isEmpty:
                        del self.canvasData[currentPos]

                    self.checkNeighbors(currentPos)

            # objects
            objectSelected = self.mouseOnObject()
            if objectSelected and not objectSelected.tileId == 0 and not objectSelected.tileId == 1:
                objectSelected.kill()

    def selectObject(self, event):
        for sprite in self.canvasGroup:
            if event.type == pygame.MOUSEBUTTONDOWN and mouseButtons()[0] and sprite.rect.collidepoint(mousePos()):
                self.activeDragObject = True
                sprite.startDrag()

            if event.type == pygame.MOUSEBUTTONUP and self.activeDragObject:
                if sprite.selected:
                    sprite.endDrag(self.origin)
                    self.activeDragObject = False

    # drawing
    def drawTileLines(self):
        cols = WINDOW_WIDTH // TILE_SIZE
        rows = WINDOW_HEIGHT // TILE_SIZE

        originOffset = vector(
            x=self.origin.x - int(self.origin.x / TILE_SIZE) * TILE_SIZE,
            y=self.origin.y - int(self.origin.y / TILE_SIZE) * TILE_SIZE)

        self.supportLineSurface.fill('green')

        for col in range(cols + 1):
            x = originOffset.x + col * TILE_SIZE
            pygame.draw.line(self.supportLineSurface, LINE_COLOR,
                             (x, 0), (x, WINDOW_HEIGHT))

        for row in range(rows + 1):
            y = originOffset.y + row * TILE_SIZE
            pygame.draw.line(self.supportLineSurface, LINE_COLOR,
                             (0, y), (WINDOW_WIDTH, y))

        self.displySurface.blit(self.supportLineSurface, (0, 0))

    def drawLevel(self):
        self.background.draw(self.displySurface)

        for cellPos, tile in self.canvasData.items():
            pos = self.origin + vector(cellPos) * TILE_SIZE

            # water
            if tile.hasWater:
                if tile.waterOnTop:
                    self.displySurface.blit(self.waterBottom, pos)
                else:
                    frame = self.animations[3]['frames']
                    index = int(self.animations[3]['frameIndex'])
                    self.displySurface.blit(frame[index], pos)

            # terrain
            if tile.hasTerrain:
                tileString = ''.join(tile.terrainNeighbors)
                terrainStyle = tileString if tileString in self.landTiles else 'X'
                self.displySurface.blit(self.landTiles[terrainStyle], pos)

            # coin
            if tile.coin:
                frame = self.animations[tile.coin]['frames']
                index = int(self.animations[tile.coin]['frameIndex'])
                surf = frame[index]
                rect = surf.get_rect(
                    center=(pos[0] + TILE_SIZE/2, pos[1] + TILE_SIZE/2))
                self.displySurface.blit(surf, rect)

            # enemy
            if tile.enemy:
                frame = self.animations[tile.enemy]['frames']
                index = int(self.animations[tile.enemy]['frameIndex'])
                surf = frame[index]
                rect = surf.get_rect(midbottom=(
                    pos[0] + TILE_SIZE/2, pos[1] + TILE_SIZE))
                self.displySurface.blit(surf, rect)

        self.forground.draw(self.displySurface)

    def preview(self):
        objectSelected = self.mouseOnObject()
        if not self.menu.rect.collidepoint(mousePos()):
            if objectSelected:
                rect = objectSelected.rect.inflate(10, 10)
                color = 'black'
                width = 3
                size = 15

                pygame.draw.lines(self.displySurface, color,
                                  False, [(rect.topleft[0], rect.topleft[1] + size), rect.topleft, (rect.topleft[0] + size, rect.topleft[1])], width)
                pygame.draw.lines(self.displySurface, color,
                                  False, [(rect.topright[0], rect.topright[1] + size), rect.topright, (rect.topright[0] - size, rect.topright[1])], width)
                pygame.draw.lines(self.displySurface, color,
                                  False, [(rect.bottomleft[0], rect.bottomleft[1] - size), rect.bottomleft, (rect.bottomleft[0] + size, rect.bottomleft[1])], width)
                pygame.draw.lines(self.displySurface, color,
                                  False, [(rect.bottomright[0], rect.bottomright[1] - size), rect.bottomright, (rect.bottomright[0] - size, rect.bottomright[1])], width)
            else:
                image = self.previewSurf[self.selectionIndex].copy()
                image.set_alpha(200)

                if EDITOR_DATA[self.selectionIndex]['type'] == 'tile':
                    currentPos = self.getCurrentPos()
                    rect = image.get_rect(
                        topleft=(self.origin + vector(currentPos) * TILE_SIZE))
                else:
                    rect = image.get_rect(center=mousePos())

                self.displySurface.blit(image, rect)

    def displaySky(self, deltaTime):
        self.displySurface.fill(SKY_COLOR)
        y = self.skyHandle.rect.centery

        # horizen lines
        if y > 0:
            horizenRect1 = pygame.Rect(0, y - 10, WINDOW_WIDTH, 10)
            horizenRect2 = pygame.Rect(0, y - 16, WINDOW_WIDTH, 4)
            horizenRect3 = pygame.Rect(0, y - 20, WINDOW_WIDTH, 2)
            pygame.draw.rect(self.displySurface,
                             HORIZON_TOP_COLOR, horizenRect1)
            pygame.draw.rect(self.displySurface,
                             HORIZON_TOP_COLOR, horizenRect2)
            pygame.draw.rect(self.displySurface,
                             HORIZON_TOP_COLOR, horizenRect3)

            self.displayClouds(deltaTime, y)

        # sea
        if 0 < y < WINDOW_HEIGHT:
            seaRect = pygame.Rect(0, y, WINDOW_WIDTH, WINDOW_HEIGHT)
            pygame.draw.rect(self.displySurface, SEA_COLOR, seaRect)
            pygame.draw.line(self.displySurface, HORIZON_COLOR,
                             (0, y), (WINDOW_WIDTH, y), 3)
        if y < 0:
            self.displySurface.fill(SEA_COLOR)

    def displayClouds(self, deltaTime, horizenY):
        for cloud in self.currentClouds:
            cloud['pos'][0] -= cloud['speed'] * deltaTime
            x = cloud['pos'][0]
            y = horizenY - cloud['pos'][1]
            self.displySurface.blit(cloud['surf'], (x, y))

    def createClouds(self, event):
        if event.type == self.cloudTimer:
            surf = random.choice(self.cloudsSurf)
            if random.randint(0, 4) < 2:
                pygame.transform.scale2x(surf)
            speed = random.randint(20, 50)
            pos = [WINDOW_WIDTH +
                   random.randint(50, 100), random.randint(0, WINDOW_HEIGHT)]

            self.currentClouds.append(
                {'surf': surf, 'pos': pos, 'speed': speed})

            self.removeClouds()

    def startClouds(self):
        for cloud in range(20):
            surf = random.choice(self.cloudsSurf)
            if random.randint(0, 4) < 2:
                pygame.transform.scale2x(surf)
            pos = [random.randint(0, WINDOW_WIDTH),
                   random.randint(0, WINDOW_HEIGHT)]
            speed = random.randint(20, 50)

            self.currentClouds.append(
                {'surf': surf, 'pos': pos, 'speed': speed})

    def removeClouds(self):
        for cloud in self.currentClouds:
            if cloud['pos'][0] <= -cloud['surf'].get_width():
                self.currentClouds.remove(cloud)

    # update
    def run(self, deltaTime):
        self.eventLoop()

        # udpate
        self.animationUpdate(deltaTime)
        self.canvasGroup.update(deltaTime)
        self.timerObject.update()

        # draw
        self.displySurface.fill('white')
        self.displaySky(deltaTime)
        self.drawLevel()
        self.drawTileLines()
        # pygame.draw.circle(self.displySurface, 'red', self.origin, 10)
        self.menu.display(self.selectionIndex)
        self.preview()


class CanvasTile:
    def __init__(self, tileId, offset=vector()):
        # terrain
        self.hasTerrain = False
        self.terrainNeighbors = []

        # water
        self.hasWater = False
        self.waterOnTop = False

        # coin
        self.coin = None

        # enemy
        self.enemy = None

        # objects
        self.objects = []

        self.addId(tileId, offset)
        self.isEmpty = False

    def addId(self, tileId, offset=vector()):
        options = {key: value['style'] for key, value in EDITOR_DATA.items()}
        match options[tileId]:
            case 'terrain': self.hasTerrain = True
            case 'water': self.hasWater = True
            case 'coin': self.coin = tileId
            case 'enemy': self.enemy = tileId
            case _:
                if (tileId, offset) not in self.objects:
                    self.objects.append((tileId, offset))

    def removeId(self, tileId):
        options = {key: value['style'] for key, value in EDITOR_DATA.items()}
        match options[tileId]:
            case 'terrain': self.hasTerrain = False
            case 'water': self.hasWater = False
            case 'coin': self.coin = None
            case 'enemy': self.enemy = None
        self.checkContent()

    def checkContent(self):
        if not self.hasTerrain and not self.hasWater and not self.coin and not self.enemy:
            self.isEmpty = True

    def getWater(self):
        if self.waterOnTop:
            return 'bottom'
        else:
            return 'top'

    def getTerrain(self):
        return ''.join(self.terrainNeighbors)


class CanvasObject(pygame.sprite.Sprite):
    def __init__(self, pos, frames, tileId, origin, group):
        super().__init__(group)
        self.tileId = tileId

        # animation
        self.frames = frames
        self.frameIndex = 0

        self.image = self.frames[int(self.frameIndex)]
        self.rect = self.image.get_rect(center=(pos))

        # movment
        self.distaceToOrigin = vector(self.rect.topleft) - origin
        self.selected = False
        self.mouseOffset = vector()

    def startDrag(self):
        self.selected = True
        self.mouseOffset = vector(mousePos()) - vector(self.rect.topleft)

    def drag(self):
        if self.selected:
            self.rect.topleft = vector(mousePos()) - self.mouseOffset

    def endDrag(self, origin):
        self.selected = False
        self.distaceToOrigin = vector(self.rect.topleft) - origin

    def panPos(self, origin):
        pos = origin + self.distaceToOrigin
        self.rect.topleft = pos

    def animate(self, deltaTime):
        self.frameIndex += ANIMATION_SPEED * deltaTime
        if self.frameIndex >= len(self.frames):
            self.frameIndex = 0
        self.image = self.frames[int(self.frameIndex)]
        self.rect = self.image.get_rect(midbottom=(self.rect.midbottom))

    def update(self, deltaTime):
        self.animate(deltaTime)
        self.drag()
