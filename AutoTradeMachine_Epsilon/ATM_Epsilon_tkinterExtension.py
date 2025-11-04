import string
import tkinter
from tkinter.tix import COLUMN
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageOps
import time
import math
from pympler import asizeof
import os

path_PROJECT = os.path.dirname(os.path.realpath(__file__))
path_IMAGES = os.path.join(path_PROJECT + r"\data\imgs")
path_SYSGRAPHICSLIBRARY = os.path.join(path_IMAGES, "sgl")

#Input Devices Control ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class tkE_userInput:
    def __init__(self, tk):
        # <mouseStatus> 
        #    [0]: MousePositionX
        #    [1]: MousePositionY
        #    [2]: LeftButtonStatus
        #    [3]: WheelButtonStatus
        #    [4]: RightButtonStatus
        self.mouseStatus = [0, 0, "DEFAULT", "DEFAULT", "DEFAULT"]
        XPOS = 0; YPOS = 1
        LEFTBUTTON  = 2; WHEELBUTTON = 3; RIGHTBUTTON = 4

        # <keyStat> 
        #[0]: shiftClicked
        #[1]: ctrlClicked
        self.keyStatus = [False, False]
        SHIFTCLICKED = 0; CTRLCLICKED = 1

        keyDictionary = {8:   "<BACKSPACE>",
                         9:   "<TAB>",
                         13:  "<ENTER>",
                         20:  "<CAPSLOCK>",
                         27:  "<ESCAPE>",
                         32:  "<SPACEBAR>",
                         33:  "<PAGEUP>",
                         34:  "<PAGEDOWN>",
                         35:  "<END>",
                         36:  "<HOME>",
                         37:  "<LEFT>",
                         38:  "<UP>",
                         39:  "<RIGHT>",
                         40:  "<DOWN>",
                         45:  "<INSERT>",
                         46:  "<DELETE>",
                         48:  "0",  1048: ")",
                         49:  "1",  1049: "!",
                         50:  "2",  1050: "@",
                         51:  "3",  1051: "#",
                         52:  "4",  1052: "$",
                         53:  "5",  1053: "%",
                         54:  "6",  1054: "^",
                         55:  "7",  1055: "&",
                         56:  "8",  1056: "*",
                         57:  "9",  1057: "(",
                         65:  "a",  1065: "A",
                         66:  "b",  1066: "B",
                         67:  "c",  1067: "C",
                         68:  "d",  1068: "D",
                         69:  "e",  1069: "E",
                         70:  "f",  1070: "F",
                         71:  "g",  1071: "G",
                         72:  "h",  1072: "H",
                         73:  "i",  1073: "I",
                         74:  "j",  1074: "J",
                         75:  "k",  1075: "K",
                         76:  "l",  1076: "L",
                         77:  "m",  1077: "M",
                         78:  "n",  1078: "N",
                         79:  "o",  1079: "O",
                         80:  "p",  1080: "P",
                         81:  "q",  1081: "Q",
                         82:  "r",  1082: "R",
                         83:  "s",  1083: "S",
                         84:  "t",  1084: "T",
                         85:  "u",  1085: "U",
                         86:  "v",  1086: "V",
                         87:  "w",  1087: "W",
                         88:  "x",  1088: "X",
                         89:  "y",  1089: "Y",
                         90:  "z",  1090: "Z",
                         96:  "0",  1096: "<INSERT>",
                         97:  "1",  1097: "<END>",
                         98:  "2",  1098: "<DOWN>",
                         99:  "3",  1099: "<PAGEDOWN>",
                         100: "4",  1100: "<LEFT>",
                         101: "5",  1101: "5",
                         102: "6",  1102: "<RIGHT>",
                         103: "7",  1103: "<HOME>",
                         104: "8",  1104: "<UP>",
                         105: "9",  1105: "<PAGEUP>",
                         106: "*",  1106: "*",
                         107: "+",  1107: "+",
                         109: "-",  1109: "-",
                         110: ".",  1110: "<DELETE>",
                         111: "/",  1111: "/",
                         186: ";",  1186: ":",
                         187: "=",  1187: "+",
                         188: ",",  1188: "<",
                         189: "-",  1189: "_",
                         190: ".",  1190: ">",
                         191: "/",  1191: "?",
                         192: "`",  1192: "~",
                         219: "[",  1219: "{",
                         220: "\\", 1220: "|",
                         221: "]",  1221: "}",
                         222: "'",  1222: "\"",
                         }

        self.eventLogger = list()

        def __mouseClicked(event):
            if   (event.num == 1): self.mouseStatus[LEFTBUTTON]  = "CLICKED"; self.eventLogger.append(("<MOUSE_LEFTBUTTON_CLICKED>",  event.x, event.y))
            elif (event.num == 2): self.mouseStatus[WHEELBUTTON] = "CLICKED"; self.eventLogger.append(("<MOUSE_WHEELBUTTON_CLICKED>", event.x, event.y))
            elif (event.num == 3): self.mouseStatus[RIGHTBUTTON] = "CLICKED"; self.eventLogger.append(("<MOUSE_RIGHTBUTTON_CLICKED>", event.x, event.y))
        def __mouseReleased(event):
            if   (event.num == 1): self.mouseStatus[LEFTBUTTON]  = "DEFAULT"; self.eventLogger.append(("<MOUSE_LEFTBUTTON_RELEASED>",  event.x, event.y))
            elif (event.num == 2): self.mouseStatus[WHEELBUTTON] = "DEFAULT"; self.eventLogger.append(("<MOUSE_WHEELBUTTON_RELEASED>", event.x, event.y))
            elif (event.num == 3): self.mouseStatus[RIGHTBUTTON] = "DEFAULT"; self.eventLogger.append(("<MOUSE_RIGHTBUTTON_RELEASED>", event.x, event.y))
        def __mouseMoved(event):
            self.mouseStatus[XPOS] = event.x; self.mouseStatus[YPOS] = event.y
            self.eventLogger.append(("<MOUSE_MOVED>", event.x, event.y))
        def __mouseWheelMoved(event):
            if   int(event.delta) == 120:
                if   (int(event.state) == 8): self.eventLogger.append(("<MOUSE_WHEEL_UP>", event.x, event.y))
                elif (int(event.state) == 9): self.eventLogger.append(("<MOUSE_WHEEL_RIGHT>", event.x, event.y))
            elif int(event.delta) == -120:
                if   (int(event.state) == 8): self.eventLogger.append(("<MOUSE_WHEEL_DOWN>", event.x, event.y))
                elif (int(event.state) == 9): self.eventLogger.append(("<MOUSE_WHEEL_LEFT>", event.x, event.y))
        def __keyClicked(event):
            if event.keycode in keyDictionary.keys():
                if (event.keycode < 48): lastClickedChar = keyDictionary[event.keycode]
                elif (48 <= event.keycode and event.keycode  <= 57)  or \
                     (65 <= event.keycode and event.keycode  <= 90)  or \
                     (96 <= event.keycode and event.keycode  <= 111) or \
                     (186 <= event.keycode and event.keycode <= 192) or \
                     (219 <= event.keycode and event.keycode <= 222):
                    if (self.keyStatus[SHIFTCLICKED] == True): lastClickedChar = keyDictionary[event.keycode + 1000]
                    else:                                      lastClickedChar = keyDictionary[event.keycode]
                lastClicked = keyDictionary[event.keycode]
                if (self.keyStatus[SHIFTCLICKED] == True): lastClicked = "<SHIFT>" + lastClicked
                if (self.keyStatus[CTRLCLICKED]  == True): lastClicked = "<CTRL>"  + lastClicked
                self.eventLogger.append(("KEY_CLICKED", lastClicked, lastClickedChar))
            else: print("KEY UNRECOGNIZABLE", event.keycode)
        def __keyReleased(event):
            if   event.keycode == 16: self.keyStatus[SHIFTCLICKED] = False;
            elif event.keycode == 17: self.keyStatus[CTRLCLICKED]  = False;
        def __keyPressed_SHIFT(event): self.keyStatus[SHIFTCLICKED] = True;
        def __keyPressed_CTRL(event):  self.keyStatus[CTRLCLICKED]  = True;
                
        tk.bind("<Button>", __mouseClicked)
        tk.bind("<ButtonRelease>", __mouseReleased)
        tk.bind("<Motion>", __mouseMoved)
        tk.bind("<MouseWheel>", __mouseWheelMoved)
        tk.bind("<Key>", __keyClicked)
        tk.bind("<KeyRelease>", __keyReleased)
        tk.bind("<Shift_L>", __keyPressed_SHIFT)
        tk.bind("<Shift_R>", __keyPressed_SHIFT)
        tk.bind("<Control_L>", __keyPressed_CTRL)
        tk.bind("<Control_R>", __keyPressed_CTRL)
        
    def isInputAvailable(self): return (len(self.eventLogger) > 0)
    def getEvent(self): return self.eventLogger.pop(0)
    def getMousePos(self): return (self.mouseStatus[0], self.mouseStatus[1])
#Input Devices Control END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




















#Graphical Objects ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#constantGraphic_TypeA -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class constantGraphic_typeA:
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
#passiveGraphic_TypeA END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#constantTextGraphic_TypeA ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class constantTextGraphic_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, style, layer = 0, text = "", textFill = "black", textSize = 12, textStrokeFill = (255, 255, 255, 255), textStrokeWidth = 0):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height

        #Object Graphics Control
        self.canvas = canvas
        self.graphic = graphicsGenerator.generate_constantTextGraphic_TypeA_Images(style, width, height, text, textFill, textSize, textStrokeFill, textStrokeWidth)
        self.canvasID = canvas.create_image(self.xPos, self.yPos, image = self.graphic, anchor = "nw", state = 'hidden') #Draw the button graphics
        self.layer = layer
        
    def processUserInput(self, event): return None

    def process(self): return None

    def show(self): self.canvas.itemconfigure(self.canvasID, state = 'normal')
    def hide(self): self.canvas.itemconfigure(self.canvasID, state = 'hidden')
#passiveTextGraphic_TypeA END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#constantImageGraphic_typeA -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class constantImageGraphic_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, style, imagePath, layer = 0, frameGOffset = 5):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height

        #Object Graphics Control
        self.canvas = canvas
        self.graphic = graphicsGenerator.generate_constantImageGraphic_TypeA_Images(style, width, height, imagePath)
        self.canvasID = canvas.create_image(self.xPos, self.yPos, image = self.graphic, anchor = "nw", state = 'hidden') #Draw the button graphics
        self.layer = layer
        
    def processUserInput(self, event): return None

    def process(self): return None

    def show(self): self.canvas.itemconfigure(self.canvasID, state = 'normal')
    def hide(self): self.canvas.itemconfigure(self.canvasID, state = 'hidden')
#constantImageGraphic_typeA END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#constantImageGraphic_typeB -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class constantImageGraphic_typeB:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, photoImage, layer = 0):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height

        #Object Graphics Control
        self.canvas = canvas
        self.photoImage = photoImage
        self.canvasID = canvas.create_image(self.xPos, self.yPos, image = self.photoImage, anchor = "nw", state = 'hidden') #Draw the button graphics
        self.layer = layer
        
    def processUserInput(self, event): return None

    def process(self): return None

    def show(self): self.canvas.itemconfigure(self.canvasID, state = 'normal')
    def hide(self): self.canvas.itemconfigure(self.canvasID, state = 'hidden')
#constantImageGraphic_typeB END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------










#button_TypeA -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class button_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, style, layer = 0, text = None, textSize = 12, mode = "DEFAULT"):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height
        self.textSize = textSize

        #Object Control Parameters
        self.mode = mode

        #Object Graphics Control
        self.canvas = canvas
        self.graphics = graphicsGenerator.generate_button_TypeA_Images(style, width, height, text, textSize)
        self.canvasID = canvas.create_image(self.xPos, self.yPos, image = self.graphics[self.mode], anchor = "nw", state = 'hidden') #Create Canvas Label
        self.layer = layer
        
    def processUserInput(self, event):
        if (self.mode == "DEFAULT"):
            if (event == "HOVERED"): self.mode = "HOVERED"; self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode]); return None
        elif (self.mode == "HOVERED"):
            if   (event == "ESCAPED"): self.mode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"):  self.mode = "CLICKED"; self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode]); return None
        elif (self.mode == "CLICKED"): 
            if   (event == "ESCAPED"):                        self.mode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_RELEASED>"): self.mode = "HOVERED"; self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode]); return "ACTIVATED"

    def process(self): return None

    def show(self): self.canvas.itemconfigure(self.canvasID, state = 'normal')
    def hide(self): self.canvas.itemconfigure(self.canvasID, state = 'hidden')
    def activate(self):   self.mode = "DEFAULT";  self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode])
    def deactivate(self): self.mode = "INACTIVE"; self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode])
#button_TypeA END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#switch_TypeA -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class switch_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, style, layer = 0, mode = "DEFAULT", status = False, align = "horizontal"):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height

        #Object Control Parameters
        self.mode = mode
        self.status = status

        #Object Graphics Control
        self.canvas = canvas
        self.graphics = graphicsGenerator.generate_switch_TypeA_Images(style, width, height, align)
        if (self.status == True): self.canvasID = canvas.create_image(self.xPos, self.yPos, image = self.graphics[self.mode + "_ON"],  anchor = "nw", state = 'hidden') #Create Canvas Label
        else:                     self.canvasID = canvas.create_image(self.xPos, self.yPos, image = self.graphics[self.mode + "_OFF"], anchor = "nw", state = 'hidden') #Create Canvas Label
        self.layer = layer
        
    def processUserInput(self, event):
        if (self.mode == "DEFAULT"):
            if (event == "HOVERED"): 
                self.mode = "HOVERED"; 
                if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);  return None
                else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]); return None
        elif (self.mode == "HOVERED"):
            if   (event == "ESCAPED"): 
                self.mode = "DEFAULT"
                if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);  return None
                else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"):  
                self.mode = "CLICKED"
                if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);  return None
                else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]); return None
        elif (self.mode == "CLICKED"): 
            if   (event == "ESCAPED"):                        
                self.mode = "DEFAULT"
                if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);  return None
                else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_RELEASED>"):
               self.mode = "HOVERED"
               self.status = not(self.status)
               if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);  return "SWITCHUPDATED"
               else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]); return "SWITCHUPDATED"

    def process(self): return None

    def setMode(self, status):
        self.status = status
        if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);
        else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]);
    def activate(self):
        self.mode = "DEFAULT"
        if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);
        else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]);
    def deactivate(self):
        self.mode = "INACTIVE"
        if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);
        else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]);
    def getStatus(self):
        return self.status

    def show(self): self.canvas.itemconfigure(self.canvasID, state = 'normal')
    def hide(self): self.canvas.itemconfigure(self.canvasID, state = 'hidden')
#switch_TypeA END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#switch_TypeB -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class switch_typeB:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, style, layer = 0, mode = "DEFAULT", status = False):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height

        #Object Control Parameters
        self.mode = mode
        self.status = status

        #Object Graphics Control
        self.canvas = canvas
        self.graphics = graphicsGenerator.generate_switch_TypeB_Images(style, width, height)
        if (self.status == True): self.canvasID = canvas.create_image(self.xPos, self.yPos, image = self.graphics[self.mode + "_ON"],  anchor = "nw", state = 'hidden') #Create Canvas Label
        else:                     self.canvasID = canvas.create_image(self.xPos, self.yPos, image = self.graphics[self.mode + "_OFF"], anchor = "nw", state = 'hidden') #Create Canvas Label
        self.layer = layer
        
    def processUserInput(self, event):
        if (self.mode == "DEFAULT"):
            if (event == "HOVERED"): 
                self.mode = "HOVERED"; 
                if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);  return None
                else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]); return None
        elif (self.mode == "HOVERED"):
            if   (event == "ESCAPED"): 
                self.mode = "DEFAULT"
                if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);  return None
                else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"):  
                self.mode = "CLICKED"
                if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);  return None
                else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]); return None
        elif (self.mode == "CLICKED"): 
            if   (event == "ESCAPED"):                        
                self.mode = "DEFAULT"
                if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);  return None
                else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_RELEASED>"):
               self.mode = "HOVERED"
               self.status = not(self.status)
               if (self.status == True): self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_ON"]);  return "SWITCHON"
               else:                     self.canvas.itemconfigure(self.canvasID, image = self.graphics[self.mode + "_OFF"]); return "SWITCHOFF"

    def process(self): return None

    def show(self): self.canvas.itemconfigure(self.canvasID, state = 'normal')
    def hide(self): self.canvas.itemconfigure(self.canvasID, state = 'hidden')

    def getStatus(self): return self.status
#switch_TypeB END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#activeTextBox_TypeA ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class activeTextBox_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, boxStyle, layer = 0, text = "", textSize = 12, textStyle = "generalText_StyleA", textAnchor = 'center'):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height
        self.text = text
        self.textSize = textSize
        self.textStyle = textStyle
        self.textAnchor = textAnchor

        #Object Graphics Control
        self.canvas = canvas
        self.graphicsGenerator = graphicsGenerator
        if (boxStyle == "empty"): self.canvasID_box = None
        else: 
            self.boxGraphic = graphicsGenerator.generate_constantGraphic_TypeA_Images(boxStyle, width, height)
            self.canvasID_box = canvas.create_image(self.xPos, self.yPos, image = self.boxGraphic, anchor = "nw", state = 'hidden')
        textStyleTheme = graphicsGenerator.getTextStyleThemeTk(textStyle); cTextFont = (textStyleTheme['fontFamily'], textSize, textStyleTheme['style'])
        self.canvasID_text = canvas.create_text(self.xPos + self.width / 2, (self.yPos + self.height / 2) + 1, text = text, fill = textStyleTheme['fill'], font = cTextFont, width = self.width, anchor = "center", state = 'hidden')
        self.layer = layer

    def processUserInput(self, event): return None

    def process(self): return None

    def show(self): 
        if (self.canvasID_box is not None): self.canvas.itemconfigure(self.canvasID_box, state = 'normal')
        self.canvas.itemconfigure(self.canvasID_text, state = 'normal')
    def hide(self): 
        if (self.canvasID_box is not None): self.canvas.itemconfigure(self.canvasID_box, state = 'hidden')
        self.canvas.itemconfigure(self.canvasID_text, state = 'hidden')

    def updateText(self, text):
        self.text = text
        self.canvas.itemconfigure(self.canvasID_text, text = text)
    def getText(self):
        return self.text
#activeTextBox_TypeA END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#LED_TypeA ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class LED_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, boxStyle, layer = 0, colors = dict(), mode = "OFF", status = False):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height

        #Object Graphics Control
        self.canvas = canvas
        self.graphicsGenerator = graphicsGenerator
        self.boxStyle = boxStyle
        
        self.LEDGraphics = dict()
        self.colorDict = dict()
        self.undefiendNameIndex = 0
        if ("OFF" not in colors.keys()): colors.update({"OFF": (0, 0, 0, 255)}); #If a unique 'colors' parameter is passed and does not contain a color for "OFF", add one
        for color in colors.keys(): 
            self.LEDGraphics[color] = graphicsGenerator.generate_LED_TypeA_Images(boxStyle, width, height, colors[color])
            self.colorDict[color] = colors[color]
        self.mode = mode
        self.status = status

        self.canvasID_LED = canvas.create_image(self.xPos, self.yPos, image = self.LEDGraphics[self.mode], anchor = "nw", state = 'hidden')

        self.layer = layer

    def processUserInput(self, event): return None
    def process(self): return None

    def show(self): self.canvas.itemconfigure(self.canvasID_LED, state = 'normal')
    def hide(self): self.canvas.itemconfigure(self.canvasID_LED, state = 'hidden')

    def updateColor(self, color):
        paramType = type(color)
        if (paramType is str):
            if (color in self.LEDGraphics.keys()):
                self.canvas.itemconfigure(self.canvasID_LED, image = self.LEDGraphics[color])
                self.mode = color
        elif (paramType is tuple):
            if (color in self.colorDict.values()): #If the color exists in the color Dictionary
                #Look for the key that has the color
                colorName = list(self.colorDict.keys())[list(self.colorDict.values()).index(color)]
                self.mode = colorName
                self.changeState(self.status)
            else: #If the color does not exist in the color Dictionary
                newColorName = "UNDEFINED" + str(self.undefiendNameIndex); self.undefiendNameIndex += 1
                self.LEDGraphics[newColorName] = self.graphicsGenerator.generate_LED_TypeA_Images(self.boxStyle, self.width, self.height, color)
                self.colorDict[newColorName] = color
                self.mode = newColorName
                self.changeState(self.status)

    def changeState(self, state):
        if   (state == True):     self.status = True
        elif (state == False):    self.status = False
        elif (state == "toggle"): self.status = not(self.status)
        if (self.status == True): self.canvas.itemconfigure(self.canvasID_LED, image = self.LEDGraphics[self.mode])
        else:                     self.canvas.itemconfigure(self.canvasID_LED, image = self.LEDGraphics["OFF"])

    def getColors(self): return (self.mode, self.colorDict.copy())

