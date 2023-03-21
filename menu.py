from operator import index
import pygame
from settings import *
from pygame.image import load as imageLoad


class Menu:
    def __init__(self):
        self.displaySurface = pygame.display.get_surface()
        self.createData()
        self.createButtons()

    def createData(self):
        self.menuSurfs = {}

        for key, value in EDITOR_DATA.items():
            if value['menu']:
                if not value['menu'] in self.menuSurfs:
                    self.menuSurfs[value['menu']] = [
                        (key, imageLoad(value['menu_surf']))]
                else:
                    self.menuSurfs[value['menu']].append(
                        (key, imageLoad(value['menu_surf'])))

    def createButtons(self):
        # menu area
        size = 180
        margin = 6
        topLeft = (WINDOW_WIDTH - size - margin, WINDOW_HEIGHT - size - margin)
        self.rect = pygame.Rect(topLeft, (size, size))
        # button area
        generic_button_rect = pygame.Rect(
            topLeft, (self.rect.width / 2, self.rect.height / 2))
        buttonMargin = 5
        self.tileButtonRect = generic_button_rect.copy().inflate(-buttonMargin, -buttonMargin)
        self.coinButtonRect = generic_button_rect.move(
            self.rect.width / 2, 0).inflate(-buttonMargin, -buttonMargin)
        self.enemyButtonRect = generic_button_rect.move(
            0, self.rect.height / 2).inflate(-buttonMargin, -buttonMargin)
        self.palmButtonRect = generic_button_rect.move(
            self.rect.width / 2, self.rect.height / 2).inflate(-buttonMargin, -buttonMargin)

        self.buttons = pygame.sprite.Group()
        Button(self.tileButtonRect, self.buttons, self.menuSurfs['terrain'])
        Button(self.coinButtonRect, self.buttons, self.menuSurfs['coin'])
        Button(self.enemyButtonRect, self.buttons, self.menuSurfs['enemy'])
        Button(self.palmButtonRect, self.buttons,
               self.menuSurfs['palm fg'], self.menuSurfs['palm bg'])

    def display(self, index):
        self.buttons.update()
        self.buttons.draw(self.displaySurface)
        self.highlightIndicator(index)

    def click(self, mousePos, mouseButton):
        for button in self.buttons:
            if button.rect.collidepoint(mousePos):
                if mouseButton[1]:
                    button.mainActive = not button.mainActive if button.items['alt'] else True
                if mouseButton[2]:
                    button.switch()
                return button.get_id()

    def highlightIndicator(self, index):
        if EDITOR_DATA[index]['menu'] == 'terrain':
            pygame.draw.rect(self.displaySurface,
                             BUTTON_LINE_COLOR, self.tileButtonRect.inflate(4, 4), 5, 4)
        if EDITOR_DATA[index]['menu'] == 'coin':
            pygame.draw.rect(self.displaySurface,
                             BUTTON_LINE_COLOR, self.coinButtonRect.inflate(4, 4), 5, 4)
        if EDITOR_DATA[index]['menu'] == 'enemy':
            pygame.draw.rect(self.displaySurface,
                             BUTTON_LINE_COLOR, self.enemyButtonRect.inflate(4, 4), 5, 4)
        if EDITOR_DATA[index]['menu'] == 'palm fg' or EDITOR_DATA[index]['menu'] == 'palm bg':
            pygame.draw.rect(self.displaySurface,
                             BUTTON_LINE_COLOR, self.palmButtonRect.inflate(4, 4), 5, 4)


class Button(pygame.sprite.Sprite):
    def __init__(self, rect, group, items, itemsAlt=None):
        super().__init__(group)
        self.image = pygame.Surface(rect.size)
        self.rect = rect

        # items
        self.items = {'main': items, 'alt': itemsAlt}
        self.index = 0
        self.mainActive = True

    def update(self):
        self.image.fill(BUTTON_BG_COLOR)
        surf = self.items['main' if self.mainActive else 'alt'][self.index][1]
        rect = surf.get_rect(
            center=(self.rect.width / 2, self.rect.height / 2))
        self.image.blit(surf, rect)

    def get_id(self):
        return self.items['main' if self.mainActive else 'alt'][self.index][0]

    def switch(self):
        if self.index < len(self.items['main' if self.mainActive else 'alt']) - 1:
            self.index += 1
        else:
            self.index = 0
