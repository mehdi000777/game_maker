import pygame
from pygame.math import Vector2 as vector
from timer import Timer
from random import choice

from settings import ANIMATION_SPEED, LEVEL_LAYERS, TILE_SIZE, WINDOW_WIDTH


class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, image, group, z=LEVEL_LAYERS['main']):
        super().__init__(group)
        self.pos = pos
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)
        self.z = z


class Block(Generic):
    def __init__(self, pos, size, group):
        image = pygame.Surface(size)
        super().__init__(pos, image, group)


class Animated(Generic):
    def __init__(self, pos, images, group, z=LEVEL_LAYERS['main']):
        self.animationFrames = images
        self.frameIndex = 0
        self.image = self.animationFrames[self.frameIndex]
        super().__init__(pos, self.image, group, z)

    def animate(self, deltaTime):
        self.frameIndex += ANIMATION_SPEED * deltaTime
        if self.frameIndex >= len(self.animationFrames):
            self.frameIndex = 0
        self.image = self.animationFrames[int(self.frameIndex)]

    def update(self, deltaTime):
        self.animate(deltaTime)


class Cloud(Generic):
    def __init__(self, pos, image, speed, group, levelLimit):
        super().__init__(pos, image, group, LEVEL_LAYERS['clouds'])

        # movment
        self.pos = vector(self.rect.topleft)
        self.speed = speed

        self.levelLimit = levelLimit

    def move(self, deltaTime):
        self.pos.x -= self.speed * deltaTime
        self.rect.x = round(self.pos.x)

    def removeCloud(self):
        if self.rect.x <= self.levelLimit:
            self.kill()

    def update(self, deltaTime):
        self.move(deltaTime)
        self.removeCloud()


class Player(Generic):
    def __init__(self, pos, group, collisionSprites, images, jumpSound):
        # animation
        self.animationFrames = images
        self.frameIndex = 0
        self.status = 'idle'
        self.orientation = 'right'
        surf = self.animationFrames[f'{self.status}_{self.orientation}'][self.frameIndex]
        super().__init__(pos, surf, group)

        # movment
        self.direction = vector()
        self.pos = vector(self.rect.center)
        self.speed = 300
        self.gravity = 4
        self.onFloor = False

        # collision
        self.collisionSprites = collisionSprites
        self.hitBox = self.rect.inflate(-50, 0)

        self.mask = pygame.mask.from_surface(self.image)
        self.invulTimer = Timer(200)

        self.jumpSound = jumpSound
        self.jumpSound.set_volume(0.2)

    def damage(self):
        if not self.invulTimer.active:
            self.invulTimer.activat()
            self.direction.y -= 1.5

    def getStatus(self):
        if self.direction.y < 0:
            self.status = 'jump'
        elif self.direction.y > 0 and not self.onFloor:
            self.status = 'fall'
        else:
            self.status = 'run' if self.direction.x != 0 else 'idle'

    def animate(self, deltaTime):
        self.frameIndex += ANIMATION_SPEED * deltaTime
        if self.frameIndex > len(self.animationFrames[f'{self.status}_{self.orientation}']):
            self.frameIndex = 0
        self.image = self.animationFrames[f'{self.status}_{self.orientation}'][int(
            self.frameIndex)]
        self.mask = pygame.mask.from_surface(self.image)

        if self.invulTimer.active:
            surf = self.mask.to_surface()
            surf.set_colorkey('black')
            self.image = surf

    def input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            self.direction.x = 1
            self.orientation = 'right'
        elif keys[pygame.K_LEFT]:
            self.direction.x = -1
            self.orientation = 'left'
        else:
            self.direction.x = 0

        if keys[pygame.K_UP] and self.onFloor:
            self.direction.y = -2
            self.jumpSound.play()

    def move(self, deltaTime):
        # horizontal
        self.pos.x += self.direction.x * self.speed * deltaTime
        self.hitBox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitBox.centerx
        self.checkCollision('horizontal')

        # vertical
        self.pos.y += self.direction.y * self.speed * deltaTime
        self.hitBox.centery = round(self.pos.y)
        self.rect.centery = self.hitBox.centery
        self.checkCollision('vertical')

    def applyGravity(self, deltaTime):
        self.direction.y += self.gravity * deltaTime
        self.rect.y += self.direction.y

    def chekcOnFloor(self):
        floorRect = pygame.Rect(
            self.hitBox.left, self.hitBox.bottom, self.hitBox.width, 2)
        floorSprites = [
            sprite for sprite in self.collisionSprites if sprite.rect.colliderect(floorRect)]
        self.onFloor = True if floorSprites else False

    def checkCollision(self, direction):
        for sprite in self.collisionSprites:
            if sprite.rect.colliderect(self.hitBox):
                if direction == 'horizontal':
                    self.hitBox.right = sprite.rect.left if self.direction.x > 0 else self.hitBox.right
                    self.hitBox.left = sprite.rect.right if self.direction.x < 0 else self.hitBox.left
                    self.rect.centerx, self.pos.x = self.hitBox.centerx, self.hitBox.centerx
                else:
                    self.hitBox.top = sprite.rect.bottom if self.direction.y < 0 else self.hitBox.top
                    self.hitBox.bottom = sprite.rect.top if self.direction.y > 0 else self.hitBox.bottom
                    self.rect.centery, self.pos.y = self.hitBox.centery, self.hitBox.centery
                    self.direction.y = 0

    def update(self, deltaTime):
        self.input()
        self.applyGravity(deltaTime)
        self.chekcOnFloor()
        self.move(deltaTime)
        self.invulTimer.update()

        self.getStatus()
        self.animate(deltaTime)