#LED_TypeA END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#gaugeBar_TypeA -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class gaugeBar_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, boxStyle = "empty", layer = 0, value = 0, gaugeColor = (200, 100, 100), gaugeGOffset = 5, align = "horizontal", showText = True, textStyle = "generalText_StyleA", textSize = None):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height

        #Object Graphics Control
        self.canvas = canvas
        self.graphicsGenerator = graphicsGenerator
        self.boxStyle = boxStyle
        self.gaugeGOffset = gaugeGOffset
        self.value = value
        self.align = align
        self.gaugeColor = gaugeColor
        self.zeroHide = (self.value == 0)
        self.showText = showText
        
        if (boxStyle == "empty"): 
            self.gaugeGOffset = 0
            self.canvasID_Box = None
        else:
            self.boxGraphic = graphicsGenerator.generate_constantGraphic_TypeA_Images(boxStyle, width, height)
            self.canvasID_Box = canvas.create_image(self.xPos, self.yPos, image = self.boxGraphic, anchor = "nw", state = 'hidden')
        if (self.align == "horizontal"): 
            self.canvasID_Gauge = canvas.create_rectangle(self.xPos + self.gaugeGOffset, 
                                                          self.yPos + self.gaugeGOffset, 
                                                          self.xPos + self.gaugeGOffset + (self.width - 2 * self.gaugeGOffset) * self.value / 100, 
                                                          self.yPos + self.height - self.gaugeGOffset,
                                                          fill = convertRGBtoHex(self.gaugeColor[0], self.gaugeColor[1], self.gaugeColor[2]), state = 'hidden', width = 0)
            if (textSize == None): textSize = round(self.height * 0.4)
            textStyleTheme = graphicsGenerator.getTextStyleThemeTk(textStyle); cTextFont = (textStyleTheme['fontFamily'], textSize, textStyleTheme['style'])
            self.canvasID_Text = canvas.create_text(self.xPos + self.width / 2, (self.yPos + self.height / 2) + 1, text = "", fill = textStyleTheme['fill'], font = cTextFont, width = self.width - 2 * self.gaugeGOffset, anchor = "center", state = 'hidden')
        elif (self.align == "vertical"):
            self.canvasID_Gauge = canvas.create_rectangle(self.xPos + self.gaugeGOffset, 
                                                         self.yPos + self.height - self.gaugeGOffset, 
                                                         self.xPos + self.width - self.gaugeGOffset, 
                                                         self.yPos + self.height - self.gaugeGOffset - (self.height - 2 * self.gaugeGOffset) * self.value / 100,
                                                         fill = convertRGBtoHex(self.gaugeColor[0], self.gaugeColor[1], self.gaugeColor[2]), state = 'hidden', width = 0)
            if (textSize == None): textSize = round(self.width * 0.3)
            textStyleTheme = graphicsGenerator.getTextStyleThemeTk(textStyle); cTextFont = (textStyleTheme['fontFamily'], textSize, textStyleTheme['style'])
            self.canvasID_Text = canvas.create_text(self.xPos + self.width / 2, (self.yPos + self.height / 2) + 1, text = "", fill = textStyleTheme['fill'], font = cTextFont, width = self.width - 2 * self.gaugeGOffset, anchor = "center", state = 'hidden')
        self.layer = layer

    def processUserInput(self, event): return None
    def process(self): return None

    def show(self):
        if (self.canvasID_Box != None): self.canvas.itemconfigure(self.canvasID_Box, state = 'normal')
        if (self.showText == True): self.canvas.itemconfigure(self.canvasID_Text, state = 'normal')
        if (self.zeroHide == False): self.canvas.itemconfigure(self.canvasID_Gauge, state = 'normal')
    def hide(self): 
        if (self.canvasID_Box != None): self.canvas.itemconfigure(self.canvasID_Box, state = 'hidden')
        if (self.showText == True): self.canvas.itemconfigure(self.canvasID_Text, state = 'hidden')
        self.canvas.itemconfigure(self.canvasID_Gauge, state = 'hidden')

    def updateValue(self, value):
        if   (value <= 0):   self.value = 0
        elif (100 <= value): self.value = 100
        else:                self.value = value
        if (value == 0): self.canvas.itemconfigure(self.canvasID_Gauge, state = 'hidden'); self.zeroHide = True
        else:
            if (self.align == "horizontal"): self.canvas.coords(self.canvasID_Gauge, self.xPos + self.gaugeGOffset, 
                                                                                     self.yPos + self.gaugeGOffset, 
                                                                                     self.xPos + self.gaugeGOffset + (self.width - 2 * self.gaugeGOffset) * self.value / 100, 
                                                                                     self.yPos + self.height - self.gaugeGOffset)
            elif (self.align == "vertical"): self.canvas.coords(self.canvasID_Gauge, self.xPos + self.gaugeGOffset, 
                                                                                     self.yPos + self.height - self.gaugeGOffset, 
                                                                                     self.xPos + self.width - self.gaugeGOffset, 
                                                                                     self.yPos + self.height - self.gaugeGOffset - (self.height - 2 * self.gaugeGOffset) * self.value / 100)
            if (self.zeroHide == True): self.canvas.itemconfigure(self.canvasID_Gauge, state = 'normal'); self.zeroHide = False
    def getValue(self): return self.value
    def updateText(self, text): self.canvas.itemconfigure(self.canvasID_Text, text = text)
    def showText(self): self.canvas.itemconfigure(self.canvasID_Text, state = 'normal'); self.showText = True
    def hideText(self): self.canvas.itemconfigure(self.canvasID_Text, text = 'hidden'); self.showText = False
    def changeColor(self, color): self.canvas.itemconfigure(self.canvasID_Gauge, fill = convertRGBtoHex(color[0], color[1], color[2]))
