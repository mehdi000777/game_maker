import pygame


class Timer():
    def __init__(self, duration):
        self.duration = duration
        self.active = False
        self.startTime = 0

    def activat(self):
        self.active = True
        self.startTime = pygame.time.get_ticks()

    def deActivat(self):
        self.active = False
        self.startTime = 0

    def update(self):
        currentTime = pygame.time.get_ticks()
        if currentTime - self.startTime >= self.duration:
            self.deActivat()