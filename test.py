import pygame
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Key Event Test")

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            print("KEYDOWN:", event.key)
        elif event.type == KEYUP:
            print("KEYUP:", event.key)