#gaugeBar_TypeA END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#textInputBox_TypeA -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class textInputBox_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, style, layer = 0, mode = "DEFAULT", textStyle = "generalText_StyleA", maxTextLength = 1000, insertModeMask = (255, 255, 255, 100), multiSelectMask = (160, 250, 140, 100), cursorColor = ((255, 255, 255, 255))):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height
        self.layer = layer

        #Object Control Parameters
        self.mode = mode

        #generate_characterImage(self, text, textSize, style = None, textFont = None, textFill = None, textStrokeFill = None, textStrokeWidth = None)

        #Object Graphics Control
        self.canvas = canvas
        self.graphicsGenerator = graphicsGenerator
        self.graphics = graphicsGenerator.generate_textInputBox_TypeA_Images(style, width, height)
        self.canvasID_objectBox = canvas.create_image(self.xPos, self.yPos, image = self.graphics[self.mode], anchor = "nw", state = 'hidden') #Create Canvas Label For Object Box

        #Text Control
        self.maxTextLength = maxTextLength
        self.emptyImage = ImageTk.PhotoImage(Image.new(mode = "RGBA", size = (1, 1), color = (0, 0, 0, 0)))
        self.text = list()
        self.canvasIDs_text = list()
        self.canvasIDs_text_availables = list()
        self.canvasIDs_text_taken = list()
        for i in range (self.maxTextLength): 
            self.canvasIDs_text.append(canvas.create_image(self.xPos, self.yPos, image = self.emptyImage, anchor = "nw", state = 'hidden'))
            self.canvasIDs_text_availables.append(i)

        self.caps_lock = False
        self.insert = False
        self.textSelectionIndex = [0, 0]
        self.cursorShow = False
        self.cursorTimerThreshold = 500 #in ms
        self.cursorTimerCounter = 0
        
        self.insertModeMask  = insertModeMask
        self.multiSelectMask = multiSelectMask
        
        self.textGOffset = 5
        self.textDisplayBoxSize = ((self.width - 2 * self.textGOffset), (self.height - 2 * self.textGOffset))
        self.textDisplayBoxPosition = 0
        self.textDisplayBoxAnchor = "left"
        self.textSize = int(self.textDisplayBoxSize[1] * 0.8)
        self.textStyle = textStyle
        self.textImageHeight = self.graphicsGenerator.generate_characterImage(" ", self.textSize, style = self.textStyle)[2]
        self.__updateTextGraphics()

        #Cursor Configuration
        cursorWidth = 1;
        self.cursorImage = ImageTk.PhotoImage(Image.new(mode = "RGBA", size = (cursorWidth, self.textDisplayBoxSize[1]), color = cursorColor))
        self.canvadID_cursor = (canvas.create_image(self.xPos + self.textGOffset, self.yPos + self.textGOffset, image = self.cursorImage, anchor = "nw", state = 'hidden'))

    def processUserInput(self, event):
        if (self.mode == "DEFAULT"):
            if (event == "HOVERED"): self.mode = "HOVERED"; self.canvas.itemconfigure(self.canvasID_objectBox, image = self.graphics[self.mode]); return None
        elif (self.mode == "HOVERED"):
            if   (event == "ESCAPED"): self.mode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_objectBox, image = self.graphics[self.mode]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"):  
                self.mode = "CLICKED"
                self.canvas.itemconfigure(self.canvasID_objectBox, image = self.graphics[self.mode])
                self.__calcCursorWithMouse(event[1])
                return None
        elif (self.mode == "CLICKED"):
            if (event[0] == "<MOUSE_LEFTBUTTON_RELEASED>"): 
                self.mode = "READING"
                self.canvas.itemconfigure(self.canvasID_objectBox, image = self.graphics[self.mode])
                return None
            elif (event[0] == "<MOUSE_MOVED>"):
                self.__calcCursorWithMouse(event[1], clicked = False)
                return None
            elif (event == "ESCAPED"): return "SUBSCRIBEUSERINPUT"
            elif (event == "HOVERED"): return "UNSUBSCRIBEUSERINPUT"
        elif (self.mode == "READING"):
            if   (event == "ESCAPED"): return "SUBSCRIBEUSERINPUT"
            elif (event == "HOVERED"): return "UNSUBSCRIBEUSERINPUT"
            elif (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"): 
                #If Clicked Inside this Object
                if ((self.xPos < event[1]) and (event[1] < self.xPos + self.width) and (self.yPos < event[2]) and (event[2] < self.yPos + self.height)):
                    self.mode = "CLICKED"
                    self.canvas.itemconfigure(self.canvasID_objectBox, image = self.graphics[self.mode])
                    self.__calcCursorWithMouse(event[1])
                    return None
                #If Clicked Outside this Object
                else: 
                    self.mode = "DEFAULT"
                    self.canvas.itemconfigure(self.canvasID_objectBox, image = self.graphics[self.mode])
                    if (self.textSelectionIndex[0] == self.textSelectionIndex[1]):
                        if ((self.insert == True) and (self.textSelectionIndex[0] < len(self.text))):
                            self.text[self.textSelectionIndex[0]][4] = 1
                    else: 
                        if self.textSelectionIndex[0] > self.textSelectionIndex[1]: textSelectionIndex = (self.textSelectionIndex[1], self.textSelectionIndex[0])
                        else:                                                       textSelectionIndex = (self.textSelectionIndex[0], self.textSelectionIndex[1])
                        for targetText in self.text[textSelectionIndex[0]:textSelectionIndex[1]]: targetText[4] = 1
                    self.textSelectionIndex = [0, 0]
                    self.__updateTextDisplayBoxPosition("cursor_moved_right")
                    self.__updateTextGraphics()
                    self.__hideCursor()
                    return "UNSUBSCRIBEUSERINPUT"
            elif (event[0] == "KEY_CLICKED"):
                #Special Cursor Navigation - Place topmost due to condition checkings in 'Text Edit'
                #'CTRL' + 's' Keys Clicked
                if (event[1] == "<CTRL>a"):
                    for targetText in self.text: targetText[4] = 2
                    self.textSelectionIndex = [0, len(self.text)]
                    self.__updateTextDisplayBoxPosition("cursor_moved_right")
                    self.__updateTextGraphics()
                #Text Edit
                elif ((event[2]) in self.graphicsGenerator.allCharSamples):   self.__editText("add", event[2]); return "TEXTUPDATED"
                elif (event[1] == "<SPACEBAR>"):                              self.__editText("add", " ");      return "TEXTUPDATED"
                elif (event[1] == "<TAB>"):                                   self.__editText("add", "   ");    return "TEXTUPDATED"
                elif (event[1] == "<DELETE>") or (event[1] == "<BACKSPACE>"): self.__editText("remove");        return "TEXTUPDATED"
                #Cursor Navigation
                #'LEFT' Key Clicked
                elif (event[1] == "<LEFT>"):
                    if (self.textSelectionIndex[0] == self.textSelectionIndex[1]):
                        if (self.textSelectionIndex[0] > 0): 
                            self.textSelectionIndex[0] -= 1; self.textSelectionIndex[1] -= 1
                            if (self.insert == True): #Insert Mode Control
                                self.text[self.textSelectionIndex[0]][4] = 3; 
                                if (self.textSelectionIndex[0] < len(self.text)):
                                    if ((self.textSelectionIndex[0] + 1) < len(self.text)):
                                        self.text[self.textSelectionIndex[0] + 1][4] = 1
                                    self.__hideCursor()
                            self.__updateTextDisplayBoxPosition("cursor_moved_left")
                            self.__updateTextGraphics()
                    else:
                        if self.textSelectionIndex[0] > self.textSelectionIndex[1]: textSelectionIndex = (self.textSelectionIndex[1], self.textSelectionIndex[0])
                        else:                                                       textSelectionIndex = (self.textSelectionIndex[0], self.textSelectionIndex[1])
                        for targetText in self.text[textSelectionIndex[0]:textSelectionIndex[1]]: targetText[4] = 1
                        self.textSelectionIndex = [textSelectionIndex[0], textSelectionIndex[0]]
                        if (self.insert == True):
                            self.text[self.textSelectionIndex[0]][4] = 3
                            self.__hideCursor()
                        self.__updateTextDisplayBoxPosition("cursor_moved_left")
                        self.__updateTextGraphics()
                #'RIGHT' Key Clicked
                elif (event[1] == "<RIGHT>"):
                    if (self.textSelectionIndex[0] == self.textSelectionIndex[1]):
                        if (self.textSelectionIndex[0] < len(self.text)): 
                            self.textSelectionIndex[0] += 1; self.textSelectionIndex[1] += 1
                            if (self.insert == True): #Insert Mode Control
                                if (self.textSelectionIndex[0] < len(self.text)): 
                                    self.text[self.textSelectionIndex[0]][4] = 3;
                                    self.__hideCursor()
                                elif (self.textSelectionIndex[0] == len(self.text)):
                                    self.__showCursor()
                                self.text[self.textSelectionIndex[0] - 1][4] = 1
                            self.__updateTextDisplayBoxPosition("cursor_moved_right")
                            self.__updateTextGraphics()
                    else:
                        if self.textSelectionIndex[0] > self.textSelectionIndex[1]: textSelectionIndex = (self.textSelectionIndex[1], self.textSelectionIndex[0])
                        else:                                                       textSelectionIndex = (self.textSelectionIndex[0], self.textSelectionIndex[1])
                        for targetText in self.text[textSelectionIndex[0]:textSelectionIndex[1]]: targetText[4] = 1
                        self.textSelectionIndex = [textSelectionIndex[1], textSelectionIndex[1]]
                        if (self.insert == True):
                            if ((self.textSelectionIndex[0]) < len(self.text)):
                                self.text[self.textSelectionIndex[0]][4] = 3
                                self.__hideCursor()
                            elif (self.textSelectionIndex[0] == len(self.text)):
                                self.__showCursor()
                        self.__updateTextDisplayBoxPosition("cursor_moved_right")
                        self.__updateTextGraphics()
                #'SHIFT' + 'LEFT' Keys Clicked
                elif (event[1] == "<SHIFT><LEFT>"):
                    if (self.textSelectionIndex[1] > 0):
                        self.textSelectionIndex[1] -= 1
                        if (self.insert == True):
                            if (self.textSelectionIndex[0] == self.textSelectionIndex[1]): 
                                self.text[self.textSelectionIndex[0]][4] = 3
                                self.__hideCursor()
                            else:
                                if (self.textSelectionIndex[0] == self.textSelectionIndex[1] + 1): 
                                    if (self.textSelectionIndex[0] != len(self.text)): self.text[self.textSelectionIndex[0]][4] = 1
                                    self.text[self.textSelectionIndex[1]][4] = 2
                                elif (self.textSelectionIndex[1] < self.textSelectionIndex[0]):    self.text[self.textSelectionIndex[1]][4] = 2
                                else:                                                              self.text[self.textSelectionIndex[1]][4] = 1
                                if (self.textSelectionIndex[0] != self.textSelectionIndex[1]): self.__showCursor()
                        else:
                            if (self.textSelectionIndex[1] < self.textSelectionIndex[0]): self.text[self.textSelectionIndex[1]][4] = 2
                            else:                                                         self.text[self.textSelectionIndex[1]][4] = 1
                        self.__updateTextDisplayBoxPosition("cursor_moved_left")
                        self.__updateTextGraphics()
                #'SHIFT' + 'RIGHT' Keys Clicked
                elif (event[1] == "<SHIFT><RIGHT>"):
                    if (self.textSelectionIndex[1] < len(self.text)): 
                        self.textSelectionIndex[1] += 1
                        if (self.insert == True):
                            if (self.textSelectionIndex[0] == self.textSelectionIndex[1]):
                                self.__hideCursor()
                                self.text[self.textSelectionIndex[0]][4] = 3
                            else:
                                self.__showCursor()
                        if (self.textSelectionIndex[1] > self.textSelectionIndex[0]): self.text[self.textSelectionIndex[1] - 1][4] = 2
                        else:                                                         self.text[self.textSelectionIndex[1] - 1][4] = 1
                        self.__updateTextDisplayBoxPosition("cursor_moved_right")
                        self.__updateTextGraphics()
                #'HOME' Key Clicked
                elif (event[1] == "<HOME>"):
                    if self.textSelectionIndex[0] > self.textSelectionIndex[1]: textSelectionIndex = (self.textSelectionIndex[1], self.textSelectionIndex[0])
                    else:                                                       textSelectionIndex = (self.textSelectionIndex[0], self.textSelectionIndex[1])
                    if (textSelectionIndex[0] == textSelectionIndex[1]):
                        if (self.insert == True):
                            if (len(self.text) != 0):
                                if not(self.textSelectionIndex[0] == len(self.text)): self.text[self.textSelectionIndex[0]][4] = 1
                                else:                                                 self.__hideCursor()
                                self.text[0][4] = 3
                    else:
                        for targetText in self.text[textSelectionIndex[0]:textSelectionIndex[1]]: targetText[4] = 1
                    self.textSelectionIndex = [0, 0]
                    self.__updateTextDisplayBoxPosition("cursor_moved_left")
                    self.__updateTextGraphics()
                #'END' Key Clicked
                elif (event[1] == "<END>"):
                    if self.textSelectionIndex[0] > self.textSelectionIndex[1]: textSelectionIndex = (self.textSelectionIndex[1], self.textSelectionIndex[0])
                    else:                                                       textSelectionIndex = (self.textSelectionIndex[0], self.textSelectionIndex[1])
                    if (textSelectionIndex[0] == textSelectionIndex[1]):
                        if (self.insert == True):
                            if (len(self.text) != 0):
                                if not(self.textSelectionIndex[0] == len(self.text)): self.text[self.textSelectionIndex[0]][4] = 1
                                self.__showCursor()
                    else:
                        for targetText in self.text[textSelectionIndex[0]:textSelectionIndex[1]]: targetText[4] = 1
                    self.textSelectionIndex = [len(self.text), len(self.text)]
                    self.__updateTextDisplayBoxPosition("cursor_moved_right")
                    self.__updateTextGraphics()
                #'ESC' Key Clicked
                elif (event[1] == "<ESCAPE>"):
                    if self.textSelectionIndex[0] > self.textSelectionIndex[1]: textSelectionIndex = (self.textSelectionIndex[1], self.textSelectionIndex[0])
                    else:                                                       textSelectionIndex = (self.textSelectionIndex[0], self.textSelectionIndex[1])
                    for targetText in self.text[textSelectionIndex[0]:textSelectionIndex[1]]: targetText[4] = 1
                    self.textSelectionIndex = [self.textSelectionIndex[1], self.textSelectionIndex[1]]
                    self.__updateTextGraphics()

                #Text Edit Mode & Object Control
                elif (event[1] == "<CAPSLOCK>"): self.caps_lock = not(self.caps_lock)
                elif (event[1] == "<INSERT>"):   
                    if (self.insert == True): #If Insert Mode was originally on
                        self.insert = False
                        if (self.textSelectionIndex[0] == self.textSelectionIndex[1]):
                            if (self.textSelectionIndex[0] < len(self.text)):
                                self.text[self.textSelectionIndex[0]][4] = 1
                                self.__showCursor()
                                self.__updateTextGraphics()
                    else: #If Insert Mode was originally off
                        self.insert = True
                        if (self.textSelectionIndex[0] == self.textSelectionIndex[1]):
                            if (self.textSelectionIndex[0] < len(self.text)):
                                self.text[self.textSelectionIndex[0]][4] = 3
                                self.__hideCursor() 
                                self.__updateTextDisplayBoxPosition("cursor_moved_right")
                                self.__updateTextGraphics()

    def process(self): 
        if (((self.mode == "CLICKED") or (self.mode == "READING")) and (time.perf_counter_ns() - self.cursorTimerCounter) > self.cursorTimerThreshold * 1e6):
            if (self.cursorShow == True):
                self.cursorTimerCounter = time.perf_counter_ns()
                if   (self.canvas.itemcget(self.canvadID_cursor, 'state') == 'hidden'): self.canvas.itemconfigure(self.canvadID_cursor, state = 'normal')
                elif (self.canvas.itemcget(self.canvadID_cursor, 'state') == 'normal'): self.canvas.itemconfigure(self.canvadID_cursor, state = 'hidden')
            elif (self.insert == True):
                self.cursorTimerCounter = time.perf_counter_ns()
                if ((self.textSelectionIndex[0] == self.textSelectionIndex[1]) and self.textSelectionIndex[0] < len(self.text)):
                    if   (self.text[self.textSelectionIndex[0]][4] == 3): self.text[self.textSelectionIndex[0]][4] = 1; self.canvas.itemconfigure(self.canvasIDs_text[self.text[self.textSelectionIndex[0]][2]], image = self.text[self.textSelectionIndex[0]][0][1])
                    elif (self.text[self.textSelectionIndex[0]][4] == 1): self.text[self.textSelectionIndex[0]][4] = 3; self.canvas.itemconfigure(self.canvasIDs_text[self.text[self.textSelectionIndex[0]][2]], image = self.text[self.textSelectionIndex[0]][0][3])
        return None

    def show(self): 
        self.canvas.itemconfigure(self.canvasID_objectBox, state = 'normal')
        for charData in self.text:
            if (charData[3] > 0): self.canvas.itemconfigure(self.canvasIDs_text[charData[2]], state = 'normal')
            else: break
    def hide(self): 
        self.canvas.itemconfigure(self.canvasID_objectBox, state = 'hidden')
        for charData in self.text:
            if (charData[3] > 0): self.canvas.itemconfigure(self.canvasIDs_text[charData[2]], state = 'hidden')
            else: break

    def activate(self):
        self.mode = "DEFAULT"
        self.canvas.itemconfigure(self.canvasID_objectBox, image = self.graphics[self.mode])

    def deactivate(self):
        self.mode = "INACTIVE"
        self.canvas.itemconfigure(self.canvasID_objectBox, image = self.graphics[self.mode])

    def editText(self, newText):
        self.mode = "DEFAULT"
        self.canvas.itemconfigure(self.canvasID_objectBox, image = self.graphics[self.mode])
        for charData in self.text:
            self.canvas.itemconfigure(self.canvasIDs_text[charData[2]], state = 'hidden', image = self.emptyImage)
            self.__releaseTextCIDIndex(charData[2])
        self.text.clear()
        self.textSelectionIndex = [0, 0]
        for char in newText:
            if (len(self.text) < self.maxTextLength):
                textImageData               = self.graphicsGenerator.generate_characterImage(char, self.textSize, style = self.textStyle, mask = (255, 255, 255, 0))
                textImageMasked_insert      = self.graphicsGenerator.generate_characterImage(char, self.textSize, style = self.textStyle, mask = self.insertModeMask)[0]
                textImageMasked_multiSelect = self.graphicsGenerator.generate_characterImage(char, self.textSize, style = self.textStyle, mask = self.multiSelectMask)[0]
                self.text.append([[char, textImageData[0], textImageMasked_multiSelect, textImageMasked_insert, None], textImageData[1], self.__getAvailableTextCIDIndex(), False, 1])
                self.canvas.itemconfigure(self.canvasIDs_text[self.text[len(self.text) - 1][2]], image = self.text[len(self.text) - 1][0][1])
            else: break;
        self.__updateTextDisplayBoxPosition("cursor_moved_left")
        self.__updateTextGraphics()

    def getText(self):
        returnText = ""
        for charData in self.text: returnText += charData[0][0]
        return returnText

    def getTextLength(self):
        return (len(self.text))

    def __getAvailableTextCIDIndex(self):
        cIDIndex = self.canvasIDs_text_availables.pop(0)
        self.canvasIDs_text_taken.append(cIDIndex)
        return cIDIndex
    def __releaseTextCIDIndex(self, cIDIndex):
        self.canvasIDs_text_taken.remove(cIDIndex)
        self.canvasIDs_text_availables.append(cIDIndex)

    def __calcCursorWithMouse(self, mouseX, clicked = True):
        newSelectionIndex = 0
        objAbsoluteX = mouseX - self.xPos - self.textGOffset + self.textDisplayBoxPosition
        position = 0
        if ((self.xPos + self.textGOffset <= mouseX) and (mouseX <= self.xPos + self.width - self.textGOffset)): 
            for i in range (len(self.text)):
                if (position - self.text[i - 1][1] / 2 <= objAbsoluteX) and (objAbsoluteX < position + self.text[i][1] / 2): newSelectionIndex = i; break;
                elif ((position + self.text[i][1] / 2 <= objAbsoluteX) and (i == len(self.text) - 1)): newSelectionIndex = i + 1
                position += self.text[i][1]
            if (clicked == True):
                if self.textSelectionIndex[0] > self.textSelectionIndex[1]: textSelectionIndex = (self.textSelectionIndex[1], self.textSelectionIndex[0])
                else:                                                       textSelectionIndex = (self.textSelectionIndex[0], self.textSelectionIndex[1])
                for charData in self.text[textSelectionIndex[0]:textSelectionIndex[1]]: charData[4] = 1
                if (self.insert == True):
                    if (self.textSelectionIndex[0] != len(self.text)): self.text[self.textSelectionIndex[0]][4] = 1
                    if (newSelectionIndex == len(self.text)): self.__showCursor()
                    else:                                     self.text[newSelectionIndex][4] = 3; self.__hideCursor()
                else: self.__showCursor()
                self.textSelectionIndex = [newSelectionIndex, newSelectionIndex]
                if (newSelectionIndex <= self.textSelectionIndex[1]): 
                    self.__updateTextDisplayBoxPosition("cursor_moved_left")
                elif (self.textSelectionIndex[1] < newSelectionIndex): 
                    self.__updateTextDisplayBoxPosition("cursor_moved_right")
            else:
                if (newSelectionIndex < self.textSelectionIndex[1]):
                    self.textSelectionIndex[1] = newSelectionIndex
                    self.__updateTextDisplayBoxPosition("cursor_moved_left")
                elif (self.textSelectionIndex[1] < newSelectionIndex):
                    self.textSelectionIndex[1] = newSelectionIndex
                    self.__updateTextDisplayBoxPosition("cursor_moved_right")
                if self.textSelectionIndex[0] > self.textSelectionIndex[1]: textSelectionIndex = (self.textSelectionIndex[1], self.textSelectionIndex[0])
                else:                                                       textSelectionIndex = (self.textSelectionIndex[0], self.textSelectionIndex[1])
                for i in range (len(self.text)):
                    if ((textSelectionIndex[0] <= i) and (i < textSelectionIndex[1])): self.text[i][4] = 2
                    else:                                                              self.text[i][4] = 1
                self.__showCursor()
                if ((self.insert == True) and (self.textSelectionIndex[0] == self.textSelectionIndex[1]) and self.textSelectionIndex[0] < len(self.text)): self.text[self.textSelectionIndex[0]][4] = 3; self.__hideCursor()
        elif (mouseX < self.xPos + self.textGOffset):
            if (self.textSelectionIndex[1] > 0):
                self.textSelectionIndex[1] -= 1
                if (self.insert == True):
                    if (self.textSelectionIndex[0] == self.textSelectionIndex[1]): 
                        self.text[self.textSelectionIndex[0]][4] = 3
                        self.__hideCursor()
                    else:
                        if (self.textSelectionIndex[0] == self.textSelectionIndex[1] + 1): 
                            if (self.textSelectionIndex[0] != len(self.text)): self.text[self.textSelectionIndex[0]][4] = 1
                            self.text[self.textSelectionIndex[1]][4] = 2
                        elif (self.textSelectionIndex[1] < self.textSelectionIndex[0]):    self.text[self.textSelectionIndex[1]][4] = 2
                        else:                                                              self.text[self.textSelectionIndex[1]][4] = 1
                        if (self.textSelectionIndex[0] != self.textSelectionIndex[1]): self.__showCursor()
                else:
                    if (self.textSelectionIndex[1] < self.textSelectionIndex[0]): self.text[self.textSelectionIndex[1]][4] = 2
                    else:                                                         self.text[self.textSelectionIndex[1]][4] = 1
                self.__updateTextDisplayBoxPosition("cursor_moved_left")
        elif (self.xPos + self.width - self.textGOffset <= mouseX):
            if (self.textSelectionIndex[1] < len(self.text)): 
                self.textSelectionIndex[1] += 1
                if (self.insert == True):
                    if (self.textSelectionIndex[0] == self.textSelectionIndex[1]):
                        self.__hideCursor()
                        self.text[self.textSelectionIndex[0]][4] = 3
                    else:
                        self.__showCursor()
                if (self.textSelectionIndex[1] > self.textSelectionIndex[0]): self.text[self.textSelectionIndex[1] - 1][4] = 2
                else:                                                         self.text[self.textSelectionIndex[1] - 1][4] = 1
                self.__updateTextDisplayBoxPosition("cursor_moved_right")
        self.__updateTextGraphics()

    def __showCursor(self):
        if (self.cursorShow == False):
            self.cursorTimerCounter = time.perf_counter_ns()
            self.canvas.itemconfigure(self.canvadID_cursor, state = 'normal')
            self.cursorShow = True
    def __hideCursor(self):
        if (self.cursorShow == True):
            self.canvas.itemconfigure(self.canvadID_cursor, state = 'hidden')
            self.cursorShow = False

    def __editText(self, mode, text = None):
        if (self.cursorShow == True): self.cursorTimerCounter = time.perf_counter_ns(); self.canvas.itemconfigure(self.canvadID_cursor, state = 'normal');
        if self.textSelectionIndex[0] > self.textSelectionIndex[1]: textSelectionIndex = (self.textSelectionIndex[1], self.textSelectionIndex[0])
        else:                                                       textSelectionIndex = (self.textSelectionIndex[0], self.textSelectionIndex[1])
        if (mode == "add"):
            if (len(self.text) < self.maxTextLength):
                textImageData               = self.graphicsGenerator.generate_characterImage(text, self.textSize, style = self.textStyle, mask = (255, 255, 255, 0))
                textImageMasked_insert      = self.graphicsGenerator.generate_characterImage(text, self.textSize, style = self.textStyle, mask = self.insertModeMask)[0]
                textImageMasked_multiSelect = self.graphicsGenerator.generate_characterImage(text, self.textSize, style = self.textStyle, mask = self.multiSelectMask)[0]

                if (textSelectionIndex[0] == textSelectionIndex[1]):
                    if ((self.insert == True) and (textSelectionIndex[0] < len(self.text))):
                        self.canvas.itemconfigure(self.canvasIDs_text[self.text[textSelectionIndex[0]][2]], state = 'hidden', image = self.emptyImage)
                        self.__releaseTextCIDIndex(self.text[textSelectionIndex[0]][2])
                        self.text = self.text[:textSelectionIndex[0]] + self.text[textSelectionIndex[1] + 1:]
                        if (textSelectionIndex[0] != len(self.text)): self.text[textSelectionIndex[0]][4] = 3
                        else:                                         self.canvas.itemconfigure(self.canvadID_cursor, state = 'normal')
                    self.text.insert(textSelectionIndex[0], [[text, textImageData[0], textImageMasked_multiSelect, textImageMasked_insert, None], textImageData[1], self.__getAvailableTextCIDIndex(), False, 1]) #Text Editing
                    self.canvas.itemconfigure(self.canvasIDs_text[self.text[textSelectionIndex[0]][2]], image = self.text[textSelectionIndex[0]][0][1])                                                           #Canvas Label Configuration
                    self.textSelectionIndex[0] += 1; self.textSelectionIndex[1] += 1                                                                                                                              #SelectionIndex Editing
                    self.__updateTextDisplayBoxPosition("cursor_moved_right")
                else:
                    removed = self.text[textSelectionIndex[0]:textSelectionIndex[1]]                                                                                                                              #Text Editing
                    for removedText in removed:                                                                                                                                                                   # ---
                        self.canvas.itemconfigure(self.canvasIDs_text[removedText[2]], state = 'hidden', image = self.emptyImage)                                                                                 # ---
                        self.__releaseTextCIDIndex(removedText[2])                                                                                                                                                # ---
                    self.text = self.text[:textSelectionIndex[0]] + self.text[textSelectionIndex[1]:]                                                                                                             # ---
                    self.text.insert(textSelectionIndex[0], [[text, textImageData[0], textImageMasked_multiSelect, textImageMasked_insert, None], textImageData[1], self.__getAvailableTextCIDIndex(), False, 1]) # ---
                    self.canvas.itemconfigure(self.canvasIDs_text[self.text[textSelectionIndex[0]][2]], image = self.text[textSelectionIndex[0]][0][1])                                                           #Canvas Label Configuration
                    self.textSelectionIndex = [textSelectionIndex[0] + 1, textSelectionIndex[0] + 1]                                                                                                              #SelectionIndex Editing
                    if ((self.insert == True) and (self.textSelectionIndex[0] < len(self.text))): self.text[self.textSelectionIndex[0]][4] = 3; self.__hideCursor()
                    self.__updateTextDisplayBoxPosition("cursor_moved_right")
        elif (mode == "remove"):
            if (textSelectionIndex[0] == textSelectionIndex[1]):
                if (textSelectionIndex[0] > 0):
                    self.canvas.itemconfigure(self.canvasIDs_text[self.text[textSelectionIndex[0] - 1][2]], state = 'hidden', image = self.emptyImage) #Canvas Label Initialization
                    self.__releaseTextCIDIndex(self.text[textSelectionIndex[0] - 1][2])                                                                #Release cID Index
                    self.text = self.text[:textSelectionIndex[0] - 1] + self.text[textSelectionIndex[1]:]                                              #Text Editing
                    self.textSelectionIndex[0] -= 1; self.textSelectionIndex[1] -= 1                                                                   #SelectionIndex Editing
                    self.__updateTextDisplayBoxPosition("cursor_moved_left")
            else:
                removed = self.text[textSelectionIndex[0]:textSelectionIndex[1]]                                                                       #Release cID Index
                for removedText in removed:
                    self.canvas.itemconfigure(self.canvasIDs_text[removedText[2]], state = 'hidden', image = self.emptyImage)                          #Canvas Label Initialization
                    self.__releaseTextCIDIndex(removedText[2])                                                                                         #Release cID Index
                self.text = self.text[:textSelectionIndex[0]] + self.text[textSelectionIndex[1]:]                                                      #Text Editing
                self.textSelectionIndex = [textSelectionIndex[0], textSelectionIndex[0]]                                                               #SelectionIndex Editing
                self.__updateTextDisplayBoxPosition("cursor_moved_left")
        self.__updateTextGraphics()

    def __updateTextDisplayBoxPosition(self, editComment):
        if (self.cursorShow == True): self.cursorTimerCounter = time.perf_counter_ns(); self.canvas.itemconfigure(self.canvadID_cursor, state = 'normal');
        if editComment == "cursor_moved_right":
            tDisplayBoxBoundary_right = self.textDisplayBoxPosition + self.textDisplayBoxSize[0]
            cursorPixelPosition = 0
            for i in range (len(self.text)):
                if (i == self.textSelectionIndex[1]): break
                cursorPixelPosition += self.text[i][1]
            #If the cursor absolute position is outside the display box, move the display box
            if (tDisplayBoxBoundary_right < cursorPixelPosition):
                self.textDisplayBoxAnchor = "right"
                self.textDisplayBoxPosition = cursorPixelPosition - self.textDisplayBoxSize[0]
                self.canvas.moveto(self.canvadID_cursor, self.xPos + self.textGOffset + self.textDisplayBoxSize[0], self.yPos + self.textGOffset)
            #If the cursor absolute position is inside the display box, simply move the displayed cursor position
            else: self.canvas.moveto(self.canvadID_cursor, self.xPos + self.textGOffset + cursorPixelPosition - self.textDisplayBoxPosition, self.yPos + self.textGOffset)
        if editComment == "cursor_moved_left":
            tDisplayBoxBoundary_left = self.textDisplayBoxPosition
            cursorPixelPosition = 0
            for i in range (len(self.text)):
                if (i == self.textSelectionIndex[1]): break
                cursorPixelPosition += self.text[i][1]
            #If the cursor absolute position is outside the display box, move the display box
            if (cursorPixelPosition < tDisplayBoxBoundary_left):
                self.textDisplayBoxAnchor = "left"
                self.textDisplayBoxPosition = cursorPixelPosition
                self.canvas.moveto(self.canvadID_cursor, self.xPos + self.textGOffset, self.yPos + self.textGOffset)
            #If the cursor absolute position is inside the display box, simply move the displayed cursor position
            else: self.canvas.moveto(self.canvadID_cursor, self.xPos + self.textGOffset + cursorPixelPosition - self.textDisplayBoxPosition, self.yPos + self.textGOffset)

    def __updateTextGraphics(self):
        if (self.textDisplayBoxAnchor == "left"):
            #Determine which character needs to be displayed
            position = 0; displayed = None;
            for i in range (len(self.text)):
                if ((displayed == None) and (position == self.textDisplayBoxPosition)):                             displayed = True;
                if ((displayed == True) and (self.textDisplayBoxPosition + self.textDisplayBoxSize[0] < position)): displayed = False;
                cID = self.canvasIDs_text[self.text[i][2]]
                if (displayed == True):
                    #Chracter Image Edit
                    if (self.canvas.itemcget(cID, 'image') != self.text[i][0][self.text[i][3]]): self.canvas.itemconfigure(cID, image = self.text[i][0][self.text[i][4]])
                    #Rightmost Character Partially Hidden by the Box Boundary
                    if (self.textDisplayBoxPosition + self.textDisplayBoxSize[0] < position + self.text[i][1]):
                        self.text[i][0][4] = ImageTk.PhotoImage(ImageTk.getimage(self.text[i][0][self.text[i][4]]).crop((0, 0, self.textDisplayBoxPosition + self.textDisplayBoxSize[0] - position, self.textDisplayBoxSize[1])))
                        self.canvas.itemconfigure(cID, state = 'normal', image = self.text[i][0][4])
                        self.canvas.moveto(cID, self.xPos + self.textGOffset + position - self.textDisplayBoxPosition, int(self.yPos + (self.height - self.textImageHeight) / 2))
                    #Character Position Edit
                    else:
                        if (self.canvas.itemcget(cID, 'state') == 'hidden'): self.canvas.itemconfigure(cID, state = 'normal')
                        if (self.canvas.coords(cID)[0] != self.xPos + self.textGOffset + position - self.textDisplayBoxPosition):
                            self.canvas.moveto(cID, self.xPos + self.textGOffset + position - self.textDisplayBoxPosition, int(self.yPos + (self.height - self.textImageHeight) / 2))
                    self.text[i][3] = True;
                elif (displayed == False or displayed == None):
                    self.text[i][3] = False;
                    if (self.canvas.itemcget(cID, 'state') == 'normal'): self.canvas.itemconfigure(cID, state = 'hidden')
                position += self.text[i][1]
        elif (self.textDisplayBoxAnchor == "right"):
            #Determine which character needs to be displayed
            position = 0; displayed = None;
            for i in range (len(self.text)):
                if ((displayed == None) and (self.textDisplayBoxPosition < position + self.text[i][1])):                              displayed = True
                if ((displayed == True) and (position + self.text[i][1] > self.textDisplayBoxPosition + self.textDisplayBoxSize[0])): displayed = False
                cID = self.canvasIDs_text[self.text[i][2]]
                if (displayed == True):
                    #Chracter Image Edit
                    if (self.canvas.itemcget(cID, 'image') != self.text[i][0][self.text[i][3]]): self.canvas.itemconfigure(cID, image = self.text[i][0][self.text[i][4]])
                    #Leftmost Character Partially Hidden by the Box Boundary
                    if (position < self.textDisplayBoxPosition):
                        self.text[i][0][4] = ImageTk.PhotoImage(ImageTk.getimage(self.text[i][0][self.text[i][4]]).crop((self.textDisplayBoxPosition - position, 0, self.text[i][1], self.textDisplayBoxSize[1])))
                        self.canvas.itemconfigure(cID, state = 'normal', image = self.text[i][0][4])
                        self.canvas.moveto(cID, self.xPos + self.textGOffset, int(self.yPos + (self.height - self.textImageHeight) / 2))
                    #Normal Characters Position Edit
                    else:
                        if (self.canvas.itemcget(cID, 'state') == 'hidden'): self.canvas.itemconfigure(cID, state = 'normal')
                        if (self.canvas.coords(cID)[0] != self.xPos + self.textGOffset + position - self.textDisplayBoxPosition):
                            self.canvas.moveto(cID, self.xPos + self.textGOffset + position - self.textDisplayBoxPosition, int(self.yPos + (self.height - self.textImageHeight) / 2))
                    self.text[i][3] = True;
                elif (displayed == False or displayed == None):
                    self.text[i][3] = False;
                    if (self.canvas.itemcget(cID, 'state') == 'normal'): self.canvas.itemconfigure(cID, state = 'hidden')
                position += self.text[i][1]
#textInputBox_TypeA END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#slider_TypeA -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class slider_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, length, width, boxStyle, buttonStyle, align = "horizontal", buttonLength = 10, layer = 0, value = 50, buttonGOffset = 5):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.layer = layer

        #Object Graphics Control
        self.canvas = canvas
        self.graphicsGenerator = graphicsGenerator
        
        self.buttonGOffset = buttonGOffset
        self.boxGraphics = graphicsGenerator.generate_slider_TypeA_RailImages(boxStyle, length, width, align); self.boxGraphicsMode = "DEFAULT"
        self.canvasID_box = canvas.create_image(self.xPos, self.yPos, image = self.boxGraphics[self.boxGraphicsMode], anchor = "nw", state = 'hidden')
        self.align = align; self.value = value
        
        buttonLength  = int(length * min([buttonLength, 50]) / 100) - self.buttonGOffset * 2;
        buttonWidth = width - self.buttonGOffset * 2
        self.buttonGraphics = graphicsGenerator.generate_slider_TypeA_ButtonImages(buttonStyle, buttonLength, buttonWidth, align); self.buttonGraphicsMode = "DEFAULT"
        self.canvasID_button = canvas.create_image(0, 0, image = self.buttonGraphics[self.buttonGraphicsMode], anchor = "nw", state = 'hidden')
        
        self.sliderLength = length - buttonLength - self.buttonGOffset * 2
        
        if (self.align == "horizontal"):
            self.buttonXPos = self.xPos + self.buttonGOffset + (self.sliderLength * self.value / 100)
            self.buttonYPos = self.yPos + self.buttonGOffset
            self.canvas.moveto(self.canvasID_button, self.buttonXPos, self.buttonYPos)

            self.width = length; self.height = width
            self.buttonWidth = buttonLength; self.buttonHeight = buttonWidth

        elif (self.align == "vertical"):
            self.buttonXPos = self.xPos + self.buttonGOffset
            self.buttonYPos = self.yPos + self.buttonGOffset + (self.sliderLength * self.value / 100)
            self.canvas.moveto(self.canvasID_button, self.buttonXPos, self.buttonYPos)
            
            self.width = width; self.height = length
            self.buttonWidth = buttonWidth; self.buttonHeight = buttonLength

        self.moveRefPoint = None

    def processUserInput(self, event):
        """
        <[0]: boxGMode, [1]: buttonGMode>
        [0]:  [DEFAULT]  [DEFAULT]  - Check for (1) box Hover
        [1]:  [DEFAULT]  [HOVERED]  - Not Possible
        [2]:  [DEFAULT]  [CLICKED]  - Not Possible
        [3]:  [DEFAULT]  [INACTIVE] - Not Possible
        [4]:  [HOVERED]  [DEFAULT]  - Check for (1) box Escape, or (2) button Hover, or (3) mouse Click
        [5]:  [HOVERED]  [HOVERED]  - Check for (1) button Click or (2) button Escape or (3) box & button Escape 
        [6]:  [HOVERED]  [CLICKED]  - Check for (1) button Release, (2) button Move
        [7]:  [HOVERED]  [INACTIVE] - Not Possible
        [8]:  [INACTIVE] [DEFAULT]  - Not Possible
        [9]:  [INACTIVE] [HOVERED]  - Not Possible
        [10]: [INACTIVE] [CLICKED]  - Not Possible
        [11]: [INACTIVE] [INACTIVE] - Do nothing
        """
        if (self.boxGraphicsMode == "DEFAULT"): #Check for (1) box Hover
            if (event == "HOVERED"): self.boxGraphicsMode = "HOVERED"; self.canvas.itemconfigure(self.canvasID_box, image = self.boxGraphics[self.boxGraphicsMode]); return None
        elif (self.boxGraphicsMode == "HOVERED"):
            if (self.buttonGraphicsMode == "DEFAULT"): #Check for (1) box Escape, or (2) button Hover
                if (event == "ESCAPED"): self.boxGraphicsMode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_box, image = self.boxGraphics[self.boxGraphicsMode]); return None #(1) Box Escape Check
                elif ((event[0] == "<MOUSE_MOVED>") and ((self.buttonXPos < event[1]) and (event[1] < self.buttonXPos + self.buttonWidth) and (self.buttonYPos < event[2]) and (event[2] < self.buttonYPos + self.buttonHeight))): #(2) Button Hover Check
                    self.buttonGraphicsMode = "HOVERED"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode]); return None
                elif (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"):
                    if (self.align == "horizontal"): pixelDelta = event[1] - (self.buttonXPos + self.buttonWidth / 2);  self.moveRefPoint = event[1]
                    elif (self.align == "vertical"): pixelDelta = event[2] - (self.buttonYPos + self.buttonHeight / 2); self.moveRefPoint = event[2]
                    self.value += pixelDelta / self.sliderLength * 100
                    self.__moveButton()
                    self.buttonGraphicsMode = "CLICKED"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode]); return ("GUIOSEARCHOFF", "VALUEUPDATED")
            elif (self.buttonGraphicsMode == "HOVERED"): #Check for (1) button Click or (2) button Escape
                if (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"): #(1) Button Click Check
                    if (self.align == "horizontal"): self.moveRefPoint = event[1]
                    elif (self.align == "vertical"): self.moveRefPoint = event[2]
                    self.buttonGraphicsMode = "CLICKED"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode]); return "GUIOSEARCHOFF"
                elif ((event[0] == "<MOUSE_MOVED>") and ((event[1] < self.buttonXPos) or (self.buttonXPos + self.buttonWidth < event[1]) or (event[2] < self.buttonYPos) or (self.buttonYPos + self.buttonHeight < event[2]))): #(2) Button Escape Check
                    self.buttonGraphicsMode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode]); return None
                if (event == "ESCAPED"): #(3) Box & Button Escape Check
                    self.boxGraphicsMode    = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_box, image = self.boxGraphics[self.boxGraphicsMode]) 
                    self.buttonGraphicsMode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode])
            elif (self.buttonGraphicsMode == "CLICKED"): #Check for (1) button Move, (2) button Release
                if (event[0] == "<MOUSE_LEFTBUTTON_RELEASED>"): #(1) Button Release Check
                    if ((self.xPos < event[1]) and (event[1] < self.xPos + self.width) and (self.yPos < event[2]) and (event[2] < self.yPos + self.height)):
                        if ((self.buttonXPos < event[1]) and (event[1] < self.buttonXPos + self.buttonWidth) and (self.buttonYPos < event[2]) and (event[2] < self.buttonYPos + self.buttonHeight)):
                            self.boxGraphicsMode    = "HOVERED"; self.canvas.itemconfigure(self.canvasID_box,    image = self.boxGraphics[self.boxGraphicsMode])
                            self.buttonGraphicsMode = "HOVERED"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode])
                        else: 
                            self.boxGraphicsMode    = "HOVERED"; self.canvas.itemconfigure(self.canvasID_box,    image = self.boxGraphics[self.boxGraphicsMode])
                            self.buttonGraphicsMode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode])
                    else:
                        self.boxGraphicsMode    = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_box,    image = self.boxGraphics[self.boxGraphicsMode])
                        self.buttonGraphicsMode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode])
                    return "GUIOSEARCHON" 
                elif (event[0] == "<MOUSE_MOVED>"):
                    if (self.align == "horizontal"): pixelDelta = event[1] - self.moveRefPoint; self.moveRefPoint = event[1]
                    elif (self.align == "vertical"): pixelDelta = event[2] - self.moveRefPoint; self.moveRefPoint = event[2]
                    self.value += pixelDelta / self.sliderLength * 100
                    self.__moveButton()
                    return "VALUEUPDATED"
    def process(self): return None
    def show(self): self.canvas.itemconfigure(self.canvasID_box,    state = 'normal'); self.canvas.itemconfigure(self.canvasID_button, state = 'normal')
    def hide(self): self.canvas.itemconfigure(self.canvasID_box,    state = 'hidden'); self.canvas.itemconfigure(self.canvasID_button, state = 'hidden')

    def __moveButton(self):
        if   (self.value > 100): self.value = 100
        elif (self.value < 0):   self.value = 0
        if (self.align == "horizontal"): self.buttonXPos = self.xPos + self.buttonGOffset + (self.sliderLength * self.value / 100); self.canvas.moveto(self.canvasID_button, self.buttonXPos, self.buttonYPos)
        elif (self.align == "vertical"): self.buttonYPos = self.yPos + self.buttonGOffset + (self.sliderLength * self.value / 100); self.canvas.moveto(self.canvasID_button, self.buttonXPos, self.buttonYPos)
