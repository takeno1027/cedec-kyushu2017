#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
"""
Name: blockgame.py
Author:tomita
Date: 2017/10/20(Fri) AM 09:48:18
Description:

ゲームを作りながら楽しく学べるPythonプログラミング 田中 賢一郎  (著)
のブロック崩しゲームを Maya Pythonの学習用にアレンジ

"""
########################################################################
import sys
import os

import maya.cmds as cmds

import math
import random

from PyQtUtil import QtCore, QtWidgets, getMayaMainWindow

DISPLAY_SIZE = (600, 800)

class Rect(object):
    def __init__(self,left,top,width,height, depth = -1, isball = False):
        self.halfwidth  = width / 2
        self.halfheight = height / 2

        if depth == -1:
            depth = height
        
        self.width  = width
        self.height = height
        
        if not isball:
            self.model = cmds.polyCube(w = width, h = height, d = depth)[0]
        else:
            self.model = cmds.polySphere(r = width / 2, sx = 20, sy = 20, ax = [0,1,0])[0]
        
        self.centerx = left + self.halfwidth
        self.centery = top  + self.halfheight
        
    @property
    def centerx(self):
        try:
            x = cmds.getAttr('%s.tx' % self.model)
            return x
        except:
            return 0
        
    @centerx.setter
    def centerx(self,value):
        x = value
        try:
            cmds.setAttr('%s.tx' % self.model,x)
        except:
            pass
        
    @property
    def centery(self):
        try:
            y = cmds.getAttr('%s.ty' % self.model)
            return DISPLAY_SIZE[1] - y
        except:
            return 0
    
    @centery.setter
    def centery(self,value):
        y = DISPLAY_SIZE[1] - value
        try:
            cmds.setAttr('%s.ty' % self.model,y)
        except:
            pass
        
    def _aabb(self):
        x = self.centerx
        y = self.centery
        
        return ((x- self.halfwidth, y - self.halfheight),
                (x + self.halfwidth, y + self.halfheight))
    
    def colliderect(self,rect):
        a = rect._aabb()
        b = self._aabb()
        
        X = 0
        Y = 1
        MIN = 0
        MAX = 1
        
        if a[MAX][X] < b[MIN][X] or a[MIN][X] > b[MAX][X]: return False
        if a[MAX][Y] < b[MIN][Y] or a[MIN][Y] > b[MAX][Y]: return False
        
        return True
    
        
class Block(object):
    """ ブロック・ボール・パドルオブジェクト """
    def __init__(self, col, rect, speed=0):
        self.rect = rect
        self.speed = speed
        self.dir = random.randint(-45, 45) + 270
        
        lambert = cmds.shadingNode('lambert',asShader=True)
        lambertSG = '%sSG' % lambert
        cmds.sets(renderable = True,noSurfaceShader = True,empty=True,name = lambertSG)
        cmds.connectAttr('%s.outColor' % lambert, '%s.surfaceShader' % lambertSG)
        cmds.sets(self.rect.model,e = True, forceElement = lambertSG)
        cmds.setAttr('%s.colorR' % lambert,col[0] / 255.0)
        cmds.setAttr('%s.colorG' % lambert,col[1] / 255.0)
        cmds.setAttr('%s.colorB' % lambert,col[2] / 255.0)
        
    def move(self):
        """ ボールを動かす """
        self.rect.centerx += math.cos(math.radians(self.dir)) * self.speed
             
        self.rect.centery -= math.sin(math.radians(self.dir)) * self.speed

        
    def hide(self):
        try:
            cmds.setAttr('%s.visibility' % self.rect.model,False)
        except:
            pass
    

KEYDOWN = 2
K_RIGHT = 275
K_LEFT  = 276

def tick():
    """ 毎フレーム処理 """
    global BLOCKS,gameStarted
    
    if event.type == KEYDOWN:
        if event.key == K_LEFT:
            PADDLE.rect.centerx -= 10
            
        elif event.key == K_RIGHT:
            PADDLE.rect.centerx += 10

    if not gameStarted:
        return
    
    if BALL.rect.centery < 1000:
        BALL.move()
    
    # ブロックと衝突？
    prevlen = len(BLOCKS)
    
    tmpBLOCKS = list(BLOCKS)
    BLOCKS = []
    
    for block in tmpBLOCKS:
        if block.rect.colliderect(BALL.rect):
            block.hide()
        else:
            BLOCKS.append(block)
    
    if len(BLOCKS) != prevlen:
        BALL.dir *= -1

    # パドルと衝突？
    if PADDLE.rect.colliderect(BALL.rect):
        BALL.dir = 90 + (PADDLE.rect.centerx - BALL.rect.centerx) / PADDLE.rect.width * 80
    
    # 壁と衝突？
    if BALL.rect.centerx < 0 or BALL.rect.centerx > 600:
        BALL.dir = 180 - BALL.dir
    if BALL.rect.centery < 0:
        BALL.dir = -BALL.dir
        BALL.speed += 1
    
class Event(object):
    def __init__(self):
        self.type = 0
        self.key = 0
    
class EventFilter(QtCore.QObject):
    global timer,event
    
    def eventFilter(self,qObj,evt):
        stat = QtCore.QObject.eventFilter(self,qObj,evt)
        evtTyp = evt.type()
        
        event.type = 0
        
        if evtTyp == QtCore.QEvent.KeyPress:
            if evt.key() == QtCore.Qt.Key_Left:
                event.type = KEYDOWN
                event.key = K_LEFT
                
            elif evt.key() == QtCore.Qt.Key_Right:
                event.type = KEYDOWN
                event.key = K_RIGHT
            
        elif evtTyp == QtCore.QEvent.Close:
            timer.stop()
        
        return stat
    
def init():
    global BLOCKS,PADDLE,BALL
    
    PADDLE = Block((242, 242, 0), Rect(300, 700, 100, 30))
    BALL = Block((242, 242, 0), Rect(300, 400, 20, 20, isball = True), 5)
    
    colors = [(255, 0, 0), (255, 165, 0), (242, 242, 0),
              (0, 128, 0), (128, 0, 128), (0, 0, 250)]
    
    BLOCKS = []
    
    for ypos, color in enumerate(colors, start=0):
        for xpos in range(0, 5):
            BLOCKS.append(Block(color,
                                Rect(xpos * 100 + 60, ypos * 50 + 40, 80, 30)))
    
    # 壁
    Rect(-20,-20,10,DISPLAY_SIZE[1],10)
    Rect(DISPLAY_SIZE[0]+10,-20,10,DISPLAY_SIZE[1],10)
    Rect(-10,-20,DISPLAY_SIZE[0]+ 20,10,10)
    
    
def clean():
    cmds.file(f = True, new = True)
    
def main():
    global window,timer,event,eventFilter,gameStarted

    gameStarted = False
    
    init()
    
    event = Event()
    
    window = QtWidgets.QMainWindow(parent = getMayaMainWindow())    
    window.setFixedWidth(500)
    window.setWindowTitle(u'九州CEDEC ブロック崩しゲームデモ')
    
    button = QtWidgets.QPushButton(u'ゲームスタート',parent = window)
    
    def startGame():
        global gameStarted,BALL
        gameStarted = True
        
        BALL.rect.centerx = 300
        BALL.rect.centery = 400
        BALL.speed = 5
        
        
        
    button.clicked.connect(startGame)
    
    eventFilter = EventFilter()
    window.installEventFilter(eventFilter)
    
    timer = QtCore.QTimer()
    timer.timeout.connect(tick)
    timer.start(1000 / 60.0)
    
    window.show()
    
    
    
    
    
    
    










