import string
import tkinter
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageOps
import time
import math
from pympler import asizeof

#dataStatusImager -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class dataStatusImager:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, style, layer = 0):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height

        #Object Graphics Control
        self.canvas = canvas
        self.graphic = graphicsGenerator.generate_constantGraphic_TypeA_Images(style, width, height)
        self.canvasID = canvas.create_image(self.xPos, self.yPos, image = self.graphic, anchor = "nw", state = 'hidden') #Draw the button graphics
        self.layer = layer
        
    def processUserInput(self, event): return None

    def process(self): return None

    def show(self): self.canvas.itemconfigure(self.canvasID, state = 'normal')
    def hide(self): self.canvas.itemconfigure(self.canvasID, state = 'hidden')
#dataStatusImager END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------