#slider_TypeA END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#scrollBar_TypeA ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class scrollBar_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, length, width, boxStyle, buttonStyle, viewRange = (40, 60), align = "horizontal", layer = 0, buttonGOffset = 5):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.layer = layer

        #Object Graphics Control
        self.canvas = canvas
        self.graphicsGenerator = graphicsGenerator
        self.buttonStyle = buttonStyle

        self.buttonGOffset = buttonGOffset
        self.boxGraphics = graphicsGenerator.generate_scrollBar_TypeA_RailImages(boxStyle, length, width, align); self.boxGraphicsMode = "DEFAULT"
        self.canvasID_box = canvas.create_image(self.xPos, self.yPos, image = self.boxGraphics[self.boxGraphicsMode], anchor = "nw", state = 'hidden')
        self.align = align; self.__setViewRange(viewRange)

        buttonLength = round((length - self.buttonGOffset * 2) * (self.viewRange[1] - self.viewRange[0]) / 100)
        buttonWidth = width - self.buttonGOffset * 2
        self.buttonGraphics = graphicsGenerator.generate_scrollBar_TypeA_ButtonImages(buttonStyle, buttonLength, buttonWidth, align); self.buttonGraphicsMode = "DEFAULT"
        self.canvasID_button = canvas.create_image(0, 0, image = self.buttonGraphics[self.buttonGraphicsMode], anchor = "nw", state = 'hidden')
        
        self.sliderLength = length - (self.buttonGOffset * 2)
        
        if (self.align == "horizontal"):
            self.buttonXPos = self.xPos + self.buttonGOffset + (self.sliderLength * self.viewRange[0] / 100); self.buttonYPos = self.yPos + self.buttonGOffset
            self.canvas.moveto(self.canvasID_button, self.buttonXPos, self.buttonYPos)
            self.width = length; self.height = width
            self.buttonWidth = buttonLength; self.buttonHeight = buttonWidth
        elif (self.align == "vertical"):
            self.buttonXPos = self.xPos + self.buttonGOffset; self.buttonYPos = self.yPos + self.buttonGOffset + (self.sliderLength * self.viewRange[0] / 100)
            self.canvas.moveto(self.canvasID_button, self.buttonXPos, self.buttonYPos)
            self.width = width; self.height = length
            self.buttonWidth = buttonWidth; self.buttonHeight = buttonLength

        self.moveRefPoint = None

    def processUserInput(self, event):
        """
        <[0]: boxGMode, [1]: buttonGMode>
        [0]:  [DEFAULT]  [DEFAULT]  - Check for (1) box Hover
        [1]:  [DEFAULT]  [HOVERED]  - Not Possible
        [2]:  [DEFAULT]  [CLICKED]  - Not Possible
        [3]:  [DEFAULT]  [INACTIVE] - Not Possible
        [4]:  [HOVERED]  [DEFAULT]  - Check for (1) box Escape, or (2) button Hover, or (3) mouse Click
        [5]:  [HOVERED]  [HOVERED]  - Check for (1) button Click or (2) button Escape or (3) box & button Escape 
        [6]:  [HOVERED]  [CLICKED]  - Check for (1) button Release, (2) button Move
        [7]:  [HOVERED]  [INACTIVE] - Not Possible
        [8]:  [INACTIVE] [DEFAULT]  - Not Possible
        [9]:  [INACTIVE] [HOVERED]  - Not Possible
        [10]: [INACTIVE] [CLICKED]  - Not Possible
        [11]: [INACTIVE] [INACTIVE] - Do nothing
        """
        if (self.boxGraphicsMode == "DEFAULT"): #Check for (1) box Hover
            if (event == "HOVERED"): self.boxGraphicsMode = "HOVERED"; self.canvas.itemconfigure(self.canvasID_box, image = self.boxGraphics[self.boxGraphicsMode]); return None
        elif (self.boxGraphicsMode == "HOVERED"):
            if (self.buttonGraphicsMode == "DEFAULT"): #Check for (1) box Escape, or (2) button Hover
                if (event == "ESCAPED"): self.boxGraphicsMode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_box, image = self.boxGraphics[self.boxGraphicsMode]); return None #(1) Box Escape Check
                elif ((event[0] == "<MOUSE_MOVED>") and ((self.buttonXPos < event[1]) and (event[1] < self.buttonXPos + self.buttonWidth) and (self.buttonYPos < event[2]) and (event[2] < self.buttonYPos + self.buttonHeight))): #(2) Button Hover Check
                    self.buttonGraphicsMode = "HOVERED"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode]); return None
                elif (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"):
                    if (self.align == "horizontal"): pixelDelta = event[1] - (self.buttonXPos + self.buttonWidth / 2);  self.moveRefPoint = event[1]
                    elif (self.align == "vertical"): pixelDelta = event[2] - (self.buttonYPos + self.buttonHeight / 2); self.moveRefPoint = event[2]
                    self.viewRange[0] += pixelDelta / self.sliderLength * 100; self.viewRange[1] += pixelDelta / self.sliderLength * 100
                    self.__moveButton()
                    self.buttonGraphicsMode = "CLICKED"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode]); return ("GUIOSEARCHOFF", "VALUEUPDATED")
            elif (self.buttonGraphicsMode == "HOVERED"): #Check for (1) button Click or (2) button Escape
                if (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"): #(1) Button Click Check
                    if (self.align == "horizontal"): self.moveRefPoint = event[1]
                    elif (self.align == "vertical"): self.moveRefPoint = event[2]
                    self.buttonGraphicsMode = "CLICKED"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode]); return "GUIOSEARCHOFF"
                elif ((event[0] == "<MOUSE_MOVED>") and ((event[1] < self.buttonXPos) or (self.buttonXPos + self.buttonWidth < event[1]) or (event[2] < self.buttonYPos) or (self.buttonYPos + self.buttonHeight < event[2]))): #(2) Button Escape Check
                    self.buttonGraphicsMode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode]); return None
                if (event == "ESCAPED"): #(3) Box & Button Escape Check
                    self.boxGraphicsMode    = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_box, image = self.boxGraphics[self.boxGraphicsMode]) 
                    self.buttonGraphicsMode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode])
            elif (self.buttonGraphicsMode == "CLICKED"): #Check for (1) button Move, (2) button Release
                if (event[0] == "<MOUSE_LEFTBUTTON_RELEASED>"): #(1) Button Release Check
                    if ((self.xPos < event[1]) and (event[1] < self.xPos + self.width) and (self.yPos < event[2]) and (event[2] < self.yPos + self.height)):
                        if ((self.buttonXPos < event[1]) and (event[1] < self.buttonXPos + self.buttonWidth) and (self.buttonYPos < event[2]) and (event[2] < self.buttonYPos + self.buttonHeight)):
                            self.boxGraphicsMode    = "HOVERED"; self.canvas.itemconfigure(self.canvasID_box,    image = self.boxGraphics[self.boxGraphicsMode])
                            self.buttonGraphicsMode = "HOVERED"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode])
                        else: 
                            self.boxGraphicsMode    = "HOVERED"; self.canvas.itemconfigure(self.canvasID_box,    image = self.boxGraphics[self.boxGraphicsMode])
                            self.buttonGraphicsMode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode])
                    else:
                        self.boxGraphicsMode    = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_box,    image = self.boxGraphics[self.boxGraphicsMode])
                        self.buttonGraphicsMode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode])
                    return "GUIOSEARCHON" 
                elif (event[0] == "<MOUSE_MOVED>"):
                    if (self.align == "horizontal"): pixelDelta = event[1] - self.moveRefPoint; self.moveRefPoint = event[1]
                    elif (self.align == "vertical"): pixelDelta = event[2] - self.moveRefPoint; self.moveRefPoint = event[2]
                    self.viewRange[0] += pixelDelta / self.sliderLength * 100; self.viewRange[1] += pixelDelta / self.sliderLength * 100
                    self.__moveButton()
                    return "VALUEUPDATED"
    def process(self): return None
    def show(self): self.canvas.itemconfigure(self.canvasID_box, state = 'normal'); self.canvas.itemconfigure(self.canvasID_button, state = 'normal')
    def hide(self): self.canvas.itemconfigure(self.canvasID_box, state = 'hidden'); self.canvas.itemconfigure(self.canvasID_button, state = 'hidden')

    def getViewRange(self): return tuple(self.viewRange)
    def changeViewRange(self, viewRange):
        self.__setViewRange(viewRange)
        if (self.align == "horizontal"):
            buttonLength = round((self.width - self.buttonGOffset * 2) * (self.viewRange[1] - self.viewRange[0]) / 100); buttonWidth = self.height - self.buttonGOffset * 2
            self.buttonGraphics = self.graphicsGenerator.generate_scrollBar_TypeA_ButtonImages(self.buttonStyle, buttonLength, buttonWidth, align = "horizontal"); self.buttonGraphicsMode = "DEFAULT"
            self.sliderLength = self.width - (self.buttonGOffset * 2)
            self.buttonWidth = buttonLength; self.buttonHeight = buttonWidth
        elif (self.align == "vertical"):
            buttonLength = round((self.height - self.buttonGOffset * 2) * (self.viewRange[1] - self.viewRange[0]) / 100); buttonWidth = self.width - self.buttonGOffset * 2
            self.buttonGraphics = self.graphicsGenerator.generate_scrollBar_TypeA_ButtonImages(self.buttonStyle, buttonLength, buttonWidth, align = "vertical"); self.buttonGraphicsMode = "DEFAULT"
            self.sliderLength = self.height - (self.buttonGOffset * 2)
            self.buttonWidth = buttonWidth; self.buttonHeight = buttonLength
        self.canvas.itemconfigure(self.canvasID_button, image = self.buttonGraphics[self.buttonGraphicsMode])
        self.__moveButton()

    def __moveButton(self):
        viewRangeDelta = self.viewRange[1] - self.viewRange[0]
        if (self.viewRange[0] < 0):   self.viewRange[0] = 0;   self.viewRange[1] = viewRangeDelta
        if (100 < self.viewRange[1]): self.viewRange[1] = 100; self.viewRange[0] = 100 - viewRangeDelta
        if (self.align == "horizontal"): self.buttonXPos = round(self.xPos + self.buttonGOffset + (self.sliderLength * self.viewRange[0] / 100)); self.canvas.moveto(self.canvasID_button, self.buttonXPos, self.buttonYPos)
        elif (self.align == "vertical"): self.buttonYPos = round(self.yPos + self.buttonGOffset + (self.sliderLength * self.viewRange[0] / 100)); self.canvas.moveto(self.canvasID_button, self.buttonXPos, self.buttonYPos)
    def __setViewRange(self, viewRange):
        viewRangeSet = [0, 0]
        if (viewRange[0] < 0):
            if (viewRange[1] < 1): viewRangeSet[0] = 0; viewRangeSet[1] = 1
            else:                  viewRangeSet[0] = 0; viewRangeSet[1] = viewRange[1]
        elif (viewRange[1] > 100):
            if (viewRange[0] > 99): viewRangeSet[0] = 99;           viewRangeSet[1] = 100
            else:                   viewRangeSet[0] = viewRange[0]; viewRangeSet[1] = 100
        elif (viewRange[0] > viewRange[1]): viewRangeSet[0] = viewRange[1]; viewRangeSet[1] = viewRange[0]
        else: viewRangeSet = list(viewRange)
        self.viewRange = viewRangeSet