class Coin(Animated):
    def __init__(self, coinType, pos, images, group):
        super().__init__(pos, images, group)
        self.rect = self.image.get_rect(center=pos)
        self.coinType = coinType


class Particle(Animated):
    def __init__(self, pos, images, group):
        super().__init__(pos, images, group)
        self.rect = self.image.get_rect(center=pos)

    def animate(self, deltaTime):
        self.frameIndex += ANIMATION_SPEED * deltaTime
        if self.frameIndex < len(self.animationFrames):
            self.image = self.animationFrames[int(self.frameIndex)]
        else:
            self.kill()


class Spikes(Generic):
    def __init__(self, pos, image, group):
        super().__init__(pos, image, group)
        self.mask = pygame.mask.from_surface(self.image)


class Tooth(Generic):
    def __init__(self, pos, images, group, collisionSprites):
        self.orientation = 'right'
        self.frameIndex = 0
        self.animationFrames = images
        super().__init__(
            pos, self.animationFrames[f'run_{self.orientation}'][self.frameIndex], group)
        self.rect.bottom = self.rect.top + TILE_SIZE

        # movment
        self.direction = vector(choice((1, -1)), 0)
        self.orientation = 'right' if self.direction.x > 0 else 'left'
        self.pos = vector(self.rect.topleft)
        self.speed = 150
        self.collisionSprites = collisionSprites

        self.mask = pygame.mask.from_surface(self.image)

        if not [sprite for sprite in collisionSprites if sprite.rect.collidepoint(self.rect.midbottom + vector(0, 10))]:
            self.kill()

    def move(self, deltaTime):
        rightGap = self.rect.bottomright + vector(1, 1)
        rightBlock = self.rect.midright + vector(1, 0)
        leftGap = self.rect.bottomleft + vector(-1, 1)
        leftBlock = self.rect.midleft + vector(-1, 0)

        if self.direction.x > 0:
            if not [sprite for sprite in self.collisionSprites if sprite.rect.collidepoint(rightGap)]:
                self.direction = vector(-1, 0)
                self.orientation = 'left'

            if [sprite for sprite in self.collisionSprites if sprite.rect.collidepoint(rightBlock)]:
                self.direction = vector(-1, 0)
                self.orientation = 'left'
        else:
            if not [sprite for sprite in self.collisionSprites if sprite.rect.collidepoint(leftGap)]:
                self.direction = vector(1, 0)
                self.orientation = 'right'

            if [sprite for sprite in self.collisionSprites if sprite.rect.collidepoint(leftBlock)]:
                self.direction = vector(1, 0)
                self.orientation = 'right'

        self.pos.x += self.direction.x * self.speed * deltaTime
        self.rect.x = round(self.pos.x)

    def animate(self, deltaTime):
        animation = self.animationFrames[f'run_{self.orientation}']
        self.frameIndex += ANIMATION_SPEED * deltaTime
        if self.frameIndex >= len(animation):
            self.frameIndex = 0
        self.image = animation[int(self.frameIndex)]
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, deltaTime):
        self.move(deltaTime)
        self.animate(deltaTime)


class Shell(Generic):
    def __init__(self, orientation, pos, images, group, pearlImage, damageSprites):
        self.orientaion = orientation
        self.frameIndex = 0
        self.animationFrames = images.copy()
        if self.orientaion == 'right':
            for key, value in self.animationFrames.items():
                self.animationFrames[key] = [pygame.transform.flip(
                    image, True, False) for image in value]
        self.status = 'idle'
        super().__init__(
            pos, self.animationFrames[self.status][self.frameIndex], group)
        self.rect.bottom = self.rect.top + TILE_SIZE

        # pearl
        self.pearlImage = pearlImage
        self.hasShot = False
        self.attackCoolDown = Timer(2000)
        self.damageSprites = damageSprites

    def animate(self, deltaTime):
        animation = self.animationFrames[self.status]
        self.frameIndex += ANIMATION_SPEED * deltaTime
        if self.frameIndex >= len(animation):
            self.frameIndex = 0
            if self.hasShot:
                self.attackCoolDown.activat()
                self.hasShot = False
        self.image = animation[int(self.frameIndex)]

        if int(self.frameIndex) == 2 and self.status == 'attack' and not self.hasShot:
            pearlDirection = vector(
                1, 0) if self.orientaion == 'right' else vector(-1, 0)
            offset = pearlDirection * 50 + \
                vector(
                    0, -10) if self.orientaion == 'left' else pearlDirection * 20 + vector(0, -10)
            Pearl(self.rect.center + offset, self.pearlImage,
                  pearlDirection, [self.groups()[0], self.damageSprites])
            self.hasShot = True

    def getStatus(self):
        if abs(self.player.rect.centerx - self.rect.centerx) <= 500 and not self.attackCoolDown.active:
            self.status = 'attack'
        else:
            self.status = 'idle'

    def update(self, deltaTime):
        self.getStatus()
        self.animate(deltaTime)
        self.attackCoolDown.update()


class Pearl(Generic):
    def __init__(self, pos, image, direction, group):
        super().__init__(pos, image, group)

        # movment
        self.pos = vector(self.rect.topleft)
        self.direction = direction
        self.speed = 150

        # distruct
        self.timer = Timer(6000)
        self.timer.activat()

        self.mask = pygame.mask.from_surface(self.image)

    def update(self, deltaTime):
        # movment
        self.pos.x += self.direction.x * self.speed * deltaTime
        self.rect.x = round(self.pos.x)

        self.timer.update()
        if not self.timer.active:
            self.kill()
