import pygame
from os import walk


def importFolder(path):
    surfList = []

    for foldername, subFolders, imgFiles in walk(path):
        for imgName in imgFiles:
            fullPath = f'{path}/{imgName}'
            image = pygame.image.load(fullPath).convert_alpha()
            surfList.append(image)

    return surfList


def importFolderDict(path):
    surfDict = {}

    for foldername, subFolders, imgFiles in walk(path):
        for imgName in imgFiles:
            fullPath = f'{path}/{imgName}'
            image = pygame.image.load(fullPath).convert_alpha()
            surfDict[imgName.split('.')[0]] = image

    return surfDict