#scrollBar_TypeA END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#selectionBox_TypeA -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class selectionBox_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, style, elementList = list(), layer = 0, textStyle = "generalText_StyleA", textSize = 12, mode = "DEFAULT_OFF", maxDisplayList = 5):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height
        self.textSize = 12

        #Object Control Parameters
        self.mode_mainBox = mode
        self.mode_listBox = "INACTIVE"
        self.maxDisplayList = maxDisplayList
        self.displayPosition = 0
        self.elementList = elementList
        self.selectedElement = None
        self.hoveredTextColor = "lightskyblue"
        self.displaySize = min([maxDisplayList, len(self.elementList)])

        #Object Graphics Control
        self.canvas = canvas
        self.graphicsGenerator = graphicsGenerator
        self.style = style
        self.graphics_mainBox = graphicsGenerator.generate_selectionBox_TypeA_MainBoxImages(style, width, height)
        self.graphics_listBox = graphicsGenerator.generate_selectionBox_TypeA_ListBoxImages(style, width, height, self.displaySize)
        self.canvasID_listBox = canvas.create_image(self.xPos, self.yPos + self.height, image = self.graphics_listBox["DEFAULT"], anchor = "nw", state = 'hidden') #Create List Box Canvas Label First
        self.canvasID_mainBox = canvas.create_image(self.xPos, self.yPos, image = self.graphics_mainBox[self.mode_mainBox], anchor = "nw", state = 'hidden') #Create Main Box Canvas Label Second
        self.textStyleTheme = graphicsGenerator.getTextStyleThemeTk(textStyle); cTextFont = (self.textStyleTheme['fontFamily'], textSize, self.textStyleTheme['style'])
        self.canvasID_texts = [canvas.create_text((self.xPos + self.width * 0.45), (self.yPos + self.height / 2), text = "", fill = self.textStyleTheme['fill'], font = cTextFont, width = self.width, anchor = "center", state = 'hidden'),]
        for i in range (self.maxDisplayList): self.canvasID_texts.append(canvas.create_text((self.xPos + self.width / 2), (self.yPos + self.height / 2) + height * (i + 1), text = "", fill = self.textStyleTheme['fill'], font = cTextFont, width = self.width, anchor = "center", state = 'hidden'))
        for i in range (self.displaySize): self.canvas.itemconfigure(self.canvasID_texts[i + 1], text = self.elementList[self.displayPosition + i])
        self.layer = layer
        
    def processUserInput(self, event):
        if (self.mode_mainBox == "DEFAULT_OFF"):
            if (event == "HOVERED"): self.mode_mainBox = "HOVERED_OFF"; self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox]); return None
        elif (self.mode_mainBox == "HOVERED_OFF"):
            if   (event == "ESCAPED"): self.mode_mainBox = "DEFAULT_OFF"; self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"):  self.mode_mainBox = "CLICKED_OFF"; self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox]); return None
        elif (self.mode_mainBox == "CLICKED_OFF"): 
            if   (event == "ESCAPED"):                        self.mode_mainBox = "DEFAULT_OFF"; self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_RELEASED>"): 
                self.mode_mainBox = "HOVERED_ON"
                self.mode_listBox = "DEFAULT"
                self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox])
                self.canvas.itemconfigure(self.canvasID_listBox, image = self.graphics_listBox[self.mode_listBox])
                self.canvas.itemconfigure(self.canvasID_listBox, state = 'normal')
                self.canvas.tag_raise(self.canvasID_listBox)
                for i in range (self.displaySize): 
                    self.canvas.itemconfigure(self.canvasID_texts[i + 1], state = 'normal')
                    self.canvas.tag_raise(self.canvasID_texts[i + 1])
                return ("SUBSCRIBEUSERINPUT", "GUIOSEARCHOFF", "SELECTIONBOXOPENED")
        if (self.mode_mainBox == "DEFAULT_ON"):
            if (event == "HOVERED"): self.mode_mainBox = "HOVERED_ON"; self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox]); return None
        elif (self.mode_mainBox == "HOVERED_ON"):
            if   (event == "ESCAPED"): self.mode_mainBox = "DEFAULT_ON"; self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"): self.mode_mainBox = "CLICKED_ON"; self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox])
        elif (self.mode_mainBox == "CLICKED_ON"): 
            if   (event == "ESCAPED"): self.mode_mainBox = "DEFAULT_ON"; self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox]); return None
            elif (event[0] == "<MOUSE_LEFTBUTTON_RELEASED>"):
                self.mode_mainBox = "HOVERED_OFF"
                self.mode_listBox = "INACTIVE"
                self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox])
                self.canvas.itemconfigure(self.canvasID_listBox, state = 'hidden')
                for i in range (self.displaySize): self.canvas.itemconfigure(self.canvasID_texts[i + 1], state = 'hidden')
                return ("UNSUBSCRIBEUSERINPUT", "GUIOSEARCHON")

        if (self.mode_listBox != "INACTIVE"):
            if (event[0] == "<MOUSE_MOVED>"):
                if (self.xPos < event[1]) and (event[1] < self.xPos + self.width) and (self.yPos + self.height < event[2]) and (event[2] < self.yPos + self.height * (1 + self.displaySize)):
                    index = int((event[2] - self.yPos) / self.height) - 1
                    for i in range (self.displaySize):
                        if (self.canvas.itemcget(self.canvasID_texts[i + 1], 'state') != self.textStyleTheme['fill']): self.canvas.itemconfigure(self.canvasID_texts[i + 1], fill = self.textStyleTheme['fill'])
                    self.canvas.itemconfigure(self.canvasID_texts[index + 1], fill = self.hoveredTextColor)
                    self.mode_listBox = "HOVERED"
                    self.canvas.itemconfigure(self.canvasID_listBox, image = self.graphics_listBox[self.mode_listBox])
                else:
                    for i in range (self.displaySize): 
                        if (self.canvas.itemcget(self.canvasID_texts[i + 1], 'state') != self.textStyleTheme['fill']): self.canvas.itemconfigure(self.canvasID_texts[i + 1], fill = self.textStyleTheme['fill'])
                    self.mode_listBox = "DEFAULT"
                    self.canvas.itemconfigure(self.canvasID_listBox, image = self.graphics_listBox[self.mode_listBox])
            if (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"):
                if ((self.xPos < event[1]) and (event[1] < self.xPos + self.width) and (self.yPos < event[2]) and (event[2] < self.yPos + self.height * (1 + self.displaySize))):
                    index = int((event[2] - self.yPos) / self.height) - 1
                    if (0 <= index): 
                        updated = not(self.selectedElement == self.elementList[index + self.displayPosition])
                        self.selectedElement = self.elementList[index + self.displayPosition]
                        self.canvas.itemconfigure(self.canvasID_texts[0], text = self.selectedElement)
                        self.mode_mainBox = "DEFAULT_OFF"
                        self.mode_listBox = "INACTIVE"
                        self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox])
                        self.canvas.itemconfigure(self.canvasID_listBox, state = 'hidden')
                        for i in range (self.displaySize): 
                            if (self.canvas.itemcget(self.canvasID_texts[i + 1], 'state') != self.textStyleTheme['fill']): self.canvas.itemconfigure(self.canvasID_texts[i + 1], fill = self.textStyleTheme['fill'])
                            self.canvas.itemconfigure(self.canvasID_texts[i + 1], state = 'hidden')
                        if (updated == True): return ("UNSUBSCRIBEUSERINPUT", "GUIOSEARCHON", "SELECTIONUPDATED")
                        else:                 return ("UNSUBSCRIBEUSERINPUT", "GUIOSEARCHON")
                else:
                    self.mode_mainBox = "DEFAULT_OFF"
                    self.mode_listBox = "INACTIVE"
                    self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox])
                    self.canvas.itemconfigure(self.canvasID_listBox, state = 'hidden')
                    for i in range (self.displaySize): 
                        if (self.canvas.itemcget(self.canvasID_texts[i + 1], 'state') != self.textStyleTheme['fill']): self.canvas.itemconfigure(self.canvasID_texts[i + 1], fill = self.textStyleTheme['fill'])
                        self.canvas.itemconfigure(self.canvasID_texts[i + 1], state = 'hidden')
                    return ("UNSUBSCRIBEUSERINPUT", "GUIOSEARCHON")
            if (event[0] == "<MOUSE_WHEEL_UP>"):
                if (0 < self.displayPosition):
                    self.displayPosition -= 1
                    for i in range (self.displaySize): self.canvas.itemconfigure(self.canvasID_texts[i + 1], text = self.elementList[self.displayPosition + i])
            if (event[0] == "<MOUSE_WHEEL_DOWN>"):
                if (self.displayPosition + self.maxDisplayList < len(self.elementList)):
                    self.displayPosition += 1
                    for i in range (self.displaySize): self.canvas.itemconfigure(self.canvasID_texts[i + 1], text = self.elementList[self.displayPosition + i])
                    
    def process(self): return None

    def show(self): 
        self.canvas.itemconfigure(self.canvasID_mainBox,  state = 'normal')
        self.canvas.itemconfigure(self.canvasID_texts[0], state = 'normal')
    def hide(self): 
        self.canvas.itemconfigure(self.canvasID_mainBox,  state = 'hidden')
        self.canvas.itemconfigure(self.canvasID_listBox,  state = 'hidden')
        self.canvas.itemconfigure(self.canvasID_texts[0], state = 'hidden')
        
    def activate(self):
        self.mode_mainBox = "DEFAULT_OFF"
        self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox])
    def deactivate(self):
        self.mode_mainBox = "INACTIVE_OFF"
        self.canvas.itemconfigure(self.canvasID_mainBox, image = self.graphics_mainBox[self.mode_mainBox])

    def getSelected(self): return self.selectedElement
    def editSelected(self, selection):
        if (selection in self.elementList):
            self.selectedElement = selection
            self.canvas.itemconfigure(self.canvasID_texts[0], text = self.selectedElement)
            return True
        else: return False
    def getList(self): return self.elementList.copy()
    def updateList(self, newElementList):
        for i in range (self.displaySize): self.canvas.itemconfigure(self.canvasID_texts[i + 1], state = 'hidden')
        self.displayPosition = 0
        self.elementList = newElementList
        self.displaySize = min([self.maxDisplayList, len(self.elementList)])
        self.graphics_listBox = self.graphicsGenerator.generate_selectionBox_TypeA_ListBoxImages(self.style, self.width, self.height, self.displaySize)
        self.canvas.itemconfigure(self.canvasID_listBox, image = self.graphics_listBox["DEFAULT"])
        if not(self.selectedElement in newElementList): self.canvas.itemconfigure(self.canvasID_texts[0], text = ""); self.selectedElement = None
        for i in range (self.displaySize): 
            self.canvas.itemconfigure(self.canvasID_texts[i + 1], text = self.elementList[self.displayPosition + i])
            if not(self.mode_listBox == "INACTIVE"): self.canvas.itemconfigure(self.canvasID_texts[i + 1], state = 'normal'); self.canvas.tag_raise(self.canvasID_texts[i + 1])
    def resetList(self):
        self.updateList(list())
#selectionBox_TypeA END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#matrixDisplayBox_TypeA -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class matrixDisplayBox_typeA:
    def __init__(self, canvas, graphicsGenerator, xPos, yPos, width, height, style, layer = 0, matrix = None, nDisplayedColumns = 3, nDisplayedRows = 10, columnTitles = None, customColumnRatio = None, mode = "DEFAULT", allowSelection = False):
        #Object Basic Parameters
        self.xPos = xPos
        self.yPos = yPos
        self.width  = width
        self.height = height

        #Object Control Parameters
        self.mode = mode
        self.frameGOffset = 10
        self.textGOffset = 5
        self.columnTitles = columnTitles
        if (self.columnTitles == None): self.nDisplayedRows = nDisplayedRows
        else:                           self.nDisplayedRows = nDisplayedRows + 1
        self.nDisplayedColumns = nDisplayedColumns
        self.elementWidth  = ((self.width  - self.frameGOffset * 2) / self.nDisplayedColumns)
        self.elementHeight = ((self.height - self.frameGOffset * 2) / self.nDisplayedRows)
        self.displayPositionIndex = [0, 0]
        self.allowSelection = allowSelection
        self.indexSelection = None

        self.matrix = matrix

        #If the length of the passed 'customColumnRatio' does not matched 'nDisplayedColumns', do not used it. Else, normalize the ratio values
        if ((customColumnRatio != None) and (self.nDisplayedColumns == len(customColumnRatio))): 
            customColumnRatio = list(customColumnRatio)
            ratioSum = sum(customColumnRatio)
            for i in range (len(customColumnRatio)): customColumnRatio[i] = customColumnRatio[i] / ratioSum
        else: customColumnRatio = None
        #[0]: Position, [1]: Width
        self.columnData = list()
        if (customColumnRatio == None):
            columnWidth = ((self.width - self.frameGOffset * 2) / self.nDisplayedColumns)
            for i in range (self.nDisplayedColumns): self.columnData.append((i * columnWidth, columnWidth))
        else:
            positionGeneration = 0
            for i in range (len(customColumnRatio)): 
                columnWidth = ((self.width - self.frameGOffset * 2) * customColumnRatio[i])
                self.columnData.append((round(positionGeneration), columnWidth))
                positionGeneration += columnWidth

        #Object Graphics Control
        self.canvas = canvas
        self.graphicsGenerator = graphicsGenerator
        self.graphics_Frame = graphicsGenerator.generate_matrixDisplayBox_TypeA_Images(style, width, height, self.elementWidth, self.elementHeight, self.nDisplayedColumns, self.nDisplayedRows, self.frameGOffset, self.columnData)
        self.canvasID_Frame = canvas.create_image(self.xPos, self.yPos, image = self.graphics_Frame[self.mode], anchor = "nw", state = 'hidden') #Create Canvas Label
        self.canvasID_Texts = list()
        self.textStyleTheme_default = graphicsGenerator.getTextStyleThemeTk("generalText_StyleA"); self.cTextFont_default = (self.textStyleTheme_default['fontFamily'], 12, self.textStyleTheme_default['style'])
        for i in range (self.nDisplayedColumns):
            self.canvasID_Texts.append(list())
            for j in range (self.nDisplayedRows):
                self.canvasID_Texts[i].append(canvas.create_text((self.xPos + self.frameGOffset + self.columnData[i][0] + self.columnData[i][1] / 2), (self.yPos + self.frameGOffset + self.elementHeight * j + self.elementHeight / 2), 
                                                                 text = "", fill = self.textStyleTheme_default['fill'], font = self.cTextFont_default, width = self.columnData[i][1] - 2 * self.textGOffset, anchor = "nw", state = 'hidden'))
        if (self.allowSelection == True):
            self.selectionImageMask = ImageTk.PhotoImage(Image.new(mode = "RGBA", size = (width - 2 * self.frameGOffset + 1, int(self.elementHeight) + 1), color = (255, 255, 255, 50)))
            self.canvasID_Selection = canvas.create_image(self.xPos, self.yPos, image = self.selectionImageMask, anchor = "nw", state = 'hidden')
        self.updateMatrix(self.matrix)
        self.layer = layer

    def processUserInput(self, event):
        if (self.mode == "DEFAULT"):
            if (event == "HOVERED"): self.mode = "HOVERED"; self.canvas.itemconfigure(self.canvasID_Frame, image = self.graphics_Frame[self.mode]); return None
        elif (self.mode == "HOVERED"):
            if (event == "ESCAPED"): self.mode = "DEFAULT"; self.canvas.itemconfigure(self.canvasID_Frame, image = self.graphics_Frame[self.mode]); return None
            elif (self.matrix != None):
                if (event[0] == "<MOUSE_WHEEL_UP>"):
                    if (0 < self.displayPositionIndex[1]):
                        self.displayPositionIndex[1] -= 1
                        self.__updateSelectionBoxGraphics()
                        self.__updateDisplayMatrix()
                        return "VIEWRANGEUPDATED"
                elif (event[0] == "<MOUSE_WHEEL_DOWN>"):
                    if (self.columnTitles == None): lowEnd = self.displayPositionIndex[1] + self.nDisplayedRows
                    else:                           lowEnd = self.displayPositionIndex[1] + self.nDisplayedRows - 1
                    if (lowEnd < len(self.matrix[0])):
                        self.displayPositionIndex[1] += 1
                        self.__updateSelectionBoxGraphics()
                        self.__updateDisplayMatrix()
                        return "VIEWRANGEUPDATED"
                elif (event[0] == "<MOUSE_WHEEL_LEFT>"):
                    if (0 < self.displayPositionIndex[0]):
                        self.displayPositionIndex[0] -= 1
                        self.__updateDisplayMatrix()
                        return "VIEWRANGEUPDATED"
                elif (event[0] == "<MOUSE_WHEEL_RIGHT>"):
                    if (self.displayPositionIndex[0] + self.nDisplayedColumns < len(self.matrix)):
                        self.displayPositionIndex[0] += 1
                        self.__updateDisplayMatrix()
                        return "VIEWRANGEUPDATED"
                elif (event[0] == "<MOUSE_LEFTBUTTON_CLICKED>"):
                    if (self.allowSelection == True):
                        selectedIndex = None
                        if (self.columnTitles == None): 
                            if ((self.xPos + self.frameGOffset <= event[1]) and (event[1] <= self.xPos + self.width - self.frameGOffset) and (self.yPos + self.frameGOffset <= event[2]) and (event[2] <= self.yPos + self.height - self.frameGOffset)):
                                relIndex = int((event[2] - self.yPos - self.frameGOffset) / self.elementHeight)
                                selectedIndex = relIndex + self.displayPositionIndex[1]
                        else:
                            if ((self.xPos + self.frameGOffset <= event[1]) and (event[1] <= self.xPos + self.width - self.frameGOffset) and (self.yPos + self.frameGOffset + self.elementHeight <= event[2]) and (event[2] <= self.yPos + self.height - self.frameGOffset)):
                                relIndex = int((event[2] - self.yPos - self.frameGOffset) / self.elementHeight)
                                selectedIndex = relIndex + self.displayPositionIndex[1] - 1
                        if (selectedIndex != None) and (selectedIndex < len(self.matrix[0])):
                            if (self.indexSelection == selectedIndex):
                                self.indexSelection = None
                                self.canvas.itemconfigure(self.canvasID_Selection, state = 'hidden')
                            else:
                                self.indexSelection = selectedIndex
                                self.canvas.moveto(self.canvasID_Selection, self.xPos + self.frameGOffset, self.yPos + self.frameGOffset + relIndex * self.elementHeight)
                                self.canvas.itemconfigure(self.canvasID_Selection, state = 'normal')
                            return "SELECTIONUPDATED"

    def process(self): return None

    def show(self): 
        self.canvas.itemconfigure(self.canvasID_Frame, state = 'normal')
        for columnIndex in range (len(self.canvasID_Texts)):
            for rowIndex in range (len(self.canvasID_Texts[columnIndex])):
                self.canvas.itemconfigure(self.canvasID_Texts[columnIndex][rowIndex], state = 'normal')
        if (self.allowSelection == True): self.__updateSelectionBoxGraphics()
    def hide(self): 
        self.canvas.itemconfigure(self.canvasID_Frame, state = 'hidden')
        for columnIndex in range (len(self.canvasID_Texts)):
            for rowIndex in range (len(self.canvasID_Texts[columnIndex])):
                self.canvas.itemconfigure(self.canvasID_Texts[columnIndex][rowIndex], state = 'hidden')
        if (self.allowSelection == True): self.canvas.itemconfigure(self.canvasID_Selection, state = 'hidden')
    #Each element of the matrix contains
    #[0]: Text, [1]: TextAnchor, [2]: TextFill, [3]: TextFont
    def updateMatrix(self, matrix, textOnly = False, holdPosition = False, holdSelection = False):
        if (self.matrix != None):
            for columnIndex in range (len(self.canvasID_Texts)):
                for rowIndex in range (len(self.canvasID_Texts[0])):
                    self.canvas.itemconfigure(self.canvasID_Texts[columnIndex][rowIndex], text = "")
        if (textOnly == True):
            for columnIndex in range (len(matrix)):
                if columnIndex >= len(self.matrix): self.matrix.append(list())
                for rowIndex in range (len(matrix[columnIndex])):
                    if rowIndex >= len(matrix[columnIndex]): self.matrix[columnIndex].append((matrix[columnIndex][rowIndex], "center", "textStyleTheme_default", self.cTextFont_default))
                    else:                                    self.matrix[columnIndex][rowIndex][0] = matrix[columnIndex][rowIndex]
            for columnIndex in range (min([len(self.matrix), self.nDisplayedColumns])):
                for rowIndex in range (min([len(self.matrix[columnIndex]), self.nDisplayedRows])):
                    self.canvas.itemconfigure(self.canvasID_Texts[columnIndex][rowIndex], text = self.matrix[columnIndex][rowIndex])
        else:
            if (self.matrix != None):
                if (len(matrix) < len(self.matrix)):       self.displayPositionIndex[0] = 0
                elif (holdPosition == False):              self.displayPositionIndex[0] = 0
                if (len(matrix[0]) < len(self.matrix[0])): self.displayPositionIndex[1] = 0
                elif (holdPosition == False):              self.displayPositionIndex[1] = 0
                if ((self.allowSelection == True) and (self.indexSelection != None)):
                    if not((holdSelection == True) and (self.indexSelection <= len(matrix[0]))): self.indexSelection = None; self.canvas.itemconfigure(self.canvasID_Selection, state = 'hidden')
            if ((matrix == None) or (len(matrix) == 0) or (len(matrix[0]) == 0)): self.matrix = None
            else:                                                                 self.matrix = matrix
            self.__updateDisplayMatrix()

    def resetMatrix(self):
        self.matrix = None
        for columnIndex in range (self.nDisplayedColumns):
            if (self.columnTitles == None): rowIndexBegin = 0
            else                          : rowIndexBegin = 1
            for rowIndex in range (rowIndexBegin, self.nDisplayedRows): self.canvas.itemconfigure(self.canvasID_Texts[columnIndex][rowIndex], text = "")
        if (self.allowSelection == True): self.indexSelection = None; self.canvas.itemconfigure(self.canvasID_Selection, state = 'hidden')

    def getViewRange(self):
        if (self.matrix == None): return {'horizontal': (0, 100), 'vertical': (0, 100)}
        else:
            viewRangeH = (self.displayPositionIndex[0] / len(self.matrix) * 100, (self.displayPositionIndex[0] + self.nDisplayedColumns) / len(self.matrix) * 100)
            if (self.columnTitles == None): viewRangeV = (self.displayPositionIndex[1] / len(self.matrix[0]) * 100, (self.displayPositionIndex[1] + self.nDisplayedRows)     / max([self.nDisplayedRows,     len(self.matrix[0])]) * 100)
            else:                           viewRangeV = (self.displayPositionIndex[1] / len(self.matrix[0]) * 100, (self.displayPositionIndex[1] + self.nDisplayedRows - 1) / max([self.nDisplayedRows - 1, len(self.matrix[0])]) * 100)
            return {'horizontal': viewRangeH, 'vertical': viewRangeV}
    def changeViewRangeH(self, viewRange):
        if (self.matrix != None):
            self.displayPositionIndex[0] = round(viewRange[0] * len(self.matrix) / 100)
            self.__updateDisplayMatrix()
    def changeViewRangeV(self, viewRange):
        if (self.matrix != None):
            self.displayPositionIndex[1] = round(viewRange[0] * len(self.matrix[0]) / 100)
            self.__updateSelectionBoxGraphics()
            self.__updateDisplayMatrix()
    def changeSelectionIndex(self, selectionIndex):
        if ((self.matrix != None) and (self.allowSelection == True)):
            if (selectionIndex == None):
                self.indexSelection = None
                self.__updateSelectionBoxGraphics()
            elif ((0 <= selectionIndex) and (selectionIndex < len(self.matrix[0]))):
                self.indexSelection = selectionIndex
                self.__updateSelectionBoxGraphics()
    def getSelected(self): return self.indexSelection
    def releaseSelected(self):
        if (self.allowSelection == True): self.indexSelection = None; self.canvas.itemconfigure(self.canvasID_Selection, state = 'hidden')

    def __updateDisplayMatrix(self):
        if (self.matrix != None):
            for columnIndex in range (min([len(self.matrix), self.nDisplayedColumns])):
                if (self.columnTitles == None): rowIndexUpperLimit = min([len(self.matrix[columnIndex]),     self.nDisplayedRows])
                else:                           rowIndexUpperLimit = min([len(self.matrix[columnIndex]) + 1, self.nDisplayedRows])
                for rowIndex in range (rowIndexUpperLimit):
                    e_CIndex = columnIndex + self.displayPositionIndex[0]
                    e_RIndex = rowIndex    + self.displayPositionIndex[1]
                    if (self.columnTitles == None):
                        targetText   = self.matrix[e_CIndex][e_RIndex][0]
                        targetAnchor = self.matrix[e_CIndex][e_RIndex][1]
                        targetFill   = self.matrix[e_CIndex][e_RIndex][2]
                        targetFont   = self.matrix[e_CIndex][e_RIndex][3]
                    else:
                        if (rowIndex == 0):
                            if (e_CIndex < len(self.columnTitles)):
                                targetText   = self.columnTitles[e_CIndex][0]
                                targetAnchor = self.columnTitles[e_CIndex][1]
                                targetFill   = self.columnTitles[e_CIndex][2]
                                targetFont   = self.columnTitles[e_CIndex][3]
                            else:
                                targetText   = ""
                                targetAnchor = "center"
                                targetFill   = "white"
                                targetFont   = ("Arial", 12, "bold")
                        else: 
                            targetText   = self.matrix[e_CIndex][e_RIndex - 1][0]
                            targetAnchor = self.matrix[e_CIndex][e_RIndex - 1][1]
                            targetFill   = self.matrix[e_CIndex][e_RIndex - 1][2]
                            targetFont   = self.matrix[e_CIndex][e_RIndex - 1][3]
                    if   (targetAnchor == "n"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] / 2
                        y = self.yPos + self.frameGOffset + self.elementHeight * rowIndex + self.textGOffset
                    elif (targetAnchor == "ne"):
                        if (columnIndex + 1 < len(self.columnData)): x = self.xPos + self.frameGOffset + self.columnData[columnIndex + 1][0] - self.textGOffset
                        else:                                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] - self.textGOffset
                        y = self.yPos + self.frameGOffset + self.elementHeight * rowIndex + self.textGOffset
                    elif (targetAnchor == "e"):
                        if (columnIndex + 1 < len(self.columnData)): x = self.xPos + self.frameGOffset + self.columnData[columnIndex + 1][0] - self.textGOffset
                        else:                                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] - self.textGOffset
                        y = self.yPos + self.frameGOffset + self.elementHeight * rowIndex + self.elementHeight / 2
                    elif (targetAnchor == "se"):
                        if (columnIndex + 1 < len(self.columnData)): x = self.xPos + self.frameGOffset + self.columnData[columnIndex + 1][0] - self.textGOffset
                        else:                                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] - self.textGOffset
                        y = self.yPos + self.frameGOffset + self.elementHeight * (rowIndex + 1) - self.textGOffset
                    elif (targetAnchor == "s"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] / 2
                        y = self.yPos + self.frameGOffset + self.elementHeight * (rowIndex + 1) - self.textGOffset
                    elif (targetAnchor == "sw"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.textGOffset
                        y = self.yPos + self.frameGOffset + self.elementHeight * (rowIndex + 1) - self.textGOffset
                    elif (targetAnchor == "w"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.textGOffset
                        y = self.yPos + self.frameGOffset + self.elementHeight * rowIndex + self.elementHeight / 2
                    elif (targetAnchor == "nw"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.textGOffset
                        y = self.yPos + self.frameGOffset + self.elementHeight * rowIndex + self.textGOffset
                    elif (targetAnchor == "center"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] / 2
                        y = self.yPos + self.frameGOffset + self.elementHeight * rowIndex + self.elementHeight / 2
                    self.canvas.itemconfigure(self.canvasID_Texts[columnIndex][rowIndex], anchor = "nw")
                    self.canvas.moveto(self.canvasID_Texts[columnIndex][rowIndex], int(x), int(y))
                    self.canvas.itemconfigure(self.canvasID_Texts[columnIndex][rowIndex], text = targetText, anchor = targetAnchor, fill = targetFill, font = targetFont, width = self.columnData[columnIndex][1] - 2 * self.textGOffset)
        else:
            if (self.columnTitles != None):
                for columnIndex in range (self.nDisplayedColumns):
                    targetText   = self.columnTitles[columnIndex][0]
                    targetAnchor = self.columnTitles[columnIndex][1]
                    targetFill   = self.columnTitles[columnIndex][2]
                    targetFont   = self.columnTitles[columnIndex][3]
                    if   (targetAnchor == "n"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] / 2
                        y = self.yPos + self.frameGOffset + self.textGOffset
                    elif (targetAnchor == "ne"):
                        if (columnIndex + 1 < len(self.columnData)): x = self.xPos + self.frameGOffset + self.columnData[columnIndex + 1][0] - self.textGOffset
                        else:                                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] - self.textGOffset
                        y = self.yPos + self.frameGOffset + self.textGOffset
                    elif (targetAnchor == "e"):
                        if (columnIndex + 1 < len(self.columnData)): x = self.xPos + self.frameGOffset + self.columnData[columnIndex + 1][0] - self.textGOffset
                        else:                                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] - self.textGOffset
                        y = self.yPos + self.frameGOffset + self.elementHeight / 2
                    elif (targetAnchor == "se"):
                        if (columnIndex + 1 < len(self.columnData)): x = self.xPos + self.frameGOffset + self.columnData[columnIndex + 1][0] - self.textGOffset
                        else:                                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] - self.textGOffset
                        y = self.yPos + self.frameGOffset + self.elementHeight - self.textGOffset
                    elif (targetAnchor == "s"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] / 2
                        y = self.yPos + self.frameGOffset + self.elementHeight - self.textGOffset
                    elif (targetAnchor == "sw"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.textGOffset
                        y = self.yPos + self.frameGOffset + self.elementHeight - self.textGOffset
                    elif (targetAnchor == "w"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.textGOffset
                        y = self.yPos + self.frameGOffset + self.elementHeight / 2
                    elif (targetAnchor == "nw"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.textGOffset
                        y = self.yPos + self.frameGOffset + self.textGOffset
                    elif (targetAnchor == "center"):
                        x = self.xPos + self.frameGOffset + self.columnData[columnIndex][0] + self.columnData[columnIndex][1] / 2
                        y = self.yPos + self.frameGOffset + self.elementHeight / 2
                    self.canvas.itemconfigure(self.canvasID_Texts[columnIndex][0], anchor = "nw")
                    self.canvas.moveto(self.canvasID_Texts[columnIndex][0], int(x), int(y))
                    self.canvas.itemconfigure(self.canvasID_Texts[columnIndex][0], text = targetText, anchor = targetAnchor, fill = targetFill, font = targetFont, width = self.columnData[columnIndex][1] - 2 * self.textGOffset)


    def __updateSelectionBoxGraphics(self):
        if (self.allowSelection == True):
            if (self.columnTitles == None):
                if ((self.indexSelection != None) and (self.displayPositionIndex[1] <= self.indexSelection) and (self.indexSelection < self.displayPositionIndex[1] + self.nDisplayedRows)):
                    relIndex = self.indexSelection - self.displayPositionIndex[1]
                    self.canvas.moveto(self.canvasID_Selection, self.xPos + self.frameGOffset, self.yPos + self.frameGOffset + relIndex * self.elementHeight)
                    self.canvas.itemconfigure(self.canvasID_Selection, state = 'normal')
                else: self.canvas.itemconfigure(self.canvasID_Selection, state = 'hidden')
            else:
                if ((self.indexSelection != None) and (self.displayPositionIndex[1] <= self.indexSelection) and (self.indexSelection < self.displayPositionIndex[1] + self.nDisplayedRows - 1)):
                    relIndex = self.indexSelection - self.displayPositionIndex[1] + 1
                    self.canvas.moveto(self.canvasID_Selection, self.xPos + self.frameGOffset, self.yPos + self.frameGOffset + relIndex * self.elementHeight)
                    self.canvas.itemconfigure(self.canvasID_Selection, state = 'normal')
                else: self.canvas.itemconfigure(self.canvasID_Selection, state = 'hidden')
#matrixDisplayBox_TypeA END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Graphical Objects END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




















#Graphical Object Styles ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class graphics_Generator:
    #Graphics Generator Initialization ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __init__(self, resamplingFactor = 4):
        #Resampling Factor, default value is 4
        self.resamplingFactor = resamplingFactor

        #Character Images: [CHARACTER]_[FONTTYPE]_[TEXTSIZE]_[TEXTFILL]_[TEXTSTROKEFILL]_[TEXTSTROKEWIDTH]
        self.allCharSamples = ("a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z",
                               "A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z",
                               "1","2","3","4","5","6","7","8","9","0","!","@","#","$","%","^","&","&","*","(",")",     
                               "`","~","-","_","=","+","[","{","]","}","\\","|",";",":","'","\"",",","<",".",">","/","?")
        self.textWidthCompensationCoefficient  = 1
        self.textHeightCompensationCoefficient = 1.2
        self.imageDictionary = dict()
        
        files_SGL = os.listdir(path_SYSGRAPHICSLIBRARY)
        for file in files_SGL:
            fileInfo = file.split(".")
            fileName = fileInfo[0]; fileExtension = fileInfo[1]
            if (fileExtension == "png"): self.imageDictionary[fileName] = ImageTk.PhotoImage(Image.open(os.path.join(path_SYSGRAPHICSLIBRARY, file)))

        self.textStyleThemeDictionary = dict()
        #[fontFamily]: Any available fontFamily in tkinter
        #[fill]:       Any available color in tkinter
        #[style]:      ('bold') ('italic') ('underline') ('overstrike')
        fill = (255, 255, 255, 255)
        self.textStyleThemeDictionary["generalText_StyleA_Tk"]  = {'fontFamily': 'Arial',     'fill': convertRGBtoHex(fill[0], fill[1], fill[2]), 'style': ''}
        self.textStyleThemeDictionary["generalText_StyleA_PIL"] = {'fontFamily': 'arial.ttf', 'fill': fill, 'strokeFill': (0, 0, 0, 0), 'strokeWidth': 0, }

        self.textStyleThemeDictionary["pageClockFont_Tk"]       = {'fontFamily': 'Arial', 'fill': convertRGBtoHex(160, 230, 255), 'style': ''}


        self.styleThemeDictionary = dict()
        #Navigation Button Theme 0
        self.styleThemeDictionary["button_TypeA_styleA_themeA"] = {'fill_DEFAULT':  (115, 115, 115, 255), 'outline_DEFAULT':  (40,  40,  40,  255), 'textFill_DEFAULT':  (255, 255, 255, 255), 'textStrokeFill_DEFAULT':  (0, 0, 0, 0), 'textStrokeWidth_DEFAULT':  0,
                                                                   'fill_HOVERED':  (115, 115, 115, 255), 'outline_HOVERED':  (160, 230, 255, 255), 'textFill_HOVERED':  (255, 255, 255, 255), 'textStrokeFill_HOVERED':  (0, 0, 0, 0), 'textStrokeWidth_HOVERED':  0,
                                                                   'fill_CLICKED':  (60,  60,  60,  255), 'outline_CLICKED':  (160, 230, 255, 255), 'textFill_CLICKED':  (255, 255, 255, 255), 'textStrokeFill_CLICKED':  (0, 0, 0, 0), 'textStrokeWidth_CLICKED':  0,
                                                                   'fill_INACTIVE': (60,  60,  60,  255), 'outline_INACTIVE': (160, 230, 255, 255), 'textFill_INACTIVE': (160, 230, 255, 255), 'textStrokeFill_INACTIVE': (0, 0, 0, 0), 'textStrokeWidth_INACTIVE': 0,
                                                                   'outlineWidth': 3, 'cornerRadius': 8}
        #Navigation Button Theme 1
        self.styleThemeDictionary["button_TypeA_styleA_themeC"] = {'fill_DEFAULT':  (140, 140, 140, 255), 'outline_DEFAULT':  (40,  40,  40,  255), 'textFill_DEFAULT':  (220, 220, 220, 255), 'textStrokeFill_DEFAULT':  (0, 0, 0, 0), 'textStrokeWidth_DEFAULT':  0,
                                                                   'fill_HOVERED':  (140, 140, 140, 255), 'outline_HOVERED':  (160, 230, 255, 255), 'textFill_HOVERED':  (220, 220, 220, 255), 'textStrokeFill_HOVERED':  (0, 0, 0, 0), 'textStrokeWidth_HOVERED':  0,
                                                                   'fill_CLICKED':  (80,  80,  80,  255), 'outline_CLICKED':  (160, 230, 255, 255), 'textFill_CLICKED':  (220, 220, 220, 255), 'textStrokeFill_CLICKED':  (0, 0, 0, 0), 'textStrokeWidth_CLICKED':  0,
                                                                   'fill_INACTIVE': (80,  80,  80,  255), 'outline_INACTIVE': (160, 230, 255, 255), 'textFill_INACTIVE': (160, 230, 255, 255), 'textStrokeFill_INACTIVE': (0, 0, 0, 0), 'textStrokeWidth_INACTIVE': 0,
                                                                   'outlineWidth': 2, 'cornerRadius': 5}
        #General Button Theme 0
        self.styleThemeDictionary["button_TypeA_styleA_themeB"] = {'fill_DEFAULT':  (90, 90, 90, 255), 'outline_DEFAULT':  (40,  40,  40,  255), 'textFill_DEFAULT':  (255, 255, 255, 255), 'textStrokeFill_DEFAULT':  (0, 0, 0, 0), 'textStrokeWidth_DEFAULT':  0,
                                                                   'fill_HOVERED':  (90, 90, 90, 255), 'outline_HOVERED':  (150, 150, 150, 255), 'textFill_HOVERED':  (255, 255, 255, 255), 'textStrokeFill_HOVERED':  (0, 0, 0, 0), 'textStrokeWidth_HOVERED':  0,
                                                                   'fill_CLICKED':  (60, 60, 60, 255), 'outline_CLICKED':  (150, 150, 150, 255), 'textFill_CLICKED':  (255, 255, 255, 255), 'textStrokeFill_CLICKED':  (0, 0, 0, 0), 'textStrokeWidth_CLICKED':  0,
                                                                   'fill_INACTIVE': (75, 75, 75, 255), 'outline_INACTIVE': ( 40,  40,  40, 255), 'textFill_INACTIVE': (100, 100, 100, 255), 'textStrokeFill_INACTIVE': (0, 0, 0, 0), 'textStrokeWidth_INACTIVE': 0,
                                                                   'outlineWidth': 2, 'cornerRadius': 8}
        #Page "APICONTROL" Navigation Button Theme 0
        self.styleThemeDictionary["button_TypeA_styleA_themeD"] = {'fill_DEFAULT':  (70, 70, 70, 255), 'outline_DEFAULT':  (40,  40,  40,  255), 'textFill_DEFAULT':  (255, 255, 255, 255), 'textStrokeFill_DEFAULT':  (0, 0, 0, 0), 'textStrokeWidth_DEFAULT':  0,
                                                                   'fill_HOVERED':  (70, 70, 70, 255), 'outline_HOVERED':  (160, 230, 255, 255), 'textFill_HOVERED':  (255, 255, 255, 255), 'textStrokeFill_HOVERED':  (0, 0, 0, 0), 'textStrokeWidth_HOVERED':  0,
                                                                   'fill_CLICKED':  (60, 60, 60, 255), 'outline_CLICKED':  (160, 230, 255, 255), 'textFill_CLICKED':  (255, 255, 255, 255), 'textStrokeFill_CLICKED':  (0, 0, 0, 0), 'textStrokeWidth_CLICKED':  0,
                                                                   'fill_INACTIVE': (60, 60, 60, 255), 'outline_INACTIVE': (160, 230, 255, 255), 'textFill_INACTIVE': (100, 100, 100, 255), 'textStrokeFill_INACTIVE': (0, 0, 0, 0), 'textStrokeWidth_INACTIVE': 0,
                                                                   'outlineWidth': 3, 'cornerRadius': 15}
        #Page "APICONTROL" Navigation Button Theme 1
        self.styleThemeDictionary["button_TypeA_styleA_themeE"] = {'fill_DEFAULT':  (50, 50, 50, 255), 'outline_DEFAULT':  (30,  30,  30,  255), 'textFill_DEFAULT':  (255, 255, 255, 255), 'textStrokeFill_DEFAULT':  (0, 0, 0, 0), 'textStrokeWidth_DEFAULT':  0,
                                                                   'fill_HOVERED':  (50, 50, 50, 255), 'outline_HOVERED':  (160, 230, 255, 255), 'textFill_HOVERED':  (255, 255, 255, 255), 'textStrokeFill_HOVERED':  (0, 0, 0, 0), 'textStrokeWidth_HOVERED':  0,
                                                                   'fill_CLICKED':  (40, 40, 40, 255), 'outline_CLICKED':  (160, 230, 255, 255), 'textFill_CLICKED':  (255, 255, 255, 255), 'textStrokeFill_CLICKED':  (0, 0, 0, 0), 'textStrokeWidth_CLICKED':  0,
                                                                   'fill_INACTIVE': (40, 40, 40, 255), 'outline_INACTIVE': (160, 230, 255, 255), 'textFill_INACTIVE': (100, 100, 100, 255), 'textStrokeFill_INACTIVE': (0, 0, 0, 0), 'textStrokeWidth_INACTIVE': 0,
                                                                   'outlineWidth': 2, 'cornerRadius': 5}
        #Page "APICONTROL" Navigation Button Theme 0
        self.styleThemeDictionary["constantTextGraphics_TypeA_styleA_themeB"] = {'fill': (0, 0, 0, 0), 'outline': (0, 0, 0, 0), 'outlineWidth': 3, 'cornerRadius': 8, 'textSize': None, 'textFill': (255, 255, 255, 255), 'textStrokeFill': (0, 0, 0, 0), 'textStrokeWidth': 0}
        #Page "APICONTROL" Navigation LED Theme 0
        self.styleThemeDictionary["LED_TypeA_styleA_themeB"] = {'outline': (30, 30, 30, 255), 'outlineWidth': 2, 'cornerRadius': 5}

        #General TextInputBox Theme 0
        self.styleThemeDictionary["textInputBox_TypeA_styleA_themeA"] = {'fill_DEFAULT':  (90, 90, 90, 255), 'outline_DEFAULT':  ( 40,  40,  40, 255),
                                                                         'fill_HOVERED':  (90, 90, 90, 255), 'outline_HOVERED':  (150, 150, 150, 255),
                                                                         'fill_CLICKED':  (60, 60, 60, 255), 'outline_CLICKED':  (150, 150, 150, 255),
                                                                         'fill_READING':  (60, 60, 60, 255), 'outline_READING':  (150, 150, 150, 255),
                                                                         'fill_INACTIVE': (75, 75, 75, 255), 'outline_INACTIVE': ( 40,  40,  40, 255),
                                                                         'outlineWidth': 2, 'cornerRadius': 8}
        #General Switch_TypeA Theme 0
        self.styleThemeDictionary["switch_TypeA_styleA_themeA"] = {'fill_DEFAULT_OFF':  (50, 50, 50, 255), 'fill_DEFAULT_ON':  (120, 250, 80, 255),
                                                                   'fill_HOVERED_OFF':  (50, 50, 50, 255), 'fill_HOVERED_ON':  (120, 250, 80, 255),
                                                                   'fill_CLICKED_OFF':  (50, 50, 50, 255), 'fill_CLICKED_ON':  (120, 250, 80, 255),
                                                                   'fill_INACTIVE_OFF': (40, 40, 40, 255), 'fill_INACTIVE_ON': ( 96, 200, 64, 255),
                                                                   'outlineWidth': 2, 'cornerRadius': 8,

                                                                   'outline_DEFAULT': (40, 40, 40, 255), 'outline_HOVERED': (150, 150, 150, 255), 'outline_CLICKED': (150, 150, 150, 255), 'outline_INACTIVE': (40, 40, 40, 255),
                                                                   'buttonFill_DEFAULT': (150, 150, 150, 255), 'buttonFill_HOVERED': (180, 180, 180, 255), 'buttonFill_CLICKED': (160, 160, 160, 255), 'buttonFill_INACTIVE': (160, 160, 160, 255),
                                                                   'buttonOutline_DEFAULT': (40, 40, 40, 255), 'buttonOutline_HOVERED': (40, 40, 40, 255), 'buttonOutline_CLICKED': (40, 40, 40, 255), 'buttonOutline_INACTIVE': (40, 40, 40, 40),
                                                                   'buttonOutlineWidth': 2, 'buttonCornerRadius': 5}
        #General Switch_TypeB Theme 0
        self.styleThemeDictionary["switch_TypeB_styleA_themeA"] = {'fill_DEFAULT':  (50, 50, 50, 255), 'fill_HOVERED':  (50, 50, 50, 255), 'fill_CLICKED':  (40, 40, 40, 255), 'fill_INACTIVE': (50, 50, 50, 255),
                                                                   'outline_DEFAULT': (40, 40, 40, 255), 'outline_HOVERED': (150, 150, 150, 255), 'outline_CLICKED': (150, 150, 150, 255), 'outline_INACTIVE': (150, 150, 150, 255),
                                                                   'outlineWidth': 2, 'cornerRadius': 8,
                                                                   
                                                                   'buttonFill_DEFAULT': (150, 150, 150, 255), 'buttonFill_HOVERED': (180, 180, 180, 255), 'buttonFill_CLICKED': (160, 160, 160, 255), 'buttonFill_INACTIVE': (160, 160, 160, 255),
                                                                   'buttonOutline_DEFAULT': (40, 40, 40, 255), 'buttonOutline_HOVERED': (40, 40, 40, 255), 'buttonOutline_CLICKED': (40, 40, 40, 255), 'buttonOutline_INACTIVE': (40, 40, 40, 40),
                                                                   'buttonOutlineWidth': 2, 'buttonCornerRadius': 5}

        #General LED_TypeA Theme 0
        self.styleThemeDictionary["LED_TypeA_styleA_themeA"] = {'outline': (200, 200, 200, 255), 'outlineWidth': 2, 'cornerRadius': 8}

        #Program Background Theme 0
        self.styleThemeDictionary["constantGraphics_TypeA_styleA_themeA"] = {'fill': (15, 15, 15, 255), 'outline': (10, 10, 10, 255), 'outlineWidth': 3, 'cornerRadius': 8}
        #Program Background Theme 1
        self.styleThemeDictionary["constantGraphics_TypeA_styleA_themeB"] = {'fill': (20, 20, 20, 255), 'outline': (10, 10, 10, 255), 'outlineWidth': 3, 'cornerRadius': 8}
        #General ActiveTextBox Theme 0
        self.styleThemeDictionary["constantGraphics_TypeA_styleA_themeC"] = {'fill': (70, 70, 70, 255), 'outline': (40, 40, 40, 255), 'outlineWidth': 2, 'cornerRadius': 8}
        #General GaugeBarBox Theme 0
        self.styleThemeDictionary["constantGraphics_TypeA_styleA_themeD"] = {'fill': (20, 20, 20, 255), 'outline': (40, 40, 40, 255), 'outlineWidth': 2, 'cornerRadius': 5}
        #Program Boundary Line Theme 0
        self.styleThemeDictionary["constantGraphics_TypeA_styleB_themeA"] = {'fill': (100, 100, 100, 255)}
        #Page Clock Frame Design
        self.styleThemeDictionary["constantGraphics_TypeA_styleA_pageClock"] = {'fill': (15, 15, 15, 255), 'outline': (100, 100, 100, 255), 'outlineWidth': 3, 'cornerRadius': 8}
        #General TextBox Theme 0
        self.styleThemeDictionary["constantTextGraphics_TypeA_styleA_themeA"] = {'fill': (60, 60, 60, 255), 'outline': (40, 40, 40, 255), 'outlineWidth': 2, 'cornerRadius': 8, 'textSize': None, 'textFill': None, 'textStrokeFill': None, 'textStrokeWidth': None}
        #General TextBox Theme 0
        self.styleThemeDictionary["constantTextGraphics_TypeA_styleA_themeC"] = {'fill': (70, 70, 70, 255), 'outline': (40, 40, 40, 255), 'outlineWidth': 2, 'cornerRadius': 8, 'textSize': None, 'textFill': None, 'textStrokeFill': None, 'textStrokeWidth': None}

        #Program Background Theme 0
        self.styleThemeDictionary["constantImageGraphics_TypeA_styleA_themeA"] = {'fill': (255, 255, 255, 255), 'outline': (40, 40, 40, 255), 'outlineWidth': 2, 'cornerRadius': 5, 'gOffset': 5}

        #Slider Rail Theme 0
        self.styleThemeDictionary["slider_TypeA_Rail_styleA_themeA"] = {'fill_DEFAULT':  (90, 90, 90, 255), 'outline_DEFAULT':  (40,  40,  40,  255), 'textFill_DEFAULT':  (255, 255, 255, 255), 'textStrokeFill_DEFAULT':  (0, 0, 0, 0), 'textStrokeWidth_DEFAULT':  0,
                                                                        'fill_HOVERED':  (90, 90, 90, 255), 'outline_HOVERED':  (150, 150, 150, 255), 'textFill_HOVERED':  (255, 255, 255, 255), 'textStrokeFill_HOVERED':  (0, 0, 0, 0), 'textStrokeWidth_HOVERED':  0,
                                                                        'fill_INACTIVE': (60, 60, 60, 255), 'outline_INACTIVE': (150, 150, 150, 255), 'textFill_INACTIVE': (100, 100, 100, 255), 'textStrokeFill_INACTIVE': (0, 0, 0, 0), 'textStrokeWidth_INACTIVE': 0,
                                                                        'outlineWidth': 2, 'cornerRadius': 8}
        #Slider Button Theme 0
        self.styleThemeDictionary["slider_TypeA_Button_styleA_themeA"] = {'fill_DEFAULT':  (120, 120, 120, 255), 'outline_DEFAULT':  (40,  40,  40,  255), 'textFill_DEFAULT':  (255, 255, 255, 255), 'textStrokeFill_DEFAULT':  (0, 0, 0, 0), 'textStrokeWidth_DEFAULT':  0,
                                                                          'fill_HOVERED':  (120, 120, 120, 255), 'outline_HOVERED':  (150, 150, 150, 255), 'textFill_HOVERED':  (255, 255, 255, 255), 'textStrokeFill_HOVERED':  (0, 0, 0, 0), 'textStrokeWidth_HOVERED':  0,
                                                                          'fill_CLICKED':  ( 60,  60,  60, 255), 'outline_CLICKED':  (150, 150, 150, 255), 'textFill_CLICKED':  (255, 255, 255, 255), 'textStrokeFill_CLICKED':  (0, 0, 0, 0), 'textStrokeWidth_CLICKED':  0,
                                                                          'fill_INACTIVE': ( 60,  60,  60, 255), 'outline_INACTIVE': (150, 150, 150, 255), 'textFill_INACTIVE': (100, 100, 100, 255), 'textStrokeFill_INACTIVE': (0, 0, 0, 0), 'textStrokeWidth_INACTIVE': 0,
                                                                          'outlineWidth': 2, 'cornerRadius': 8}

        #ScrollBar Rail Theme 0
        self.styleThemeDictionary["scrollBar_TypeA_Rail_styleA_themeA"] = {'fill_DEFAULT':  (90, 90, 90, 255), 'outline_DEFAULT':  (40,  40,  40,  255), 'textFill_DEFAULT':  (255, 255, 255, 255), 'textStrokeFill_DEFAULT':  (0, 0, 0, 0), 'textStrokeWidth_DEFAULT':  0,
                                                                           'fill_HOVERED':  (90, 90, 90, 255), 'outline_HOVERED':  (150, 150, 150, 255), 'textFill_HOVERED':  (255, 255, 255, 255), 'textStrokeFill_HOVERED':  (0, 0, 0, 0), 'textStrokeWidth_HOVERED':  0,
                                                                           'fill_INACTIVE': (60, 60, 60, 255), 'outline_INACTIVE': (150, 150, 150, 255), 'textFill_INACTIVE': (100, 100, 100, 255), 'textStrokeFill_INACTIVE': (0, 0, 0, 0), 'textStrokeWidth_INACTIVE': 0,
                                                                           'outlineWidth': 2, 'cornerRadius': 8}
        #ScrollBar Button Theme 0
        self.styleThemeDictionary["scrollBar_TypeA_Button_styleA_themeA"] = {'fill_DEFAULT':  (120, 120, 120, 255), 'outline_DEFAULT':  (40,  40,  40,  255), 'textFill_DEFAULT':  (255, 255, 255, 255), 'textStrokeFill_DEFAULT':  (0, 0, 0, 0), 'textStrokeWidth_DEFAULT':  0,
                                                                             'fill_HOVERED':  (120, 120, 120, 255), 'outline_HOVERED':  (150, 150, 150, 255), 'textFill_HOVERED':  (255, 255, 255, 255), 'textStrokeFill_HOVERED':  (0, 0, 0, 0), 'textStrokeWidth_HOVERED':  0,
                                                                             'fill_CLICKED':  ( 60,  60,  60, 255), 'outline_CLICKED':  (150, 150, 150, 255), 'textFill_CLICKED':  (255, 255, 255, 255), 'textStrokeFill_CLICKED':  (0, 0, 0, 0), 'textStrokeWidth_CLICKED':  0,
                                                                             'fill_INACTIVE': ( 60,  60,  60, 255), 'outline_INACTIVE': (150, 150, 150, 255), 'textFill_INACTIVE': (100, 100, 100, 255), 'textStrokeFill_INACTIVE': (0, 0, 0, 0), 'textStrokeWidth_INACTIVE': 0,
                                                                             'outlineWidth': 2, 'cornerRadius': 8}
        #SelectionBox mainBox Theme 0
        self.styleThemeDictionary["selectionBox_TypeA_MainBox_styleA_themeA"] = {'fill_DEFAULT':  (115, 115, 115, 255), 'outline_DEFAULT':  ( 40,  40,  40, 255),
                                                                                 'fill_HOVERED':  (115, 115, 115, 255), 'outline_HOVERED':  (150, 150, 150, 255),
                                                                                 'fill_CLICKED':  ( 60,  60,  60, 255), 'outline_CLICKED':  (150, 150, 150, 255),
                                                                                 'fill_INACTIVE': ( 90,  90,  90, 255), 'outline_INACTIVE': ( 40,  40,  40, 255),
                                                                                 'outlineWidth': 2, 'cornerRadius': 8, 'arrowFill': (185, 185, 185, 255)}
        #SelectionBox listBox Theme 0
        self.styleThemeDictionary["selectionBox_TypeA_ListBox_styleA_themeA"] = {'fill_DEFAULT': (120, 120, 120, 255),  'outline_DEFAULT': (40, 40, 40, 255),
                                                                                 'fill_HOVERED': (120, 120, 120, 255),  'outline_HOVERED': (60, 60, 60, 255),
                                                                                 'boundaryFill': (255, 255, 255, 255),  'boundaryWidth': 1,
                                                                                 'outlineWidth': 2, 'cornerRadius': 8}
        #MatrixBox Theme 0
        self.styleThemeDictionary["matrixDisplayBox_TypeA_styleA_themeA"] = {'fill_DEFAULT':  (90, 90, 90, 255), 'outline_DEFAULT':  (40,  40,  40,  255), 'textFill_DEFAULT':  (255, 255, 255, 255), 'textStrokeFill_DEFAULT':  (0, 0, 0, 0), 'textStrokeWidth_DEFAULT':  0,
                                                                             'fill_HOVERED':  (90, 90, 90, 255), 'outline_HOVERED':  (150, 150, 150, 255), 'textFill_HOVERED':  (255, 255, 255, 255), 'textStrokeFill_HOVERED':  (0, 0, 0, 0), 'textStrokeWidth_HOVERED':  0,
                                                                             'fill_INACTIVE': (60, 60, 60, 255), 'outline_INACTIVE': (150, 150, 150, 255), 'textFill_INACTIVE': (100, 100, 100, 255), 'textStrokeFill_INACTIVE': (0, 0, 0, 0), 'textStrokeWidth_INACTIVE': 0,
                                                                             'boundaryFill': (150, 150, 150, 255),  'boundaryWidth': 2,
                                                                             'outlineWidth': 2, 'cornerRadius': 8}
        
    #Graphics Generator Initialization END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





    #Generate a image of constantGraphic_TypeA
    def generate_constantGraphic_TypeA_Images(self, style, sizeX, sizeY):
        def generateStyleA():
            imageName = "@g@{:s}#{:s}#{:s}".format(style, str(sizeX), str(sizeY))
            if imageName in self.imageDictionary.keys(): objectImage = self.imageDictionary[imageName]
            else:
                objectImage = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                draw  = ImageDraw.Draw(objectImage)
                draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill'],
                                               outline = params['outline'], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                               radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                objectImage = ImageTk.PhotoImage(objectImage.resize((sizeX, sizeY), resample=Image.LANCZOS))
                self.__saveImage(objectImage, imageName)
                self.imageDictionary[imageName] = objectImage
            return objectImage
        def generateStyleB():
            imageName = "@g@{:s}#{:s}#{:s}".format(style, str(sizeX), str(sizeY))
            if imageName in self.imageDictionary.keys(): objectImage = self.imageDictionary[imageName]
            else:
                objectImage = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                draw  = ImageDraw.Draw(objectImage)
                draw.rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill'], outline = (0, 0, 0, 0), width = 0)
                objectImage = ImageTk.PhotoImage(objectImage.resize((sizeX, sizeY), resample=Image.LANCZOS))
                self.__saveImage(objectImage, imageName)
                self.imageDictionary[imageName] = objectImage
            return objectImage

        style = "constantGraphics_TypeA_" + style
        params = self.styleThemeDictionary[style]
        if   (style.split("_")[2] == "styleA"): return generateStyleA()
        elif (style.split("_")[2] == "styleB"): return generateStyleB()





    #Generate a image of constantTextGraphic_TypeA
    def generate_constantTextGraphic_TypeA_Images(self, style, sizeX, sizeY, text = None, textFill = None, textSize = None, textStrokeFill = None, textStrokeWidth = None):
        def generateStyleA():
            imageName = "@g@{:s}#{:s}#{:s}".format(style, str(sizeX), str(sizeY))
            if imageName in self.imageDictionary.keys(): boxImage = self.imageDictionary[imageName]
            else:
                boxImage = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                draw  = ImageDraw.Draw(boxImage)
                draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill'],
                                               outline = params['outline'], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                               radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                boxImage = ImageTk.PhotoImage(boxImage.resize((sizeX, sizeY), resample=Image.LANCZOS))
                self.__saveImage(boxImage, imageName)
                self.imageDictionary[imageName] = boxImage
            if (text is not None):
                textImage = ImageTk.getimage(self.generate_textImage(text, params['textSize'], "generalText_StyleA", textFill = params['textFill'], textStrokeFill = params['textStrokeFill'], textStrokeWidth = params['textStrokeWidth']))
                boxImage = ImageTk.getimage(boxImage)
                imageFrame = Image.new(mode = "RGBA", size = (sizeX, sizeY), color = (0, 0, 0, 0))
                imageFrame.paste(textImage, (int(math.ceil((sizeX - textImage.width) / 2)), int(math.ceil((sizeY - textImage.height) / 2))))
                boxImage = Image.alpha_composite(boxImage, imageFrame)
                boxImage = ImageTk.PhotoImage(boxImage)
            return boxImage

        style = "constantTextGraphics_TypeA_" + style
        params = self.styleThemeDictionary[style]
        if textSize is None:        params['textSize'] = int(sizeY * 0.2)
        else:                       params['textSize'] = textSize
        if textFill is None:        params['textFill'] = (255, 255, 255, 255)
        else:                       params['textFill'] = textFill
        if textStrokeFill  is None: params['textStrokeFill'] = (0, 0, 0, 0)
        else:                       params['textStrokeFill'] = textStrokeFill
        if textStrokeWidth is None: params['textStrokeWidth'] = 0
        else:                       params['textStrokeWidth'] = textStrokeWidth
        if (style.split("_")[2] == "styleA"): return generateStyleA()





    #Generate a image of constantImageGraphic_TypeA
    def generate_constantImageGraphic_TypeA_Images(self, style, sizeX, sizeY, imagePath):
        def generateStyleA():
            imageName = "@g@{:s}#{:s}#{:s}#{:s}".format(style, str(sizeX), str(sizeY), imagePath.split("\\")[-1].split(".")[0])
            if imageName in self.imageDictionary.keys(): objectImage = self.imageDictionary[imageName]
            else:
                frameImage = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                frameDraw = ImageDraw.Draw(frameImage)
                frameDraw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill'],
                                               outline = params['outline'], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                               radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                mainImageBase = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                mainImage = Image.open(imagePath).resize(((sizeX - 2 * params['gOffset']) * self.resamplingFactor, (sizeY - 2 * params['gOffset']) * self.resamplingFactor), Image.LANCZOS)
                mainImageBase.paste(mainImage, (params['gOffset'] * self.resamplingFactor, params['gOffset'] * self.resamplingFactor))
                objectImage = ImageTk.PhotoImage(Image.alpha_composite(frameImage, mainImageBase).resize((sizeX, sizeY), resample=Image.LANCZOS))
                self.__saveImage(objectImage, imageName)
                self.imageDictionary[imageName] = objectImage
            return objectImage
        if (style == "empty"): return ImageTk.PhotoImage(Image.open(imagePath).resize((sizeX, sizeY), Image.LANCZOS))
        else:
            style = "constantImageGraphics_TypeA_" + style
            params = self.styleThemeDictionary[style]
            if (style.split("_")[2] == "styleA"): return generateStyleA()





    #Generate a image of button_typeA
    def generate_button_TypeA_Images(self, style, sizeX, sizeY, text = None, textSize = None):
        def generateStyleA():
            images = {"DEFAULT": None, "HOVERED": None, "CLICKED": None, "INACTIVE": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:s}#{:s}".format(style, mode, str(sizeX), str(sizeY))
                if imageName in self.imageDictionary.keys(): buttonImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                    draw  = ImageDraw.Draw(image)
                    draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill_'+mode],
                                           outline = params['outline_'+mode], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                           radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                    buttonImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                    self.__saveImage(buttonImage, imageName)
                    self.imageDictionary[imageName] = buttonImage
                if (text is not None):
                    textImage = ImageTk.getimage(self.generate_textImage(text, params['textSize'], "generalText_StyleA", textFill = params['textFill_'+mode], textStrokeFill = params['textStrokeFill_'+mode], textStrokeWidth = params['textStrokeWidth_'+mode]))
                    buttonImage = ImageTk.getimage(buttonImage)
                    imageFrame = Image.new(mode = "RGBA", size = (sizeX, sizeY), color = (0, 0, 0, 0))
                    imageFrame.paste(textImage, (int(round((sizeX - textImage.width) / 2)), int(round((sizeY - textImage.height) / 2))))
                    buttonImage = Image.alpha_composite(buttonImage, imageFrame)
                    buttonImage = ImageTk.PhotoImage(buttonImage)
                images[mode] = buttonImage
            return images
        
        style = "button_TypeA_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[2] == "styleA"):
            if textSize is None: params['textSize'] = int(sizeY * 0.2)
            else:                params['textSize'] = textSize
            return generateStyleA()





    #Generate a image of textInputBox_typeA
    def generate_textInputBox_TypeA_Images(self, style, sizeX, sizeY):
        def generateStyleA():
            images = {"DEFAULT": None, "HOVERED": None, "CLICKED": None, "READING": None, "INACTIVE": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:s}#{:s}".format(style, mode, str(sizeX), str(sizeY))
                if imageName in self.imageDictionary.keys(): buttonImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                    draw  = ImageDraw.Draw(image)
                    draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill_'+mode],
                                           outline = params['outline_'+mode], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                           radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                    buttonImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                    self.__saveImage(buttonImage, imageName)
                    self.imageDictionary[imageName] = buttonImage
                images[mode] = buttonImage
            return images
        
        style = "textInputBox_TypeA_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[2] == "styleA"):
            return generateStyleA()





    #Generate a image of switch_typeA
    def generate_switch_TypeA_Images(self, style, sizeX, sizeY, align):
        def generateStyleA():
            images = {"DEFAULT_OFF": None, "HOVERED_OFF": None, "CLICKED_OFF": None, "INACTIVE_OFF": None, "DEFAULT_ON": None, "HOVERED_ON": None, "CLICKED_ON": None, "INACTIVE_ON": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:s}#{:s}".format(style, mode, str(sizeX), str(sizeY))
                if imageName in self.imageDictionary.keys(): buttonImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                    draw  = ImageDraw.Draw(image)
                    #Box Drawing
                    draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill_'+mode],
                                           outline = params['outline_' + mode.split("_")[0]], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                           radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                    #Button Drawing
                    gOffset = 3; buttonWidthRatio = 0.4
                    if (align == "horizontal"):
                        draw.rounded_rectangle((gOffset * self.resamplingFactor, gOffset * self.resamplingFactor, sizeX * buttonWidthRatio * self.resamplingFactor, (sizeY - gOffset) * self.resamplingFactor), 
                                               fill = params['buttonFill_' + mode.split("_")[0]], outline = params['buttonOutline_' + mode.split("_")[0]], width = params['buttonOutlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                               radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['buttonCornerRadius'] * self.resamplingFactor)]))
                    elif (align == "vertical"):
                        draw.rounded_rectangle((gOffset * self.resamplingFactor, gOffset * self.resamplingFactor, (sizeX - gOffset) * self.resamplingFactor, sizeY * buttonWidthRatio * self.resamplingFactor), 
                                               fill = params['buttonFill_' + mode.split("_")[0]], outline = params['buttonOutline_' + mode.split("_")[0]], width = params['buttonOutlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                               radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['buttonCornerRadius'] * self.resamplingFactor)]))
                    if (mode.split("_")[1] == "ON"): image = image.rotate(180)
                    buttonImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                    self.__saveImage(buttonImage, imageName)
                    self.imageDictionary[imageName] = buttonImage
                images[mode] = buttonImage
            return images
        style = "switch_TypeA_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[2] == "styleA"): return generateStyleA()





    #Generate a image of switch_typeA
    def generate_LED_TypeA_Images(self, style, sizeX, sizeY, color):
        def generateStyleA():
            imageName = "@g@{:s}#{:s}#{:s}#{:s}".format(style, str(sizeX), str(sizeY), str(color))
            if imageName in self.imageDictionary.keys(): LEDImage = self.imageDictionary[imageName]
            else:
                image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                draw  = ImageDraw.Draw(image)
                draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = color,
                                        outline = params['outline'], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                        radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                LEDImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                self.__saveImage(LEDImage, imageName)
                self.imageDictionary[imageName] = LEDImage
            return LEDImage

        style = "LED_TypeA_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[2] == "styleA"): return generateStyleA()





    #Generate a image of switch_typeB
    def generate_switch_TypeB_Images(self, style, sizeX, sizeY):
        def generateStyleA():
            images = {"DEFAULT_OFF": None, "HOVERED_OFF": None, "CLICKED_OFF": None, "INACTIVE_OFF": None, "DEFAULT_ON": None, "HOVERED_ON": None, "CLICKED_ON": None, "INACTIVE_ON": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:s}#{:s}".format(style, mode, str(sizeX), str(sizeY))
                if imageName in self.imageDictionary.keys(): buttonImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                    draw  = ImageDraw.Draw(image)
                    #Box Drawing
                    draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill_'+mode.split("_")[0]],
                                           outline = params['outline_' + mode.split("_")[0]], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                           radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                    #Button Drawing
                    if (mode.split("_")[1] == "ON"):
                        gOffset = 3;
                        draw.rounded_rectangle((gOffset * self.resamplingFactor, gOffset * self.resamplingFactor, (sizeX - gOffset) * self.resamplingFactor, (sizeY - gOffset) * self.resamplingFactor), 
                                                fill = params['buttonFill_' + mode.split("_")[0]], outline = params['buttonOutline_' + mode.split("_")[0]], width = params['buttonOutlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                                radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['buttonCornerRadius'] * self.resamplingFactor)]))
                    buttonImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                    self.__saveImage(buttonImage, imageName)
                    self.imageDictionary[imageName] = buttonImage
                images[mode] = buttonImage
            return images
        style = "switch_TypeB_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[2] == "styleA"): return generateStyleA()
        




    #Generate a rail image of slider_TypeA
    def generate_slider_TypeA_RailImages(self, style, sizeX, sizeY, align = "horizontal"):
        def generateStyleA():
            images = {"DEFAULT": None, "HOVERED": None, "INACTIVE": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:s}#{:s}#{:s}".format(style, mode, str(sizeX), str(sizeY), align[0])
                if imageName in self.imageDictionary.keys(): railImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                    draw  = ImageDraw.Draw(image)
                    draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill_'+mode],
                                           outline = params['outline_'+mode], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                           radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                    if (align == "horizontal"):                                          railImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                    elif (align == "vertical"): image = image.rotate(90, expand = True); railImage = ImageTk.PhotoImage(image.resize((sizeY, sizeX), resample=Image.LANCZOS))
                    self.__saveImage(railImage, imageName)
                    self.imageDictionary[imageName] = railImage
                images[mode] = railImage
            return images

        style = "slider_TypeA_Rail_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[3] == "styleA"): return generateStyleA()

    #Generate a button image of slider_TypeA
    def generate_slider_TypeA_ButtonImages(self, style, sizeX, sizeY, align = "horizontal"):
        def generateStyleA():
            images = {"DEFAULT": None, "HOVERED": None, "CLICKED": None, "INACTIVE": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:s}#{:s}#{:s}".format(style, mode, str(sizeX), str(sizeY), align[0])
                if imageName in self.imageDictionary.keys(): buttonImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                    draw  = ImageDraw.Draw(image)
                    draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill_'+mode],
                                           outline = params['outline_'+mode], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                           radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                    if (align == "horizontal"):                                          buttonImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                    elif (align == "vertical"): image = image.rotate(90, expand = True); buttonImage = ImageTk.PhotoImage(image.resize((sizeY, sizeX), resample=Image.LANCZOS))
                    self.__saveImage(buttonImage, imageName)
                    self.imageDictionary[imageName] = buttonImage
                images[mode] = buttonImage
            return images

        style = "slider_TypeA_Button_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[3] == "styleA"): return generateStyleA()
        




    #Generate a rail image of scrollBar_TypeA
    def generate_scrollBar_TypeA_RailImages(self, style, sizeX, sizeY, align = "horizontal"):
        def generateStyleA():
            images = {"DEFAULT": None, "HOVERED": None, "INACTIVE": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:s}#{:s}#{:s}".format(style, mode, str(sizeX), str(sizeY), align[0])
                if imageName in self.imageDictionary.keys(): railImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                    draw  = ImageDraw.Draw(image)
                    draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill_'+mode],
                                           outline = params['outline_'+mode], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                           radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                    if (align == "horizontal"):                                          railImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                    elif (align == "vertical"): image = image.rotate(90, expand = True); railImage = ImageTk.PhotoImage(image.resize((sizeY, sizeX), resample=Image.LANCZOS))
                    self.__saveImage(railImage, imageName)
                    self.imageDictionary[imageName] = railImage
                images[mode] = railImage
            return images

        style = "scrollBar_TypeA_Rail_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[3] == "styleA"): return generateStyleA()

    #Generate a button image of scrollBar_TypeA
    def generate_scrollBar_TypeA_ButtonImages(self, style, sizeX, sizeY, align = "horizontal"):
        def generateStyleA():
            images = {"DEFAULT": None, "HOVERED": None, "CLICKED": None, "INACTIVE": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:s}#{:s}#{:s}".format(style, mode, str(sizeX), str(sizeY), align[0])
                if imageName in self.imageDictionary.keys(): buttonImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                    draw  = ImageDraw.Draw(image)
                    draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill_'+mode],
                                           outline = params['outline_'+mode], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                           radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                    if (align == "horizontal"):                                          buttonImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                    elif (align == "vertical"): image = image.rotate(90, expand = True); buttonImage = ImageTk.PhotoImage(image.resize((sizeY, sizeX), resample=Image.LANCZOS))
                    self.__saveImage(buttonImage, imageName)
                    self.imageDictionary[imageName] = buttonImage
                images[mode] = buttonImage
            return images

        style = "scrollBar_TypeA_Button_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[3] == "styleA"): return generateStyleA()
        




    #Generate a mainBox image of selectionBox_typeA
    def generate_selectionBox_TypeA_MainBoxImages(self, style, sizeX, sizeY):
        def generateStyleA():
            images = {"DEFAULT_OFF": None, "HOVERED_OFF": None, "CLICKED_OFF": None, "INACTIVE_OFF": None, "DEFAULT_ON": None, "HOVERED_ON": None, "CLICKED_ON": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:s}#{:s}".format(style, mode, str(sizeX), str(sizeY))
                if imageName in self.imageDictionary.keys(): mainBoxImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                    draw  = ImageDraw.Draw(image)
                    draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill_'+mode.split("_")[0]],
                                            outline = params['outline_'+mode.split("_")[0]], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                            radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                    sizeFactor = min([sizeX * 0.05, sizeY * 0.3])
                    xOff = sizeX - sizeFactor * 2
                    yOff = (sizeY - sizeFactor) / 2
                    draw.line(((xOff * self.resamplingFactor, yOff * self.resamplingFactor), ((xOff + sizeFactor / 2) * self.resamplingFactor, (yOff + sizeFactor) * self.resamplingFactor), ((xOff + sizeFactor) * self.resamplingFactor, yOff * self.resamplingFactor)), 
                                params['arrowFill'], width = 2 * self.resamplingFactor)
                    if (mode.split("_")[1] == "OFF"): image = ImageOps.flip(image)
                    mainBoxImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                    self.__saveImage(mainBoxImage, imageName)
                    self.imageDictionary[imageName] = mainBoxImage
                images[mode] = mainBoxImage
            return images
        style = "selectionBox_TypeA_MainBox_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[3] == "styleA"): return generateStyleA()

    #Generate a listBox image of selectionBox_typeA
    def generate_selectionBox_TypeA_ListBoxImages(self, style, sizeX, sizeY, displaySize):
        def generateStyleA():
            images = {"DEFAULT": None, "HOVERED": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:s}#{:s}#{:s}".format(style, mode, str(sizeX), str(sizeY), str(displaySize))
                if imageName in self.imageDictionary.keys(): listBoxImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor * displaySize), color = (0, 0, 0, 0))
                    if (0 < displaySize):
                        draw  = ImageDraw.Draw(image)
                        draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor * displaySize), fill = params['fill_'+mode],
                                                outline = params['outline_'+mode], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                                radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                        for i in range (displaySize - 1):
                            draw.line(((10 * self.resamplingFactor, (sizeY * (i + 1)) * self.resamplingFactor), ((sizeX - 10) * self.resamplingFactor, (sizeY * (i + 1)) * self.resamplingFactor)), 
                                        fill = params['boundaryFill'], width = params['boundaryWidth'] * self.resamplingFactor)
                        listBoxImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY * displaySize), resample=Image.LANCZOS))
                    else: listBoxImage = ImageTk.PhotoImage(Image.new(mode = "RGBA", size = (1, 1), color = (0, 0, 0, 0)))
                    self.__saveImage(listBoxImage, imageName)
                    self.imageDictionary[imageName] = listBoxImage
                images[mode] = listBoxImage
            return images
        style = "selectionBox_TypeA_ListBox_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[3] == "styleA"): return generateStyleA()





    #Generate a image of matrixDisplayBox_typeA
    def generate_matrixDisplayBox_TypeA_Images(self, style, sizeX, sizeY, elementWidth, elementHeight, nDisplayedColumns, nDisplayedRows, gOffset, columnData):
        def generateStyleA():
            images = {"DEFAULT": None, "HOVERED": None, "INACTIVE": None}
            for mode in images.keys():
                imageName = "@g@{:s}#{:s}#{:d}#{:d}#{:d}x{:d}#{:d}#".format(style, mode, sizeX, sizeY, nDisplayedColumns, nDisplayedRows, gOffset)
                for i in range (len(columnData)): imageName += "o{:.1f}%{:.1f}c".format(columnData[i][0],columnData[i][1]).replace(".", "d")
                if imageName in self.imageDictionary.keys(): frameImage = self.imageDictionary[imageName]
                else:
                    image = Image.new(mode = "RGBA", size = (sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), color = (0, 0, 0, 0))
                    draw  = ImageDraw.Draw(image)
                    draw.rounded_rectangle((0, 0, sizeX * self.resamplingFactor, sizeY * self.resamplingFactor), fill = params['fill_'+mode],
                                           outline = params['outline_'+mode], width = params['outlineWidth'] * self.resamplingFactor, corners = (True, True, True, True), 
                                           radius = min([(min([sizeX * self.resamplingFactor, sizeY * self.resamplingFactor]) / 2 - 1), (params['cornerRadius'] * self.resamplingFactor)]))
                    #Draw Horizontal Boundaries
                    for i in range (nDisplayedRows + 1):
                        draw.line(((gOffset * self.resamplingFactor, (gOffset + elementHeight * i) * self.resamplingFactor), ((sizeX - gOffset) * self.resamplingFactor, (gOffset + elementHeight * i) * self.resamplingFactor)), 
                                    fill = params['boundaryFill'], width = params['boundaryWidth'] * self.resamplingFactor)
                    #Draw Vertical Boundaries
                    drawPosition_H = gOffset
                    for i in range (nDisplayedColumns + 1):
                        draw.line(((drawPosition_H * self.resamplingFactor, gOffset * self.resamplingFactor), (drawPosition_H * self.resamplingFactor, (sizeY - gOffset) * self.resamplingFactor)), 
                                    fill = params['boundaryFill'], width = params['boundaryWidth'] * self.resamplingFactor)
                        if (i < len(columnData)): drawPosition_H += columnData[i][1]
                    frameImage = ImageTk.PhotoImage(image.resize((sizeX, sizeY), resample=Image.LANCZOS))
                    self.__saveImage(frameImage, imageName)
                    self.imageDictionary[imageName] = frameImage
                images[mode] = frameImage
            return images
        style = "matrixDisplayBox_TypeA_" + style
        params = self.styleThemeDictionary[style]
        if (style.split("_")[2] == "styleA"):
            return generateStyleA()





    #Generate a image of multiple characters
    def generate_textImage(self, text, textSize, style = None, textFont = None, textFill = None, textStrokeFill = None, textStrokeWidth = None):
        charImages = list()
        textImageLength = 0
        for i in range (len(text)): 
            charImages.append(self.generate_characterImage(text[i], textSize, style = style, textFont = textFont, textFill = textFill, textStrokeFill = textStrokeFill, textStrokeWidth = textStrokeWidth))
            textImageLength += charImages[i][1]
        textImageHeight = charImages[0][0].height()

        textImage = Image.new(mode = "RGBA", size = (textImageLength, textImageHeight), color = (0, 0, 0, 0))
        pastePosition = 0
        for charData in charImages:
            charImage = ImageTk.getimage(charData[0])
            textImage.paste(charImage, (pastePosition, 0))
            pastePosition += charData[1]
        textImage = ImageTk.PhotoImage(textImage)

        return textImage

    #Generate a image of a single character
    #"style" defines the pre-determined textFill, textStrokeFill, and textStrokeWidth
    #Character Images: [CHARACTER]_[FONTTYPE]_[TEXTSIZE]_[TEXTFILL]_[TEXTSTROKEFILL]_[TEXTSTROKEWIDTH]
    def generate_characterImage(self, text, textSize, style = None, textFont = None, textFill = None, textStrokeFill = None, textStrokeWidth = None, mask = (0, 0, 0, 0)):
        def generateImage(self):
            imageName = "@c@{:s}#{:s}#{:s}#{:s}#{:s}#{:s}#{:s}".format(text, textFont, str(textSize), str(textFill), str(textStrokeFill), str(textStrokeWidth), str(mask))
            if imageName in self.imageDictionary.keys(): #If the image already exists in the library, simply return the tuple of image data from the library
                return self.imageDictionary[imageName]
            else: #If the image does not exist in the library, create one, save it to the library, and return the image data
                font_PIL = ImageFont.truetype(textFont, textSize * self.resamplingFactor)
                textPixelLength = int(font_PIL.getlength(text) * self.textWidthCompensationCoefficient / self.resamplingFactor)
                textPixelHeight = int(textSize * self.textHeightCompensationCoefficient)
                image = Image.new(mode = "RGBA", size = (textPixelLength * self.resamplingFactor, textPixelHeight * self.resamplingFactor), color = mask)
                draw  = ImageDraw.Draw(image)
                draw.text((textPixelLength * self.resamplingFactor / 2, textPixelHeight * self.resamplingFactor / 2 + 1), text, fill = textFill, font = font_PIL, anchor = 'mm', spacing = 3, align = 'center', stroke_fill = textStrokeFill, stroke_width = textStrokeWidth * self.resamplingFactor)
                image = ImageTk.PhotoImage(image.resize((textPixelLength, textPixelHeight), resample=Image.LANCZOS))
                self.imageDictionary[imageName] = (image, textPixelLength, textPixelHeight)
                return self.imageDictionary[imageName]

        if (style is None): #Use the parameters 'textFont', 'textFill', 'textStrokeFill', and 'textStrokeWidth' when no style is selected
            return generateImage(self)
        else: #Use the pre-determined parameters of the style 'generalText_StyleA', but when the parameter passed is not 'None', used the passed parameter
            if (textFont is None):        textFont = self.textStyleThemeDictionary[style + "_PIL"]['fontFamily']
            if (textFill is None):        textFill = self.textStyleThemeDictionary[style + "_PIL"]['fill']
            if (textStrokeFill is None):  textStrokeFill = self.textStyleThemeDictionary[style + "_PIL"]['strokeFill']
            if (textStrokeWidth is None): textStrokeWidth = self.textStyleThemeDictionary[style + "_PIL"]['strokeWidth']
            return generateImage(self)
    
    def getTextStyleThemeTk(self, stID):
        stID += "_Tk"
        if (stID in self.textStyleThemeDictionary.keys()): return self.textStyleThemeDictionary[stID].copy()
        else: return self.textStyleThemeDictionary["generalText_StyleA_Tk"].copy()

    def getTextStyleThemePIL(self, stID):
        stID += "_PIL"
        if (stID in self.textStyleThemeDictionary.keys()): return self.textStyleThemeDictionary[stID].copy()
        else: return self.textStyleThemeDictionary["generalText_StyleA_PIL"].copy()

    def __saveImage(self, image, imageName):
        saveImage = ImageTk.getimage(image); saveImage.save(os.path.join(path_SYSGRAPHICSLIBRARY, imageName + ".png"), "PNG")
#Graphical Object Styles END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Auxillary Functions --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def convertRGBtoHex(rValue, gValue, bValue):
    return "#" + hex(rValue)[2:] + hex(gValue)[2:] + hex(bValue)[2:]

#Auxillary Functions END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------