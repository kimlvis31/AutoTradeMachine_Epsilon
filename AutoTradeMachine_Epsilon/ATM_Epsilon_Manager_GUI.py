from lib2to3.pygram import Symbols
from random import randint
from ATM_Epsilon_Manager_IPC import assistant_IPC
from ATM_Epsilon_tkinterExtension import tkE_userInput, \
                                         graphics_Generator, \
                                         constantGraphic_typeA, constantTextGraphic_typeA, constantImageGraphic_typeA, constantImageGraphic_typeB, \
                                         button_typeA, switch_typeA, switch_typeB, activeTextBox_typeA, textInputBox_typeA, LED_typeA, gaugeBar_typeA, slider_typeA, scrollBar_typeA, selectionBox_typeA, matrixDisplayBox_typeA, \
                                         convertRGBtoHex
from ATM_Epsilon_tkinterExtension_MS import dataStatusImager

import tkinter
import time
from PIL import Image, ImageTk, ImageDraw
from shapely.geometry import Point, Polygon
import screeninfo
from pympler import asizeof
import copy
import os
import types
import numpy
import pprint
from datetime import datetime
import ciso8601

path_PROJECT = os.path.dirname(os.path.realpath(__file__))
path_IMAGES = os.path.join(path_PROJECT + r"\data\imgs")

MANAGERNAME = "GUI"

class manager_GUI:
    #MANAGER INITIALIZATION -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __init__(self, programLogger, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T):
        #Create Local Instance of Program Data Logger
        self.programLogger = programLogger
        self.programLogger.clearPMessages()
        
        #Send Initialization Start Message
        self.programLogger.printPMessage("INITIALIZING {:s} MANAGER...".format(MANAGERNAME))
        
        #Get Screen Info
        self.screens = screeninfo.get_monitors()
        self.pScreen = None
        for screen in self.screens:
            if (screen.is_primary == True): self.pScreen = screen

        #Process Control Variables
        self.processRepeat = True
        self.processTimersUpdateBuffer = None
        self.processTimers = {'updated': False, 'records': list(), 't_processLoop_avg':  0, 't_process_avg':      0, 't_processTk_avg':    0, 
                                                                   'ipcb_readTime_avg':  0, 'ipcb_readSize_avg':  0, 'ipcb_readRate_avg':  0,
                                                                   'ipcb_writeTime_avg': 0, 'ipcb_writeSize_avg': 0, 'ipcb_writeRate_avg': 0, 'nRecords': 0}
        self.processTimerAvgStandard = 1

        #Program Managers List Read
        self.atm_Managers = atm_Managers.copy(); self.atm_Managers.remove(MANAGERNAME)

        #IPC Assistant Initialization
        self.assistantIPC = assistant_IPC(programLogger, MANAGERNAME, self.atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T)
        self.darHanlderDictionary = {"DAR TEST": "[GUI] DAR TEST SUCCESSFUL", "ATMMANAGERS": self.atm_Managers, "PTIMERS": self.processTimers, "PTIMERS_AVGSTANDARD": self.processTimerAvgStandard}
        self.farHanlderDictionary = dict(); self.__initializeFARs()
        self.IPCResultHandlers = dict()

        #TKinter Initialization
        self.window = tkinter.Tk()
        self.window.title("ATM_EPSILON")
        self.window.geometry("{:d}x{:d}".format(self.pScreen.width, self.pScreen.height)) #Window size setting, 2560x1440
        self.window.resizable(False, False)
        self.window.attributes("-fullscreen", True) #Set the window to start as fullscreen mode
        self.window.bind("<F11>", lambda event: self.window.attributes("-fullscreen", not self.window.attributes("-fullscreen"))) #Enables F11 Key to go to and escape from fullScreen]

        #Canvas Initialization
        self.canvas = tkinter.Canvas(self.window, width = self.pScreen.width, height = self.pScreen.height, bg = "gray10", bd = 0, highlightthickness = 0)
        self.canvas.pack()

        #Input Devices Control
        self.tkE_userInput = tkE_userInput(self.window)

        #GUIOs Initialization
        self.graphicsGenerator = graphics_Generator(resamplingFactor = 4)
        
        #PAGE SETUP --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #GUIO Control Variables
        self.searchGUIO = True
        self.selectedGUIO = None
        self.userInputSubscriber = list()
        
        #General Functions
        self.generalFunctions = dict()
        self.generalFunctions["GUIOSEARCHON"] = self.__GUIOSearchOn
        self.generalFunctions["GUIOSEARCHOFF"] = self.__GUIOSearchOff
        self.generalFunctions["SUBSCRIBEUSERINPUT"] = self.__addUserInputSubscriber
        self.generalFunctions["UNSUBSCRIBEUSERINPUT"] = self.__removeUserInputSubscriber

        #Timer Function Assignments
        self.timerFunctions = {"ALL": dict()}

        #Page Data Initialization
        self.pages = dict()
        self.currentPage = None
        self.pageVariables = dict()
        self.objectFunctions = dict()
        self.pageNavigationFunctions = dict()

        def __loadPage(manager, pageName):
            #Call Page Closing Function and Hide all the elements of the current page
            if manager.currentPage is not None:
                manager.pageNavigationFunctions[manager.currentPage+"_CLOSE"](manager)
                for objectName in manager.pages[manager.currentPage].keys(): manager.pages[manager.currentPage][objectName].hide()
            mousePos = manager.tkE_userInput.getMousePos() #Get current mouse position
            if (manager.selectedGUIO is not None):
                manager.__resultInterpreter(manager.currentPage, manager.selectedGUIO, manager.pages[manager.currentPage][manager.selectedGUIO].processUserInput("ESCAPED")) #Release the last selected GUIO
                manager.selectedGUIO = None
            manager.currentPage = pageName
            manager.pageNavigationFunctions[manager.currentPage+"_LOAD"](manager)
            #Perform a new GUIO search
            manager.__searchGUIO(mousePos[0], mousePos[1])
            #Show all the elements of the new page
            for objectName in manager.pages[manager.currentPage].keys(): manager.pages[manager.currentPage][objectName].show()
        
        #Other Processes Initialization Check & Load Loading Page -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAMLOAD"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAMLOAD = dict()
        def page_PROGRAMLOAD_load(manager):
            pass
        def page_PROGRAMLOAD_close(manager):
            currentTimeString = time.ctime()
            day = currentTimeString[0:3]; month = currentTimeString[4:7]; dayNum = currentTimeString[8:10].strip(); timeN = currentTimeString[11:19]; year = currentTimeString[20:24]
            if   (dayNum == "1"):  dayNum = "1st"
            elif (dayNum == "2"):  dayNum = "2nd"
            elif (dayNum == "3"):  dayNum = "3rd"
            elif (dayNum == "21"): dayNum = "21st"
            elif (dayNum == "22"): dayNum = "22nd"
            elif (dayNum == "31"): dayNum = "31st"
            else:                  dayNum += "th"
            main_navigationGUIOs["PAGECLOCK"].updateText("{:s} {:s} {:s} {:s} {:s}".format(year, month, dayNum, day, timeN))
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAMLOAD_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAMLOAD_close
        
        self.pageVariables["PROGRAMLOAD"] = {'procInitMsgs': dict(), 'initComplete': False}
        page_PROGRAMLOAD["PROGRAMTITLE"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 0, 520, 2560, 200, style = "styleA_themeB", layer = 1, text = "AUTO TRADE MACHINE EPSILON", textFill = (255, 255, 255, 255), textSize = 80)
        page_PROGRAMLOAD["LOADPERCENTAGEBAR"] = gaugeBar_typeA(self.canvas, self.graphicsGenerator, 20, 1380, 2520, 40, "styleA_themeD", layer = 1, align = "horizontal", showText = True)
        page_PROGRAMLOAD["INITIALIZATIONMSG"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator, 20, 1340, 2520, 40, boxStyle = "empty", layer = 1, text = "", textSize = 18, textStyle = "generalText_StyleA")

        self.pages[thisPage] = page_PROGRAMLOAD
        
        #Object Functions

        #Page Timer Functions
        def timerFunction_page_PROGRAMLOAD0(manager):
            targetManagers = ["SECURITYCONTROL", "AUTOTRADER", "BINANCEAPI", "DATAANALYSIS", "DATAMANAGEMENT"]
            completionPercentage = 0
            updateText = None
            for targetManager in targetManagers:
                procStatus = manager.assistantIPC.getPRD(targetManager, "PROC_STATUS")
                if   (procStatus == None):     managerCompletion = 0
                elif (procStatus == "ACTIVE"): managerCompletion = 100
                elif (procStatus.split("_")[0] == "INITIALIZING"): 
                    managerCompletion = int(procStatus.split("_")[1])
                    initMsg = procStatus.split("_")[2]
                    if (targetManager in manager.pageVariables["PROGRAMLOAD"]["procInitMsgs"].keys()):
                        if (manager.pageVariables["PROGRAMLOAD"]["procInitMsgs"][targetManager] != initMsg): manager.pageVariables["PROGRAMLOAD"]["procInitMsgs"][targetManager] = initMsg; updateText = initMsg
                    else: manager.pageVariables["PROGRAMLOAD"]["procInitMsgs"][targetManager] = initMsg; updateText = initMsg
                completionPercentage += managerCompletion / len(targetManagers)
            manager.pages["PROGRAMLOAD"]["LOADPERCENTAGEBAR"].updateValue(completionPercentage)
            newGaugeBarColor = (250 - int(130 * completionPercentage / 100), int(100 * completionPercentage / 100) + 100, 100)
            manager.pages["PROGRAMLOAD"]["LOADPERCENTAGEBAR"].changeColor(newGaugeBarColor)
            manager.pages["PROGRAMLOAD"]["LOADPERCENTAGEBAR"].updateText("{:.1f} %".format(completionPercentage))
            if (updateText != None): manager.pages["PROGRAMLOAD"]["INITIALIZATIONMSG"].updateText(updateText)
            if (completionPercentage == 100): 
                manager.pages["PROGRAMLOAD"]["LOADPERCENTAGEBAR"].updateText("Initialization Complete")
                manager.pages["PROGRAMLOAD"]["INITIALIZATIONMSG"].updateText("<PRESS ANY KEY TO CONTINUE>")
                manager.pageVariables["PROGRAMLOAD"]['initComplete'] = True
                return False
        self.timerFunctions[thisPage]["CHECKINITIALIZATIONSTATUS"] = self.__timerFunction(function = timerFunction_page_PROGRAMLOAD0, interval = 10)
        #Check User Input Once Initialization Completes
        def timerFunction_page_PROGRAMLOAD1(manager):
            if (manager.pageVariables["PROGRAMLOAD"]['initComplete'] == True):
                while (manager.tkE_userInput.isInputAvailable() == True):
                    if (manager.tkE_userInput.getEvent()[0] == "KEY_CLICKED"): __loadPage(manager, "DASHBOARD"); return False
        self.timerFunctions[thisPage]["CHECKUSERINPUT"] = self.__timerFunction(function = timerFunction_page_PROGRAMLOAD1, interval = 10)
        #Other Processes Initialization Check & Load Loading Page END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #Commonly Used GUIO Set
        main_navigationGUIOs = dict()
        main_navigationGUIOs["MAINNAVIGATION_FRAME"]      = constantGraphic_typeA(self.canvas, self.graphicsGenerator, 5, 5, 2225, 50, "styleA_themeA", layer = 0)
        main_navigationGUIOs["MAINNAVIGATION_DASHBOARD"]  = button_typeA(self.canvas, self.graphicsGenerator,   10, 10, 180, 40, "styleA_themeA", layer = 1, text = "DASHBOARD",   textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_MANAGEDATA"] = button_typeA(self.canvas, self.graphicsGenerator,  195, 10, 180, 40, "styleA_themeA", layer = 1, text = "MANAGE DATA", textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_ANALYSIS"]   = button_typeA(self.canvas, self.graphicsGenerator,  380, 10, 180, 40, "styleA_themeA", layer = 1, text = "ANALYSIS",    textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_EMPTY0"]     = button_typeA(self.canvas, self.graphicsGenerator,  565, 10, 180, 40, "styleA_themeA", layer = 1, text = "EMPTY0",      textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_EMPTY1"]     = button_typeA(self.canvas, self.graphicsGenerator,  750, 10, 180, 40, "styleA_themeA", layer = 1, text = "EMPTY1",      textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_EMPTY2"]     = button_typeA(self.canvas, self.graphicsGenerator,  935, 10, 180, 40, "styleA_themeA", layer = 1, text = "EMPTY2",      textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_EMPTY3"]     = button_typeA(self.canvas, self.graphicsGenerator, 1120, 10, 180, 40, "styleA_themeA", layer = 1, text = "EMPTY3",      textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_EMPTY4"]     = button_typeA(self.canvas, self.graphicsGenerator, 1305, 10, 180, 40, "styleA_themeA", layer = 1, text = "EMPTY4",      textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_EMPTY5"]     = button_typeA(self.canvas, self.graphicsGenerator, 1490, 10, 180, 40, "styleA_themeA", layer = 1, text = "EMPTY5",      textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_EMPTY6"]     = button_typeA(self.canvas, self.graphicsGenerator, 1675, 10, 180, 40, "styleA_themeA", layer = 1, text = "EMPTY6", textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_APICONTROL"] = button_typeA(self.canvas, self.graphicsGenerator, 1860, 10, 180, 40, "styleA_themeA", layer = 1, text = "API CONTROL",     textSize = 18)
        main_navigationGUIOs["MAINNAVIGATION_PROGRAM"]    = button_typeA(self.canvas, self.graphicsGenerator, 2045, 10, 180, 40, "styleA_themeA", layer = 1, text = "PROGRAM",    textSize = 18)
        main_navigationGUIOs["PAGECLOCKFRAME"] = constantGraphic_typeA(self.canvas, self.graphicsGenerator, 2235, 5, 320, 50, "styleA_themeA", layer = 0)
        main_navigationGUIOs["PAGECLOCK"]      = activeTextBox_typeA(self.canvas, self.graphicsGenerator, 2240, 10, 310, 40, boxStyle = "styleA_pageClock", layer = 1, text = "", textSize = 16, textStyle = "pageClockFont")
        main_navigationGUIOs["PAGEOBJECTFRAME"] = constantGraphic_typeA(self.canvas, self.graphicsGenerator, 5, 60, 2550, 1375, "styleA_themeA", layer = 0)

        #PAGE "DASHBOARD" -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "DASHBOARD"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_DASHBOARD = dict()
        page_DASHBOARD.update(main_navigationGUIOs)

        def page_DASHBOARD_load(manager):
            manager.pages["DASHBOARD"]["MAINNAVIGATION_DASHBOARD"].deactivate()
        def page_DASHBOARD_close(manager):
            manager.pages["DASHBOARD"]["MAINNAVIGATION_DASHBOARD"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_DASHBOARD_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_DASHBOARD_close
        self.pages[thisPage] = page_DASHBOARD

        #Object Functions
        self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        #PAGE "DASHBOARD" END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "MANAGE DATA" -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "MANAGEDATA"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_MANAGEDATA = dict()
        page_MANAGEDATA.update(main_navigationGUIOs)

        self.pageVariables[thisPage]["SS_MRT"] = None #Selected Symbol Market Registration Timestamp

        def page_MANAGEDATA_load(manager):
            manager.pages["MANAGEDATA"]["MAINNAVIGATION_MANAGEDATA"].deactivate()
            sdsData = manager.assistantIPC.getPRD("DATAMANAGEMENT", "SDS")
            manager.pages["MANAGEDATA"]["MARKETDATA_MARKETSELECTIONBOX"].updateList(list(sdsData.keys()))

        def page_MANAGEDATA_close(manager):
            manager.pages["MANAGEDATA"]["MAINNAVIGATION_MANAGEDATA"].activate()
            
        self.pageVariables[thisPage]["DBCONNECTION"] = False
        page_MANAGEDATA["STATUSLED"] = LED_typeA(self.canvas, self.graphicsGenerator, 10, 65, 2540, 30, "styleA_themeB", layer = 1, colors = {'online': (130, 210, 65, 255), 'offline': (240, 90, 90, 255)}, mode = 'offline')
        page_MANAGEDATA["STATUSLEDTEXT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator, 10, 64, 2540, 30, boxStyle = "empty", layer = 1, text = "DATABASE NOT FOUND", textSize = 12, textStyle = "generalText_StyleA")
        page_MANAGEDATA["DBSTATUSBAR"] = gaugeBar_typeA(self.canvas, self.graphicsGenerator, 10, 100, 2540, 30, "styleA_themeD", layer = 1, align = "horizontal", showText = True); page_MANAGEDATA["DBSTATUSBAR"].updateText("N/A")

        page_MANAGEDATA["DBDRIVENAMETEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 135, 230, 30, style = "styleA_themeA", layer = 1, text = "DATABASE DRIVENAME", textFill = (255, 255, 255, 255), textSize = 14)
        page_MANAGEDATA["DBDRIVENAMEACTIVETEXT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator, 245, 135, 230, 30, boxStyle = "styleA_themeC", layer = 1, text = "N/A", textSize = 10, textStyle = "generalText_StyleA")
        page_MANAGEDATA["DBDIRTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 480, 135, 230, 30, style = "styleA_themeA", layer = 1, text = "DATABASE DIRECTORY", textFill = (255, 255, 255, 255), textSize = 14)
        page_MANAGEDATA["DBDIRACTIVETEXT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator, 715, 135, 230, 30, boxStyle = "styleA_themeC", layer = 1, text = "N/A", textSize = 10, textStyle = "generalText_StyleA")
        page_MANAGEDATA["MARKETDATA_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 170, 935, 30, style = "styleA_themeA", layer = 1, text = "MARKET DATA", textFill = (255, 255, 255, 255), textSize = 14)
        self.pageVariables[thisPage]["MARKETSELECTED"] = None
        page_MANAGEDATA["MARKETDATA_MARKETSELECTIONTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 205, 250, 30, style = "styleA_themeA", layer = 1, text = "MARKET", textFill = (255, 255, 255, 255), textSize = 14)
        page_MANAGEDATA["MARKETDATA_MARKETSELECTIONBOX"]  = selectionBox_typeA(self.canvas, self.graphicsGenerator, 265, 205, 250, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        page_MANAGEDATA["MARKETDATA_FILTERSELECTIONTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  520, 205, 210, 30, style = "styleA_themeA", layer = 1, text = "SHOW", textFill = (255, 255, 255, 255), textSize = 14)
        page_MANAGEDATA["MARKETDATA_FILTERSELECTIONTBOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator, 735, 205, 210, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5, elementList = ["ALL", "ACTIVE", "SUBSCRIBED"])
        page_MANAGEDATA["MARKETDATA_FILTERSELECTIONTBOX"].editSelected("ALL"); self.pageVariables[thisPage]["MARKETDATAFILTERSELECTED"] = "ALL"
        page_MANAGEDATA["MARKETDATA_SEARCHINPUTBOXTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,   10, 240, 250, 30, style = "styleA_themeA", layer = 1, text = "SEARCH", textFill = (255, 255, 255, 255), textSize = 14)
        page_MANAGEDATA["MARKETDATA_SEARCHINPUTBOX"]     = textInputBox_typeA(self.canvas, self.graphicsGenerator,         265, 240, 680, 30, "styleA_themeA", layer = 1, maxTextLength = 64)
        page_MANAGEDATA["MARKETDATA_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator, 10, 275, 900, 1120, "styleA_themeA", layer = 1, nDisplayedColumns = 5, nDisplayedRows = 20, 
                                                               columnTitles= [("INDEX",               "center", "white",  ("Arial", 12, "bold")),
                                                                              ("SYMBOL",              "center", "white",  ("Arial", 12, "bold")),
                                                                              ("MARKET REGISTRATION", "center", "white",  ("Arial", 12, "bold")),
                                                                              ("MARKET TYPE",         "center", "white",  ("Arial", 12, "bold")),
                                                                              ("SUBSCRBIED",          "center", "white",  ("Arial", 12, "bold"))],
                                                               customColumnRatio = (1, 2, 3, 1.5, 1.5), allowSelection = True)
        page_MANAGEDATA["MARKETDATA_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator, 915, 275, 1120, 30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_MANAGEDATA["MARKETDATA_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        self.pageVariables[thisPage]["MARKETDATAMATRIX_SYMBOLS"] = None
        self.pageVariables[thisPage]["SYMBOLSELECTED"] = None

        page_MANAGEDATA["MARKETDATASUBSCRIPTION_BUTTON1"] = button_typeA(self.canvas, self.graphicsGenerator,  10, 1400, 200, 30, "styleA_themeB", layer = 1, text = "SUBSCRIBE", textSize = 16, mode = "INACTIVE")
        page_MANAGEDATA["MARKETDATASUBSCRIPTION_BUTTON2"] = button_typeA(self.canvas, self.graphicsGenerator, 215, 1400, 200, 30, "styleA_themeB", layer = 1, text = "UNSUBSCRIBE", textSize = 16, mode = "INACTIVE")
        page_MANAGEDATA["DATAMANAGEMENTMESSAGEBOX"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator, 420, 1400, 525, 30, boxStyle = "styleA_themeC", layer = 1, text = "-", textSize = 10, textStyle = "generalText_StyleA")

        page_MANAGEDATA["SYMBOLDATAMATRIXTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,   1230, 135, 800, 30, style = "styleA_themeA", layer = 1, text = "DATA INFORMATION", textFill = (255, 255, 255, 255), textSize = 14)
        page_MANAGEDATA["SELECTEDDATANAMETEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,   1230, 170, 395, 30, style = "styleA_themeA", layer = 1, text = "SELECTED SYMBOL", textFill = (255, 255, 255, 255), textSize = 14)
        page_MANAGEDATA["SELECTEDDATANAMEACTIVETEXT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,  1630, 170, 400, 30, boxStyle = "styleA_themeC", layer = 1, text = "-", textSize = 10, textStyle = "generalText_StyleA")

        

        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_MANAGEDATA_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_MANAGEDATA_close
        self.pages[thisPage] = page_MANAGEDATA

        #Object Functions
        self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")

        #General Auxillary Function for 'thisPage'
        def __pageAux_MANAGEDATA_UPDATEMARKETDATA_MATRIX(manager, holdPosition = False, holdSelection = False):
            if (manager.pageVariables["MANAGEDATA"]["MARKETSELECTED"] == "BINANCE"):
                marketData = manager.assistantIPC.getPRD("BINANCEAPI", "MARKET")             #Bring in Binance Market Data via PRD
                sdsData    = manager.assistantIPC.getPRD("DATAMANAGEMENT", "SDS")["BINANCE"] #Bring in SDS via PRD
                marketDataKeys = list(marketData.keys()); marketDataLen = len(marketDataKeys)
                #Filter the displaylist
                filterSelected = manager.pageVariables["MANAGEDATA"]["MARKETDATAFILTERSELECTED"]
                if (filterSelected == "ACTIVE"):
                    newMarketDataKeys = list()
                    for i in range (marketDataLen):
                        symbolAPI = marketDataKeys[i]
                        if (marketData[symbolAPI]['active'] == True): newMarketDataKeys.append(symbolAPI)
                    marketDataKeys = newMarketDataKeys; marketDataLen = len(marketDataKeys)
                elif (filterSelected == "SUBSCRIBED"):
                    marketDataKeys = list(sdsData.keys()); marketDataLen = len(marketDataKeys)
                #Sort the displaylist
                stringFilter = manager.pages["MANAGEDATA"]["MARKETDATA_SEARCHINPUTBOX"].getText()
                if (0 < len(stringFilter)):
                    newMarketDataKeys = list()
                    for i in range (marketDataLen):
                        symbolAPI = marketDataKeys[i]
                        if (stringFilter in symbolAPI): newMarketDataKeys.append(symbolAPI)
                    marketDataKeys = newMarketDataKeys; marketDataLen = len(marketDataKeys)
                manager.pageVariables["MANAGEDATA"]["MARKETDATAMATRIX_SYMBOLS"] = marketDataKeys
                #Create and Update the Matrix
                sdsMatrix = [[],[],[],[],[]]
                for i in range (marketDataLen):
                    symbolAPI          = marketDataKeys[i]
                    symbolMarketStatus = marketData[symbolAPI]['active']
                    marketType         = marketData[symbolAPI]['marketType']
                    if (symbolMarketStatus == True): generalTextColor = "white"
                    else:                            generalTextColor = "grey"
                    sdsMatrix[0].append(("{:d} / {:d}".format(i + 1, marketDataLen),     "center", generalTextColor, ("Arial", 10, "")))
                    sdsMatrix[1].append((symbolAPI,                                      "center", generalTextColor, ("Arial", 10, "")))
                    timestamp = marketData[symbolAPI]['mrktRegTimeStamp']
                    if (timestamp == None): sdsMatrix[2].append(("None", "center", generalTextColor, ("Arial", 10, "")))
                    else:
                        timestamp_str = datetime.fromtimestamp(timestamp/1000).strftime("%Y-%m-%d %H:%M")
                        sdsMatrix[2].append(("{:s} [{:s} UTC]".format(str(int(timestamp/1000)), timestamp_str), "center", generalTextColor, ("Arial", 10, "")))
                    if (symbolMarketStatus == True):
                        if   (marketType == "SPOT"):   sdsMatrix[3].append(("SPOT",       "center", "skyblue",    ("Arial", 10, "")))
                        elif (marketType == "USDS-M"): sdsMatrix[3].append(("USD(S) - M", "center", "lightgreen", ("Arial", 10, "")))
                        elif (marketType == "COIN-M"): sdsMatrix[3].append(("COIN - M",   "center", "orange",     ("Arial", 10, "")))
                        if (symbolAPI in sdsData.keys()): sdsMatrix[4].append(("TRUE",  "center", "skyblue", ("Arial", 10, "")))
                        else:                             sdsMatrix[4].append(("FALSE", "center", "salmon",  ("Arial", 10, "")))
                    else: 
                        sdsMatrix[3].append((marketType, "center", "grey",    ("Arial", 10, "")))
                        sdsMatrix[4].append(("FALSE",    "center", "grey",    ("Arial", 10, "")))
                manager.pages["MANAGEDATA"]["MARKETDATA_MATRIX"].updateMatrix(sdsMatrix, holdPosition = holdPosition, holdSelection = holdSelection)
                manager.pages["MANAGEDATA"]["MARKETDATA_MATRIX_SB_V"].changeViewRange(manager.pages["MANAGEDATA"]["MARKETDATA_MATRIX"].getViewRange()['vertical'])
        def __guioF_MANAGEDATA_MARKETDATA_MARKETSELECTIONBOX_SELECTIONUPDATED(manager):
            manager.pageVariables["MANAGEDATA"]["MARKETSELECTED"] = manager.pages["MANAGEDATA"]["MARKETDATA_MARKETSELECTIONBOX"].getSelected()
            page_MANAGEDATA["MARKETDATA_FILTERSELECTIONTBOX"].editSelected("ALL")
            __pageAux_MANAGEDATA_UPDATEMARKETDATA_MATRIX(manager)
        self.objectFunctions[thisPage+"-MARKETDATA_MARKETSELECTIONBOX-SELECTIONUPDATED"] = __guioF_MANAGEDATA_MARKETDATA_MARKETSELECTIONBOX_SELECTIONUPDATED
        def __guioF_MANAGEDATA_MARKETDATA_FILTERSELECTIONTBOX_SELECTIONUPDATED(manager):
            newSelected = page_MANAGEDATA["MARKETDATA_FILTERSELECTIONTBOX"].getSelected()
            if (manager.pageVariables["MANAGEDATA"]["MARKETDATAFILTERSELECTED"] != newSelected): 
                manager.pageVariables["MANAGEDATA"]["MARKETDATAFILTERSELECTED"] = newSelected
                __pageAux_MANAGEDATA_UPDATEMARKETDATA_MATRIX(manager)
        self.objectFunctions[thisPage+"-MARKETDATA_FILTERSELECTIONTBOX-SELECTIONUPDATED"] = __guioF_MANAGEDATA_MARKETDATA_FILTERSELECTIONTBOX_SELECTIONUPDATED
        def __guioF_APICONTROL_MARKETDATA_SEARCHINPUTBOX_TEXTUPDATED(manager):
            __pageAux_MANAGEDATA_UPDATEMARKETDATA_MATRIX(manager)
        self.objectFunctions[thisPage+"-MARKETDATA_SEARCHINPUTBOX-TEXTUPDATED"] = __guioF_APICONTROL_MARKETDATA_SEARCHINPUTBOX_TEXTUPDATED

        def __guioF_MANAGEDATA_MARKETDATA_MATRIX_SELECTIONUPDATED(manager):
            selectionIndex = manager.pages["MANAGEDATA"]["MARKETDATA_MATRIX"].getSelected()
            manager.pages["MANAGEDATA"]["DATAMANAGEMENTMESSAGEBOX"].updateText("-")
            if (selectionIndex == None):
                manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON1"].deactivate()
                manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON2"].deactivate()
                manager.pageVariables["MANAGEDATA"]["SYMBOLSELECTED"] = None
            else:
                selectedSymbol = manager.pageVariables["MANAGEDATA"]["MARKETDATAMATRIX_SYMBOLS"][selectionIndex]; manager.pageVariables["MANAGEDATA"]["SYMBOLSELECTED"] = selectedSymbol
                marketSelected = manager.pageVariables["MANAGEDATA"]["MARKETSELECTED"]
                sdsData = manager.assistantIPC.getPRD("DATAMANAGEMENT", "SDS")[marketSelected]
                if (selectedSymbol in sdsData.keys()):
                    manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON1"].deactivate()
                    manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON2"].activate()
                else:
                    if (marketSelected == "BINANCE"):
                        marketData = manager.assistantIPC.getPRD("BINANCEAPI", "MARKET")
                        if (marketData[selectedSymbol]['active'] == True):
                            manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON1"].activate()
                            manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON2"].deactivate()
                        else:
                            manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON1"].deactivate()
                            manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON2"].deactivate()
                            manager.pages["MANAGEDATA"]["MARKETDATA_MATRIX"].releaseSelected()
            
        self.objectFunctions[thisPage+"-MARKETDATA_MATRIX-SELECTIONUPDATED"] = __guioF_MANAGEDATA_MARKETDATA_MATRIX_SELECTIONUPDATED
        def __guioF_MANAGEDATA_MARKETDATA_MATRIX_VIEWRANGEUPDATED(manager): manager.pages["MANAGEDATA"]["MARKETDATA_MATRIX_SB_V"].changeViewRange(manager.pages["MANAGEDATA"]["MARKETDATA_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-MARKETDATA_MATRIX-VIEWRANGEUPDATED"] = __guioF_MANAGEDATA_MARKETDATA_MATRIX_VIEWRANGEUPDATED
        def __guioF_MANAGEDATA_MARKETDATA_MATRIX_SB_V_VALUEUPDATED(manager): manager.pages["MANAGEDATA"]["MARKETDATA_MATRIX"].changeViewRangeV(manager.pages["MANAGEDATA"]["MARKETDATA_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-MARKETDATA_MATRIX_SB_V-VALUEUPDATED"] = __guioF_MANAGEDATA_MARKETDATA_MATRIX_SB_V_VALUEUPDATED
        

        def __guioF_MANAGEDATA_MARKETDATASUBSCRIPTION_BUTTON1_ACTIVATED(manager):
            selectedMarket = manager.pageVariables["MANAGEDATA"]["MARKETSELECTED"]
            selectedSymbol = manager.pageVariables["MANAGEDATA"]["SYMBOLSELECTED"]
            manager.pages["MANAGEDATA"]["DATAMANAGEMENTMESSAGEBOX"].updateText("-")
            if (selectedMarket == "BINANCE"):
                selectedSymbol_mrktRegTimeStamp = manager.assistantIPC.getPRD("BINANCEAPI", "MARKET")[selectedSymbol]['mrktRegTimeStamp']
                tID = manager.assistantIPC.sendFAR("DATAMANAGEMENT", "APPEND_SDS_BINANCE", (selectedSymbol, selectedSymbol_mrktRegTimeStamp))
                def __guioF_MANAGEDATA_MARKETDATASUBSCRIPTION_BUTTON1_ACTIVATED_FARHandler0(manager, result):
                    if (result[0] == True): 
                        __pageAux_MANAGEDATA_UPDATEMARKETDATA_MATRIX(manager, holdPosition = True, holdSelection = True)
                        manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON2"].activate(); manager.__postObjectActivationSearch()
                        manager.pages["MANAGEDATA"]["DATAMANAGEMENTMESSAGEBOX"].updateText(result[1])
                    else: 
                        manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON1"].activate(); manager.__postObjectActivationSearch()
                        manager.pages["MANAGEDATA"]["DATAMANAGEMENTMESSAGEBOX"].updateText(result[1])
                manager.IPCResultHandlers[tID] = __guioF_MANAGEDATA_MARKETDATASUBSCRIPTION_BUTTON1_ACTIVATED_FARHandler0
                manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON1"].deactivate()
        self.objectFunctions[thisPage+"-MARKETDATASUBSCRIPTION_BUTTON1-ACTIVATED"] = __guioF_MANAGEDATA_MARKETDATASUBSCRIPTION_BUTTON1_ACTIVATED
        
        def __guioF_MANAGEDATA_MARKETDATASUBSCRIPTION_BUTTON2_ACTIVATED(manager):
            selectedMarket = manager.pageVariables["MANAGEDATA"]["MARKETSELECTED"]
            selectedSymbol = manager.pageVariables["MANAGEDATA"]["SYMBOLSELECTED"]
            manager.pages["MANAGEDATA"]["DATAMANAGEMENTMESSAGEBOX"].updateText("-")
            if (selectedMarket == "BINANCE"):
                tID = manager.assistantIPC.sendFAR("DATAMANAGEMENT", "REMOVE_SDS_BINANCE", selectedSymbol)
                def __guioF_MANAGEDATA_MARKETDATASUBSCRIPTION_BUTTON2_ACTIVATED_FARHandler0(manager, result):
                    if (result[0] == True): 
                        if (manager.pageVariables["MANAGEDATA"]["MARKETDATAFILTERSELECTED"] == "SUBSCRIBED"): __pageAux_MANAGEDATA_UPDATEMARKETDATA_MATRIX(manager, holdPosition = True, holdSelection = False)
                        else:                                                                                 __pageAux_MANAGEDATA_UPDATEMARKETDATA_MATRIX(manager, holdPosition = True, holdSelection = True)
                        manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON1"].activate(); manager.__postObjectActivationSearch()
                        manager.pages["MANAGEDATA"]["DATAMANAGEMENTMESSAGEBOX"].updateText(result[1])
                    else:
                        manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON2"].activate(); manager.__postObjectActivationSearch()
                        manager.pages["MANAGEDATA"]["DATAMANAGEMENTMESSAGEBOX"].updateText(result[1])
                manager.IPCResultHandlers[tID] = __guioF_MANAGEDATA_MARKETDATASUBSCRIPTION_BUTTON2_ACTIVATED_FARHandler0
                manager.pages["MANAGEDATA"]["MARKETDATASUBSCRIPTION_BUTTON2"].deactivate()
        self.objectFunctions[thisPage+"-MARKETDATASUBSCRIPTION_BUTTON2-ACTIVATED"] = __guioF_MANAGEDATA_MARKETDATASUBSCRIPTION_BUTTON2_ACTIVATED



        #Timer Functinos
        #Update DB Connection Status
        def timerFunction_page_MANAGEDATA_UPDATEDBSTATUSBAR(manager):
            dbConnection = manager.assistantIPC.getPRD("DATAMANAGEMENT", "DBCONNECTION")
            if (manager.pageVariables["MANAGEDATA"]["DBCONNECTION"] == True):
                if (dbConnection[0] == False): #Connected -> Disconnected
                    manager.pageVariables["MANAGEDATA"]["DBCONNECTION"] = False
                    manager.pages["MANAGEDATA"]["STATUSLED"].updateColor("offline");
                    manager.pages["MANAGEDATA"]["STATUSLEDTEXT"].updateText("DATABASE DISCONNECTED <{:s}>".format(time.ctime(dbConnection[2])))
                    manager.pages["MANAGEDATA"]["DBSTATUSBAR"].updateValue(0)
                    manager.pages["MANAGEDATA"]["DBSTATUSBAR"].updateText("N/A")
                    manager.pages["MANAGEDATA"]["DBDIRACTIVETEXT"].updateText("N/A")
                    __pageAux_MANAGEDATA_UPDATEMARKETDATA_MATRIX(manager)
                else:
                    manager.pages["MANAGEDATA"]["STATUSLEDTEXT"].updateText("DATABASE CONNECTED <{:s}>".format(time.ctime(dbConnection[2])))
                    diskVolume = manager.assistantIPC.getPRD("DATAMANAGEMENT", "DBVOLUME")
                    usedPercentage = diskVolume['used'] / diskVolume['total'] * 100
                    #(70, 170, 250) -> (130, 210, 65) -> (250,55,55)
                    if (usedPercentage < 50): newGaugeBarColor = (int(60 * usedPercentage / 50) + 70,          int(40 * usedPercentage / 50) + 170,         250 - int(185 * usedPercentage / 50))
                    else:                     newGaugeBarColor = (int(120 * (usedPercentage - 50) / 50) + 130, 210 - int(155 * (usedPercentage - 50) / 50), 65 - int(10 * (usedPercentage - 50) / 50))
                    manager.pages["MANAGEDATA"]["DBSTATUSBAR"].changeColor(newGaugeBarColor)
                    manager.pages["MANAGEDATA"]["DBSTATUSBAR"].updateValue(round(usedPercentage, 3))
                    manager.pages["MANAGEDATA"]["DBSTATUSBAR"].updateText("{:.3f} GB Available / {:.3f} GB Total   ({:.3f} %)".format(diskVolume['free'] / pow(1024,3), diskVolume['total'] / pow(1024,3), usedPercentage))
            else:
                if (dbConnection[0] == True): #Disconnected -> Connected
                    manager.pageVariables["MANAGEDATA"]["DBCONNECTION"] = True
                    manager.pages["MANAGEDATA"]["STATUSLED"].updateColor("online");
                    manager.pages["MANAGEDATA"]["STATUSLEDTEXT"].updateText("DATABASE CONNECTED <{:s}>".format(time.ctime(dbConnection[2])))
                    diskVolume = manager.assistantIPC.getPRD("DATAMANAGEMENT", "DBVOLUME")
                    usedPercentage = diskVolume['used'] / diskVolume['total'] * 100
                    #(70, 170, 250) -> (130, 210, 65) -> (250,55,55)
                    if (usedPercentage < 50): newGaugeBarColor = (int(60 * usedPercentage / 50) + 70,          int(40 * usedPercentage / 50) + 170,         250 - int(185 * usedPercentage / 50))
                    else:                     newGaugeBarColor = (int(120 * (usedPercentage - 50) / 50) + 130, 210 - int(155 * (usedPercentage - 50) / 50), 65 - int(10 * (usedPercentage - 50) / 50))
                    manager.pages["MANAGEDATA"]["DBSTATUSBAR"].changeColor(newGaugeBarColor)
                    manager.pages["MANAGEDATA"]["DBSTATUSBAR"].updateValue(round(usedPercentage, 3))
                    manager.pages["MANAGEDATA"]["DBSTATUSBAR"].updateText("{:.3f} GB Available / {:.3f} GB Total   ({:.3f} %)".format(diskVolume['free'] / pow(1024,3), diskVolume['total'] / pow(1024,3), usedPercentage))
                    manager.pages["MANAGEDATA"]["DBDIRACTIVETEXT"].updateText(dbConnection[1])
                    __pageAux_MANAGEDATA_UPDATEMARKETDATA_MATRIX(manager)
            return True
        self.timerFunctions[thisPage]["UPDATEDBSTATUSBAR"] = self.__timerFunction(function = timerFunction_page_MANAGEDATA_UPDATEDBSTATUSBAR, interval = 500)
        

        #Update DB Drive Name
        def timerFunction_page_MANAGEDATA_UPDATEDBDRIVENAME(manager):
            dbDriveName = manager.assistantIPC.getPRD("DATAMANAGEMENT", "DMI_DBDRIVENAME")
            if (dbDriveName != None): manager.pages["MANAGEDATA"]["DBDRIVENAMEACTIVETEXT"].updateText(dbDriveName); return False
        self.timerFunctions[thisPage]["UPDATEDBDRIVENAME"] = self.__timerFunction(function = timerFunction_page_MANAGEDATA_UPDATEDBDRIVENAME, interval = 100)

        #PAGE "MANAGE DATA" END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "ANALYSIS" --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "ANALYSIS"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_ANALYSIS = dict()
        page_ANALYSIS.update(main_navigationGUIOs)

        def page_ANALYSIS_load(manager):
            manager.pages["ANALYSIS"]["MAINNAVIGATION_ANALYSIS"].deactivate()
        def page_ANALYSIS_close(manager):
            manager.pages["ANALYSIS"]["MAINNAVIGATION_ANALYSIS"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_ANALYSIS_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_ANALYSIS_close
        self.pages[thisPage] = page_ANALYSIS

        #Object Functions
        self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        #PAGE "ANALYSIS" END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "EMPTY0" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "EMPTY0"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_EMPTY0 = dict()
        page_EMPTY0.update(main_navigationGUIOs)

        def page_EMPTY0_load(manager):
            manager.pages["EMPTY0"]["MAINNAVIGATION_EMPTY0"].deactivate()
        def page_EMPTY0_close(manager):
            manager.pages["EMPTY0"]["MAINNAVIGATION_EMPTY0"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_EMPTY0_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_EMPTY0_close
        self.pages[thisPage] = page_EMPTY0

        #Object Functions
        self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        #PAGE "EMPTY0" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "EMPTY1" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "EMPTY1"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_EMPTY1 = dict()
        page_EMPTY1.update(main_navigationGUIOs)

        def page_EMPTY1_load(manager):
            manager.pages["EMPTY1"]["MAINNAVIGATION_EMPTY1"].deactivate()
        def page_EMPTY1_close(manager):
            manager.pages["EMPTY1"]["MAINNAVIGATION_EMPTY1"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_EMPTY1_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_EMPTY1_close
        self.pages[thisPage] = page_EMPTY1

        #Object Functions
        self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        #PAGE "EMPTY1" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "EMPTY2" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "EMPTY2"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_EMPTY2 = dict()
        page_EMPTY2.update(main_navigationGUIOs)

        def page_EMPTY2_load(manager):
            manager.pages["EMPTY2"]["MAINNAVIGATION_EMPTY2"].deactivate()
        def page_EMPTY2_close(manager):
            manager.pages["EMPTY2"]["MAINNAVIGATION_EMPTY2"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_EMPTY2_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_EMPTY2_close
        self.pages[thisPage] = page_EMPTY2

        #Object Functions
        self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        #PAGE "EMPTY2" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "EMPTY3" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "EMPTY3"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_EMPTY3 = dict()
        page_EMPTY3.update(main_navigationGUIOs)

        def page_EMPTY3_load(manager):
            manager.pages["EMPTY3"]["MAINNAVIGATION_EMPTY3"].deactivate()
        def page_EMPTY3_close(manager):
            manager.pages["EMPTY3"]["MAINNAVIGATION_EMPTY3"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_EMPTY3_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_EMPTY3_close
        self.pages[thisPage] = page_EMPTY3

        #Object Functions
        self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        #PAGE "EMPTY3" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "EMPTY5" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "EMPTY4"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_EMPTY4 = dict()
        page_EMPTY4.update(main_navigationGUIOs)

        def page_EMPTY4_load(manager):
            manager.pages["EMPTY4"]["MAINNAVIGATION_EMPTY4"].deactivate()
        def page_EMPTY4_close(manager):
            manager.pages["EMPTY4"]["MAINNAVIGATION_EMPTY4"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_EMPTY4_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_EMPTY4_close
        self.pages[thisPage] = page_EMPTY4

        #Object Functions
        self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        #PAGE "EMPTY5" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "EMPTY5" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "EMPTY5"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_EMPTY5 = dict()
        page_EMPTY5.update(main_navigationGUIOs)

        def page_EMPTY5_load(manager):
            manager.pages["EMPTY5"]["MAINNAVIGATION_EMPTY5"].deactivate()
        def page_EMPTY5_close(manager):
            manager.pages["EMPTY5"]["MAINNAVIGATION_EMPTY5"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_EMPTY5_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_EMPTY5_close
        self.pages[thisPage] = page_EMPTY5

        #Object Functions
        self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        #PAGE "EMPTY5" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "EMPTY6" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "EMPTY6"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_EMPTY6 = dict()
        page_EMPTY6.update(main_navigationGUIOs)

        def page_EMPTY6_load(manager):
            manager.pages["EMPTY6"]["MAINNAVIGATION_EMPTY6"].deactivate()
        def page_EMPTY6_close(manager):
            manager.pages["EMPTY6"]["MAINNAVIGATION_EMPTY6"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_EMPTY6_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_EMPTY6_close
        self.pages[thisPage] = page_EMPTY6

        #Object Functions
        self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
        self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        #PAGE "EMPTY5" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "APICONTROL" ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "APICONTROL"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_APICONTROL = dict()
        page_APICONTROL.update(main_navigationGUIOs)

        def page_APICONTROL_load(manager):
            manager.pages["APICONTROL"]["MAINNAVIGATION_APICONTROL"].deactivate()
        def page_APICONTROL_close(manager):
            manager.pages["APICONTROL"]["MAINNAVIGATION_APICONTROL"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_APICONTROL_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_APICONTROL_close

        tempPosX = 1130; tempPosY = 550; tempWidth = 300; tempHeight = 350
        page_APICONTROL["LOCALNAVIGATION_BINANCEAPI"] = button_typeA(self.canvas, self.graphicsGenerator, tempPosX, tempPosY, tempWidth, tempHeight, "styleA_themeD", layer = 1)
        page_APICONTROL["LOCALNAVIGATION_BINANCEAPI_TITLE"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, tempPosX, tempPosY, tempWidth, 70, style = "styleA_themeB", layer = 1, text = "BINANCE API", textFill = (255, 255, 255, 255), textSize = 30)
        temp_ledHeight = 30
        page_APICONTROL["LOCALNAVIGATION_BINANCEAPI_LED"] = LED_typeA(self.canvas, self.graphicsGenerator, tempPosX + 10, tempPosY + tempHeight - temp_ledHeight - 10, tempWidth - 20, temp_ledHeight, "styleA_themeB", layer = 1, colors = {'accountOnline': (130, 210, 65, 255), 'marketOnline': (80, 195, 220, 255), 'offline': (240, 90, 90, 255)}, mode = 'offline')
        page_APICONTROL["LOCALNAVIGATION_BINANCEAPI_LEDTEXT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator, tempPosX + 10, tempPosY + tempHeight - temp_ledHeight - 10 - 1, tempWidth - 20, temp_ledHeight, boxStyle = "empty", layer = 1, text = "OFFLINE", textSize = 14, textStyle = "generalText_StyleA")
        page_APICONTROL["LOCALNAVIGATION_BINANCEAPI_ICON"] = constantImageGraphic_typeA(self.canvas, self.graphicsGenerator, tempPosX + tempWidth / 2 - 75, tempPosY + tempHeight / 2 - 75, 150, 150, "empty", imagePath = os.path.join(path_IMAGES + r"\binanceIcon_512x512.png"), layer = 1)

        self.pages[thisPage] = page_APICONTROL

        #Object Functions
        self.objectFunctions[thisPage+"-LOCALNAVIGATION_BINANCEAPI-ACTIVATED"] = (__loadPage, "APICONTROL_BINANCEAPI")

        #PAGE "APICONTROL_BINANCEAPI" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "APICONTROL_BINANCEAPI"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_APICONTROL_BINANCEAPI = dict()
        page_APICONTROL_BINANCEAPI.update(main_navigationGUIOs)
        
        self.pageVariables[thisPage]["MARKETCONNECTIONSTATUS"]  = False
        self.pageVariables[thisPage]["ACCOUNTCONNECTIONSTATUS"] = False
        self.pageVariables[thisPage]["LASTCONNECTIONCHECKTIME"] = 0
        self.pageVariables[thisPage]["MARKETDATALOADED"] = False
        self.pageVariables[thisPage]["MARKETSYMBOLSELECTED"] = None
        self.pageVariables[thisPage]["MARKETSYMBOLSELECTED_CURRENTPRICEUNIT"] = None

        def page_APICONTROL_BINANCEAPI_load(manager):
            manager.pages["APICONTROL_BINANCEAPI"]["MAINNAVIGATION_APICONTROL"].deactivate()
            if (manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETDATALOADED"] == False):
                manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETDATALOADED"] = True
                marketData = manager.assistantIPC.getPRD("BINANCEAPI", "MARKET")
                marketDataLength = len(marketData)
                marketDataKeys = list(marketData.keys())
                marketDataKeys_spot = list(); marketDataKeys_usdm = list(); marketDataKeys_coinm = list();
                for key in marketDataKeys:
                    marketType = marketData[key]['marketType']
                    if   (marketType == "SPOT"):   marketDataKeys_spot.append(key)
                    elif (marketType == "USDS-M"): marketDataKeys_usdm.append(key)
                    elif (marketType == "COIN-M"): marketDataKeys_coinm.append(key)
                marketDataKeys_spot.sort(); marketDataKeys_usdm.sort(); marketDataKeys_coinm.sort()
                marketDataKeys = marketDataKeys_spot + marketDataKeys_usdm + marketDataKeys_coinm
                manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETDATAKEYS"] = marketDataKeys
                newMatrix = [[],[],[]]
                for i in range (marketDataLength): 
                    activeStatus = marketData[marketDataKeys[i]]['active']
                    marketType   = marketData[marketDataKeys[i]]['marketType']
                    newMatrix[0].append(("{:d} / {:d}".format(i + 1, marketDataLength), "center", "white", ("Arial", 10, "")))
                    if (activeStatus == True): newMatrix[1].append((marketDataKeys[i], "center", "white",  ("Arial", 10, "")))
                    else:                      newMatrix[1].append((marketDataKeys[i], "center", "gray50", ("Arial", 10, "")))
                    if   (marketType == "SPOT"):   newMatrix[2].append(("SPOT",       "center", "skyblue",    ("Arial", 10, "")))
                    elif (marketType == "USDS-M"): newMatrix[2].append(("USD(S) - M", "center", "lightgreen", ("Arial", 10, "")))
                    elif (marketType == "COIN-M"): newMatrix[2].append(("COIN - M",   "center", "orange",     ("Arial", 10, "")))
                manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_MATRIX"].updateMatrix(newMatrix)
                manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_MATRIX_SB_V"].changeViewRange(manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_MATRIX"].getViewRange()['vertical'])
                manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_SEARCHINPUTBOX"].activate()

        def page_APICONTROL_BINANCEAPI_close(manager):
            manager.pages["APICONTROL_BINANCEAPI"]["MAINNAVIGATION_APICONTROL"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_APICONTROL_BINANCEAPI_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_APICONTROL_BINANCEAPI_close
        
        page_APICONTROL_BINANCEAPI["LOCALNAVIGATION_MAIN"] = button_typeA(self.canvas, self.graphicsGenerator, 2450, 65, 100, 30, "styleA_themeE", layer = 1, text = "API MENU", textSize = 16)
        page_APICONTROL_BINANCEAPI["STATUSLED"] = LED_typeA(self.canvas, self.graphicsGenerator, 10, 65, 2435, 30, "styleA_themeB", layer = 1, colors = {'accountOnline': (130, 210, 65, 255), 'marketOnline': (80, 195, 220, 255), 'offline': (240, 90, 90, 255)}, mode = 'offline')
        page_APICONTROL_BINANCEAPI["STATUSLEDTEXT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator, 10, 64, 2435, 30, boxStyle = "empty", layer = 1, text = "OFFLINE", textSize = 12, textStyle = "generalText_StyleA")
        page_APICONTROL_BINANCEAPI["PRE_REGISTEREDKEYS_SELECTIONBOX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 10, 100, 200, 30, style = "styleA_themeA", layer = 1, text = "REGISTERED KEYS", textFill = (255, 255, 255, 255), textSize = 14)
        page_APICONTROL_BINANCEAPI["PRE_REGISTEREDKEYS_PASSWORD_TEXT"]     = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 10, 135, 200, 30, style = "styleA_themeA", layer = 1, text = "PASSWORD", textFill = (255, 255, 255, 255), textSize = 14)
        page_APICONTROL_BINANCEAPI["PRE_REGISTEREDKEYS_SELECTIONBOX"]      = selectionBox_typeA(self.canvas, self.graphicsGenerator, 215, 100, 300, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        page_APICONTROL_BINANCEAPI["PRE_REGISTEREDKEYS_SELECTIONBOX"].updateList(["<MANUAL TYPE>",]); page_APICONTROL_BINANCEAPI["PRE_REGISTEREDKEYS_SELECTIONBOX"].editSelected("<MANUAL TYPE>")
        page_APICONTROL_BINANCEAPI["PRE_REGISTEREDKEYS_PASSWORDINPUTBOX"]  = textInputBox_typeA(self.canvas, self.graphicsGenerator, 215, 135, 300, 30, "styleA_themeA", layer = 1, maxTextLength = 128, mode = "INACTIVE")
        page_APICONTROL_BINANCEAPI["INPUTBOX_APIKEY_TEXT"]    = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 520, 100, 150, 30, style = "styleA_themeA", layer = 1, text = "API KEY",    textFill = (255, 255, 255, 255), textSize = 14)
        page_APICONTROL_BINANCEAPI["INPUTBOX_SECRETKEY_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 520, 135, 150, 30, style = "styleA_themeA", layer = 1, text = "SECRET KEY", textFill = (255, 255, 255, 255), textSize = 14)
        page_APICONTROL_BINANCEAPI["INPUTBOX_APIKEY"]    = textInputBox_typeA(self.canvas, self.graphicsGenerator, 675, 100, 1100, 30, "styleA_themeA", layer = 1, maxTextLength = 64)
        page_APICONTROL_BINANCEAPI["INPUTBOX_SECRETKEY"] = textInputBox_typeA(self.canvas, self.graphicsGenerator, 675, 135, 1100, 30, "styleA_themeA", layer = 1, maxTextLength = 64)
        page_APICONTROL_BINANCEAPI["API_LOGIN_BUTTON"] = button_typeA(self.canvas, self.graphicsGenerator, 1780, 100, 160, 65, "styleA_themeB", layer = 1, text = None, textSize = 16, mode = "INACTIVE")
        page_APICONTROL_BINANCEAPI["API_LOGIN_BUTTONTEXT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator, 1780, 100, 160, 65, boxStyle = "empty", layer = 1, text = "CONNECT", textSize = 13, textStyle = "generalText_StyleA")
        page_APICONTROL_BINANCEAPI["API_LOGIN_RESULTTEXT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator, 1945, 100, 605, 65, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 12, textStyle = "generalText_StyleA")

        page_APICONTROL_BINANCEAPI["MARKETDATA_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 10, 170, 910, 30, style = "styleA_themeA", layer = 1, text = "BINANCE MARKET DATA", textFill = (255, 255, 255, 255), textSize = 14)
        page_APICONTROL_BINANCEAPI["MARKETDATA_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator, 10, 205, 470, 1225, "styleA_themeA", layer = 1, nDisplayedColumns = 3, nDisplayedRows = 30, 
                                                                                 columnTitles= [("INDEX", "center", "white",  ("Arial", 12, "bold")),
                                                                                                ("SYMBOL", "center", "white",  ("Arial", 12, "bold")),
                                                                                                ("TYPE", "center", "white",  ("Arial", 12, "bold"))],
                                                                                 customColumnRatio = (2, 3, 2))
        page_APICONTROL_BINANCEAPI["MARKETDATA_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator, 485, 205, 1225, 30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_APICONTROL_BINANCEAPI["MARKETDATA_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_APICONTROL_BINANCEAPI["MARKETDATA_SEARCHTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 520, 205, 70, 30, style = "styleA_themeA", layer = 1, text = "SYMBOL", textFill = (240, 240, 240, 200), textSize = 14)
        page_APICONTROL_BINANCEAPI["MARKETDATA_SEARCHINPUTBOX"] = textInputBox_typeA(self.canvas, self.graphicsGenerator, 595, 205, 225, 30, "styleA_themeA", layer = 1, maxTextLength = 32, mode = "INACTIVE")
        page_APICONTROL_BINANCEAPI["MARKETDATA_SEARCHBUTTON"] = button_typeA(self.canvas, self.graphicsGenerator, 825, 205, 95, 30, "styleA_themeB", layer = 1, text = "SEARCH", textSize = 14, mode = "INACTIVE")
        page_APICONTROL_BINANCEAPI["MARKETDATA_SEARCHEDDATAMATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator, 520, 240, 400, 1155, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 30, 
                                                                                             columnTitles= [("KEY",     "center", "white",  ("Arial", 12, "bold")), ("CONTENT", "center", "white",  ("Arial", 12, "bold"))],
                                                                                             customColumnRatio = (2, 3))
        page_APICONTROL_BINANCEAPI["MARKETDATA_CURRENTPRICETEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 520, 1400, 150, 30, style = "styleA_themeA", layer = 1, text = "CURRENT PRICE", textFill = (230, 230, 230, 255), textSize = 14)
        page_APICONTROL_BINANCEAPI["MARKETDATA_CURRENTPRICE"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator, 675, 1400, 245, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 12, textStyle = "generalText_StyleA")

        page_APICONTROL_BINANCEAPI["SPOTWALLETTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 925, 170, 400, 30, style = "styleA_themeA", layer = 1, text = "SPOT WALLET", textFill = (255, 255, 255, 255), textSize = 14)
        page_APICONTROL_BINANCEAPI["SPOTWALLET_BALANCEMATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator, 925, 205, 365, 920, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 20, customColumnRatio = (2, 3), 
                                                                                        columnTitles = [("SYMBOL", "center", "white", ("Arial", 12, "bold")),
                                                                                                        ("FREE / USED / TOTAL", "center", "white",   ("Arial", 12, "bold"))])
        page_APICONTROL_BINANCEAPI["SPOTWALLET_BALANCEMATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator, 1295, 205, 920, 30, "styleA_themeA", "styleA_themeA", layer = 1, 
                                                                                      viewRange = page_APICONTROL_BINANCEAPI["SPOTWALLET_BALANCEMATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        matrix = [[],[]]
        matrix[0].append(("Deposit Available",  "center", "white", ("Arial", 10, ""))); matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Trade Available",    "center", "white", ("Arial", 10, ""))); matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Withdrawal Available", "center", "white", ("Arial", 10, ""))); matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Maker Commision Rate",  "center", "white", ("Arial", 10, ""))); matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Taker Commision Rate",  "center", "white", ("Arial", 10, ""))); matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Buyer Commision Rate",  "center", "white", ("Arial", 10, ""))); matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Seller Commision Rate", "center", "white", ("Arial", 10, ""))); matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("uID", "center", "white", ("Arial", 10, ""))); matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        self.pageVariables[thisPage]["SPOTWALLET_PROPERTYMATRIX_DEFAULT"] = matrix
        page_APICONTROL_BINANCEAPI["SPOTWALLET_PROPERTYMATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator, 925, 1130, 400, 300, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 8, customColumnRatio = (2, 3), matrix = matrix,
                                                                                         columnTitles = [("PROPERTY", "center", "white", ("Arial", 12, "bold")),
                                                                                                         ("CONTENT",  "center", "white", ("Arial", 12, "bold"))])




        page_APICONTROL_BINANCEAPI["FUTURESWALLETTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1330, 170, 1220, 30, style = "styleA_themeA", layer = 1, text = "FUTURES WALLET", textFill = (255, 255, 255, 255), textSize = 14)
        page_APICONTROL_BINANCEAPI["FUTURESWALLET_BALANCEMATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator, 1330, 205, 870, 350, "styleA_themeA", layer = 1, nDisplayedColumns = 5, nDisplayedRows = 9, customColumnRatio = (1.2, 2, 2, 2, 2),
                                                                                           columnTitles = [("SYMBOL", "center", "white", ("Arial", 11, "bold")),
                                                                                                           ("WALLET BALANCE",    "center", "white",  ("Arial", 11, "bold")),
                                                                                                           ("MARGIN BALANCE",    "center", "white",  ("Arial", 11, "bold")),
                                                                                                           ("UNREALIZED PROFIT", "center", "white",  ("Arial", 11, "bold")),
                                                                                                           ("MAXIMUM WITHDRAWL", "center", "white",  ("Arial", 11, "bold"))])

        
        matrix = [[],[]]
        matrix[0].append(("Deposit Available",  "center", "white", ("Arial", 10, "")));    matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Trade Available",  "center", "white", ("Arial", 10, "")));      matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Withdrawal Available",  "center", "white", ("Arial", 10, ""))); matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Fee Tier",  "center", "white", ("Arial", 10, "")));             matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Multi-Assets Margin",  "center", "white", ("Arial", 10, "")));  matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        matrix[0].append(("Trade Group ID",  "center", "white", ("Arial", 10, "")));       matrix[1].append(("N/A",  "center", "white", ("Arial", 10, "")))
        self.pageVariables[thisPage]["FUTURESWALLET_PROPERTYMATRIX_DEFAULT"] = matrix
        page_APICONTROL_BINANCEAPI["FUTURESWALLET_PROPERTYMATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator, 2205, 205, 345, 350, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 6, customColumnRatio = (5, 6), matrix = matrix,
                                                                                                  columnTitles = [("PROPERTY", "center", "white", ("Arial", 12, "bold")),
                                                                                                                  ("CONTENT",  "center", "white", ("Arial", 12, "bold"))])

        page_APICONTROL_BINANCEAPI["FUTURESWALLET_POSITIONMATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator, 1330, 560, 1185, 870, "styleA_themeA", layer = 1, nDisplayedColumns = 7, nDisplayedRows = 20, customColumnRatio = (2, 3, 3, 3, 2, 2, 3),
                                                                                            columnTitles = [("INDEX", "center", "white", ("Arial", 12, "bold")),
                                                                                                            ("POSITION SYMBOL", "center", "white", ("Arial", 12, "bold")),
                                                                                                            ("ENTRY PRICE",  "center", "white", ("Arial", 12, "bold")),
                                                                                                            ("POSITION AMOUNT",  "center", "white", ("Arial", 12, "bold")),
                                                                                                            ("LEVERAGE",  "center", "white", ("Arial", 12, "bold")),
                                                                                                            ("ISOLATED",  "center", "white", ("Arial", 12, "bold")),
                                                                                                            ("UNREALIZED PROFIT",  "center", "white", ("Arial", 12, "bold"))])
        page_APICONTROL_BINANCEAPI["FUTURESWALLET_POSITIONMATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator, 2520, 560, 870, 30, "styleA_themeA", "styleA_themeA", layer = 1, 
                                                                                          viewRange = page_APICONTROL_BINANCEAPI["FUTURESWALLET_POSITIONMATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)

        self.pages[thisPage] = page_APICONTROL_BINANCEAPI

        #Object Functions
        self.objectFunctions[thisPage+"-LOCALNAVIGATION_MAIN-ACTIVATED"] = (__loadPage, "APICONTROL")
        def __guioF_APICONTROL_BINANCEAPI_PRE_REGISTEREDKEYS_SELECTIONBOX_SELECTIONBOXOPENED(manager):
            tID = manager.assistantIPC.sendDAR("BINANCEAPI", "PRKeyList")
            def __guioF_APICONTROL_BINANCEAPI_PRE_REGISTEREDKEYS_SELECTIONBOX_SELECTIONBOXOPENED_DARHandler0(manager, result): manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_SELECTIONBOX"].updateList(["<MANUAL TYPE>",] + result)
            manager.IPCResultHandlers[tID] = __guioF_APICONTROL_BINANCEAPI_PRE_REGISTEREDKEYS_SELECTIONBOX_SELECTIONBOXOPENED_DARHandler0
        self.objectFunctions[thisPage+"-PRE_REGISTEREDKEYS_SELECTIONBOX-SELECTIONBOXOPENED"] = __guioF_APICONTROL_BINANCEAPI_PRE_REGISTEREDKEYS_SELECTIONBOX_SELECTIONBOXOPENED 
        def __guioF_APICONTROL_BINANCEAPI_PRE_REGISTEREDKEYS_SELECTIONBOX_SELECTIONUPDATED(manager):
            selectedOption = manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_SELECTIONBOX"].getSelected()
            if (selectedOption == "<MANUAL TYPE>"):
                manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].deactivate()
                manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_PASSWORDINPUTBOX"].editText(""); manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_PASSWORDINPUTBOX"].deactivate()
                manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_APIKEY"].editText("");    manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_APIKEY"].activate()
                manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_SECRETKEY"].editText(""); manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_SECRETKEY"].activate()
            else: 
                tID = manager.assistantIPC.sendDAR("BINANCEAPI", "PRKey_"+selectedOption)
                def __guioF_APICONTROL_BINANCEAPI_PRE_REGISTEREDKEYS_SELECTIONBOX_SELECTIONUPDATED_DARHandler0(manager, result):
                    manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].activate()
                    manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_PASSWORDINPUTBOX"].activate(); manager.__postObjectActivationSearch()
                    manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_APIKEY"].editText(result[0]);    manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_APIKEY"].deactivate();
                    manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_SECRETKEY"].editText(result[1]); manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_SECRETKEY"].deactivate();
                manager.IPCResultHandlers[tID] = __guioF_APICONTROL_BINANCEAPI_PRE_REGISTEREDKEYS_SELECTIONBOX_SELECTIONUPDATED_DARHandler0
        self.objectFunctions[thisPage+"-PRE_REGISTEREDKEYS_SELECTIONBOX-SELECTIONUPDATED"] = __guioF_APICONTROL_BINANCEAPI_PRE_REGISTEREDKEYS_SELECTIONBOX_SELECTIONUPDATED 
        def __guioF_APICONTROL_BINANCEAPI_INPUTBOX_APIKEY_TEXTUPDATED(manager):
            apiKeyLength    = manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_APIKEY"].getTextLength()
            secretKeyLength = manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_SECRETKEY"].getTextLength()
            if ((apiKeyLength == 64) and (secretKeyLength == 64)):
                if (manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].mode == "INACTIVE"): manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].activate()
                if not(manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].mode == "INACTIVE"): manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].deactivate()
        self.objectFunctions[thisPage+"-INPUTBOX_APIKEY-TEXTUPDATED"] = __guioF_APICONTROL_BINANCEAPI_INPUTBOX_APIKEY_TEXTUPDATED
        def __guioF_APICONTROL_BINANCEAPI_INPUTBOX_SECRETKEY_TEXTUPDATED(manager):
            apiKeyLength    = manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_APIKEY"].getTextLength()
            secretKeyLength = manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_SECRETKEY"].getTextLength()
            if ((apiKeyLength == 64) and (secretKeyLength == 64)):
                if (manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].mode == "INACTIVE"): manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].activate()
            else:
                if not(manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].mode == "INACTIVE"): manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].deactivate()
        self.objectFunctions[thisPage+"-INPUTBOX_SECRETKEY-TEXTUPDATED"] = __guioF_APICONTROL_BINANCEAPI_INPUTBOX_SECRETKEY_TEXTUPDATED

        #General Auxillary Function for 'thisPage'
        def __pageAux_APICONTROL_BINANCEAPI_UPDATEBALANCES(manager):
            spotWallet = manager.assistantIPC.getPRD("BINANCEAPI", "SPOTWALLET")
            matrix = [[],[]]
            for symbol in spotWallet['balances'].keys():
                if ((0 < spotWallet['balances'][symbol]['free']) or (0 < spotWallet['balances'][symbol]['used']) or (0 < spotWallet['balances'][symbol]['total'])): textColor = "skyblue"
                else:                                                                                                                                               textColor = "white"
                matrix[0].append((symbol, "center", textColor,   ("Arial", 10, "")))
                matrix[1].append(("{:s} / {:s} / {:s}".format(str(spotWallet['balances'][symbol]['free']), str(spotWallet['balances'][symbol]['used']), str(spotWallet['balances'][symbol]['total'])), "center", textColor, ("Arial", 10, "")))
            manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_BALANCEMATRIX"].updateMatrix(matrix, holdPosition = True)
            
            futuresWallet = manager.assistantIPC.getPRD("BINANCEAPI", "FUTURESWALLET")
            matrix = [[],[],[],[],[]]
            for asset in futuresWallet['info']['assets']:
                if (0 < float(asset['walletBalance'])): textColor = "skyblue"
                else:                                   textColor = "white"
                matrix[0].append((asset['asset'],             "center", textColor, ("Arial", 10, "")))
                matrix[1].append((asset['walletBalance'],     "center", textColor, ("Arial", 10, "")))
                matrix[2].append((asset['marginBalance'],     "center", textColor, ("Arial", 10, "")))
                matrix[3].append((asset['unrealizedProfit'],  "center", textColor, ("Arial", 10, "")))
                matrix[4].append((asset['maxWithdrawAmount'], "center", textColor, ("Arial", 10, "")))
            manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_BALANCEMATRIX"].updateMatrix(matrix, holdPosition = True)
            matrix = [[],[],[],[],[],[],[]]
            listLength = len(futuresWallet['info']['positions'])
            for index in range (listLength):
                position = futuresWallet['info']['positions'][index]
                if (0 < float(position['positionAmt'])): textColor = "skyblue"
                else:                                    textColor = "white"
                matrix[0].append(("{:d} / {:d}".format(index, listLength), "center", textColor, ("Arial", 10, "")))
                matrix[1].append((position['symbol'],                      "center", textColor, ("Arial", 10, "")))
                matrix[2].append((str(position['entryPrice']),             "center", textColor, ("Arial", 10, "")))
                matrix[3].append((str(position['positionAmt']),            "center", textColor, ("Arial", 10, "")))
                matrix[4].append((str(position['leverage']),               "center", textColor, ("Arial", 10, "")))
                matrix[5].append((str(position['isolated']),               "center", textColor, ("Arial", 10, "")))
                if (0 < float(position['unrealizedProfit'])):   textColor_profit = "lawngreen";   unrealizedProfitString = "+" + str(position['unrealizedProfit'])
                elif (float(position['unrealizedProfit']) < 0): textColor_profit = "salmon";      unrealizedProfitString = str(position['unrealizedProfit'])
                else:                                           textColor_profit = "white";       unrealizedProfitString = str(position['unrealizedProfit'])
                matrix[6].append((unrealizedProfitString, "center", textColor_profit, ("Arial", 10, "")))
            manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_POSITIONMATRIX"].updateMatrix(matrix, holdPosition = True)

        #Auxillary Function for '__guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED'
        def __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED_auxf0(manager):
            __pageAux_APICONTROL_BINANCEAPI_UPDATEBALANCES(manager)
            spotWallet = manager.assistantIPC.getPRD("BINANCEAPI", "SPOTWALLET")
            matrix = [[],[]]
            matrix[0].append(("Deposit Available",  "center", "white", ("Arial", 10, ""))); matrix[1].append((str(spotWallet['info']['canDeposit']),  "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Trade Available",    "center", "white", ("Arial", 10, ""))); matrix[1].append((str(spotWallet['info']['canTrade']),    "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Withdrawal Available", "center", "white", ("Arial", 10, ""))); matrix[1].append((str(spotWallet['info']['canWithdraw']), "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Maker Commision Rate",  "center", "white", ("Arial", 10, ""))); matrix[1].append(("{:.3f} %".format(float(spotWallet['info']['commissionRates']['maker']) * 100),  "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Taker Commision Rate",  "center", "white", ("Arial", 10, ""))); matrix[1].append(("{:.3f} %".format(float(spotWallet['info']['commissionRates']['taker']) * 100),  "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Buyer Commision Rate",  "center", "white", ("Arial", 10, ""))); matrix[1].append(("{:.3f} %".format(float(spotWallet['info']['commissionRates']['buyer']) * 100),  "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Seller Commision Rate", "center", "white", ("Arial", 10, ""))); matrix[1].append(("{:.3f} %".format(float(spotWallet['info']['commissionRates']['seller']) * 100), "center", "white", ("Arial", 10, "")))
            matrix[0].append(("uID", "center", "white", ("Arial", 10, ""))); matrix[1].append((spotWallet['info']['uid'], "center", "white", ("Arial", 10, "")))
            manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_PROPERTYMATRIX"].updateMatrix(matrix)
            
            futuresWallet = manager.assistantIPC.getPRD("BINANCEAPI", "FUTURESWALLET")
            matrix = [[],[]]
            matrix[0].append(("Deposit Available",  "center", "white", ("Arial", 10, "")));    matrix[1].append((str(futuresWallet['info']['canDeposit']),        "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Trade Available",  "center", "white", ("Arial", 10, "")));      matrix[1].append((str(futuresWallet['info']['canTrade']),          "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Withdrawal Available",  "center", "white", ("Arial", 10, ""))); matrix[1].append((str(futuresWallet['info']['canWithdraw']),       "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Fee Tier",  "center", "white", ("Arial", 10, "")));             matrix[1].append((str(futuresWallet['info']['feeTier']),           "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Multi-Assets Margin",  "center", "white", ("Arial", 10, "")));  matrix[1].append((str(futuresWallet['info']['multiAssetsMargin']), "center", "white", ("Arial", 10, "")))
            matrix[0].append(("Trade Group ID",  "center", "white", ("Arial", 10, "")));       matrix[1].append((str(futuresWallet['info']['tradeGroupId']),      "center", "white", ("Arial", 10, "")))
            manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_PROPERTYMATRIX"].updateMatrix(matrix)    

        def __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED(manager):
            selectedOption = manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_SELECTIONBOX"].getSelected()
            manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].deactivate()
            if (manager.pageVariables["APICONTROL_BINANCEAPI"]["ACCOUNTCONNECTIONSTATUS"] == False):
                if (selectedOption == "<MANUAL TYPE>"):
                    page_APICONTROL_BINANCEAPI["API_LOGIN_RESULTTEXT"].updateText("Attempting API Connection with Manually Entered Keys")
                    apiKey    = manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_APIKEY"].getText()
                    secretKey = manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_SECRETKEY"].getText()
                    tID = manager.assistantIPC.sendFAR("BINANCEAPI", "CONNECTAPI_byKEY", (apiKey, secretKey), nRetry = "INF")
                    def __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED_FARHandler0(manager, result):
                        if (result[0] == True):
                            manager.pageVariables["APICONTROL_BINANCEAPI"]["ACCOUNTCONNECTIONSTATUS"] = True
                            manager.pageVariables["APICONTROL_BINANCEAPI"]["LASTCONNECTIONCHECKTIME"] = result[1]
                            displayText = "[{:s}] API CONNECTION SUCCESSFUL".format(time.ctime(result[1]))
                            page_APICONTROL_BINANCEAPI["API_LOGIN_RESULTTEXT"].updateText(displayText)
                            manager.pages["APICONTROL_BINANCEAPI"]["STATUSLED"].updateColor("accountOnline")
                            manager.pages["APICONTROL_BINANCEAPI"]["STATUSLEDTEXT"].updateText("ACCOUNT CONNECTED <{:s}>".format(time.ctime(result[1])))
                            manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LED"].updateColor("accountOnline")
                            manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LEDTEXT"].updateText("ACCOUNT CONNECTED")
                            manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTONTEXT"].updateText("DISCONNECT")
                            manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_SELECTIONBOX"].deactivate() 
                            manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_APIKEY"].deactivate()
                            manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_SECRETKEY"].deactivate()
                            __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED_auxf0(manager)
                            manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_BALANCEMATRIX_SB_V"].changeViewRange(manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_BALANCEMATRIX"].getViewRange()['vertical'])
                            manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_POSITIONMATRIX_SB_V"].changeViewRange(manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_POSITIONMATRIX"].getViewRange()['vertical'])
                        else:
                            displayText = "[{:s}] CONNECTION FAILED <{:s}>".format(result[1], str(result[2]))
                            page_APICONTROL_BINANCEAPI["API_LOGIN_RESULTTEXT"].updateText(displayText)
                        manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].activate(); manager.__postObjectActivationSearch()
                    manager.IPCResultHandlers[tID] = __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED_FARHandler0
                else:
                    page_APICONTROL_BINANCEAPI["API_LOGIN_RESULTTEXT"].updateText("Attempting API Connection with PRID <{:s}>".format(selectedOption))
                    password = manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_PASSWORDINPUTBOX"].getText()
                    tID = manager.assistantIPC.sendFAR("BINANCEAPI", "CONNECTAPI_byPRID", (selectedOption, password), nRetry = "INF")
                    def __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED_FARHandler1(manager, result):
                        if (result[0] == True): 
                            manager.pageVariables["APICONTROL_BINANCEAPI"]["ACCOUNTCONNECTIONSTATUS"] = True
                            manager.pageVariables["APICONTROL_BINANCEAPI"]["LASTCONNECTIONCHECKTIME"] = result[1]
                            displayText = "[{:s}] API CONNECTION SUCCESSFUL".format(time.ctime(result[1]))
                            page_APICONTROL_BINANCEAPI["API_LOGIN_RESULTTEXT"].updateText(displayText)
                            manager.pages["APICONTROL_BINANCEAPI"]["STATUSLED"].updateColor("accountOnline")
                            manager.pages["APICONTROL_BINANCEAPI"]["STATUSLEDTEXT"].updateText("ACCOUNT CONNECTED <{:s}>".format(time.ctime(result[1])))
                            manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LED"].updateColor("accountOnline")
                            manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LEDTEXT"].updateText("ACCOUNT CONNECTED")
                            manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTONTEXT"].updateText("DISCONNECT")
                            manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_PASSWORDINPUTBOX"].editText("")
                            manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_PASSWORDINPUTBOX"].deactivate()
                            manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_SELECTIONBOX"].deactivate()
                            __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED_auxf0(manager)
                            manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_BALANCEMATRIX_SB_V"].changeViewRange(manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_BALANCEMATRIX"].getViewRange()['vertical'])
                            manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_POSITIONMATRIX_SB_V"].changeViewRange(manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_POSITIONMATRIX"].getViewRange()['vertical'])
                        else: 
                            displayText = "[{:s}] CONNECTION FAILED <{:s}>".format(time.ctime(result[1]), str(result[2]))
                            page_APICONTROL_BINANCEAPI["API_LOGIN_RESULTTEXT"].updateText(displayText)
                            manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_PASSWORDINPUTBOX"].editText("")
                        manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].activate(); manager.__postObjectActivationSearch()
                    manager.IPCResultHandlers[tID] = __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED_FARHandler1
            else:
                page_APICONTROL_BINANCEAPI["API_LOGIN_RESULTTEXT"].updateText("Attempting API Disconnection")
                tID = manager.assistantIPC.sendFAR("BINANCEAPI", "DISCONNECTAPI", None, nRetry = "INF")
                def __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED_FARHandler2(manager, result):
                    if (result[0] == True):
                        manager.pageVariables["APICONTROL_BINANCEAPI"]["ACCOUNTCONNECTIONSTATUS"] = False
                        manager.pageVariables["APICONTROL_BINANCEAPI"]["LASTCONNECTIONCHECKTIME"] = result[1]
                        displayText = "[{:s}] API DISCONNECTION SUCCESSFUL".format(time.ctime(result[1]))
                        page_APICONTROL_BINANCEAPI["API_LOGIN_RESULTTEXT"].updateText(displayText)
                        manager.pages["APICONTROL_BINANCEAPI"]["STATUSLED"].updateColor("marketOnline")
                        manager.pages["APICONTROL_BINANCEAPI"]["STATUSLEDTEXT"].updateText("MARKET CONNECTED <{:s}>".format(time.ctime(manager.assistantIPC.getPRD("BINANCEAPI", "MARKETCONNECTIONSTATUS")[1])))
                        manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LED"].updateColor("marketOnline")
                        manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LEDTEXT"].updateText("MARKET CONNECTED")
                        manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTONTEXT"].updateText("CONNECT")

                        manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_PROPERTYMATRIX"].updateMatrix(manager.pageVariables["APICONTROL_BINANCEAPI"]["SPOTWALLET_PROPERTYMATRIX_DEFAULT"])
                        manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_PROPERTYMATRIX"].updateMatrix(manager.pageVariables["APICONTROL_BINANCEAPI"]["FUTURESWALLET_PROPERTYMATRIX_DEFAULT"])
                        manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_BALANCEMATRIX"].updateMatrix([[],[]])
                        manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_BALANCEMATRIX"].updateMatrix([[],[],[],[],[]])
                        manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_POSITIONMATRIX"].updateMatrix([[],[],[],[],[],[],[]])

                        if (selectedOption == "<MANUAL TYPE>"):
                            manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_APIKEY"].activate()
                            manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_SECRETKEY"].activate()
                        else:
                            manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_PASSWORDINPUTBOX"].activate()
                        manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_SELECTIONBOX"].activate()
                    else:
                        displayText = "[{:s}] DISCONNECTION FAILED <{:s}>".format(time.ctime(result[1]), str(result[2]))
                        page_APICONTROL_BINANCEAPI["API_LOGIN_RESULTTEXT"].updateText(displayText)
                    manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTON"].activate(); manager.__postObjectActivationSearch()
                manager.IPCResultHandlers[tID] = __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED_FARHandler2
        self.objectFunctions[thisPage+"-API_LOGIN_BUTTON-ACTIVATED"] = __guioF_APICONTROL_BINANCEAPI_API_LOGIN_BUTTON_ACTIVATED 
        
        def __guioF_APICONTROL_BINANCEAPI_MARKETDATA_SEARCHINPUTBOX_TEXTUPDATED(manager):
            symbolEntered = manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_SEARCHINPUTBOX"].getText()
            if symbolEntered in manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETDATAKEYS"]: manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_SEARCHBUTTON"].activate()
            else:                                                                                 manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_SEARCHBUTTON"].deactivate()
        self.objectFunctions[thisPage+"-MARKETDATA_SEARCHINPUTBOX-TEXTUPDATED"] = __guioF_APICONTROL_BINANCEAPI_MARKETDATA_SEARCHINPUTBOX_TEXTUPDATED
        def __guioF_APICONTROL_BINANCEAPI_MARKETDATA_SEARCHBUTTON_ACTIVATED(manager):
            symbolEntered = manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_SEARCHINPUTBOX"].getText()
            manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETSYMBOLSELECTED"] = symbolEntered
            selectedMarketSymbolData = manager.assistantIPC.getPRD("BINANCEAPI", "MARKET")[symbolEntered]
            newMatrix = [[],[]]
            for dataKey in selectedMarketSymbolData.keys():
                if (dataKey == "limits"):
                    newMatrix[0].append(("limits-amount-max", "center", "white", ("Arial", 10, "")));   newMatrix[1].append((str(selectedMarketSymbolData["limits"]["amount"]["max"]),   "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("limits-amount-min", "center", "white", ("Arial", 10, "")));   newMatrix[1].append((str(selectedMarketSymbolData["limits"]["amount"]["min"]),   "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("limits-cost-max", "center", "white", ("Arial", 10, "")));     newMatrix[1].append((str(selectedMarketSymbolData["limits"]["cost"]["max"]),     "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("limits-cost-min", "center", "white", ("Arial", 10, "")));     newMatrix[1].append((str(selectedMarketSymbolData["limits"]["cost"]["min"]),     "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("limits-leverage-max", "center", "white", ("Arial", 10, ""))); newMatrix[1].append((str(selectedMarketSymbolData["limits"]["leverage"]["max"]), "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("limits-leverage-min", "center", "white", ("Arial", 10, ""))); newMatrix[1].append((str(selectedMarketSymbolData["limits"]["leverage"]["min"]), "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("limits-market-max", "center", "white", ("Arial", 10, "")));   newMatrix[1].append((str(selectedMarketSymbolData["limits"]["market"]["max"]),   "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("limits-market-min", "center", "white", ("Arial", 10, "")));   newMatrix[1].append((str(selectedMarketSymbolData["limits"]["market"]["min"]),   "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("limits-price-max", "center", "white", ("Arial", 10, "")));    newMatrix[1].append((str(selectedMarketSymbolData["limits"]["price"]["max"]),    "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("limits-price-min", "center", "white", ("Arial", 10, "")));    newMatrix[1].append((str(selectedMarketSymbolData["limits"]["price"]["min"]),    "center", "white", ("Arial", 10, "")))
                elif (dataKey == "precision"):
                    newMatrix[0].append(("precision-amount", "center", "white", ("Arial", 10, ""))); newMatrix[1].append((str(selectedMarketSymbolData["precision"]["amount"]), "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("precision-base", "center", "white", ("Arial", 10, "")));   newMatrix[1].append((str(selectedMarketSymbolData["precision"]["base"]),   "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("precision-price", "center", "white", ("Arial", 10, "")));  newMatrix[1].append((str(selectedMarketSymbolData["precision"]["price"]),  "center", "white", ("Arial", 10, "")))
                    newMatrix[0].append(("precision-quote", "center", "white", ("Arial", 10, "")));  newMatrix[1].append((str(selectedMarketSymbolData["precision"]["quote"]),  "center", "white", ("Arial", 10, "")))
                elif not(dataKey == "info"):
                    newMatrix[0].append((dataKey, "center", "white", ("Arial", 10, ""))); newMatrix[1].append((str(selectedMarketSymbolData[dataKey]), "center", "white", ("Arial", 10, "")))
            page_APICONTROL_BINANCEAPI["MARKETDATA_SEARCHEDDATAMATRIX"].updateMatrix(newMatrix)
            manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETSYMBOLSELECTED_CURRENTPRICEUNIT"] = str(selectedMarketSymbolData['quote'])
        self.objectFunctions[thisPage+"-MARKETDATA_SEARCHBUTTON-ACTIVATED"] = __guioF_APICONTROL_BINANCEAPI_MARKETDATA_SEARCHBUTTON_ACTIVATED

        def __guioF_APICONTROL_BINANCEAPI_MARKETDATA_MATRIX_VIEWRANGEUPDATED(manager): manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_MATRIX_SB_V"].changeViewRange(manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-MARKETDATA_MATRIX-VIEWRANGEUPDATED"] = __guioF_APICONTROL_BINANCEAPI_MARKETDATA_MATRIX_VIEWRANGEUPDATED
        def __guioF_APICONTROL_BINANCEAPI_MARKETDATA_MATRIX_SB_V_VALUEUPDATED(manager): manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_MATRIX"].changeViewRangeV(manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-MARKETDATA_MATRIX_SB_V-VALUEUPDATED"] = __guioF_APICONTROL_BINANCEAPI_MARKETDATA_MATRIX_SB_V_VALUEUPDATED

        def __guioF_APICONTROL_BINANCEAPI_SPOTWALLET_BALANCEMATRIX_VIEWRANGEUPDATED(manager): manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_BALANCEMATRIX_SB_V"].changeViewRange(manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_BALANCEMATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-SPOTWALLET_BALANCEMATRIX-VIEWRANGEUPDATED"] = __guioF_APICONTROL_BINANCEAPI_SPOTWALLET_BALANCEMATRIX_VIEWRANGEUPDATED
        def __guioF_APICONTROL_BINANCEAPI_SPOTWALLET_BALANCEMATRIX_SB_V_VALUEUPDATED(manager): manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_BALANCEMATRIX"].changeViewRangeV(manager.pages["APICONTROL_BINANCEAPI"]["SPOTWALLET_BALANCEMATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-SPOTWALLET_BALANCEMATRIX_SB_V-VALUEUPDATED"] = __guioF_APICONTROL_BINANCEAPI_SPOTWALLET_BALANCEMATRIX_SB_V_VALUEUPDATED

        def __guioF_APICONTROL_BINANCEAPI_FUTURESWALLET_POSITIONMATRIX_VIEWRANGEUPDATED(manager): manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_POSITIONMATRIX_SB_V"].changeViewRange(manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_POSITIONMATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-FUTURESWALLET_POSITIONMATRIX-VIEWRANGEUPDATED"] = __guioF_APICONTROL_BINANCEAPI_FUTURESWALLET_POSITIONMATRIX_VIEWRANGEUPDATED
        def __guioF_APICONTROL_BINANCEAPI_FUTURESWALLET_POSITIONMATRIX_SB_V_VALUEUPDATED(manager): manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_POSITIONMATRIX"].changeViewRangeV(manager.pages["APICONTROL_BINANCEAPI"]["FUTURESWALLET_POSITIONMATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-FUTURESWALLET_POSITIONMATRIX_SB_V-VALUEUPDATED"] = __guioF_APICONTROL_BINANCEAPI_FUTURESWALLET_POSITIONMATRIX_SB_V_VALUEUPDATED
        
        #Page Timer Functions
        def timerFunction_page_APICONTROL_BINANCEAPI_CHECKBINANCEAPISTATUS(manager):
            if (manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETCONNECTIONSTATUS"] == True): #If GUI record of Binance Market Connection is True
                if (manager.pageVariables["APICONTROL_BINANCEAPI"]["ACCOUNTCONNECTIONSTATUS"] == True): #If GUI record of Account Connection is True
                    binanceAccountConnectionStatus = manager.assistantIPC.getPRD("BINANCEAPI", "ACCOUNTCONNECTIONSTATUS")
                    if (binanceAccountConnectionStatus != None):
                        status = binanceAccountConnectionStatus[0]; checkTime = binanceAccountConnectionStatus[1]
                        if (status == True): manager.pages["APICONTROL_BINANCEAPI"]["STATUSLEDTEXT"].updateText("ACCOUNT CONNECTED <{:s}>".format(time.ctime(checkTime)))
                        else:
                            manager.pageVariables["APICONTROL_BINANCEAPI"]["ACCOUNTCONNECTIONSTATUS"] = False
                            manager.pages["APICONTROL_BINANCEAPI"]["STATUSLED"].updateColor("marketOnline")
                            manager.pages["APICONTROL_BINANCEAPI"]["STATUSLEDTEXT"].updateText("MARKET CONNECTED <{:s}>".format(time.ctime(manager.assistantIPC.getPRD("BINANCEAPI", "MARKETCONNECTIONSTATUS")[1])))
                            manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LED"].updateColor("marketOnline")
                            manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LEDTEXT"].updateText("MARKET CONNECTED")
                            manager.pages["APICONTROL_BINANCEAPI"]["API_LOGIN_BUTTONTEXT"].updateText("CONNECT")
                            selectedOption = manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_SELECTIONBOX"].getSelected()
                            if (selectedOption == "<MANUAL TYPE>"):
                                manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_APIKEY"].activate()
                                manager.pages["APICONTROL_BINANCEAPI"]["INPUTBOX_SECRETKEY"].activate()
                            else:
                                manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_PASSWORDINPUTBOX"].activate()
                            manager.pages["APICONTROL_BINANCEAPI"]["PRE_REGISTEREDKEYS_SELECTIONBOX"].activate()
                        self.pageVariables["APICONTROL_BINANCEAPI"]["LASTCONNECTIONCHECKTIME"] = checkTime
                else: #If GUI record of Account Connection is False
                    if (manager.assistantIPC.getPRD("BINANCEAPI", "MARKETCONNECTIONSTATUS")[0] == False): #If Market Connection is False
                        manager.pages["APICONTROL_BINANCEAPI"]["STATUSLED"].updateColor("offline");  
                        manager.pages["APICONTROL_BINANCEAPI"]["STATUSLEDTEXT"].updateText("MARKET DISCONNECTED")
                        manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LED"].updateColor("offline")
                        manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LEDTEXT"].updateText("MARKET DISCONNECTED")
                        manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETCONNECTIONSTATUS"] = False
                    else: manager.pages["APICONTROL_BINANCEAPI"]["STATUSLEDTEXT"].updateText("MARKET CONNECTED <{:s}>".format(time.ctime(manager.assistantIPC.getPRD("BINANCEAPI", "MARKETCONNECTIONSTATUS")[1])))
            else: #If GUI record of Binance Market Connection is False
                if (manager.assistantIPC.getPRD("BINANCEAPI", "MARKETCONNECTIONSTATUS")[0] == True): #If Market Connection is True
                    manager.pages["APICONTROL_BINANCEAPI"]["STATUSLED"].updateColor("marketOnline");  
                    manager.pages["APICONTROL_BINANCEAPI"]["STATUSLEDTEXT"].updateText("MARKET CONNECTED <{:s}>".format(time.ctime(manager.assistantIPC.getPRD("BINANCEAPI", "MARKETCONNECTIONSTATUS")[1])))
                    manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LED"].updateColor("marketOnline")
                    manager.pages["APICONTROL"]["LOCALNAVIGATION_BINANCEAPI_LEDTEXT"].updateText("MARKET CONNECTED")
                    manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETCONNECTIONSTATUS"] = True
            return True
        self.timerFunctions[thisPage]["CHECKAPICONNECTION"]     = self.__timerFunction(function = timerFunction_page_APICONTROL_BINANCEAPI_CHECKBINANCEAPISTATUS, interval = 100)
        self.timerFunctions["APICONTROL"]["CHECKAPICONNECTION"] = self.__timerFunction(function = timerFunction_page_APICONTROL_BINANCEAPI_CHECKBINANCEAPISTATUS, interval = 100)
        def timerFunction_page_APICONTROL_BINANCEAPI_LOADCURRENTPRICE(manager):
            if (manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETCONNECTIONSTATUS"] == True):
                if (manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETSYMBOLSELECTED"] != None):
                    tID = manager.assistantIPC.sendFAR("BINANCEAPI", "FETCH_TICKER", manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETSYMBOLSELECTED"])
                    def timerFunction_page_APICONTROL_BINANCEAPI_LOADCURRENTPRICE_FARHandler0(manager, result):
                        manager.pages["APICONTROL_BINANCEAPI"]["MARKETDATA_CURRENTPRICE"].updateText("{:s} {:s}".format(str(result['last']), manager.pageVariables["APICONTROL_BINANCEAPI"]["MARKETSYMBOLSELECTED_CURRENTPRICEUNIT"]))
                    manager.IPCResultHandlers[tID] = timerFunction_page_APICONTROL_BINANCEAPI_LOADCURRENTPRICE_FARHandler0
            return True
        self.timerFunctions[thisPage]["LOADCURRENTPRICE"] = self.__timerFunction(function = timerFunction_page_APICONTROL_BINANCEAPI_LOADCURRENTPRICE, interval = 1000)

        def timerFunction_page_APICONTROL_BINANCEAPI_LOADBALANCES(manager): 
            if (manager.pageVariables["APICONTROL_BINANCEAPI"]["ACCOUNTCONNECTIONSTATUS"] == True): __pageAux_APICONTROL_BINANCEAPI_UPDATEBALANCES(manager)
            return True
        self.timerFunctions[thisPage]["LOADBALANCES"] = self.__timerFunction(function = timerFunction_page_APICONTROL_BINANCEAPI_LOADBALANCES, interval = 5000)
        #PAGE "APICONTROL_BINANCEAPI" END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        subPages = ["APICONTROL",
                    "APICONTROL_BINANCEAPI"]
        for pageName in subPages:
            thisPage = pageName
            self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        #PAGE "APICONTROL" END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





        #PAGE "PROGRAM" ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()

        program_navigationGUIOs = dict()
        program_navigationGUIOs["LOCALNAVIGATION_MAIN"] = button_typeA(self.canvas, self.graphicsGenerator,                10, 65, 200, 30, "styleA_themeC", layer = 1, text = "PROGRAM MAIN",      textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_P_MAIN"] = button_typeA(self.canvas, self.graphicsGenerator,             215, 65, 190, 30, "styleA_themeC", layer = 1, text = "[P] MAIN",          textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_P_AUTOTRADER"] = button_typeA(self.canvas, self.graphicsGenerator,       410, 65, 190, 30, "styleA_themeC", layer = 1, text = "[P] AUTO TRADER",   textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_P_BINANCEAPI"] = button_typeA(self.canvas, self.graphicsGenerator,       605, 65, 190, 30, "styleA_themeC", layer = 1, text = "[P] BINANCE API",   textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_P_DATAANALYSIS"] = button_typeA(self.canvas, self.graphicsGenerator,     800, 65, 190, 30, "styleA_themeC", layer = 1, text = "[P] DATA ANALYSIS", textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_P_DATAMANAGEMENT"] = button_typeA(self.canvas, self.graphicsGenerator,   995, 65, 190, 30, "styleA_themeC", layer = 1, text = "[P] DATA MANAGE",   textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_P_GUI"] = button_typeA(self.canvas, self.graphicsGenerator,             1190, 65, 190, 30, "styleA_themeC", layer = 1, text = "[P] GUI",           textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_P_IPC"] = button_typeA(self.canvas, self.graphicsGenerator,             1385, 65, 190, 30, "styleA_themeC", layer = 1, text = "[P] IPC",           textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_P_SECURITYCONTROL"] = button_typeA(self.canvas, self.graphicsGenerator, 1580, 65, 190, 30, "styleA_themeC", layer = 1, text = "[P] SECURITY",      textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_EXP0"] = button_typeA(self.canvas, self.graphicsGenerator,              1775, 65, 190, 30, "styleA_themeC", layer = 1, text = "EXPERIMENT 0",      textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_EXP1"] = button_typeA(self.canvas, self.graphicsGenerator,              1970, 65, 190, 30, "styleA_themeC", layer = 1, text = "EXPERIMENT 1",      textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_EXP2"] = button_typeA(self.canvas, self.graphicsGenerator,              2165, 65, 190, 30, "styleA_themeC", layer = 1, text = "EXPERIMENT 2",      textSize = 16)
        program_navigationGUIOs["LOCALNAVIGATION_EXP3"] = button_typeA(self.canvas, self.graphicsGenerator,              2360, 65, 190, 30, "styleA_themeC", layer = 1, text = "EXPERIMENT 3",      textSize = 16)
        program_navigationGUIOs["LOCALPAGE_FRAME"] = constantGraphic_typeA(self.canvas, self.graphicsGenerator, 10, 100, 2540, 1, "styleB_themeA", layer = 0)

        page_PROGRAM = dict()
        page_PROGRAM.update(main_navigationGUIOs)
        page_PROGRAM.update(program_navigationGUIOs)

        def page_PROGRAM_load(manager):
            manager.pages["PROGRAM"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM"]["LOCALNAVIGATION_MAIN"].deactivate()
        def page_PROGRAM_close(manager):
            manager.pages["PROGRAM"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM"]["LOCALNAVIGATION_MAIN"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_close

        self.pages[thisPage] = page_PROGRAM

        #Object Functions

        #PAGE "PROGRAM_P_MAIN" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_P_MAIN"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_P_MAIN = dict()
        page_PROGRAM_P_MAIN.update(main_navigationGUIOs)
        page_PROGRAM_P_MAIN.update(program_navigationGUIOs)

        def page_PROGRAM_P_MAIN_load(manager):
            manager.pages["PROGRAM_P_MAIN"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_P_MAIN"]["LOCALNAVIGATION_P_MAIN"].deactivate()
        def page_PROGRAM_P_MAIN_close(manager):
            manager.pages["PROGRAM_P_MAIN"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_P_MAIN"]["LOCALNAVIGATION_P_MAIN"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_P_MAIN_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_P_MAIN_close
        
        page_PROGRAM_P_MAIN["PROCESSCOUNTERS_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           10, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "PROCESS PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_MAIN["PROCESS_LASTLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["PROCESS_LASTLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["PROCESS_LASTPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["PROCESS_LASTPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["PROCESS_AVGLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["PROCESS_AVGLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["PROCESS_AVGPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["PROCESS_AVGPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["PPC_SAMPLEN_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,               10, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Number of Records", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["PPC_SAMPLEN_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,                    215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["AVG_STANDARD_SELECTIONBOXTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 340, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Count Standard", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["AVG_STANDARD_SELECTIONBOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,            545, 220, 120, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendFAR("MAIN", "GET_PTIMERS_AVGSTANDARD", None, nRetry = "INF")
        def __guioF_PROGRAM_P_MAIN_INITIALIZATIONDATAREQUEST0(manager, result): 
            manager.pages["PROGRAM_P_MAIN"]["AVG_STANDARD_SELECTIONBOX"].editSelected(str(result))
            manager.pageVariables["PROGRAM_P_MAIN"]['AVG_STANDARD'] = result
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_MAIN_INITIALIZATIONDATAREQUEST0
        page_PROGRAM_P_MAIN["AVG_STANDARD_SELECTIONBOX"].updateList(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "20", "30", "40", "50", "60"])
        page_PROGRAM_P_MAIN["P_LOG_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 265,  655,   40, style = "styleA_themeA", layer = 1, text = "PROCESS MESSAGE LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_MAIN["P_LOG"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,          10, 310,  620, 1085, "styleA_themeA", layer = 1, nDisplayedColumns = 1, nDisplayedRows = 30)
        page_PROGRAM_P_MAIN["P_LOG_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,           635, 310, 1085,   30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_MAIN["P_LOG"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_MAIN["P_LOG_COMMENT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,     10, 1400, 620, 30, boxStyle = "styleA_themeC", layer = 1, text = "PROCESS [MAIN] LOG", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["P_LOG_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,            635, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)
        page_PROGRAM_P_MAIN["IPCAPERF_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           680, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_MAIN["IPCA_READTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_READTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_READSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_READSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_READRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_READRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_AVGREADTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_AVGREADTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_AVGREADSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_AVGREADSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_AVGREADRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_AVGREADRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_WRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_WRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_WRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_WRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_WRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_WRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_AVGWRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_AVGWRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_AVGWRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_AVGWRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCA_AVGWRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_AVGWRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["PRD_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,            680, 375, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC PRE-REGISTERED DATA", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_MAIN["PRD_MANAGERSELECTION_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 420, 325, 30, style = "styleA_themeA", layer = 1, text = "PRD From", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_MAIN["PRD_MANAGERSELECTION_BOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,         1010, 420, 325, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("MAIN", "ATMMANAGERS", nRetry = "INF")
        def __guioF_PROGRAM_P_MAIN_INITIALIZATIONDATAREQUEST1(manager, result):
            manager.pages["PROGRAM_P_MAIN"]["PRD_MANAGERSELECTION_BOX"].updateList(result)
            manager.pages["PROGRAM_P_MAIN"]["PRD_MANAGERSELECTION_BOX"].editSelected(result[0])
            manager.pageVariables["PROGRAM_P_MAIN"]['PRD_ManagerSelection'] = result[0]
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_MAIN_INITIALIZATIONDATAREQUEST1
        page_PROGRAM_P_MAIN["PRD_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 455, 620, 350, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 8, columnTitles = [("[INDEX] DATA NAME", "center", "white", ("Arial", 12, "bold")), ("DATA CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (4, 6))
        page_PROGRAM_P_MAIN["PRD_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 455, 350,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_MAIN["PRD_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_MAIN["IPCLOG_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 820, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_MAIN["IPCLOG_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 865, 620, 530, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 10, columnTitles = [("[INDEX] Record Time", "center", "white", ("Arial", 12, "bold")), ("CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (3, 7))
        page_PROGRAM_P_MAIN["IPCLOG_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 865, 530,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_MAIN["IPCLOG_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_MAIN["IPCA_COMMENT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 680, 1400, 325, 30, style = "styleA_themeA", layer = 1, text = "< IPCLOGs are not recorded to avoid recursion >", textFill = (255, 255, 255, 200), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_AVAILABLETID_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 1400, 200, 30, style = "styleA_themeA", layer = 1, text = "Available Transmission IDs", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_MAIN["IPCA_AVAILABLETID_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 1400,  85, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_MAIN["IPCLOG_MATRIX_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,                1305, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)

        self.pages[thisPage] = page_PROGRAM_P_MAIN

        #Object Functions
        def __guioF_PROGRAM_P_MAIN_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED(manager): 
            selectedOption = manager.pages["PROGRAM_P_MAIN"]["AVG_STANDARD_SELECTIONBOX"].getSelected() 
            tID = manager.assistantIPC.sendFAR("MAIN", "EDIT_PTIMERAVGSTANDARD", int(selectedOption))
            def __guioF_PROGRAM_P_MAIN_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                manager.pages["PROGRAM_P_MAIN"]["AVG_STANDARD_SELECTIONBOX"].editSelected(result)
                manager.pageVariables["PROGRAM_P_MAIN"]['AVG_STANDARD'] = result
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_MAIN_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-AVG_STANDARD_SELECTIONBOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_MAIN_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED
        def __guioF_PROGRAM_P_MAIN_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED(manager):
            selectedOption = manager.pages["PROGRAM_P_MAIN"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_MAIN"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("MAIN", "GET_PRD", (selectedOption, 70))
            def __guioF_PROGRAM_P_MAIN_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                prd = result; matrix = [[],[]]; prdKeys = list(prd.keys())
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_MAIN"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_MAIN_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-PRD_MANAGERSELECTION_BOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_MAIN_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED 
        def __guioF_PROGRAM_P_MAIN_P_LOG_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_MAIN"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_MAIN"]["P_LOG"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-P_LOG-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_MAIN_P_LOG_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_MAIN_P_LOG_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_MAIN"]["P_LOG"].changeViewRangeV(manager.pages["PROGRAM_P_MAIN"]["P_LOG_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-P_LOG_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_MAIN_P_LOG_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_MAIN_IPCLOG_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_MAIN"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_MAIN"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_MAIN_IPCLOG_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_MAIN_IPCLOG_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_MAIN"]["IPCLOG_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_MAIN"]["IPCLOG_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_MAIN_IPCLOG_MATRIX_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_MAIN_PRD_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_MAIN"]["PRD_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_MAIN"]["PRD_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-PRD_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_MAIN_PRD_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_MAIN_PRD_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_MAIN"]["PRD_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_MAIN"]["PRD_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-PRD_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_MAIN_PRD_MATRIX_SB_V_VALUEUPDATED
        #Page Timer Functions
        def timerFunction_page_PROGRAM_P_MAIN_UpdateProcessData0(manager):
            tID = manager.assistantIPC.sendFAR("MAIN", "GET_PTIMERS_LAST", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_MAIN_UpdateProcessData0_FARHanlder0(manager, result):
                lastRecord = result
                if (lastRecord != None):
                    manager.pages["PROGRAM_P_MAIN"]["PROCESS_LASTLOOPTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_processLoop'], "ns"))
                    manager.pages["PROGRAM_P_MAIN"]["PROCESS_LASTPROCTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_process'], "ns"))
                    manager.pages["PROGRAM_P_MAIN"]["IPCA_READTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readTime'], "ns"))
                    manager.pages["PROGRAM_P_MAIN"]["IPCA_READSIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readSize'], "Bytes"))
                    manager.pages["PROGRAM_P_MAIN"]["IPCA_READRATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readRate'] / manager.pageVariables["PROGRAM_P_MAIN"]['AVG_STANDARD'], "Bytes/s"))
                    manager.pages["PROGRAM_P_MAIN"]["IPCA_WRITETIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeTime'], "ns"))
                    manager.pages["PROGRAM_P_MAIN"]["IPCA_WRITESIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeSize'], "Bytes"))
                    manager.pages["PROGRAM_P_MAIN"]["IPCA_WRITERATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeRate'] / manager.pageVariables["PROGRAM_P_MAIN"]['AVG_STANDARD'], "Bytes/s"))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_MAIN_UpdateProcessData0_FARHanlder0
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA0"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_MAIN_UpdateProcessData0, interval = 100)
        def timerFunction_page_PROGRAM_P_MAIN_UpdateProcessData1(manager):
            tID = manager.assistantIPC.sendFAR("MAIN", "GET_PTIMERS_AVG", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_MAIN_UpdateProcessData1_FARHanlder0(manager, result):
                processTimers = result
                manager.pages["PROGRAM_P_MAIN"]["PROCESS_AVGLOOPTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_processLoop_avg'], "ns"))
                manager.pages["PROGRAM_P_MAIN"]["PROCESS_AVGPROCTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_process_avg'], "ns"))
                manager.pages["PROGRAM_P_MAIN"]["IPCA_AVGREADTIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readTime_avg'], "ns"))
                manager.pages["PROGRAM_P_MAIN"]["IPCA_AVGREADSIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_MAIN"]["IPCA_AVGREADRATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readRate_avg'] / manager.pageVariables["PROGRAM_P_MAIN"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_MAIN"]["IPCA_AVGWRITETIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeTime_avg'], "ns"))
                manager.pages["PROGRAM_P_MAIN"]["IPCA_AVGWRITESIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_MAIN"]["IPCA_AVGWRITERATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeRate_avg'] / manager.pageVariables["PROGRAM_P_MAIN"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_MAIN"]["PPC_SAMPLEN_DATA"].updateText("{:d} samples".format(processTimers['nRecords']))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_MAIN_UpdateProcessData1_FARHanlder0
            tID = manager.assistantIPC.sendFAR("MAIN", "GET_IPC_TIDAVAILABILITY", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_MAIN_UpdateProcessData1_FARHanlder1(manager, result):
                manager.pages["PROGRAM_P_MAIN"]["IPCA_AVAILABLETID_DATA"].updateText("{:d} / {:d}".format(result[0], result[1]))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_MAIN_UpdateProcessData1_FARHanlder1
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA1"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_MAIN_UpdateProcessData1, interval = 250)
        def timerFunction_page_P_MAIN_UpdateProcessLog(manager):
            if (manager.pages["PROGRAM_P_MAIN"]["P_LOG_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("MAIN", "GET_PLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_P_MAIN_UpdateProcessLog_FARHandler0(manager, result):
                    matrix = [[]]; processLog = result; maximumDisplayStringLength = 100
                    for i in range (len(processLog)):
                        dataContent = processLog[i]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[0].append(("[{:d}] {:s}".format(i, dataContent), "w", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_MAIN"]["P_LOG"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_MAIN"]["P_LOG"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_MAIN"]["P_LOG"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_MAIN"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_MAIN"]["P_LOG"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_P_MAIN_UpdateProcessLog_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPROCESSLOG"] = self.__timerFunction(function = timerFunction_page_P_MAIN_UpdateProcessLog, interval = 1000)
        def timerFunction_page_PROGRAM_P_MAIN_UpdatePRDData(manager):
            selectedOption = manager.pages["PROGRAM_P_MAIN"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_MAIN"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("MAIN", "GET_PRD", (selectedOption, 70), nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_MAIN_UpdatePRDData_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]; maximumDisplayStringLength = 70
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_MAIN"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_MAIN_UpdatePRDData_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPRDDATA"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_MAIN_UpdatePRDData, interval = 1000)
        def timerFunction_page_PROGRAM_P_MAIN_UpdateIPCLOG(manager):
            if (manager.pages["PROGRAM_P_MAIN"]["IPCLOG_MATRIX_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("MAIN", "GET_IPCLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_PROGRAM_P_MAIN_UpdateIPCLOG_FARHandler0(manager, result):
                    ipcLog = result; matrix = [[],[]]; maximumDisplayStringLength = 100
                    for i in range (len(ipcLog)): 
                        matrix[0].append(("[{:d}] {:s}".format(i, self.__valueFormatter(ipcLog[i][0], "ns")), "center", "white", ("Arial", 10, "")))
                        dataContent = ipcLog[i][1]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[1].append((dataContent, "center", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_MAIN"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_MAIN"]["IPCLOG_MATRIX"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_MAIN"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_MAIN"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_MAIN"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_MAIN_UpdateIPCLOG_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEIPCLOG"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_MAIN_UpdateIPCLOG, interval = 1000)
        
        #PAGE "PROGRAM_P_MAIN" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_P_AUTOTRADER" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_P_AUTOTRADER"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_P_AUTOTRADER = dict()
        page_PROGRAM_P_AUTOTRADER.update(main_navigationGUIOs)
        page_PROGRAM_P_AUTOTRADER.update(program_navigationGUIOs)

        def page_PROGRAM_P_AUTOTRADER_load(manager):
            manager.pages["PROGRAM_P_AUTOTRADER"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_P_AUTOTRADER"]["LOCALNAVIGATION_P_AUTOTRADER"].deactivate()
        def page_PROGRAM_P_AUTOTRADER_close(manager):
            manager.pages["PROGRAM_P_AUTOTRADER"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_P_AUTOTRADER"]["LOCALNAVIGATION_P_AUTOTRADER"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_P_AUTOTRADER_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_P_AUTOTRADER_close
        
        page_PROGRAM_P_AUTOTRADER["PROCESSCOUNTERS_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           10, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "PROCESS PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_AUTOTRADER["PROCESS_LASTLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["PROCESS_LASTLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["PROCESS_LASTPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["PROCESS_LASTPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["PROCESS_AVGLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["PROCESS_AVGLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["PROCESS_AVGPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["PROCESS_AVGPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["PPC_SAMPLEN_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,               10, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Number of Records", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["PPC_SAMPLEN_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,                    215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["AVG_STANDARD_SELECTIONBOXTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 340, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Count Standard", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["AVG_STANDARD_SELECTIONBOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,            545, 220, 120, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("AUTOTRADER", "PTIMERS_AVGSTANDARD", nRetry = "INF")
        def __guioF_PROGRAM_P_AUTOTRADER_INITIALIZATIONDATAREQUEST0(manager, result): 
            manager.pages["PROGRAM_P_AUTOTRADER"]["AVG_STANDARD_SELECTIONBOX"].editSelected(str(result))
            manager.pageVariables["PROGRAM_P_AUTOTRADER"]['AVG_STANDARD'] = result
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_AUTOTRADER_INITIALIZATIONDATAREQUEST0
        page_PROGRAM_P_AUTOTRADER["AVG_STANDARD_SELECTIONBOX"].updateList(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "20", "30", "40", "50", "60"])
        page_PROGRAM_P_AUTOTRADER["P_LOG_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 265,  655,   40, style = "styleA_themeA", layer = 1, text = "PROCESS MESSAGE LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_AUTOTRADER["P_LOG"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,          10, 310,  620, 1085, "styleA_themeA", layer = 1, nDisplayedColumns = 1, nDisplayedRows = 30)
        page_PROGRAM_P_AUTOTRADER["P_LOG_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,           635, 310, 1085,   30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_AUTOTRADER["P_LOG"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_AUTOTRADER["P_LOG_COMMENT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,     10, 1400, 620, 30, boxStyle = "styleA_themeC", layer = 1, text = "PROCESS [AUTOTRADER] LOG", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["P_LOG_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,            635, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)
        page_PROGRAM_P_AUTOTRADER["IPCAPERF_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           680, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_AUTOTRADER["IPCA_READTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_READTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_READSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_READSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_READRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_READRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGREADTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGREADTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGREADSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGREADSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGREADRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGREADRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_WRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_WRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_WRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_WRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_WRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_WRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGWRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGWRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGWRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGWRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGWRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_AVGWRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["PRD_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,            680, 375, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC PRE-REGISTERED DATA", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_AUTOTRADER["PRD_MANAGERSELECTION_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 420, 325, 30, style = "styleA_themeA", layer = 1, text = "PRD From", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_AUTOTRADER["PRD_MANAGERSELECTION_BOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,         1010, 420, 325, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("AUTOTRADER", "ATMMANAGERS", nRetry = "INF")
        def __guioF_PROGRAM_P_AUTOTRADER_INITIALIZATIONDATAREQUEST1(manager, result):
            manager.pages["PROGRAM_P_AUTOTRADER"]["PRD_MANAGERSELECTION_BOX"].updateList(result)
            manager.pages["PROGRAM_P_AUTOTRADER"]["PRD_MANAGERSELECTION_BOX"].editSelected(result[0])
            manager.pageVariables["PROGRAM_P_AUTOTRADER"]['PRD_ManagerSelection'] = result[0]
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_AUTOTRADER_INITIALIZATIONDATAREQUEST1
        page_PROGRAM_P_AUTOTRADER["PRD_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 455, 620, 350, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 8, columnTitles = [("[INDEX] DATA NAME", "center", "white", ("Arial", 12, "bold")), ("DATA CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (4, 6))
        page_PROGRAM_P_AUTOTRADER["PRD_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 455, 350,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_AUTOTRADER["PRD_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_AUTOTRADER["IPCLOG_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 820, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_AUTOTRADER["IPCLOG_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 865, 620, 530, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 10, columnTitles = [("[INDEX] Record Time", "center", "white", ("Arial", 12, "bold")), ("CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (3, 7))
        page_PROGRAM_P_AUTOTRADER["IPCLOG_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 865, 530,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_AUTOTRADER["IPCLOG_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_AUTOTRADER["IPCA_COMMENT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 680, 1400, 325, 30, style = "styleA_themeA", layer = 1, text = "< IPCLOGs are not recorded to avoid recursion >", textFill = (255, 255, 255, 200), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_AVAILABLETID_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 1400, 200, 30, style = "styleA_themeA", layer = 1, text = "Available Transmission IDs", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_AUTOTRADER["IPCA_AVAILABLETID_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 1400,  85, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_AUTOTRADER["IPCLOG_MATRIX_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,                1305, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)

        self.pages[thisPage] = page_PROGRAM_P_AUTOTRADER

        #Object Functions
        def __guioF_PROGRAM_P_AUTOTRADER_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED(manager): 
            selectedOption = manager.pages["PROGRAM_P_AUTOTRADER"]["AVG_STANDARD_SELECTIONBOX"].getSelected() 
            tID = manager.assistantIPC.sendFAR("AUTOTRADER", "EDIT_PTIMERAVGSTANDARD", int(selectedOption))
            def __guioF_PROGRAM_P_AUTOTRADER_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                manager.pages["PROGRAM_P_AUTOTRADER"]["AVG_STANDARD_SELECTIONBOX"].editSelected(result)
                manager.pageVariables["PROGRAM_P_AUTOTRADER"]['AVG_STANDARD'] = result
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_AUTOTRADER_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-AVG_STANDARD_SELECTIONBOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_AUTOTRADER_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED
        def __guioF_PROGRAM_P_AUTOTRADER_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED(manager):
            selectedOption = manager.pages["PROGRAM_P_AUTOTRADER"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_AUTOTRADER"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("AUTOTRADER", "GET_PRD", (selectedOption, 70))
            def __guioF_PROGRAM_P_AUTOTRADER_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]; maximumDisplayStringLength = 70
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_AUTOTRADER"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_AUTOTRADER_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-PRD_MANAGERSELECTION_BOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_AUTOTRADER_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED 
        def __guioF_PROGRAM_P_AUTOTRADER_P_LOG_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_AUTOTRADER"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_AUTOTRADER"]["P_LOG"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-P_LOG-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_AUTOTRADER_P_LOG_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_AUTOTRADER_P_LOG_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_AUTOTRADER"]["P_LOG"].changeViewRangeV(manager.pages["PROGRAM_P_AUTOTRADER"]["P_LOG_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-P_LOG_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_AUTOTRADER_P_LOG_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_AUTOTRADER_IPCLOG_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_AUTOTRADER"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_AUTOTRADER"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_AUTOTRADER_IPCLOG_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_AUTOTRADER_IPCLOG_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_AUTOTRADER"]["IPCLOG_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_AUTOTRADER"]["IPCLOG_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_AUTOTRADER_IPCLOG_MATRIX_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_AUTOTRADER_PRD_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_AUTOTRADER"]["PRD_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_AUTOTRADER"]["PRD_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-PRD_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_AUTOTRADER_PRD_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_AUTOTRADER_PRD_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_AUTOTRADER"]["PRD_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_AUTOTRADER"]["PRD_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-PRD_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_AUTOTRADER_PRD_MATRIX_SB_V_VALUEUPDATED
        #Page Timer Functions
        def timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateProcessData0(manager):
            tID = manager.assistantIPC.sendFAR("AUTOTRADER", "GET_PTIMERS_LAST", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateProcessData0_FARHanlder0(manager, result):
                lastRecord = result
                if (lastRecord != None):
                    manager.pages["PROGRAM_P_AUTOTRADER"]["PROCESS_LASTLOOPTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_processLoop'], "ns"))
                    manager.pages["PROGRAM_P_AUTOTRADER"]["PROCESS_LASTPROCTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_process'], "ns"))
                    manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_READTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readTime'], "ns"))
                    manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_READSIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readSize'], "Bytes"))
                    manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_READRATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readRate'] / manager.pageVariables["PROGRAM_P_AUTOTRADER"]['AVG_STANDARD'], "Bytes/s"))
                    manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_WRITETIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeTime'], "ns"))
                    manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_WRITESIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeSize'], "Bytes"))
                    manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_WRITERATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeRate'] / manager.pageVariables["PROGRAM_P_AUTOTRADER"]['AVG_STANDARD'], "Bytes/s"))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateProcessData0_FARHanlder0
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA0"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateProcessData0, interval = 100)
        def timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateProcessData1(manager):
            tID = manager.assistantIPC.sendFAR("AUTOTRADER", "GET_PTIMERS_AVG", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateProcessData1_FARHanlder0(manager, result):
                processTimers = result
                manager.pages["PROGRAM_P_AUTOTRADER"]["PROCESS_AVGLOOPTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_processLoop_avg'], "ns"))
                manager.pages["PROGRAM_P_AUTOTRADER"]["PROCESS_AVGPROCTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_process_avg'], "ns"))
                manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_AVGREADTIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readTime_avg'], "ns"))
                manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_AVGREADSIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_AVGREADRATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readRate_avg'] / manager.pageVariables["PROGRAM_P_AUTOTRADER"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_AVGWRITETIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeTime_avg'], "ns"))
                manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_AVGWRITESIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_AVGWRITERATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeRate_avg'] / manager.pageVariables["PROGRAM_P_AUTOTRADER"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_AUTOTRADER"]["PPC_SAMPLEN_DATA"].updateText("{:d} samples".format(processTimers['nRecords']))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateProcessData1_FARHanlder0
            tID = manager.assistantIPC.sendFAR("AUTOTRADER", "GET_IPC_TIDAVAILABILITY", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateProcessData1_FARHanlder1(manager, result):
                manager.pages["PROGRAM_P_AUTOTRADER"]["IPCA_AVAILABLETID_DATA"].updateText("{:d} / {:d}".format(result[0], result[1]))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateProcessData1_FARHanlder1
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA1"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateProcessData1, interval = 250)
        def timerFunction_page_P_AUTOTRADER_UpdateProcessLog(manager):
            if (manager.pages["PROGRAM_P_AUTOTRADER"]["P_LOG_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("AUTOTRADER", "GET_PLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_P_AUTOTRADER_UpdateProcessLog_FARHandler0(manager, result):
                    matrix = [[]]; processLog = result; maximumDisplayStringLength = 100
                    for i in range (len(processLog)):
                        dataContent = processLog[i]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[0].append(("[{:d}] {:s}".format(i, dataContent), "w", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_AUTOTRADER"]["P_LOG"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_AUTOTRADER"]["P_LOG"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_AUTOTRADER"]["P_LOG"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_AUTOTRADER"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_AUTOTRADER"]["P_LOG"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_P_AUTOTRADER_UpdateProcessLog_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPROCESSLOG"] = self.__timerFunction(function = timerFunction_page_P_AUTOTRADER_UpdateProcessLog, interval = 1000)
        def timerFunction_page_PROGRAM_P_AUTOTRADER_UpdatePRDData(manager):
            selectedOption = manager.pages["PROGRAM_P_AUTOTRADER"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_AUTOTRADER"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("AUTOTRADER", "GET_PRD", (selectedOption, 70), nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_AUTOTRADER_UpdatePRDData_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_AUTOTRADER"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_AUTOTRADER_UpdatePRDData_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPRDDATA"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_AUTOTRADER_UpdatePRDData, interval = 1000)
        def timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateIPCLOG(manager):
            if (manager.pages["PROGRAM_P_AUTOTRADER"]["IPCLOG_MATRIX_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("AUTOTRADER", "GET_IPCLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateIPCLOG_FARHandler0(manager, result):
                    ipcLog = result; matrix = [[],[]]; maximumDisplayStringLength = 100
                    for i in range (len(ipcLog)): 
                        matrix[0].append(("[{:d}] {:s}".format(i, self.__valueFormatter(ipcLog[i][0], "ns")), "center", "white", ("Arial", 10, "")))
                        dataContent = ipcLog[i][1]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[1].append((dataContent, "center", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_AUTOTRADER"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_AUTOTRADER"]["IPCLOG_MATRIX"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_AUTOTRADER"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_AUTOTRADER"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_AUTOTRADER"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateIPCLOG_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEIPCLOG"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_AUTOTRADER_UpdateIPCLOG, interval = 1000)
        
        #PAGE "PROGRAM_P_AUTOTRADER" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_P_BINANCEAPI" ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_P_BINANCEAPI"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_P_BINANCEAPI = dict()
        page_PROGRAM_P_BINANCEAPI.update(main_navigationGUIOs)
        page_PROGRAM_P_BINANCEAPI.update(program_navigationGUIOs)

        def page_PROGRAM_P_BINANCEAPI_load(manager):
            manager.pages["PROGRAM_P_BINANCEAPI"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_P_BINANCEAPI"]["LOCALNAVIGATION_P_BINANCEAPI"].deactivate()
        def page_PROGRAM_P_BINANCEAPI_close(manager):
            manager.pages["PROGRAM_P_BINANCEAPI"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_P_BINANCEAPI"]["LOCALNAVIGATION_P_BINANCEAPI"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_P_BINANCEAPI_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_P_BINANCEAPI_close
        
        page_PROGRAM_P_BINANCEAPI["PROCESSCOUNTERS_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           10, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "PROCESS PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_BINANCEAPI["PROCESS_LASTLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["PROCESS_LASTLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["PROCESS_LASTPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["PROCESS_LASTPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["PROCESS_AVGLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["PROCESS_AVGLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["PROCESS_AVGPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["PROCESS_AVGPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["PPC_SAMPLEN_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,               10, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Number of Records", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["PPC_SAMPLEN_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,                    215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["AVG_STANDARD_SELECTIONBOXTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 340, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Count Standard", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["AVG_STANDARD_SELECTIONBOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,            545, 220, 120, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("BINANCEAPI", "PTIMERS_AVGSTANDARD", nRetry = "INF")
        def __guioF_PROGRAM_P_BINANCEAPI_INITIALIZATIONDATAREQUEST0(manager, result): 
            manager.pages["PROGRAM_P_BINANCEAPI"]["AVG_STANDARD_SELECTIONBOX"].editSelected(str(result))
            manager.pageVariables["PROGRAM_P_BINANCEAPI"]['AVG_STANDARD'] = result
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_BINANCEAPI_INITIALIZATIONDATAREQUEST0
        page_PROGRAM_P_BINANCEAPI["AVG_STANDARD_SELECTIONBOX"].updateList(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "20", "30", "40", "50", "60"])
        page_PROGRAM_P_BINANCEAPI["P_LOG_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 265,  655,   40, style = "styleA_themeA", layer = 1, text = "PROCESS MESSAGE LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_BINANCEAPI["P_LOG"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,          10, 310,  620, 1085, "styleA_themeA", layer = 1, nDisplayedColumns = 1, nDisplayedRows = 30)
        page_PROGRAM_P_BINANCEAPI["P_LOG_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,           635, 310, 1085,   30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_BINANCEAPI["P_LOG"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_BINANCEAPI["P_LOG_COMMENT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,     10, 1400, 620, 30, boxStyle = "styleA_themeC", layer = 1, text = "PROCESS [BINANCEAPI] LOG", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["P_LOG_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,            635, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)
        page_PROGRAM_P_BINANCEAPI["IPCAPERF_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           680, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_BINANCEAPI["IPCA_READTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_READTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_READSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_READSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_READRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_READRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGREADTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGREADTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGREADSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGREADSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGREADRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGREADRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_WRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_WRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_WRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_WRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_WRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_WRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGWRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGWRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGWRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGWRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGWRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_AVGWRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["PRD_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,            680, 375, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC PRE-REGISTERED DATA", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_BINANCEAPI["PRD_MANAGERSELECTION_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 420, 325, 30, style = "styleA_themeA", layer = 1, text = "PRD From", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_BINANCEAPI["PRD_MANAGERSELECTION_BOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,         1010, 420, 325, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("BINANCEAPI", "ATMMANAGERS", nRetry = "INF")
        def __guioF_PROGRAM_P_BINANCEAPI_INITIALIZATIONDATAREQUEST1(manager, result):
            manager.pages["PROGRAM_P_BINANCEAPI"]["PRD_MANAGERSELECTION_BOX"].updateList(result)
            manager.pages["PROGRAM_P_BINANCEAPI"]["PRD_MANAGERSELECTION_BOX"].editSelected(result[0])
            manager.pageVariables["PROGRAM_P_BINANCEAPI"]['PRD_ManagerSelection'] = result[0]
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_BINANCEAPI_INITIALIZATIONDATAREQUEST1
        page_PROGRAM_P_BINANCEAPI["PRD_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 455, 620, 350, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 8, columnTitles = [("[INDEX] DATA NAME", "center", "white", ("Arial", 12, "bold")), ("DATA CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (4, 6))
        page_PROGRAM_P_BINANCEAPI["PRD_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 455, 350,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_BINANCEAPI["PRD_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_BINANCEAPI["IPCLOG_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 820, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_BINANCEAPI["IPCLOG_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 865, 620, 530, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 10, columnTitles = [("[INDEX] Record Time", "center", "white", ("Arial", 12, "bold")), ("CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (3, 7))
        page_PROGRAM_P_BINANCEAPI["IPCLOG_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 865, 530,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_BINANCEAPI["IPCLOG_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_BINANCEAPI["IPCA_COMMENT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 680, 1400, 325, 30, style = "styleA_themeA", layer = 1, text = "< IPCLOGs are not recorded to avoid recursion >", textFill = (255, 255, 255, 200), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_AVAILABLETID_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 1400, 200, 30, style = "styleA_themeA", layer = 1, text = "Available Transmission IDs", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_BINANCEAPI["IPCA_AVAILABLETID_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 1400,  85, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_BINANCEAPI["IPCLOG_MATRIX_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,                1305, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)
        
        self.pages[thisPage] = page_PROGRAM_P_BINANCEAPI

        #Object Functions
        def __guioF_PROGRAM_P_BINANCEAPI_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED(manager): 
            selectedOption = manager.pages["PROGRAM_P_BINANCEAPI"]["AVG_STANDARD_SELECTIONBOX"].getSelected() 
            tID = manager.assistantIPC.sendFAR("BINANCEAPI", "EDIT_PTIMERAVGSTANDARD", int(selectedOption))
            def __guioF_PROGRAM_P_BINANCEAPI_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                manager.pages["PROGRAM_P_BINANCEAPI"]["AVG_STANDARD_SELECTIONBOX"].editSelected(result)
                manager.pageVariables["PROGRAM_P_BINANCEAPI"]['AVG_STANDARD'] = result
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_BINANCEAPI_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-AVG_STANDARD_SELECTIONBOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_BINANCEAPI_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED
        def __guioF_PROGRAM_P_BINANCEAPI_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED(manager):
            selectedOption = manager.pages["PROGRAM_P_BINANCEAPI"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_BINANCEAPI"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("BINANCEAPI", "GET_PRD", (selectedOption, 70))
            def __guioF_PROGRAM_P_BINANCEAPI_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_BINANCEAPI"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_BINANCEAPI_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-PRD_MANAGERSELECTION_BOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_BINANCEAPI_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED
        def __guioF_PROGRAM_P_BINANCEAPI_P_LOG_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_BINANCEAPI"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_BINANCEAPI"]["P_LOG"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-P_LOG-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_BINANCEAPI_P_LOG_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_BINANCEAPI_P_LOG_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_BINANCEAPI"]["P_LOG"].changeViewRangeV(manager.pages["PROGRAM_P_BINANCEAPI"]["P_LOG_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-P_LOG_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_BINANCEAPI_P_LOG_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_BINANCEAPI_IPCLOG_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_BINANCEAPI"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_BINANCEAPI"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_BINANCEAPI_IPCLOG_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_BINANCEAPI_IPCLOG_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_BINANCEAPI"]["IPCLOG_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_BINANCEAPI"]["IPCLOG_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_BINANCEAPI_IPCLOG_MATRIX_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_BINANCEAPI_PRD_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_BINANCEAPI"]["PRD_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_BINANCEAPI"]["PRD_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-PRD_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_BINANCEAPI_PRD_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_BINANCEAPI_PRD_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_BINANCEAPI"]["PRD_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_BINANCEAPI"]["PRD_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-PRD_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_BINANCEAPI_PRD_MATRIX_SB_V_VALUEUPDATED
        #Page Timer Functions
        def timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateProcessData0(manager):
            tID = manager.assistantIPC.sendFAR("BINANCEAPI", "GET_PTIMERS_LAST", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateProcessData0_FARHanlder0(manager, result):
                lastRecord = result
                if (lastRecord != None):
                    manager.pages["PROGRAM_P_BINANCEAPI"]["PROCESS_LASTLOOPTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_processLoop'], "ns"))
                    manager.pages["PROGRAM_P_BINANCEAPI"]["PROCESS_LASTPROCTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_process'], "ns"))
                    manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_READTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readTime'], "ns"))
                    manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_READSIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readSize'], "Bytes"))
                    manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_READRATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readRate'] / manager.pageVariables["PROGRAM_P_BINANCEAPI"]['AVG_STANDARD'], "Bytes/s"))
                    manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_WRITETIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeTime'], "ns"))
                    manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_WRITESIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeSize'], "Bytes"))
                    manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_WRITERATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeRate'] / manager.pageVariables["PROGRAM_P_BINANCEAPI"]['AVG_STANDARD'], "Bytes/s"))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateProcessData0_FARHanlder0
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA0"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateProcessData0, interval = 100)
        def timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateProcessData1(manager):
            tID = manager.assistantIPC.sendFAR("BINANCEAPI", "GET_PTIMERS_AVG", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateProcessData1_FARHanlder0(manager, result):
                processTimers = result
                manager.pages["PROGRAM_P_BINANCEAPI"]["PROCESS_AVGLOOPTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_processLoop_avg'], "ns"))
                manager.pages["PROGRAM_P_BINANCEAPI"]["PROCESS_AVGPROCTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_process_avg'], "ns"))
                manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_AVGREADTIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readTime_avg'], "ns"))
                manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_AVGREADSIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_AVGREADRATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readRate_avg'] / manager.pageVariables["PROGRAM_P_BINANCEAPI"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_AVGWRITETIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeTime_avg'], "ns"))
                manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_AVGWRITESIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_AVGWRITERATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeRate_avg'] / manager.pageVariables["PROGRAM_P_BINANCEAPI"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_BINANCEAPI"]["PPC_SAMPLEN_DATA"].updateText("{:d} samples".format(processTimers['nRecords']))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateProcessData1_FARHanlder0
            tID = manager.assistantIPC.sendFAR("BINANCEAPI", "GET_IPC_TIDAVAILABILITY", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateProcessData1_FARHanlder1(manager, result):
                manager.pages["PROGRAM_P_BINANCEAPI"]["IPCA_AVAILABLETID_DATA"].updateText("{:d} / {:d}".format(result[0], result[1]))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateProcessData1_FARHanlder1
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA1"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateProcessData1, interval = 250)
        def timerFunction_page_P_BINANCEAPI_UpdateProcessLog(manager):
            if (manager.pages["PROGRAM_P_BINANCEAPI"]["P_LOG_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("BINANCEAPI", "GET_PLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_P_BINANCEAPI_UpdateProcessLog_FARHandler0(manager, result):
                    matrix = [[]]; processLog = result; maximumDisplayStringLength = 100
                    for i in range (len(processLog)):
                        dataContent = processLog[i]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[0].append(("[{:d}] {:s}".format(i, dataContent), "w", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_BINANCEAPI"]["P_LOG"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_BINANCEAPI"]["P_LOG"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_BINANCEAPI"]["P_LOG"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_BINANCEAPI"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_BINANCEAPI"]["P_LOG"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_P_BINANCEAPI_UpdateProcessLog_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPROCESSLOG"] = self.__timerFunction(function = timerFunction_page_P_BINANCEAPI_UpdateProcessLog, interval = 1000)
        def timerFunction_page_PROGRAM_P_BINANCEAPI_UpdatePRDData(manager):
            selectedOption = manager.pages["PROGRAM_P_BINANCEAPI"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_BINANCEAPI"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("BINANCEAPI", "GET_PRD", (selectedOption, 70), nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_BINANCEAPI_UpdatePRDData_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]; maximumDisplayStringLength = 70
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_BINANCEAPI"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_BINANCEAPI_UpdatePRDData_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPRDDATA"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_BINANCEAPI_UpdatePRDData, interval = 1000)
        def timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateIPCLOG(manager):
            if (manager.pages["PROGRAM_P_BINANCEAPI"]["IPCLOG_MATRIX_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("BINANCEAPI", "GET_IPCLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateIPCLOG_FARHandler0(manager, result):
                    ipcLog = result; matrix = [[],[]]; maximumDisplayStringLength = 100
                    for i in range (len(ipcLog)): 
                        matrix[0].append(("[{:d}] {:s}".format(i, self.__valueFormatter(ipcLog[i][0], "ns")), "center", "white", ("Arial", 10, "")))
                        dataContent = ipcLog[i][1]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[1].append((dataContent, "center", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_BINANCEAPI"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_BINANCEAPI"]["IPCLOG_MATRIX"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_BINANCEAPI"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_BINANCEAPI"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_BINANCEAPI"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateIPCLOG_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEIPCLOG"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_BINANCEAPI_UpdateIPCLOG, interval = 1000)
        #PAGE "PROGRAM_P_BINANCEAPI" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_P_DATAANALYSIS" --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_P_DATAANALYSIS"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_P_DATAANALYSIS = dict()
        page_PROGRAM_P_DATAANALYSIS.update(main_navigationGUIOs)
        page_PROGRAM_P_DATAANALYSIS.update(program_navigationGUIOs)

        def page_PROGRAM_P_DATAANALYSIS_load(manager):
            manager.pages["PROGRAM_P_DATAANALYSIS"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_P_DATAANALYSIS"]["LOCALNAVIGATION_P_DATAANALYSIS"].deactivate()
        def page_PROGRAM_P_DATAANALYSIS_close(manager):
            manager.pages["PROGRAM_P_DATAANALYSIS"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_P_DATAANALYSIS"]["LOCALNAVIGATION_P_DATAANALYSIS"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_P_DATAANALYSIS_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_P_DATAANALYSIS_close
        
        page_PROGRAM_P_DATAANALYSIS["PROCESSCOUNTERS_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           10, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "PROCESS PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAANALYSIS["PROCESS_LASTLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["PROCESS_LASTLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["PROCESS_LASTPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["PROCESS_LASTPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["PROCESS_AVGLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["PROCESS_AVGLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["PROCESS_AVGPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["PROCESS_AVGPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["PPC_SAMPLEN_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,               10, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Number of Records", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["PPC_SAMPLEN_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,                    215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["AVG_STANDARD_SELECTIONBOXTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 340, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Count Standard", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["AVG_STANDARD_SELECTIONBOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,            545, 220, 120, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("DATAANALYSIS", "PTIMERS_AVGSTANDARD", nRetry = "INF")
        def __guioF_PROGRAM_P_DATAANALYSIS_INITIALIZATIONDATAREQUEST0(manager, result): 
            manager.pages["PROGRAM_P_DATAANALYSIS"]["AVG_STANDARD_SELECTIONBOX"].editSelected(str(result))
            manager.pageVariables["PROGRAM_P_DATAANALYSIS"]['AVG_STANDARD'] = result
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_DATAANALYSIS_INITIALIZATIONDATAREQUEST0
        page_PROGRAM_P_DATAANALYSIS["AVG_STANDARD_SELECTIONBOX"].updateList(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "20", "30", "40", "50", "60"])
        page_PROGRAM_P_DATAANALYSIS["P_LOG_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 265,  655,   40, style = "styleA_themeA", layer = 1, text = "PROCESS MESSAGE LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAANALYSIS["P_LOG"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,          10, 310,  620, 1085, "styleA_themeA", layer = 1, nDisplayedColumns = 1, nDisplayedRows = 30)
        page_PROGRAM_P_DATAANALYSIS["P_LOG_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,           635, 310, 1085,   30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_DATAANALYSIS["P_LOG"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_DATAANALYSIS["P_LOG_COMMENT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,     10, 1400, 620, 30, boxStyle = "styleA_themeC", layer = 1, text = "PROCESS [DATANALYSIS] LOG", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["P_LOG_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,            635, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)
        page_PROGRAM_P_DATAANALYSIS["IPCAPERF_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           680, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAANALYSIS["IPCA_READTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_READTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_READSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_READSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_READRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_READRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGREADTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGREADTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGREADSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGREADSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGREADRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGREADRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_WRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_WRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_WRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_WRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_WRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_WRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGWRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGWRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGWRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGWRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGWRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVGWRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["PRD_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,            680, 375, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC PRE-REGISTERED DATA", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAANALYSIS["PRD_MANAGERSELECTION_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 420, 325, 30, style = "styleA_themeA", layer = 1, text = "PRD From", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAANALYSIS["PRD_MANAGERSELECTION_BOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,         1010, 420, 325, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("DATAANALYSIS", "ATMMANAGERS", nRetry = "INF")
        def __guioF_PROGRAM_P_DATAANALYSIS_INITIALIZATIONDATAREQUEST1(manager, result):
            manager.pages["PROGRAM_P_DATAANALYSIS"]["PRD_MANAGERSELECTION_BOX"].updateList(result)
            manager.pages["PROGRAM_P_DATAANALYSIS"]["PRD_MANAGERSELECTION_BOX"].editSelected(result[0])
            manager.pageVariables["PROGRAM_P_DATAANALYSIS"]['PRD_ManagerSelection'] = result[0]
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_DATAANALYSIS_INITIALIZATIONDATAREQUEST1
        page_PROGRAM_P_DATAANALYSIS["PRD_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 455, 620, 350, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 8, columnTitles = [("[INDEX] DATA NAME", "center", "white", ("Arial", 12, "bold")), ("DATA CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (4, 6))
        page_PROGRAM_P_DATAANALYSIS["PRD_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 455, 350,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_DATAANALYSIS["PRD_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_DATAANALYSIS["IPCLOG_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 820, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAANALYSIS["IPCLOG_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 865, 620, 530, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 10, columnTitles = [("[INDEX] Record Time", "center", "white", ("Arial", 12, "bold")), ("CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (3, 7))
        page_PROGRAM_P_DATAANALYSIS["IPCLOG_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 865, 530,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_DATAANALYSIS["IPCLOG_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_DATAANALYSIS["IPCA_COMMENT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 680, 1400, 325, 30, style = "styleA_themeA", layer = 1, text = "< IPCLOGs are not recorded to avoid recursion >", textFill = (255, 255, 255, 200), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVAILABLETID_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 1400, 200, 30, style = "styleA_themeA", layer = 1, text = "Available Transmission IDs", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAANALYSIS["IPCA_AVAILABLETID_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 1400,  85, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAANALYSIS["IPCLOG_MATRIX_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,                1305, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)

        self.pages[thisPage] = page_PROGRAM_P_DATAANALYSIS

        #Object Functions
        def __guioF_PROGRAM_P_DATAANALYSIS_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED(manager): 
            selectedOption = manager.pages["PROGRAM_P_DATAANALYSIS"]["AVG_STANDARD_SELECTIONBOX"].getSelected() 
            tID = manager.assistantIPC.sendFAR("DATAANALYSIS", "EDIT_PTIMERAVGSTANDARD", int(selectedOption))
            def __guioF_PROGRAM_P_DATAANALYSIS_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                manager.pages["PROGRAM_P_DATAANALYSIS"]["AVG_STANDARD_SELECTIONBOX"].editSelected(result)
                manager.pageVariables["PROGRAM_P_DATAANALYSIS"]['AVG_STANDARD'] = result
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_DATAANALYSIS_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-AVG_STANDARD_SELECTIONBOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_DATAANALYSIS_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED
        def __guioF_PROGRAM_P_DATAANALYSIS_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED(manager):
            selectedOption = manager.pages["PROGRAM_P_DATAANALYSIS"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_DATAANALYSIS"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("DATAANALYSIS", "GET_PRD", (selectedOption, 70))
            def __guioF_PROGRAM_P_DATAANALYSIS_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_DATAANALYSIS"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_DATAANALYSIS_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-PRD_MANAGERSELECTION_BOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_DATAANALYSIS_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED 
        def __guioF_PROGRAM_P_DATAANALYSIS_P_LOG_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_DATAANALYSIS"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_DATAANALYSIS"]["P_LOG"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-P_LOG-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_DATAANALYSIS_P_LOG_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_DATAANALYSIS_P_LOG_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_DATAANALYSIS"]["P_LOG"].changeViewRangeV(manager.pages["PROGRAM_P_DATAANALYSIS"]["P_LOG_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-P_LOG_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_DATAANALYSIS_P_LOG_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_DATAANALYSIS_IPCLOG_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_DATAANALYSIS_IPCLOG_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_DATAANALYSIS_IPCLOG_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCLOG_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCLOG_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_DATAANALYSIS_IPCLOG_MATRIX_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_DATAANALYSIS_PRD_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_DATAANALYSIS"]["PRD_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_DATAANALYSIS"]["PRD_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-PRD_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_DATAANALYSIS_PRD_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_DATAANALYSIS_PRD_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_DATAANALYSIS"]["PRD_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_DATAANALYSIS"]["PRD_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-PRD_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_DATAANALYSIS_PRD_MATRIX_SB_V_VALUEUPDATED
        #Page Timer Functions
        def timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateProcessData0(manager):
            tID = manager.assistantIPC.sendFAR("DATAANALYSIS", "GET_PTIMERS_LAST", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateProcessData0_FARHanlder0(manager, result):
                lastRecord = result
                if (lastRecord != None):
                    manager.pages["PROGRAM_P_DATAANALYSIS"]["PROCESS_LASTLOOPTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_processLoop'], "ns"))
                    manager.pages["PROGRAM_P_DATAANALYSIS"]["PROCESS_LASTPROCTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_process'], "ns"))
                    manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_READTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readTime'], "ns"))
                    manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_READSIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readSize'], "Bytes"))
                    manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_READRATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readRate'] / manager.pageVariables["PROGRAM_P_DATAANALYSIS"]['AVG_STANDARD'], "Bytes/s"))
                    manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_WRITETIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeTime'], "ns"))
                    manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_WRITESIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeSize'], "Bytes"))
                    manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_WRITERATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeRate'] / manager.pageVariables["PROGRAM_P_DATAANALYSIS"]['AVG_STANDARD'], "Bytes/s"))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateProcessData0_FARHanlder0
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA0"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateProcessData0, interval = 100)
        def timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateProcessData1(manager):
            tID = manager.assistantIPC.sendFAR("DATAANALYSIS", "GET_PTIMERS_AVG", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateProcessData1_FARHanlder0(manager, result):
                processTimers = result
                manager.pages["PROGRAM_P_DATAANALYSIS"]["PROCESS_AVGLOOPTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_processLoop_avg'], "ns"))
                manager.pages["PROGRAM_P_DATAANALYSIS"]["PROCESS_AVGPROCTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_process_avg'], "ns"))
                manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_AVGREADTIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readTime_avg'], "ns"))
                manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_AVGREADSIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_AVGREADRATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readRate_avg'] / manager.pageVariables["PROGRAM_P_DATAANALYSIS"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_AVGWRITETIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeTime_avg'], "ns"))
                manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_AVGWRITESIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_AVGWRITERATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeRate_avg'] / manager.pageVariables["PROGRAM_P_DATAANALYSIS"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_DATAANALYSIS"]["PPC_SAMPLEN_DATA"].updateText("{:d} samples".format(processTimers['nRecords']))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateProcessData1_FARHanlder0
            tID = manager.assistantIPC.sendFAR("DATAANALYSIS", "GET_IPC_TIDAVAILABILITY", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateProcessData1_FARHanlder1(manager, result):
                manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCA_AVAILABLETID_DATA"].updateText("{:d} / {:d}".format(result[0], result[1]))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateProcessData1_FARHanlder1
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA1"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateProcessData1, interval = 250)
        def timerFunction_page_P_DATAANALYSIS_UpdateProcessLog(manager):
            if (manager.pages["PROGRAM_P_DATAANALYSIS"]["P_LOG_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("DATAANALYSIS", "GET_PLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_P_DATAANALYSIS_UpdateProcessLog_FARHandler0(manager, result):
                    matrix = [[]]; processLog = result; maximumDisplayStringLength = 100
                    for i in range (len(processLog)):
                        dataContent = processLog[i]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[0].append(("[{:d}] {:s}".format(i, dataContent), "w", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_DATAANALYSIS"]["P_LOG"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_DATAANALYSIS"]["P_LOG"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_DATAANALYSIS"]["P_LOG"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_DATAANALYSIS"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_DATAANALYSIS"]["P_LOG"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_P_DATAANALYSIS_UpdateProcessLog_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPROCESSLOG"] = self.__timerFunction(function = timerFunction_page_P_DATAANALYSIS_UpdateProcessLog, interval = 1000)
        def timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdatePRDData(manager):
            selectedOption = manager.pages["PROGRAM_P_DATAANALYSIS"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_DATAANALYSIS"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("DATAANALYSIS", "GET_PRD", (selectedOption, 70), nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdatePRDData_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_DATAANALYSIS"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdatePRDData_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPRDDATA"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdatePRDData, interval = 1000)
        def timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateIPCLOG(manager):
            if (manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCLOG_MATRIX_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("DATAANALYSIS", "GET_IPCLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateIPCLOG_FARHandler0(manager, result):
                    ipcLog = result; matrix = [[],[]]; maximumDisplayStringLength = 100
                    for i in range (len(ipcLog)): 
                        matrix[0].append(("[{:d}] {:s}".format(i, self.__valueFormatter(ipcLog[i][0], "ns")), "center", "white", ("Arial", 10, "")))
                        dataContent = ipcLog[i][1]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[1].append((dataContent, "center", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCLOG_MATRIX"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_DATAANALYSIS"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateIPCLOG_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEIPCLOG"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_DATAANALYSIS_UpdateIPCLOG, interval = 1000)
        
        #PAGE "PROGRAM_P_DATAANALYSIS" END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_P_DATAMANAGEMENT" ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_P_DATAMANAGEMENT"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_P_DATAMANAGEMENT = dict()
        page_PROGRAM_P_DATAMANAGEMENT.update(main_navigationGUIOs)
        page_PROGRAM_P_DATAMANAGEMENT.update(program_navigationGUIOs)

        def page_PROGRAM_P_DATAMANAGEMENT_load(manager):
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["LOCALNAVIGATION_P_DATAMANAGEMENT"].deactivate()
        def page_PROGRAM_P_DATAMANAGEMENT_close(manager):
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["LOCALNAVIGATION_P_DATAMANAGEMENT"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_P_DATAMANAGEMENT_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_P_DATAMANAGEMENT_close
        
        page_PROGRAM_P_DATAMANAGEMENT["PROCESSCOUNTERS_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           10, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "PROCESS PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAMANAGEMENT["PROCESS_LASTLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["PROCESS_LASTLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["PROCESS_LASTPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["PROCESS_LASTPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["PROCESS_AVGLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["PROCESS_AVGLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["PROCESS_AVGPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["PROCESS_AVGPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["PPC_SAMPLEN_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,               10, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Number of Records", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["PPC_SAMPLEN_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,                    215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["AVG_STANDARD_SELECTIONBOXTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 340, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Count Standard", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["AVG_STANDARD_SELECTIONBOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,            545, 220, 120, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("DATAMANAGEMENT", "PTIMERS_AVGSTANDARD", nRetry = "INF")
        def __guioF_PROGRAM_P_DATAMANAGEMENT_INITIALIZATIONDATAREQUEST0(manager, result): 
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["AVG_STANDARD_SELECTIONBOX"].editSelected(str(result))
            manager.pageVariables["PROGRAM_P_DATAMANAGEMENT"]['AVG_STANDARD'] = result
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_DATAMANAGEMENT_INITIALIZATIONDATAREQUEST0
        page_PROGRAM_P_DATAMANAGEMENT["AVG_STANDARD_SELECTIONBOX"].updateList(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "20", "30", "40", "50", "60"])
        page_PROGRAM_P_DATAMANAGEMENT["P_LOG_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 265,  655,   40, style = "styleA_themeA", layer = 1, text = "PROCESS MESSAGE LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAMANAGEMENT["P_LOG"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,          10, 310,  620, 1085, "styleA_themeA", layer = 1, nDisplayedColumns = 1, nDisplayedRows = 30)
        page_PROGRAM_P_DATAMANAGEMENT["P_LOG_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,           635, 310, 1085,   30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_DATAMANAGEMENT["P_LOG"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_DATAMANAGEMENT["P_LOG_COMMENT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,     10, 1400, 620, 30, boxStyle = "styleA_themeC", layer = 1, text = "PROCESS [DATAMANAGEMENT] LOG", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["P_LOG_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,            635, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)
        page_PROGRAM_P_DATAMANAGEMENT["IPCAPERF_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           680, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_READTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_READTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_READSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_READSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_READRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_READRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGREADTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGREADTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGREADSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGREADSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGREADRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGREADRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_WRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_WRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_WRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_WRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_WRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_WRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGWRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGWRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGWRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGWRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGWRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVGWRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["PRD_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,            680, 375, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC PRE-REGISTERED DATA", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAMANAGEMENT["PRD_MANAGERSELECTION_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 420, 325, 30, style = "styleA_themeA", layer = 1, text = "PRD From", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAMANAGEMENT["PRD_MANAGERSELECTION_BOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,         1010, 420, 325, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("DATAMANAGEMENT", "ATMMANAGERS", nRetry = "INF")
        def __guioF_PROGRAM_P_DATAMANAGEMENT_INITIALIZATIONDATAREQUEST1(manager, result):
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PRD_MANAGERSELECTION_BOX"].updateList(result)
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PRD_MANAGERSELECTION_BOX"].editSelected(result[0])
            manager.pageVariables["PROGRAM_P_DATAMANAGEMENT"]['PRD_ManagerSelection'] = result[0]
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_DATAMANAGEMENT_INITIALIZATIONDATAREQUEST1
        page_PROGRAM_P_DATAMANAGEMENT["PRD_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 455, 620, 350, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 8, columnTitles = [("[INDEX] DATA NAME", "center", "white", ("Arial", 12, "bold")), ("DATA CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (4, 6))
        page_PROGRAM_P_DATAMANAGEMENT["PRD_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 455, 350,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_DATAMANAGEMENT["PRD_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_DATAMANAGEMENT["IPCLOG_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 820, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_DATAMANAGEMENT["IPCLOG_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 865, 620, 530, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 10, columnTitles = [("[INDEX] Record Time", "center", "white", ("Arial", 12, "bold")), ("CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (3, 7))
        page_PROGRAM_P_DATAMANAGEMENT["IPCLOG_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 865, 530,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_DATAMANAGEMENT["IPCLOG_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_COMMENT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 680, 1400, 325, 30, style = "styleA_themeA", layer = 1, text = "< IPCLOGs are not recorded to avoid recursion >", textFill = (255, 255, 255, 200), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVAILABLETID_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 1400, 200, 30, style = "styleA_themeA", layer = 1, text = "Available Transmission IDs", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_DATAMANAGEMENT["IPCA_AVAILABLETID_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 1400,  85, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_DATAMANAGEMENT["IPCLOG_MATRIX_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,                1305, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)

        self.pages[thisPage] = page_PROGRAM_P_DATAMANAGEMENT

        #Object Functions
        def __guioF_PROGRAM_P_DATAMANAGEMENT_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED(manager): 
            selectedOption = manager.pages["PROGRAM_P_DATAMANAGEMENT"]["AVG_STANDARD_SELECTIONBOX"].getSelected() 
            tID = manager.assistantIPC.sendFAR("DATAMANAGEMENT", "EDIT_PTIMERAVGSTANDARD", int(selectedOption))
            def __guioF_PROGRAM_P_DATAMANAGEMENT_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["AVG_STANDARD_SELECTIONBOX"].editSelected(result)
                manager.pageVariables["PROGRAM_P_DATAMANAGEMENT"]['AVG_STANDARD'] = result
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_DATAMANAGEMENT_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-AVG_STANDARD_SELECTIONBOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_DATAMANAGEMENT_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED
        def __guioF_PROGRAM_P_DATAMANAGEMENT_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED(manager):
            selectedOption = manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_DATAMANAGEMENT"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("DATAMANAGEMENT", "GET_PRD", (selectedOption, 70))
            def __guioF_PROGRAM_P_DATAMANAGEMENT_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_DATAMANAGEMENT_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-PRD_MANAGERSELECTION_BOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_DATAMANAGEMENT_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED 
        def __guioF_PROGRAM_P_DATAMANAGEMENT_P_LOG_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_DATAMANAGEMENT"]["P_LOG"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-P_LOG-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_DATAMANAGEMENT_P_LOG_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_DATAMANAGEMENT_P_LOG_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["P_LOG"].changeViewRangeV(manager.pages["PROGRAM_P_DATAMANAGEMENT"]["P_LOG_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-P_LOG_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_DATAMANAGEMENT_P_LOG_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_DATAMANAGEMENT_IPCLOG_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_DATAMANAGEMENT_IPCLOG_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_DATAMANAGEMENT_IPCLOG_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCLOG_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCLOG_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_DATAMANAGEMENT_IPCLOG_MATRIX_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_DATAMANAGEMENT_PRD_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PRD_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PRD_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-PRD_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_DATAMANAGEMENT_PRD_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_DATAMANAGEMENT_PRD_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PRD_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PRD_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-PRD_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_DATAMANAGEMENT_PRD_MATRIX_SB_V_VALUEUPDATED
        #Page Timer Functions
        def timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateProcessData0(manager):
            tID = manager.assistantIPC.sendFAR("DATAMANAGEMENT", "GET_PTIMERS_LAST", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateProcessData0_FARHanlder0(manager, result):
                lastRecord = result
                if (lastRecord != None):
                    manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PROCESS_LASTLOOPTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_processLoop'], "ns"))
                    manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PROCESS_LASTPROCTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_process'], "ns"))
                    manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_READTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readTime'], "ns"))
                    manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_READSIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readSize'], "Bytes"))
                    manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_READRATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readRate'] / manager.pageVariables["PROGRAM_P_DATAMANAGEMENT"]['AVG_STANDARD'], "Bytes/s"))
                    manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_WRITETIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeTime'], "ns"))
                    manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_WRITESIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeSize'], "Bytes"))
                    manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_WRITERATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeRate'] / manager.pageVariables["PROGRAM_P_DATAMANAGEMENT"]['AVG_STANDARD'], "Bytes/s"))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateProcessData0_FARHanlder0
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA0"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateProcessData0, interval = 100)
        def timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateProcessData1(manager):
            tID = manager.assistantIPC.sendFAR("DATAMANAGEMENT", "GET_PTIMERS_AVG", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateProcessData1_FARHanlder0(manager, result):
                processTimers = result
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PROCESS_AVGLOOPTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_processLoop_avg'], "ns"))
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PROCESS_AVGPROCTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_process_avg'], "ns"))
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_AVGREADTIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readTime_avg'], "ns"))
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_AVGREADSIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_AVGREADRATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readRate_avg'] / manager.pageVariables["PROGRAM_P_DATAMANAGEMENT"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_AVGWRITETIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeTime_avg'], "ns"))
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_AVGWRITESIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_AVGWRITERATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeRate_avg'] / manager.pageVariables["PROGRAM_P_DATAMANAGEMENT"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PPC_SAMPLEN_DATA"].updateText("{:d} samples".format(processTimers['nRecords']))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateProcessData1_FARHanlder0
            tID = manager.assistantIPC.sendFAR("DATAMANAGEMENT", "GET_IPC_TIDAVAILABILITY", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateProcessData1_FARHanlder1(manager, result):
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCA_AVAILABLETID_DATA"].updateText("{:d} / {:d}".format(result[0], result[1]))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateProcessData1_FARHanlder1
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA1"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateProcessData1, interval = 250)
        def timerFunction_page_P_DATAMANAGEMENT_UpdateProcessLog(manager):
            if (manager.pages["PROGRAM_P_DATAMANAGEMENT"]["P_LOG_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("DATAMANAGEMENT", "GET_PLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_P_DATAMANAGEMENT_UpdateProcessLog_FARHandler0(manager, result):
                    matrix = [[]]; processLog = result; maximumDisplayStringLength = 100
                    for i in range (len(processLog)):
                        dataContent = processLog[i]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[0].append(("[{:d}] {:s}".format(i, dataContent), "w", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_DATAMANAGEMENT"]["P_LOG"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_DATAMANAGEMENT"]["P_LOG"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_DATAMANAGEMENT"]["P_LOG"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_DATAMANAGEMENT"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_DATAMANAGEMENT"]["P_LOG"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_P_DATAMANAGEMENT_UpdateProcessLog_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPROCESSLOG"] = self.__timerFunction(function = timerFunction_page_P_DATAMANAGEMENT_UpdateProcessLog, interval = 1000)
        def timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdatePRDData(manager):
            selectedOption = manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_DATAMANAGEMENT"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("DATAMANAGEMENT", "GET_PRD", (selectedOption, 70), nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdatePRDData_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_DATAMANAGEMENT"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdatePRDData_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPRDDATA"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdatePRDData, interval = 1000)
        def timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateIPCLOG(manager):
            if (manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCLOG_MATRIX_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("DATAMANAGEMENT", "GET_IPCLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateIPCLOG_FARHandler0(manager, result):
                    ipcLog = result; matrix = [[],[]]; maximumDisplayStringLength = 100
                    for i in range (len(ipcLog)): 
                        matrix[0].append(("[{:d}] {:s}".format(i, self.__valueFormatter(ipcLog[i][0], "ns")), "center", "white", ("Arial", 10, "")))
                        dataContent = ipcLog[i][1]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[1].append((dataContent, "center", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCLOG_MATRIX"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_DATAMANAGEMENT"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateIPCLOG_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEIPCLOG"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_DATAMANAGEMENT_UpdateIPCLOG, interval = 1000)
        
        #PAGE "PROGRAM_P_DATAMANAGEMENT" END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_P_GUI" -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_P_GUI"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_P_GUI = dict()
        page_PROGRAM_P_GUI.update(main_navigationGUIOs)
        page_PROGRAM_P_GUI.update(program_navigationGUIOs)

        def page_PROGRAM_P_GUI_load(manager):
            manager.pages["PROGRAM_P_GUI"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_P_GUI"]["LOCALNAVIGATION_P_GUI"].deactivate()
        def page_PROGRAM_P_GUI_close(manager):
            manager.pages["PROGRAM_P_GUI"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_P_GUI"]["LOCALNAVIGATION_P_GUI"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_P_GUI_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_P_GUI_close
        
        page_PROGRAM_P_GUI["PROCESSCOUNTERS_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           10, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "PROCESS PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_GUI["PROCESS_LASTLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["PROCESS_LASTLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["PROCESS_LASTPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["PROCESS_LASTPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["PROCESS_LASTTKPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,    10, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Tk Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["PROCESS_LASTTKPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,         215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["PROCESS_AVGLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["PROCESS_AVGLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["PROCESS_AVGPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["PROCESS_AVGPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["PROCESS_AVGTKPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,    340, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Tk Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["PROCESS_AVGTKPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,          545, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["PPC_SAMPLEN_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,               10, 255, 200, 30, style = "styleA_themeA", layer = 1, text = "Number of Records", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["PPC_SAMPLEN_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,                    215, 255, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["AVG_STANDARD_SELECTIONBOXTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 340, 255, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Count Standard", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["AVG_STANDARD_SELECTIONBOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,            545, 255, 120, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        page_PROGRAM_P_GUI["AVG_STANDARD_SELECTIONBOX"].updateList(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "20", "30", "40", "50", "60"]); page_PROGRAM_P_GUI["AVG_STANDARD_SELECTIONBOX"].editSelected(str(self.processTimerAvgStandard));
        page_PROGRAM_P_GUI["P_LOG_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 300,  655,   40, style = "styleA_themeA", layer = 1, text = "PROCESS MESSAGE LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_GUI["P_LOG"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,          10, 345,  620, 1050, "styleA_themeA", layer = 1, nDisplayedColumns = 1, nDisplayedRows = 30)
        page_PROGRAM_P_GUI["P_LOG_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,           635, 345, 1050,   30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_GUI["P_LOG"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_GUI["P_LOG_COMMENT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,     10, 1400, 620, 30, boxStyle = "styleA_themeC", layer = 1, text = "PROCESS [GUI] LOG", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["P_LOG_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,            635, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)
        page_PROGRAM_P_GUI["IPCAPERF_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           680, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_GUI["IPCA_READTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_READTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_READSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_READSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_READRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_READRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_AVGREADTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_AVGREADTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_AVGREADSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_AVGREADSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_AVGREADRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_AVGREADRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_WRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_WRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_WRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_WRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_WRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_WRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_AVGWRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_AVGWRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_AVGWRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_AVGWRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCA_AVGWRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_AVGWRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["PRD_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,            680, 375, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC PRE-REGISTERED DATA", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_GUI["PRD_MANAGERSELECTION_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 420, 325, 30, style = "styleA_themeA", layer = 1, text = "PRD From", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_GUI["PRD_MANAGERSELECTION_BOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,         1010, 420, 325, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        page_PROGRAM_P_GUI["PRD_MANAGERSELECTION_BOX"].updateList(self.atm_Managers); page_PROGRAM_P_GUI["PRD_MANAGERSELECTION_BOX"].editSelected(self.atm_Managers[0]);
        self.pageVariables["PROGRAM_P_GUI"]['PRD_ManagerSelection'] = self.atm_Managers[0]
        page_PROGRAM_P_GUI["PRD_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 455, 620, 350, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 8, columnTitles = [("[INDEX] DATA NAME", "center", "white", ("Arial", 12, "bold")), ("DATA CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (4, 6))
        page_PROGRAM_P_GUI["PRD_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 455, 350,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_GUI["PRD_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_GUI["IPCLOG_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 820, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_GUI["IPCLOG_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 865, 620, 530, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 10, columnTitles = [("[INDEX] Record Time", "center", "white", ("Arial", 12, "bold")), ("CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (3, 7))
        page_PROGRAM_P_GUI["IPCLOG_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 865, 530,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_GUI["IPCLOG_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_GUI["IPCA_COMMENT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 680, 1400, 325, 30, style = "styleA_themeA", layer = 1, text = "< IPCLOGs are not recorded to avoid recursion >", textFill = (255, 255, 255, 200), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_AVAILABLETID_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 1400, 200, 30, style = "styleA_themeA", layer = 1, text = "Available Transmission IDs", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_GUI["IPCA_AVAILABLETID_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 1400,  85, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_GUI["IPCLOG_MATRIX_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,                1305, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)
        
        self.pages[thisPage] = page_PROGRAM_P_GUI

        #Object Functions
        def __guioF_PROGRAM_P_GUI_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED(manager):
            selectedOption = manager.pages["PROGRAM_P_GUI"]["AVG_STANDARD_SELECTIONBOX"].getSelected()
            manager.processTimerAvgStandard = int(selectedOption)
        self.objectFunctions[thisPage+"-AVG_STANDARD_SELECTIONBOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_GUI_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED
        def __guioF_PROGRAM_P_GUI_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED(manager):
            selectedOption = manager.pages["PROGRAM_P_GUI"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_GUI"]['PRD_ManagerSelection'] = selectedOption
            prd = manager.assistantIPC.getPRD(manager.pageVariables["PROGRAM_P_GUI"]['PRD_ManagerSelection']); prdKeys = list(prd.keys()); matrix = [[],[]]; maximumDisplayStringLength = 70
            for i in range (len(prdKeys)): 
                matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, ""))); 
                dataContent = str(prd[prdKeys[i]])
                if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                matrix[1].append((dataContent, "center", "white", ("Arial", 10, "")))
            manager.pages["PROGRAM_P_GUI"]["PRD_MATRIX"].updateMatrix(matrix)
        self.objectFunctions[thisPage+"-PRD_MANAGERSELECTION_BOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_GUI_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED 
        def __guioF_PROGRAM_P_GUI_P_LOG_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_GUI"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_GUI"]["P_LOG"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-P_LOG-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_GUI_P_LOG_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_GUI_P_LOG_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_GUI"]["P_LOG"].changeViewRangeV(manager.pages["PROGRAM_P_GUI"]["P_LOG_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-P_LOG_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_GUI_P_LOG_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_GUI_IPCLOG_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_GUI"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_GUI"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_GUI_IPCLOG_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_GUI_IPCLOG_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_GUI"]["IPCLOG_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_GUI"]["IPCLOG_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_GUI_IPCLOG_MATRIX_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_GUI_PRD_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_GUI"]["PRD_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_GUI"]["PRD_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-PRD_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_GUI_PRD_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_GUI_PRD_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_GUI"]["PRD_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_GUI"]["PRD_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-PRD_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_GUI_PRD_MATRIX_SB_V_VALUEUPDATED

        #Page Timer Functions
        def timerFunction_page_PROGRAM_P_GUI_UpdateProcessData0(manager):
            if (manager.processTimers['updated'] == True):
                manager.pages["PROGRAM_P_GUI"]["PROCESS_LASTLOOPTIME_DATA"].updateText(manager.__valueFormatter(manager.processTimers['records'][-1]['t_processLoop'], "ns"))
                manager.pages["PROGRAM_P_GUI"]["PROCESS_LASTPROCTIME_DATA"].updateText(manager.__valueFormatter(manager.processTimers['records'][-1]['t_process'], "ns"))
                manager.pages["PROGRAM_P_GUI"]["PROCESS_LASTTKPROCTIME_DATA"].updateText(manager.__valueFormatter(manager.processTimers['records'][-1]['t_processTk'], "ns"))
                manager.pages["PROGRAM_P_GUI"]["IPCA_READTIME_DATA"].updateText(manager.__valueFormatter(manager.processTimers['records'][-1]['ipcb_readTime'], "ns"))
                manager.pages["PROGRAM_P_GUI"]["IPCA_READSIZE_DATA"].updateText(manager.__valueFormatter(manager.processTimers['records'][-1]['ipcb_readSize'], "Bytes"))
                manager.pages["PROGRAM_P_GUI"]["IPCA_READRATE_DATA"].updateText(manager.__valueFormatter(manager.processTimers['records'][-1]['ipcb_readRate'] / manager.processTimerAvgStandard, "Bytes/s"))
                manager.pages["PROGRAM_P_GUI"]["IPCA_WRITETIME_DATA"].updateText(manager.__valueFormatter(manager.processTimers['records'][-1]['ipcb_writeTime'], "ns"))
                manager.pages["PROGRAM_P_GUI"]["IPCA_WRITESIZE_DATA"].updateText(manager.__valueFormatter(manager.processTimers['records'][-1]['ipcb_writeSize'], "Bytes"))
                manager.pages["PROGRAM_P_GUI"]["IPCA_WRITERATE_DATA"].updateText(manager.__valueFormatter(manager.processTimers['records'][-1]['ipcb_writeRate'] / manager.processTimerAvgStandard, "Bytes/s"))
                manager.processTimers['updated'] = False
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA0"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_GUI_UpdateProcessData0, interval = 100)
        def timerFunction_page_PROGRAM_P_GUI_UpdateProcessData1(manager):
            manager.pages["PROGRAM_P_GUI"]["PROCESS_AVGLOOPTIME_DATA"].updateText(manager.__valueFormatter(manager.processTimers['t_processLoop_avg'], "ns"))
            manager.pages["PROGRAM_P_GUI"]["PROCESS_AVGPROCTIME_DATA"].updateText(manager.__valueFormatter(manager.processTimers['t_process_avg'], "ns"))
            manager.pages["PROGRAM_P_GUI"]["PROCESS_AVGTKPROCTIME_DATA"].updateText(manager.__valueFormatter(manager.processTimers['t_processTk_avg'], "ns"))
            manager.pages["PROGRAM_P_GUI"]["IPCA_AVGREADTIME_DATA"].updateText(manager.__valueFormatter(manager.processTimers['ipcb_readTime_avg'], "ns"))
            manager.pages["PROGRAM_P_GUI"]["IPCA_AVGREADSIZE_DATA"].updateText(manager.__valueFormatter(manager.processTimers['ipcb_readSize_avg'], "Bytes"))
            manager.pages["PROGRAM_P_GUI"]["IPCA_AVGREADRATE_DATA"].updateText(manager.__valueFormatter(manager.processTimers['ipcb_readRate_avg'] / manager.processTimerAvgStandard, "Bytes/s"))
            manager.pages["PROGRAM_P_GUI"]["IPCA_AVGWRITETIME_DATA"].updateText(manager.__valueFormatter(manager.processTimers['ipcb_writeTime_avg'], "ns"))
            manager.pages["PROGRAM_P_GUI"]["IPCA_AVGWRITESIZE_DATA"].updateText(manager.__valueFormatter(manager.processTimers['ipcb_writeSize_avg'], "Bytes"))
            manager.pages["PROGRAM_P_GUI"]["IPCA_AVGWRITERATE_DATA"].updateText(manager.__valueFormatter(manager.processTimers['ipcb_writeRate_avg'] / manager.processTimerAvgStandard, "Bytes/s"))
            manager.pages["PROGRAM_P_GUI"]["PPC_SAMPLEN_DATA"].updateText("{:d} samples".format(manager.processTimers['nRecords']))
            manager.pages["PROGRAM_P_GUI"]["IPCA_AVAILABLETID_DATA"].updateText("{:d} / {:d}".format(len(manager.assistantIPC.TID_Availables), manager.assistantIPC.TIDIssueLimit))
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA1"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_GUI_UpdateProcessData1, interval = 250)
        def timerFunction_page_PROGRAM_P_GUI_UpdateProcessLog(manager):
            if (manager.pages["PROGRAM_P_GUI"]["P_LOG_UPDATE"].getStatus() == True):
                processLog = self.programLogger.getPMessages(); matrix = [[]]; maximumDisplayStringLength = 100
                for i in range (len(processLog)):
                    dataContent = processLog[i]
                    if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                    matrix[0].append(("[{:d}] {:s}".format(i, dataContent), "w", "white", ("Arial", 10, "")))
                viewRangePrevious = manager.pages["PROGRAM_P_GUI"]["P_LOG"].getViewRange()['vertical']
                manager.pages["PROGRAM_P_GUI"]["P_LOG"].updateMatrix(matrix, holdPosition = True)
                viewRangeNew = manager.pages["PROGRAM_P_GUI"]["P_LOG"].getViewRange()['vertical']
                if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_GUI"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_GUI"]["P_LOG"].getViewRange()['vertical'])
            return True
        self.timerFunctions[thisPage]["UPDATEPROCESSLOG"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_GUI_UpdateProcessLog, interval = 1000)
        def timerFunction_page_PROGRAM_P_GUI_UpdatePRDData(manager):
            prd = manager.assistantIPC.getPRD(manager.pageVariables["PROGRAM_P_GUI"]['PRD_ManagerSelection']); prdKeys = list(prd.keys()); matrix = [[],[]]; maximumDisplayStringLength = 70
            for i in range (len(prdKeys)): 
                matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                dataContent = str(prd[prdKeys[i]])
                if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                matrix[1].append((dataContent, "center", "white", ("Arial", 10, "")))
            viewRangePrevious = manager.pages["PROGRAM_P_GUI"]["PRD_MATRIX"].getViewRange()['vertical']
            manager.pages["PROGRAM_P_GUI"]["PRD_MATRIX"].updateMatrix(matrix, holdPosition = True)
            viewRangeNew = manager.pages["PROGRAM_P_GUI"]["PRD_MATRIX"].getViewRange()['vertical']
            if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_GUI"]["PRD_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_GUI"]["PRD_MATRIX"].getViewRange()['vertical'])
            return True
        self.timerFunctions[thisPage]["UPDATEPRDDATA"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_GUI_UpdatePRDData, interval = 1000)
        def timerFunction_page_PROGRAM_P_GUI_UpdateIPCLOG(manager):
            if (manager.pages["PROGRAM_P_GUI"]["IPCLOG_MATRIX_UPDATE"].getStatus() == True):
                ipcLog = self.assistantIPC.getProcessLog(); matrix = [[],[]]; maximumDisplayStringLength = 70
                for i in range (len(ipcLog)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, self.__valueFormatter(ipcLog[i][0], "ns")), "center", "white", ("Arial", 10, "")))
                    dataContent = ipcLog[i][1]
                    if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                    matrix[1].append((dataContent, "center", "white", ("Arial", 10, "")))
                viewRangePrevious = manager.pages["PROGRAM_P_GUI"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                manager.pages["PROGRAM_P_GUI"]["IPCLOG_MATRIX"].updateMatrix(matrix, holdPosition = True)
                viewRangeNew = manager.pages["PROGRAM_P_GUI"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_GUI"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_GUI"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
            return True
        self.timerFunctions[thisPage]["UPDATEIPCLOG"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_GUI_UpdateIPCLOG, interval = 1000)
        #PAGE "PROGRAM_P_GUI" END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_P_IPC" -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_P_IPC"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_P_IPC = dict()
        page_PROGRAM_P_IPC.update(main_navigationGUIOs)
        page_PROGRAM_P_IPC.update(program_navigationGUIOs)

        def page_PROGRAM_P_IPC_load(manager):
            manager.pages["PROGRAM_P_IPC"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_P_IPC"]["LOCALNAVIGATION_P_IPC"].deactivate()
        def page_PROGRAM_P_IPC_close(manager):
            manager.pages["PROGRAM_P_IPC"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_P_IPC"]["LOCALNAVIGATION_P_IPC"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_P_IPC_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_P_IPC_close
        
        page_PROGRAM_P_IPC["PROCESSCOUNTERS_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           10, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "PROCESS PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_IPC["PROCESS_LASTLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["PROCESS_LASTLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["PROCESS_LASTPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["PROCESS_LASTPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["PROCESS_AVGLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["PROCESS_AVGLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["PROCESS_AVGPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["PROCESS_AVGPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["PPC_SAMPLEN_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,               10, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Number of Records", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["PPC_SAMPLEN_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,                    215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["AVG_STANDARD_SELECTIONBOXTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 340, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Count Standard", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["AVG_STANDARD_SELECTIONBOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,            545, 220, 120, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("IPC", "PTIMERS_AVGSTANDARD", nRetry = "INF")
        def __guioF_PROGRAM_P_IPC_INITIALIZATIONDATAREQUEST0(manager, result): 
            manager.pages["PROGRAM_P_IPC"]["AVG_STANDARD_SELECTIONBOX"].editSelected(str(result))
            manager.pageVariables["PROGRAM_P_IPC"]['AVG_STANDARD'] = result
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_IPC_INITIALIZATIONDATAREQUEST0
        page_PROGRAM_P_IPC["AVG_STANDARD_SELECTIONBOX"].updateList(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "20", "30", "40", "50", "60"])
        page_PROGRAM_P_IPC["P_LOG_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 265,  655,   40, style = "styleA_themeA", layer = 1, text = "PROCESS MESSAGE LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_IPC["P_LOG"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,          10, 310,  620, 1085, "styleA_themeA", layer = 1, nDisplayedColumns = 1, nDisplayedRows = 30)
        page_PROGRAM_P_IPC["P_LOG_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,           635, 310, 1085,   30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_IPC["P_LOG"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_IPC["P_LOG_COMMENT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,     10, 1400, 620, 30, boxStyle = "styleA_themeC", layer = 1, text = "PROCESS [IPC] LOG", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["P_LOG_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,            635, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)
        page_PROGRAM_P_IPC["IPCAPERF_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           680, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_IPC["IPCA_READTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_READTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_READSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_READSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_READRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_READRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_AVGREADTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_AVGREADTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_AVGREADSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_AVGREADSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_AVGREADRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_AVGREADRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_WRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_WRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_WRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_WRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_WRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_WRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_AVGWRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_AVGWRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_AVGWRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_AVGWRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCA_AVGWRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_AVGWRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["PRD_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,            680, 375, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC PRE-REGISTERED DATA", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_IPC["PRD_MANAGERSELECTION_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 420, 325, 30, style = "styleA_themeA", layer = 1, text = "PRD From", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_IPC["PRD_MANAGERSELECTION_BOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,         1010, 420, 325, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("IPC", "ATMMANAGERS", nRetry = "INF")
        def __guioF_PROGRAM_P_IPC_INITIALIZATIONDATAREQUEST1(manager, result):
            manager.pages["PROGRAM_P_IPC"]["PRD_MANAGERSELECTION_BOX"].updateList(result)
            manager.pages["PROGRAM_P_IPC"]["PRD_MANAGERSELECTION_BOX"].editSelected(result[0])
            manager.pageVariables["PROGRAM_P_IPC"]['PRD_ManagerSelection'] = result[0]
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_IPC_INITIALIZATIONDATAREQUEST1
        page_PROGRAM_P_IPC["PRD_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 455, 620, 350, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 8, columnTitles = [("[INDEX] DATA NAME", "center", "white", ("Arial", 12, "bold")), ("DATA CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (4, 6))
        page_PROGRAM_P_IPC["PRD_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 455, 350,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_IPC["PRD_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_IPC["IPCLOG_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 820, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_IPC["IPCLOG_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 865, 620, 530, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 10, columnTitles = [("[INDEX] Record Time", "center", "white", ("Arial", 12, "bold")), ("CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (3, 7))
        page_PROGRAM_P_IPC["IPCLOG_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 865, 530,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_IPC["IPCLOG_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_IPC["IPCA_COMMENT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 680, 1400, 325, 30, style = "styleA_themeA", layer = 1, text = "< IPCLOGs are not recorded to avoid recursion >", textFill = (255, 255, 255, 200), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_AVAILABLETID_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 1400, 200, 30, style = "styleA_themeA", layer = 1, text = "Available Transmission IDs", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_IPC["IPCA_AVAILABLETID_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 1400,  85, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_IPC["IPCLOG_MATRIX_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,                1305, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)

        self.pages[thisPage] = page_PROGRAM_P_IPC

        #Object Functions
        def __guioF_PROGRAM_P_IPC_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED(manager): 
            selectedOption = manager.pages["PROGRAM_P_IPC"]["AVG_STANDARD_SELECTIONBOX"].getSelected() 
            tID = manager.assistantIPC.sendFAR("IPC", "EDIT_PTIMERAVGSTANDARD", int(selectedOption))
            def __guioF_PROGRAM_P_IPC_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                manager.pages["PROGRAM_P_IPC"]["AVG_STANDARD_SELECTIONBOX"].editSelected(result)
                manager.pageVariables["PROGRAM_P_IPC"]['AVG_STANDARD'] = result
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_IPC_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-AVG_STANDARD_SELECTIONBOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_IPC_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED
        def __guioF_PROGRAM_P_IPC_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED(manager):
            selectedOption = manager.pages["PROGRAM_P_IPC"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_IPC"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("IPC", "GET_PRD", (selectedOption, 70))
            def __guioF_PROGRAM_P_IPC_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0(manager, result):
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]; maximumDisplayStringLength = 70
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_IPC"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_IPC_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-PRD_MANAGERSELECTION_BOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_IPC_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED 
        def __guioF_PROGRAM_P_IPC_P_LOG_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_IPC"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_IPC"]["P_LOG"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-P_LOG-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_IPC_P_LOG_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_IPC_P_LOG_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_IPC"]["P_LOG"].changeViewRangeV(manager.pages["PROGRAM_P_IPC"]["P_LOG_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-P_LOG_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_IPC_P_LOG_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_IPC_IPCLOG_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_IPC"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_IPC"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_IPC_IPCLOG_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_IPC_IPCLOG_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_IPC"]["IPCLOG_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_IPC"]["IPCLOG_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_IPC_IPCLOG_MATRIX_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_IPC_PRD_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_IPC"]["PRD_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_IPC"]["PRD_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-PRD_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_IPC_PRD_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_IPC_PRD_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_IPC"]["PRD_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_IPC"]["PRD_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-PRD_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_IPC_PRD_MATRIX_SB_V_VALUEUPDATED
        #Page Timer Functions
        def timerFunction_page_PROGRAM_P_IPC_UpdateProcessData0(manager):
            tID = manager.assistantIPC.sendFAR("IPC", "GET_PTIMERS_LAST", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_IPC_UpdateProcessData0_FARHanlder0(manager, result):
                lastRecord = result
                if (lastRecord != None):
                    manager.pages["PROGRAM_P_IPC"]["PROCESS_LASTLOOPTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_processLoop'], "ns"))
                    manager.pages["PROGRAM_P_IPC"]["PROCESS_LASTPROCTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_process'], "ns"))
                    manager.pages["PROGRAM_P_IPC"]["IPCA_READTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readTime'], "ns"))
                    manager.pages["PROGRAM_P_IPC"]["IPCA_READSIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readSize'], "Bytes"))
                    manager.pages["PROGRAM_P_IPC"]["IPCA_READRATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readRate'] / manager.pageVariables["PROGRAM_P_IPC"]['AVG_STANDARD'], "Bytes/s"))
                    manager.pages["PROGRAM_P_IPC"]["IPCA_WRITETIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeTime'], "ns"))
                    manager.pages["PROGRAM_P_IPC"]["IPCA_WRITESIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeSize'], "Bytes"))
                    manager.pages["PROGRAM_P_IPC"]["IPCA_WRITERATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeRate'] / manager.pageVariables["PROGRAM_P_IPC"]['AVG_STANDARD'], "Bytes/s"))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_IPC_UpdateProcessData0_FARHanlder0
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA0"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_IPC_UpdateProcessData0, interval = 100)
        def timerFunction_page_PROGRAM_P_IPC_UpdateProcessData1(manager):
            tID = manager.assistantIPC.sendFAR("IPC", "GET_PTIMERS_AVG", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_IPC_UpdateProcessData1_FARHanlder0(manager, result):
                processTimers = result
                manager.pages["PROGRAM_P_IPC"]["PROCESS_AVGLOOPTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_processLoop_avg'], "ns"))
                manager.pages["PROGRAM_P_IPC"]["PROCESS_AVGPROCTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_process_avg'], "ns"))
                manager.pages["PROGRAM_P_IPC"]["IPCA_AVGREADTIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readTime_avg'], "ns"))
                manager.pages["PROGRAM_P_IPC"]["IPCA_AVGREADSIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_IPC"]["IPCA_AVGREADRATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readRate_avg'] / manager.pageVariables["PROGRAM_P_IPC"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_IPC"]["IPCA_AVGWRITETIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeTime_avg'], "ns"))
                manager.pages["PROGRAM_P_IPC"]["IPCA_AVGWRITESIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_IPC"]["IPCA_AVGWRITERATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeRate_avg'] / manager.pageVariables["PROGRAM_P_IPC"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_IPC"]["PPC_SAMPLEN_DATA"].updateText("{:d} samples".format(processTimers['nRecords']))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_IPC_UpdateProcessData1_FARHanlder0
            tID = manager.assistantIPC.sendFAR("IPC", "GET_IPC_TIDAVAILABILITY", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_IPC_UpdateProcessData1_FARHanlder1(manager, result):
                manager.pages["PROGRAM_P_IPC"]["IPCA_AVAILABLETID_DATA"].updateText("{:d} / {:d}".format(result[0], result[1]))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_IPC_UpdateProcessData1_FARHanlder1
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA1"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_IPC_UpdateProcessData1, interval = 250)
        def timerFunction_page_P_IPC_UpdateProcessLog(manager):
            if (manager.pages["PROGRAM_P_IPC"]["P_LOG_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("IPC", "GET_PLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_P_IPC_UpdateProcessLog_FARHandler0(manager, result):
                    matrix = [[]]; processLog = result; maximumDisplayStringLength = 100
                    for i in range (len(processLog)):
                        dataContent = processLog[i]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[0].append(("[{:d}] {:s}".format(i, dataContent), "w", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_IPC"]["P_LOG"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_IPC"]["P_LOG"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_IPC"]["P_LOG"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_IPC"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_IPC"]["P_LOG"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_P_IPC_UpdateProcessLog_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPROCESSLOG"] = self.__timerFunction(function = timerFunction_page_P_IPC_UpdateProcessLog, interval = 1000)
        def timerFunction_page_PROGRAM_P_IPC_UpdatePRDData(manager):
            selectedOption = manager.pages["PROGRAM_P_IPC"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_IPC"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("IPC", "GET_PRD", (selectedOption, 70), nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_IPC_UpdatePRDData_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]; maximumDisplayStringLength = 70
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_IPC"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_IPC_UpdatePRDData_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPRDDATA"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_IPC_UpdatePRDData, interval = 1000)
        def timerFunction_page_PROGRAM_P_IPC_UpdateIPCLOG(manager):
            if (manager.pages["PROGRAM_P_IPC"]["IPCLOG_MATRIX_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("IPC", "GET_IPCLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_PROGRAM_P_IPC_UpdateIPCLOG_FARHandler0(manager, result):
                    ipcLog = result; matrix = [[],[]]; maximumDisplayStringLength = 100
                    for i in range (len(ipcLog)): 
                        matrix[0].append(("[{:d}] {:s}".format(i, self.__valueFormatter(ipcLog[i][0], "ns")), "center", "white", ("Arial", 10, "")))
                        dataContent = ipcLog[i][1]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[1].append((dataContent, "center", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_IPC"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_IPC"]["IPCLOG_MATRIX"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_IPC"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_IPC"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_IPC"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_IPC_UpdateIPCLOG_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEIPCLOG"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_IPC_UpdateIPCLOG, interval = 1000)
        
        #PAGE "PROGRAM_P_IPC" END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_P_SECURITYCONTROL" -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_P_SECURITYCONTROL"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_P_SECURITYCONTROL = dict()
        page_PROGRAM_P_SECURITYCONTROL.update(main_navigationGUIOs)
        page_PROGRAM_P_SECURITYCONTROL.update(program_navigationGUIOs)

        def page_PROGRAM_P_SECURITYCONTROL_load(manager):
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["LOCALNAVIGATION_P_SECURITYCONTROL"].deactivate()
        def page_PROGRAM_P_SECURITYCONTROL_close(manager):
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["LOCALNAVIGATION_P_SECURITYCONTROL"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_P_SECURITYCONTROL_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_P_SECURITYCONTROL_close
        
        page_PROGRAM_P_SECURITYCONTROL["PROCESSCOUNTERS_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           10, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "PROCESS PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_SECURITYCONTROL["PROCESS_LASTLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["PROCESS_LASTLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["PROCESS_LASTPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      10, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["PROCESS_LASTPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["PROCESS_AVGLOOPTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Loop Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["PROCESS_AVGLOOPTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["PROCESS_AVGPROCTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      340, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Process Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["PROCESS_AVGPROCTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            545, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["PPC_SAMPLEN_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,               10, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Number of Records", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["PPC_SAMPLEN_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,                    215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["AVG_STANDARD_SELECTIONBOXTEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 340, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average Count Standard", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["AVG_STANDARD_SELECTIONBOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,            545, 220, 120, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("SECURITYCONTROL", "PTIMERS_AVGSTANDARD", nRetry = "INF")
        def __guioF_PROGRAM_P_SECURITYCONTROL_INITIALIZATIONDATAREQUEST0(manager, result): 
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["AVG_STANDARD_SELECTIONBOX"].editSelected(str(result))
            manager.pageVariables["PROGRAM_P_SECURITYCONTROL"]['AVG_STANDARD'] = result
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_SECURITYCONTROL_INITIALIZATIONDATAREQUEST0
        page_PROGRAM_P_SECURITYCONTROL["AVG_STANDARD_SELECTIONBOX"].updateList(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "20", "30", "40", "50", "60"])
        page_PROGRAM_P_SECURITYCONTROL["P_LOG_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  10, 265,  655,   40, style = "styleA_themeA", layer = 1, text = "PROCESS MESSAGE LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_SECURITYCONTROL["P_LOG"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,          10, 310,  620, 1085, "styleA_themeA", layer = 1, nDisplayedColumns = 1, nDisplayedRows = 30)
        page_PROGRAM_P_SECURITYCONTROL["P_LOG_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,           635, 310, 1085,   30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_SECURITYCONTROL["P_LOG"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_SECURITYCONTROL["P_LOG_COMMENT"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,     10, 1400, 620, 30, boxStyle = "styleA_themeC", layer = 1, text = "PROCESS [SECURITYCONTROL] LOG", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["P_LOG_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,            635, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)
        page_PROGRAM_P_SECURITYCONTROL["IPCAPERF_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,           680, 105, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT PERFORMANCE", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_READTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_READTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_READSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_READSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_READRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,      680, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_READRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,            885, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGREADTIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 150, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGREADTIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 150, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGREADSIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 185, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGREADSIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 185, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGREADRATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  1010, 220, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Read Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGREADRATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,        1215, 220, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_WRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_WRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_WRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_WRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_WRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,     680, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Last IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_WRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,           885, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGWRITETIME_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 260, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Time", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGWRITETIME_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 260, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGWRITESIZE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 295, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Size", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGWRITESIZE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 295, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGWRITERATE_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 330, 200, 30, style = "styleA_themeA", layer = 1, text = "Average IPCB Write Rate", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVGWRITERATE_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 330, 120, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["PRD_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,            680, 375, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC PRE-REGISTERED DATA", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_SECURITYCONTROL["PRD_MANAGERSELECTION_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 420, 325, 30, style = "styleA_themeA", layer = 1, text = "PRD From", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_SECURITYCONTROL["PRD_MANAGERSELECTION_BOX"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,         1010, 420, 325, 30, "styleA_themeA", layer = 1, textSize = 12, maxDisplayList = 5)
        tID = self.assistantIPC.sendDAR("SECURITYCONTROL", "ATMMANAGERS", nRetry = "INF")
        def __guioF_PROGRAM_P_SECURITYCONTROL_INITIALIZATIONDATAREQUEST1(manager, result):
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["PRD_MANAGERSELECTION_BOX"].updateList(result)
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["PRD_MANAGERSELECTION_BOX"].editSelected(result[0])
            manager.pageVariables["PROGRAM_P_SECURITYCONTROL"]['PRD_ManagerSelection'] = result[0]
        self.IPCResultHandlers[tID] = __guioF_PROGRAM_P_SECURITYCONTROL_INITIALIZATIONDATAREQUEST1
        page_PROGRAM_P_SECURITYCONTROL["PRD_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 455, 620, 350, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 8, columnTitles = [("[INDEX] DATA NAME", "center", "white", ("Arial", 12, "bold")), ("DATA CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (4, 6))
        page_PROGRAM_P_SECURITYCONTROL["PRD_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 455, 350,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_SECURITYCONTROL["PRD_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_SECURITYCONTROL["IPCLOG_MATRIX_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator,  680, 820, 655, 40, style = "styleA_themeA", layer = 1, text = "IPC ASSISTANT LOG", textFill = (255, 255, 255, 255), textSize = 16)
        page_PROGRAM_P_SECURITYCONTROL["IPCLOG_MATRIX"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  680, 865, 620, 530, "styleA_themeA", layer = 1, nDisplayedColumns = 2, nDisplayedRows = 10, columnTitles = [("[INDEX] Record Time", "center", "white", ("Arial", 12, "bold")), ("CONTENT", "center", "white", ("Arial", 12, "bold"))], customColumnRatio = (3, 7))
        page_PROGRAM_P_SECURITYCONTROL["IPCLOG_MATRIX_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,   1305, 865, 530,  30, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = page_PROGRAM_P_SECURITYCONTROL["IPCLOG_MATRIX"].getViewRange()['vertical'], align = "vertical", buttonGOffset = 3)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_COMMENT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 680, 1400, 325, 30, style = "styleA_themeA", layer = 1, text = "< IPCLOGs are not recorded to avoid recursion >", textFill = (255, 255, 255, 200), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVAILABLETID_TEXT"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 1010, 1400, 200, 30, style = "styleA_themeA", layer = 1, text = "Available Transmission IDs", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_P_SECURITYCONTROL["IPCA_AVAILABLETID_DATA"] = activeTextBox_typeA(self.canvas, self.graphicsGenerator,       1215, 1400,  85, 30, boxStyle = "styleA_themeC", layer = 1, text = "", textSize = 10, textStyle = "generalText_StyleA")
        page_PROGRAM_P_SECURITYCONTROL["IPCLOG_MATRIX_UPDATE"] = switch_typeB(self.canvas, self.graphicsGenerator,                1305, 1400,  30, 30, "styleA_themeA", layer = 1, status = True)

        self.pages[thisPage] = page_PROGRAM_P_SECURITYCONTROL

        #Object Functions
        def __guioF_PROGRAM_P_SECURITYCONTROL_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED(manager): 
            selectedOption = manager.pages["PROGRAM_P_SECURITYCONTROL"]["AVG_STANDARD_SELECTIONBOX"].getSelected() 
            tID = manager.assistantIPC.sendFAR("SECURITYCONTROL", "EDIT_PTIMERAVGSTANDARD", int(selectedOption))
            def __guioF_PROGRAM_P_SECURITYCONTROL_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["AVG_STANDARD_SELECTIONBOX"].editSelected(result)
                manager.pageVariables["PROGRAM_P_SECURITYCONTROL"]['AVG_STANDARD'] = result
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_SECURITYCONTROL_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-AVG_STANDARD_SELECTIONBOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_SECURITYCONTROL_AVG_STANDARD_SELECTIONBOX_SELECTIONUPDATED
        def __guioF_PROGRAM_P_SECURITYCONTROL_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED(manager):
            selectedOption = manager.pages["PROGRAM_P_SECURITYCONTROL"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_SECURITYCONTROL"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("SECURITYCONTROL", "GET_PRD", (selectedOption, 70))
            def __guioF_PROGRAM_P_SECURITYCONTROL_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_P_SECURITYCONTROL_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED_FARHandler0
        self.objectFunctions[thisPage+"-PRD_MANAGERSELECTION_BOX-SELECTIONUPDATED"] = __guioF_PROGRAM_P_SECURITYCONTROL_PRD_MANAGERSELECTION_BOX_SELECTIONUPDATED 
        def __guioF_PROGRAM_P_SECURITYCONTROL_P_LOG_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_SECURITYCONTROL"]["P_LOG"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-P_LOG-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_SECURITYCONTROL_P_LOG_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_SECURITYCONTROL_P_LOG_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["P_LOG"].changeViewRangeV(manager.pages["PROGRAM_P_SECURITYCONTROL"]["P_LOG_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-P_LOG_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_SECURITYCONTROL_P_LOG_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_SECURITYCONTROL_IPCLOG_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_SECURITYCONTROL_IPCLOG_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_SECURITYCONTROL_IPCLOG_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCLOG_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCLOG_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-IPCLOG_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_SECURITYCONTROL_IPCLOG_MATRIX_SB_V_VALUEUPDATED
        def __guioF_PROGRAM_P_SECURITYCONTROL_PRD_MATRIX_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["PRD_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_SECURITYCONTROL"]["PRD_MATRIX"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-PRD_MATRIX-VIEWRANGEUPDATED"] = __guioF_PROGRAM_P_SECURITYCONTROL_PRD_MATRIX_VIEWRANGEUPDATED
        def __guioF_PROGRAM_P_SECURITYCONTROL_PRD_MATRIX_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_P_SECURITYCONTROL"]["PRD_MATRIX"].changeViewRangeV(manager.pages["PROGRAM_P_SECURITYCONTROL"]["PRD_MATRIX_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-PRD_MATRIX_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_P_SECURITYCONTROL_PRD_MATRIX_SB_V_VALUEUPDATED
        #Page Timer Functions
        def timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateProcessData0(manager):
            tID = manager.assistantIPC.sendFAR("SECURITYCONTROL", "GET_PTIMERS_LAST", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateProcessData0_FARHanlder0(manager, result):
                lastRecord = result
                if (lastRecord != None):
                    manager.pages["PROGRAM_P_SECURITYCONTROL"]["PROCESS_LASTLOOPTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_processLoop'], "ns"))
                    manager.pages["PROGRAM_P_SECURITYCONTROL"]["PROCESS_LASTPROCTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['t_process'], "ns"))
                    manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_READTIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readTime'], "ns"))
                    manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_READSIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readSize'], "Bytes"))
                    manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_READRATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_readRate'] / manager.pageVariables["PROGRAM_P_SECURITYCONTROL"]['AVG_STANDARD'], "Bytes/s"))
                    manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_WRITETIME_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeTime'], "ns"))
                    manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_WRITESIZE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeSize'], "Bytes"))
                    manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_WRITERATE_DATA"].updateText(manager.__valueFormatter(lastRecord['ipcb_writeRate'] / manager.pageVariables["PROGRAM_P_SECURITYCONTROL"]['AVG_STANDARD'], "Bytes/s"))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateProcessData0_FARHanlder0
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA0"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateProcessData0, interval = 100)
        def timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateProcessData1(manager):
            tID = manager.assistantIPC.sendFAR("SECURITYCONTROL", "GET_PTIMERS_AVG", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateProcessData1_FARHanlder0(manager, result):
                processTimers = result
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["PROCESS_AVGLOOPTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_processLoop_avg'], "ns"))
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["PROCESS_AVGPROCTIME_DATA"].updateText(manager.__valueFormatter(processTimers['t_process_avg'], "ns"))
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_AVGREADTIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readTime_avg'], "ns"))
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_AVGREADSIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_AVGREADRATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_readRate_avg'] / manager.pageVariables["PROGRAM_P_SECURITYCONTROL"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_AVGWRITETIME_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeTime_avg'], "ns"))
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_AVGWRITESIZE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeSize_avg'], "Bytes"))
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_AVGWRITERATE_DATA"].updateText(manager.__valueFormatter(processTimers['ipcb_writeRate_avg'] / manager.pageVariables["PROGRAM_P_SECURITYCONTROL"]['AVG_STANDARD'], "Bytes/s"))
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["PPC_SAMPLEN_DATA"].updateText("{:d} samples".format(processTimers['nRecords']))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateProcessData1_FARHanlder0
            tID = manager.assistantIPC.sendFAR("SECURITYCONTROL", "GET_IPC_TIDAVAILABILITY", None, nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateProcessData1_FARHanlder1(manager, result):
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCA_AVAILABLETID_DATA"].updateText("{:d} / {:d}".format(result[0], result[1]))
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateProcessData1_FARHanlder1
            return True
        self.timerFunctions[thisPage]["UPDATEPAGEDATA1"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateProcessData1, interval = 250)
        def timerFunction_page_P_SECURITYCONTROL_UpdateProcessLog(manager):
            if (manager.pages["PROGRAM_P_SECURITYCONTROL"]["P_LOG_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("SECURITYCONTROL", "GET_PLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_P_SECURITYCONTROL_UpdateProcessLog_FARHandler0(manager, result):
                    matrix = [[]]; processLog = result; maximumDisplayStringLength = 100
                    for i in range (len(processLog)):
                        dataContent = processLog[i]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[0].append(("[{:d}] {:s}".format(i, dataContent), "w", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_SECURITYCONTROL"]["P_LOG"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_SECURITYCONTROL"]["P_LOG"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_SECURITYCONTROL"]["P_LOG"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_SECURITYCONTROL"]["P_LOG_SB_V"].changeViewRange(manager.pages["PROGRAM_P_SECURITYCONTROL"]["P_LOG"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_P_SECURITYCONTROL_UpdateProcessLog_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPROCESSLOG"] = self.__timerFunction(function = timerFunction_page_P_SECURITYCONTROL_UpdateProcessLog, interval = 1000)
        def timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdatePRDData(manager):
            selectedOption = manager.pages["PROGRAM_P_SECURITYCONTROL"]["PRD_MANAGERSELECTION_BOX"].getSelected()
            manager.pageVariables["PROGRAM_P_SECURITYCONTROL"]['PRD_ManagerSelection'] = selectedOption
            tID = manager.assistantIPC.sendFAR("SECURITYCONTROL", "GET_PRD", (selectedOption, 70), nRetry = 0, nRetry_result = 0)
            def timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdatePRDData_FARHandler0(manager, result): 
                prd = result; prdKeys = list(prd.keys()); matrix = [[],[]]
                for i in range (len(prdKeys)): 
                    matrix[0].append(("[{:d}] {:s}".format(i, prdKeys[i]), "center", "white", ("Arial", 10, "")))
                    matrix[1].append((str(prd[prdKeys[i]]), "center", "white", ("Arial", 10, "")))
                manager.pages["PROGRAM_P_SECURITYCONTROL"]["PRD_MATRIX"].updateMatrix(matrix)
            manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdatePRDData_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEPRDDATA"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdatePRDData, interval = 1000)
        def timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateIPCLOG(manager):
            if (manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCLOG_MATRIX_UPDATE"].getStatus() == True):
                tID = manager.assistantIPC.sendFAR("SECURITYCONTROL", "GET_IPCLOG", None, nRetry = 0, nRetry_result = 0)
                def timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateIPCLOG_FARHandler0(manager, result):
                    ipcLog = result; matrix = [[],[]]; maximumDisplayStringLength = 100
                    for i in range (len(ipcLog)): 
                        matrix[0].append(("[{:d}] {:s}".format(i, self.__valueFormatter(ipcLog[i][0], "ns")), "center", "white", ("Arial", 10, "")))
                        dataContent = ipcLog[i][1]
                        if (len(dataContent) > maximumDisplayStringLength): dataContent = dataContent[:maximumDisplayStringLength] + "..."
                        matrix[1].append((dataContent, "center", "white", ("Arial", 10, "")))
                    viewRangePrevious = manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCLOG_MATRIX"].updateMatrix(matrix, holdPosition = True)
                    viewRangeNew = manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCLOG_MATRIX"].getViewRange()['vertical']
                    if (viewRangeNew != viewRangePrevious): manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCLOG_MATRIX_SB_V"].changeViewRange(manager.pages["PROGRAM_P_SECURITYCONTROL"]["IPCLOG_MATRIX"].getViewRange()['vertical'])
                manager.IPCResultHandlers[tID] = timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateIPCLOG_FARHandler0
            return True
        self.timerFunctions[thisPage]["UPDATEIPCLOG"] = self.__timerFunction(function = timerFunction_page_PROGRAM_P_SECURITYCONTROL_UpdateIPCLOG, interval = 1000)
        
        #PAGE "PROGRAM_P_SECURITYCONTROL" END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_EXPERIMENT0" -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_EXPERIMENT0"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_EXPERIMENT0 = dict()
        page_PROGRAM_EXPERIMENT0.update(main_navigationGUIOs)
        page_PROGRAM_EXPERIMENT0.update(program_navigationGUIOs)

        def page_PROGRAM_EXPERIMENT0_load(manager):
            manager.pages["PROGRAM_EXPERIMENT0"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_EXPERIMENT0"]["LOCALNAVIGATION_EXP0"].deactivate()
        def page_PROGRAM_EXPERIMENT0_close(manager):
            manager.pages["PROGRAM_EXPERIMENT0"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_EXPERIMENT0"]["LOCALNAVIGATION_EXP0"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_EXPERIMENT0_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_EXPERIMENT0_close
        
        page_PROGRAM_EXPERIMENT0["GENERALBUTTONTESTER"] = button_typeA(self.canvas, self.graphicsGenerator, 10, 105, 150, 40, "styleA_themeB", layer = 1, text = "GENERAL BUTTON", textSize = 14)
        page_PROGRAM_EXPERIMENT0["BUTTONTESTER_DAR"] = button_typeA(self.canvas, self.graphicsGenerator, 10, 150, 150, 40, "styleA_themeB", layer = 1, text = "DAR TEST", textSize = 14)
        page_PROGRAM_EXPERIMENT0["BUTTONTESTER_FAR"] = button_typeA(self.canvas, self.graphicsGenerator, 10, 195, 150, 40, "styleA_themeB", layer = 1, text = "FAR TEST", textSize = 14)
        page_PROGRAM_EXPERIMENT0["CONSTANTTEXTGRAPHICSTESTER"] = constantTextGraphic_typeA(self.canvas, self.graphicsGenerator, 10, 240, 150, 40, style = "styleA_themeA", layer = 1, text = "Constant Text", textFill = (255, 255, 255, 255), textSize = 14)
        page_PROGRAM_EXPERIMENT0["SLIDERH"] = slider_typeA(self.canvas, self.graphicsGenerator,  165, 105, 2385, 40, "styleA_themeA", "styleA_themeA", layer = 1, align = "horizontal")
        page_PROGRAM_EXPERIMENT0["SLIDERV"] = slider_typeA(self.canvas, self.graphicsGenerator, 2510, 195, 1235, 40, "styleA_themeA", "styleA_themeA", layer = 1, align = "vertical")
        page_PROGRAM_EXPERIMENT0["SWITCHTESTER1"] = switch_typeA(self.canvas, self.graphicsGenerator, 165, 150, 85, 40, "styleA_themeA", layer = 1, align = "horizontal")
        page_PROGRAM_EXPERIMENT0["SWITCHTESTER2"] = switch_typeA(self.canvas, self.graphicsGenerator, 165, 195, 40, 85, "styleA_themeA", layer = 1, align = "vertical")
        page_PROGRAM_EXPERIMENT0["SWITCHTESTER3"] = switch_typeB(self.canvas, self.graphicsGenerator, 210, 195, 40, 40, "styleA_themeA", layer = 1)
        ledTesterColors = {"Red": (255, 0, 0, 255), "Green": (0, 255, 0, 255), "Blue": (0, 0, 255, 255)}
        page_PROGRAM_EXPERIMENT0["LEDTESTER"] = LED_typeA(self.canvas, self.graphicsGenerator, 210, 240, 40, 40, "styleA_themeA", layer = 1, colors = ledTesterColors)
        page_PROGRAM_EXPERIMENT0["LEDBUTTON"] = button_typeA(self.canvas, self.graphicsGenerator, 255, 150, 40, 130, "styleA_themeB", layer = 1)
        page_PROGRAM_EXPERIMENT0["SCROLLBARTESTERH"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,  300, 150, 2250, 40, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = (40, 60), align = "horizontal")
        page_PROGRAM_EXPERIMENT0["SCROLLBARTESTERV"] = scrollBar_typeA(self.canvas, self.graphicsGenerator, 2465, 195, 1235, 40, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = (40, 60), align = "vertical")
        page_PROGRAM_EXPERIMENT0["SCROLLBARVIEWRANGEBUTTON0"] = button_typeA(self.canvas, self.graphicsGenerator, 300, 195, 200, 40, "styleA_themeB", layer = 1, text = "INCREASE VIEWRANGE_H", textSize = 14)
        page_PROGRAM_EXPERIMENT0["SCROLLBARVIEWRANGEBUTTON1"] = button_typeA(self.canvas, self.graphicsGenerator, 300, 240, 200, 40, "styleA_themeB", layer = 1, text = "DECREASE VIEWRANGE_H", textSize = 14)
        page_PROGRAM_EXPERIMENT0["SCROLLBARVIEWRANGEBUTTON2"] = button_typeA(self.canvas, self.graphicsGenerator, 505, 195, 200, 40, "styleA_themeB", layer = 1, text = "INCREASE VIEWRANGE_V", textSize = 14)
        page_PROGRAM_EXPERIMENT0["SCROLLBARVIEWRANGEBUTTON3"] = button_typeA(self.canvas, self.graphicsGenerator, 505, 240, 200, 40, "styleA_themeB", layer = 1, text = "DECREASE VIEWRANGE_V", textSize = 14)
        page_PROGRAM_EXPERIMENT0["TEXTINPUTBOXTESTER"] = textInputBox_typeA(self.canvas, self.graphicsGenerator, 710, 195, 1750, 40, "styleA_themeA", layer = 1)
        page_PROGRAM_EXPERIMENT0["SELECTIONBOXTESTER"] = selectionBox_typeA(self.canvas, self.graphicsGenerator,  10, 285, 150, 40, "styleA_themeA", layer = 1, textSize = 12)
        page_PROGRAM_EXPERIMENT0["SELECTIONBOXTESTERBUTTON"] = button_typeA(self.canvas, self.graphicsGenerator, 165, 285, 130, 40, "styleA_themeB", layer = 1, text = "UPDATE sLIST", textSize = 14)
        matrix = list()
        for i in range (200):
            matrix.append(list())
            for j in range (200):
                tup = ("C" + str(i) + "_R" + str(j), "center", "white", ("Arial", 12, "bold"))
                matrix[i].append(tup)
        matrix[0][0] = ("N",      "n",      "white",      ("Arial", 12, "italic"))
        matrix[0][1] = ("NE",     "ne",     "green",      ("Arial", 12, "bold"))
        matrix[0][2] = ("W",      "e",      "blue",       ("Arial", 12, "bold"))
        matrix[0][3] = ("SE",     "se",     "red",        ("Arial", 12, "bold"))
        matrix[0][4] = ("S",      "s",      "orange",     ("Arial", 12, "bold"))
        matrix[0][5] = ("SW",     "sw",     "yellow",     ("Arial", 12, "bold"))
        matrix[0][6] = ("E",      "w",      "skyblue",    ("Arial", 12, "bold"))
        matrix[0][7] = ("NW",     "nw",     "green",      ("Arial", 12, "bold"))
        matrix[0][8] = ("CENTER", "center", "lightgreen", ("Arial", 12, "bold"))
        page_PROGRAM_EXPERIMENT0["MATRIXBOXTESTER"]      = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  10,   330,  670, 1075, "styleA_themeA", layer = 1, matrix = matrix, allowSelection = True)
        page_PROGRAM_EXPERIMENT0["MATRIXBOXTESTER_SB_H"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,         10,  1410,  670,   20, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = (40, 60), align = "horizontal", buttonGOffset = 3)
        page_PROGRAM_EXPERIMENT0["MATRIXBOXTESTER_SB_V"] = scrollBar_typeA(self.canvas, self.graphicsGenerator,         685,  330, 1075,   20, "styleA_themeA", "styleA_themeA", layer = 1, viewRange = (40, 60), align = "vertical",   buttonGOffset = 3)
        page_PROGRAM_EXPERIMENT0["MATRIXBOXTESTER_SB_H"].changeViewRange(page_PROGRAM_EXPERIMENT0["MATRIXBOXTESTER"].getViewRange()['horizontal'])
        page_PROGRAM_EXPERIMENT0["MATRIXBOXTESTER_SB_V"].changeViewRange(page_PROGRAM_EXPERIMENT0["MATRIXBOXTESTER"].getViewRange()['vertical'])
        page_PROGRAM_EXPERIMENT0["GAUGEBARTESTER_H"] = gaugeBar_typeA(self.canvas, self.graphicsGenerator,  710, 240, 1750, 40, "styleA_themeD", layer = 1, value = 50, align = "horizontal", showText = True)
        page_PROGRAM_EXPERIMENT0["GAUGEBARTESTER_V"] = gaugeBar_typeA(self.canvas, self.graphicsGenerator, 2420, 285, 40, 1145, "styleA_themeD", layer = 1, value = 50, align = "vertical", showText = True)
        page_PROGRAM_EXPERIMENT0["CONSTANTIMAGEGRAPHICTESTER0"] = constantImageGraphic_typeA(self.canvas, self.graphicsGenerator, 710, 285, 200, 200, "styleA_themeA", imagePath = os.path.join(path_IMAGES + r"\testImage.png"), layer = 1)
        page_PROGRAM_EXPERIMENT0["CONSTANTIMAGEGRAPHICTESTER1"] = constantImageGraphic_typeA(self.canvas, self.graphicsGenerator, 915, 285, 200, 200, "empty",         imagePath = os.path.join(path_IMAGES + r"\testImage.png"), layer = 1)
        
        matrix[3][9]  = ("------------N/------------", "n",      "white",      ("Arial", 12, "italic"))
        matrix[3][10] = ("------------NE------------", "ne",     "green",      ("Arial", 12, "bold"))
        matrix[3][11] = ("------------W/------------", "e",      "blue",       ("Arial", 12, "bold"))
        matrix[3][12] = ("------------SE------------", "se",     "red",        ("Arial", 12, "bold"))
        matrix[3][13] = ("------------S/------------", "s",      "orange",     ("Arial", 12, "bold"))
        matrix[3][14] = ("------------SW------------", "sw",     "yellow",     ("Arial", 12, "bold"))
        matrix[3][15] = ("------------E/------------", "w",      "skyblue",    ("Arial", 12, "bold"))
        matrix[3][16] = ("------------NW------------", "nw",     "green",      ("Arial", 12, "bold"))
        matrix[3][17] = ("----------CENTER----------", "center", "lightgreen", ("Arial", 12, "bold"))
        page_PROGRAM_EXPERIMENT0["MATRIXBOXTESTER1"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  710, 490, 600, 940, "styleA_themeA", layer = 1, nDisplayedColumns = 3, nDisplayedRows = 10, matrix = matrix, 
                                                                              columnTitles = [("COLUMN0", "center", "white", ("Arial", 12, "bold")), ("COLUMN1", "center", "white", ("Arial", 12, "bold"))],
                                                                              customColumnRatio = (2, 4, 8), allowSelection = True)
        page_PROGRAM_EXPERIMENT0["MATRIXBOXTESTER2"] = matrixDisplayBox_typeA(self.canvas, self.graphicsGenerator,  1315, 490, 600, 940, "styleA_themeA", layer = 1, nDisplayedColumns = 3, nDisplayedRows = 10, matrix = matrix,
                                                                              customColumnRatio = (2, 4, 8), allowSelection = True)

        self.pages[thisPage] = page_PROGRAM_EXPERIMENT0

        #Object Functions
        def __guioF_PROGRAM_EXPERIMENT0_BUTTONTESTER_DAR(manager):
            tID = manager.assistantIPC.sendDAR("MAIN", "DAR TEST")
            def __guioF_PROGRAM_EXPERIMENT0_BUTTONTESTER_DAR_DARHandler(manager, result):
                print("DAR TEST RESULT:", result)
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_EXPERIMENT0_BUTTONTESTER_DAR_DARHandler
        self.objectFunctions[thisPage+"-BUTTONTESTER_DAR-ACTIVATED"] = __guioF_PROGRAM_EXPERIMENT0_BUTTONTESTER_DAR

        def __guioF_PROGRAM_EXPERIMENT0_BUTTONTESTER_FAR(manager):
            tID = manager.assistantIPC.sendFAR("MAIN", "FAR TEST", ("TESTCONTENT0", "TESTCONTENT1", 1))
            def __guioF_PROGRAM_EXPERIMENT0_BUTTONTESTER_FAR_FARHandler(manager, result):
                print("FAR TEST RESULT:", result)
            manager.IPCResultHandlers[tID] = __guioF_PROGRAM_EXPERIMENT0_BUTTONTESTER_FAR_FARHandler
        self.objectFunctions[thisPage+"-BUTTONTESTER_FAR-ACTIVATED"] = __guioF_PROGRAM_EXPERIMENT0_BUTTONTESTER_FAR

        def __guioF_PROGRAM_EXPERIMENT0_SLIDERH_VALUEUPDATED(manager):
            manager.pages["PROGRAM_EXPERIMENT0"]["GAUGEBARTESTER_H"].updateValue(manager.pages["PROGRAM_EXPERIMENT0"]["SLIDERH"].value)
            manager.pages["PROGRAM_EXPERIMENT0"]["GAUGEBARTESTER_H"].updateText("{:.3f}".format(manager.pages["PROGRAM_EXPERIMENT0"]["SLIDERH"].value))
        self.objectFunctions[thisPage+"-SLIDERH-VALUEUPDATED"] = __guioF_PROGRAM_EXPERIMENT0_SLIDERH_VALUEUPDATED

        def __guioF_PROGRAM_EXPERIMENT0_SLIDERV_VALUEUPDATED(manager):
            manager.pages["PROGRAM_EXPERIMENT0"]["GAUGEBARTESTER_V"].updateValue(100 - manager.pages["PROGRAM_EXPERIMENT0"]["SLIDERV"].value)
            manager.pages["PROGRAM_EXPERIMENT0"]["GAUGEBARTESTER_V"].updateText("{:.3f}".format(100 - manager.pages["PROGRAM_EXPERIMENT0"]["SLIDERV"].value))
        self.objectFunctions[thisPage+"-SLIDERV-VALUEUPDATED"] = __guioF_PROGRAM_EXPERIMENT0_SLIDERV_VALUEUPDATED

        def __guioF_PROGRAM_EXPERIMENT0_SWITCHTESTER3_SWITCHON(manager):
            manager.pages["PROGRAM_EXPERIMENT0"]["LEDTESTER"].changeState(True)
        self.objectFunctions[thisPage+"-SWITCHTESTER3-SWITCHON"]  = __guioF_PROGRAM_EXPERIMENT0_SWITCHTESTER3_SWITCHON

        def __guioF_PROGRAM_EXPERIMENT0_SWITCHTESTER3_SWITCHOFF(manager):
            manager.pages["PROGRAM_EXPERIMENT0"]["LEDTESTER"].changeState(False)
        self.objectFunctions[thisPage+"-SWITCHTESTER3-SWITCHOFF"] = __guioF_PROGRAM_EXPERIMENT0_SWITCHTESTER3_SWITCHOFF

        def __guioF_PROGRAM_EXPERIMENT0_LEDBUTTON_ACTIVATED(manager):
            newColor = (randint(0, 255), randint(0, 255), randint(0, 255), 255)
            manager.pages["PROGRAM_EXPERIMENT0"]["LEDTESTER"].updateColor(newColor)
        self.objectFunctions[thisPage+"-LEDBUTTON-ACTIVATED"] = __guioF_PROGRAM_EXPERIMENT0_LEDBUTTON_ACTIVATED 

        def __guioF_PROGRAM_EXPERIMENT0_SCROLLBARVIEWRANGEBUTTON0_ACTIVATED(manager):
            viewRange = manager.pages["PROGRAM_EXPERIMENT0"]["SCROLLBARTESTERH"].getViewRange()
            viewRangeSet = [viewRange[0] - 1, viewRange[1] + 1]
            if (viewRangeSet[0] < 0):   viewRangeSet[1] += (0 - viewRangeSet[0]);   viewRangeSet[0] = 0
            if (viewRangeSet[1] > 100): viewRangeSet[0] -= (viewRangeSet[1] - 100); viewRangeSet[1] = 100
            if (viewRangeSet[0] < 0):   viewRangeSet[0] = 0
            if (viewRangeSet[1] > 100): viewRangeSet[1] = 100
            manager.pages["PROGRAM_EXPERIMENT0"]["SCROLLBARTESTERH"].changeViewRange(tuple(viewRangeSet))
        self.objectFunctions[thisPage+"-SCROLLBARVIEWRANGEBUTTON0-ACTIVATED"] = __guioF_PROGRAM_EXPERIMENT0_SCROLLBARVIEWRANGEBUTTON0_ACTIVATED

        def __guioF_PROGRAM_EXPERIMENT0_SCROLLBARVIEWRANGEBUTTON1_ACTIVATED(manager):
            viewRange = manager.pages["PROGRAM_EXPERIMENT0"]["SCROLLBARTESTERH"].getViewRange()
            viewRangeSet = [viewRange[0] + 1, viewRange[1] - 1]
            if ((viewRangeSet[1] - viewRangeSet[0]) < 1):
                centerPoint = viewRangeSet[0] + ((viewRangeSet[1] - viewRangeSet[0]) / 2)
                viewRangeSet[0] = centerPoint - 0.5
                viewRangeSet[1] = centerPoint + 0.5
            manager.pages["PROGRAM_EXPERIMENT0"]["SCROLLBARTESTERH"].changeViewRange(tuple(viewRangeSet))
        self.objectFunctions[thisPage+"-SCROLLBARVIEWRANGEBUTTON1-ACTIVATED"] = __guioF_PROGRAM_EXPERIMENT0_SCROLLBARVIEWRANGEBUTTON1_ACTIVATED

        def __guioF_PROGRAM_EXPERIMENT0_SCROLLBARVIEWRANGEBUTTON2_ACTIVATED(manager):
            viewRange = manager.pages["PROGRAM_EXPERIMENT0"]["SCROLLBARTESTERV"].getViewRange()
            viewRangeSet = [viewRange[0] - 1, viewRange[1] + 1]
            if (viewRangeSet[0] < 0):   viewRangeSet[1] += (0 - viewRangeSet[0]);   viewRangeSet[0] = 0
            if (viewRangeSet[1] > 100): viewRangeSet[0] -= (viewRangeSet[1] - 100); viewRangeSet[1] = 100
            if (viewRangeSet[0] < 0):   viewRangeSet[0] = 0
            if (viewRangeSet[1] > 100): viewRangeSet[1] = 100
            manager.pages["PROGRAM_EXPERIMENT0"]["SCROLLBARTESTERV"].changeViewRange(tuple(viewRangeSet))
        self.objectFunctions[thisPage+"-SCROLLBARVIEWRANGEBUTTON2-ACTIVATED"] = __guioF_PROGRAM_EXPERIMENT0_SCROLLBARVIEWRANGEBUTTON2_ACTIVATED

        def __guioF_PROGRAM_EXPERIMENT0_SCROLLBARVIEWRANGEBUTTON3_ACTIVATED(manager):
            viewRange = manager.pages["PROGRAM_EXPERIMENT0"]["SCROLLBARTESTERV"].getViewRange()
            viewRangeSet = [viewRange[0] + 1, viewRange[1] - 1]
            if ((viewRangeSet[1] - viewRangeSet[0]) < 1):
                centerPoint = viewRangeSet[0] + ((viewRangeSet[1] - viewRangeSet[0]) / 2)
                viewRangeSet[0] = centerPoint - 0.5
                viewRangeSet[1] = centerPoint + 0.5
            manager.pages["PROGRAM_EXPERIMENT0"]["SCROLLBARTESTERV"].changeViewRange(tuple(viewRangeSet))
        self.objectFunctions[thisPage+"-SCROLLBARVIEWRANGEBUTTON3-ACTIVATED"] = __guioF_PROGRAM_EXPERIMENT0_SCROLLBARVIEWRANGEBUTTON3_ACTIVATED

        def __guioF_PROGRAM_EXPERIMENT0_SELECTIONBOXTESTERBUTTON_ACTIVATED(manager):
            manager.pages["PROGRAM_EXPERIMENT0"]["SELECTIONBOXTESTER"].updateList(["0","1","2","3","4","5","6","7","8","9","10"])
        self.objectFunctions[thisPage+"-SELECTIONBOXTESTERBUTTON-ACTIVATED"] = __guioF_PROGRAM_EXPERIMENT0_SELECTIONBOXTESTERBUTTON_ACTIVATED 

        def __guioF_PROGRAM_EXPERIMENT0_MATRIXBOXTESTER_VIEWRANGEUPDATED(manager): 
            manager.pages["PROGRAM_EXPERIMENT0"]["MATRIXBOXTESTER_SB_H"].changeViewRange(manager.pages["PROGRAM_EXPERIMENT0"]["MATRIXBOXTESTER"].getViewRange()['horizontal'])
            manager.pages["PROGRAM_EXPERIMENT0"]["MATRIXBOXTESTER_SB_V"].changeViewRange(manager.pages["PROGRAM_EXPERIMENT0"]["MATRIXBOXTESTER"].getViewRange()['vertical'])
        self.objectFunctions[thisPage+"-MATRIXBOXTESTER-VIEWRANGEUPDATED"] = __guioF_PROGRAM_EXPERIMENT0_MATRIXBOXTESTER_VIEWRANGEUPDATED

        def __guioF_PROGRAM_EXPERIMENT0_MATRIXBOXTESTER_SB_H_VALUEUPDATED(manager):
            manager.pages["PROGRAM_EXPERIMENT0"]["MATRIXBOXTESTER"].changeViewRangeH(manager.pages["PROGRAM_EXPERIMENT0"]["MATRIXBOXTESTER_SB_H"].getViewRange())
        self.objectFunctions[thisPage+"-MATRIXBOXTESTER_SB_H-VALUEUPDATED"] = __guioF_PROGRAM_EXPERIMENT0_MATRIXBOXTESTER_SB_H_VALUEUPDATED

        def __guioF_PROGRAM_EXPERIMENT0_MATRIXBOXTESTER_SB_V_VALUEUPDATED(manager):
            manager.pages["PROGRAM_EXPERIMENT0"]["MATRIXBOXTESTER"].changeViewRangeV(manager.pages["PROGRAM_EXPERIMENT0"]["MATRIXBOXTESTER_SB_V"].getViewRange())
        self.objectFunctions[thisPage+"-MATRIXBOXTESTER_SB_V-VALUEUPDATED"] = __guioF_PROGRAM_EXPERIMENT0_MATRIXBOXTESTER_SB_V_VALUEUPDATED
        #PAGE "PROGRAM_EXPERIMENT0" END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_EXPERIMENT1" -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_EXPERIMENT1"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_EXPERIMENT1 = dict()
        page_PROGRAM_EXPERIMENT1.update(main_navigationGUIOs)
        page_PROGRAM_EXPERIMENT1.update(program_navigationGUIOs)

        def page_PROGRAM_EXPERIMENT1_load(manager):
            manager.pages["PROGRAM_EXPERIMENT1"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_EXPERIMENT1"]["LOCALNAVIGATION_EXP1"].deactivate()
        def page_PROGRAM_EXPERIMENT1_close(manager):
            manager.pages["PROGRAM_EXPERIMENT1"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_EXPERIMENT1"]["LOCALNAVIGATION_EXP1"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_EXPERIMENT1_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_EXPERIMENT1_close
        

        self.pages[thisPage] = page_PROGRAM_EXPERIMENT1

        #Object Functions
        #PAGE "PROGRAM_EXPERIMENT1" END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_EXPERIMENT2" -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_EXPERIMENT2"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_EXPERIMENT2 = dict()
        page_PROGRAM_EXPERIMENT2.update(main_navigationGUIOs)
        page_PROGRAM_EXPERIMENT2.update(program_navigationGUIOs)

        def page_PROGRAM_EXPERIMENT2_load(manager):
            manager.pages["PROGRAM_EXPERIMENT2"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_EXPERIMENT2"]["LOCALNAVIGATION_EXP2"].deactivate()
        def page_PROGRAM_EXPERIMENT2_close(manager):
            manager.pages["PROGRAM_EXPERIMENT2"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_EXPERIMENT2"]["LOCALNAVIGATION_EXP2"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_EXPERIMENT2_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_EXPERIMENT2_close
        

        self.pages[thisPage] = page_PROGRAM_EXPERIMENT2

        #Object Functions
        #PAGE "PROGRAM_EXPERIMENT2" END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #PAGE "PROGRAM_EXPERIMENT3" -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        thisPage = "PROGRAM_EXPERIMENT3"
        self.pageVariables[thisPage]  = dict()
        self.timerFunctions[thisPage] = dict()
        page_PROGRAM_EXPERIMENT3 = dict()
        page_PROGRAM_EXPERIMENT3.update(main_navigationGUIOs)
        page_PROGRAM_EXPERIMENT3.update(program_navigationGUIOs)

        def page_PROGRAM_EXPERIMENT3_load(manager):
            manager.pages["PROGRAM_EXPERIMENT3"]["MAINNAVIGATION_PROGRAM"].deactivate()
            manager.pages["PROGRAM_EXPERIMENT3"]["LOCALNAVIGATION_EXP3"].deactivate()
        def page_PROGRAM_EXPERIMENT3_close(manager):
            manager.pages["PROGRAM_EXPERIMENT3"]["MAINNAVIGATION_PROGRAM"].activate()
            manager.pages["PROGRAM_EXPERIMENT3"]["LOCALNAVIGATION_EXP3"].activate()
        self.pageNavigationFunctions[thisPage+"_LOAD"]  = page_PROGRAM_EXPERIMENT3_load
        self.pageNavigationFunctions[thisPage+"_CLOSE"] = page_PROGRAM_EXPERIMENT3_close
        

        self.pages[thisPage] = page_PROGRAM_EXPERIMENT3

        #Object Functions
        #PAGE "PROGRAM_EXPERIMENT3" END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        pages = ["PROGRAM",
                 "PROGRAM_P_MAIN", "PROGRAM_P_AUTOTRADER", "PROGRAM_P_BINANCEAPI", "PROGRAM_P_DATAANALYSIS", "PROGRAM_P_DATAMANAGEMENT", "PROGRAM_P_GUI", "PROGRAM_P_IPC", "PROGRAM_P_SECURITYCONTROL", 
                 "PROGRAM_EXPERIMENT0", "PROGRAM_EXPERIMENT1", "PROGRAM_EXPERIMENT2", "PROGRAM_EXPERIMENT3"]

        for pageName in pages:
            thisPage = pageName
            self.objectFunctions[thisPage+"-MAINNAVIGATION_DASHBOARD-ACTIVATED"]  = (__loadPage, "DASHBOARD")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_MANAGEDATA-ACTIVATED"] = (__loadPage, "MANAGEDATA")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_ANALYSIS-ACTIVATED"]   = (__loadPage, "ANALYSIS")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY0-ACTIVATED"]     = (__loadPage, "EMPTY0")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY1-ACTIVATED"]     = (__loadPage, "EMPTY1")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY2-ACTIVATED"]     = (__loadPage, "EMPTY2")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY3-ACTIVATED"]     = (__loadPage, "EMPTY3")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY4-ACTIVATED"]     = (__loadPage, "EMPTY4")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY5-ACTIVATED"]     = (__loadPage, "EMPTY5")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_EMPTY6-ACTIVATED"]     = (__loadPage, "EMPTY6")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_APICONTROL-ACTIVATED"] = (__loadPage, "APICONTROL")
            self.objectFunctions[thisPage+"-MAINNAVIGATION_PROGRAM-ACTIVATED"]    = (__loadPage, "PROGRAM")
        
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_MAIN-ACTIVATED"]              = (__loadPage, "PROGRAM")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_P_MAIN-ACTIVATED"]            = (__loadPage, "PROGRAM_P_MAIN")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_P_AUTOTRADER-ACTIVATED"]      = (__loadPage, "PROGRAM_P_AUTOTRADER")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_P_BINANCEAPI-ACTIVATED"]      = (__loadPage, "PROGRAM_P_BINANCEAPI")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_P_DATAANALYSIS-ACTIVATED"]    = (__loadPage, "PROGRAM_P_DATAANALYSIS")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_P_DATAMANAGEMENT-ACTIVATED"]  = (__loadPage, "PROGRAM_P_DATAMANAGEMENT")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_P_GUI-ACTIVATED"]             = (__loadPage, "PROGRAM_P_GUI")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_P_IPC-ACTIVATED"]             = (__loadPage, "PROGRAM_P_IPC")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_P_SECURITYCONTROL-ACTIVATED"] = (__loadPage, "PROGRAM_P_SECURITYCONTROL")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_EXP0-ACTIVATED"]              = (__loadPage, "PROGRAM_EXPERIMENT0")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_EXP1-ACTIVATED"]              = (__loadPage, "PROGRAM_EXPERIMENT1")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_EXP2-ACTIVATED"]              = (__loadPage, "PROGRAM_EXPERIMENT2")
            self.objectFunctions[thisPage+"-LOCALNAVIGATION_EXP3-ACTIVATED"]              = (__loadPage, "PROGRAM_EXPERIMENT3")
        #PAGE "PROGRAM" END -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #Global Timer Functions -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #Update Page Clocks
        def timerFunction_GLOBAL_0(manager):
            currentTimeString = time.ctime()
            day = currentTimeString[0:3]; month = currentTimeString[4:7]; dayNum = currentTimeString[8:10].strip(); timeN = currentTimeString[11:19]; year = currentTimeString[20:24]
            if   (dayNum == "1"):  dayNum = "1st"
            elif (dayNum == "2"):  dayNum = "2nd"
            elif (dayNum == "3"):  dayNum = "3rd"
            elif (dayNum == "21"): dayNum = "21st"
            elif (dayNum == "22"): dayNum = "22nd"
            elif (dayNum == "31"): dayNum = "31st"
            else:                  dayNum += "th"
            if ("PAGECLOCK" in manager.pages[manager.currentPage].keys()): manager.pages[manager.currentPage]["PAGECLOCK"].updateText("{:s} {:s} {:s} {:s} {:s}".format(year, month, dayNum, day, timeN))
        self.timerFunctions["ALL"]["PAGECLOCKUPDATER"] = self.__timerFunction(function = timerFunction_GLOBAL_0, interval = 1000)
        #Global Timer Functions END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        __loadPage(self, "PROGRAMLOAD")
        #PAGE SETUP END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        if (False): #Print Generated Images List During Initialization
            print("<Image Dictionary>")
            imageDictKeys = list(self.graphicsGenerator.imageDictionary.keys())
            imageDictKeys.sort()
            totalSize = 0
            for imageDictKey in imageDictKeys: 
                size = asizeof.asizeof(self.graphicsGenerator.imageDictionary[imageDictKey])
                totalSize += size
                if   size > (1024 * 1024 * 1024): size = size / 1024 / 1024 / 1024; size = "{:.3f} GB".format(size)
                elif size > (1024 * 1024):        size = size / 1024 / 1024;        size = "{:.3f} MB".format(size)
                elif size > (1024):               size = size / 1024;               size = "{:.3f} KB".format(size)
                else:                                                               size = "{:d} Bytes".format(size)
                print(" [{:s}]: {:s} ({:s})".format(imageDictKey, str(self.graphicsGenerator.imageDictionary[imageDictKey]), size))
            if   totalSize > (1024 * 1024 * 1024): totalSize = totalSize / 1024 / 1024 / 1024; totalSize = "{:.3f} GB".format(totalSize)
            elif totalSize > (1024 * 1024):        totalSize = totalSize / 1024 / 1024;        totalSize = "{:.3f} MB".format(totalSize)
            elif totalSize > (1024):               totalSize = totalSize / 1024;               totalSize = "{:.3f} KB".format(totalSize)
            else:                                                                              totalSize = "{:d} Bytes".format(totalSize)
            print("The total size of Image Dictionary is {:s}".format(totalSize))

        #Send Initialization End Message
        self.programLogger.printPMessage("{:s} MANAGER INITIALIZATION COMPLETE!".format(MANAGERNAME))




        self.assistantIPC.sendPRD("PROC_STATUS", "ACTIVE", nRetry = "INF"); self.assistantIPC.patchIPCB_T() #Process Status Report
    #MANAGER INITIALIZATION END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



      
    
    #MANAGER MAIN PROCESS ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def process(self):
        #IPC Control ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.assistantIPC.readIPCB_R()

        for targetManager in self.atm_Managers:
            #Process DARs and send DARRs
            for DAR in self.assistantIPC.getDARs(targetManager):  #DAR:  [0]: dataName, [1]: requestID, [2]: timeoutTrigger_result, [3]: nRetry_result
                self.assistantIPC.sendDARR(targetManager, self.__DARHandler(DAR[0]), DAR[1], timeoutTrigger = DAR[2], nRetry = DAR[3]) #Activate the requested function and Send FARR to the corresponding targetManager, attaching the requestID
            #Process FARs and send FARRs
            for FAR in self.assistantIPC.getFARs(targetManager):  #FAR:  [0]: functionID, [1]: functionParameters, [2]: requestID, [3]: timeoutTrigger_result, [4]: nRetry_result
                self.assistantIPC.sendFARR(targetManager, self.__FARHandler(FAR[0], FAR[1]), FAR[2], timeoutTrigger = FAR[3], nRetry = FAR[4]) #Activate the requested function and Send FARR to the corresponding targetManager, attaching the requestID
        handledTIDs = []
        for tID in self.IPCResultHandlers.keys():
            result = self.assistantIPC.getResult(tID)
            if ((result != "#NYR#") and (result != "#TIDDISPOSED#")): self.IPCResultHandlers[tID](self, result); handledTIDs.append(tID)
        for handledTID in handledTIDs: del self.IPCResultHandlers[handledTID]

        #Objects Control Processing ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        for fID in self.timerFunctions["ALL"].keys():
            if (self.timerFunctions["ALL"][fID].process(self) == False): del self.timerFunctions["ALL"][fID]
        for fID in self.timerFunctions[self.currentPage].keys():
            if (self.timerFunctions[self.currentPage][fID].process(self) == False): del self.timerFunctions[self.currentPage][fID]
        #Objects Control Processing END -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #Graphical Objects Control ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #Read the input events
        while (self.tkE_userInput.isInputAvailable() == True):
            event = self.tkE_userInput.getEvent()
            #If mouse has moved and 'self.searchGUIO' is true, find a GUIO at the current position
            if (event[0] == "<MOUSE_MOVED>") and (self.searchGUIO == True): self.__searchGUIO(event[1], event[2])
            if (self.selectedGUIO is not None): self.__resultInterpreter(self.currentPage, self.selectedGUIO, self.pages[self.currentPage][self.selectedGUIO].processUserInput(event))
            for subscribingGUIO in self.userInputSubscriber:
                if not((self.currentPage, self.selectedGUIO) == subscribingGUIO):
                    self.__resultInterpreter(subscribingGUIO[0], subscribingGUIO[1], self.pages[subscribingGUIO[0]][subscribingGUIO[1]].processUserInput(event))
                    

        #Objects Processing
        for objectName in self.pages[self.currentPage].keys(): self.__resultInterpreter(self.currentPage, objectName, self.pages[self.currentPage][objectName].process())
        #Graphical Objects Control END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        self.assistantIPC.patchIPCB_T() #Place near the end of the process, patch IPCB Data
        self.__calculateProcessTimers() #Calculate 'process timer averages' and control number of records
        return self.processRepeat
    #MANAGER MAIN PROCESS END -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #IPC HANDLING FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __DARHandler(self, dataName):
        if dataName in self.darHanlderDictionary.keys():
            if (type(self.darHanlderDictionary[dataName]) == types.BuiltinFunctionType): return self.darHanlderDictionary[dataName]()
            else:                                                                        return self.darHanlderDictionary[dataName]
        else: return None

    def __initializeFARs(self):
        def __FA_TESTFUNCTION(managerInstance, functionParams):
            try: return ("[GUI] FAR TEST SUCCESSFUL with Function Params: " + str(functionParams))
            except Exception as e: print("ERROR OCCURED WHILE PROCESSING FUNCTION ACTIVATION RESULT", e)
        self.farHanlderDictionary["FAR TEST"] = __FA_TESTFUNCTION

    def __FARHandler(self, functionID, functionParams):
        if functionID in self.farHanlderDictionary.keys():
            return self.farHanlderDictionary[functionID](self, functionParams)
    #IPC HANDLING FUNCTIONS END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #MANAGER PROCESS CONTROL ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def recordProcessTimers(self, t_loop, t_process, t_Tk_process):
        self.processTimersUpdateBuffer = (time.perf_counter_ns(), t_loop, t_process, t_Tk_process)
    def __calculateProcessTimers(self):
        if (self.processTimersUpdateBuffer != None):
            ipcProcessingTimes = self.assistantIPC.getProcessingTimes(mode = "returnAsValues")
            self.processTimers['records'].append({'recordTime': self.processTimersUpdateBuffer[0], 't_processLoop': self.processTimersUpdateBuffer[1],       't_process': self.processTimersUpdateBuffer[2],           't_processTk': self.processTimersUpdateBuffer[3],
                                                                                                   'ipcb_readTime':  ipcProcessingTimes['ipcb_r_readTime'],  'ipcb_readSize':  ipcProcessingTimes['ipcb_r_readSize'],  'ipcb_readRate':  ipcProcessingTimes['ipcb_r_readRate'],
                                                                                                   'ipcb_writeTime': ipcProcessingTimes['ipcb_t_writeTime'], 'ipcb_writeSize': ipcProcessingTimes['ipcb_t_writeSize'], 'ipcb_writeRate': ipcProcessingTimes['ipcb_t_writeRate']})
            recordLength = len(self.processTimers['records'])
            #Remove all the expired records
            while (True):
                recordTime = self.processTimers['records'][0]['recordTime']
                if (((time.perf_counter_ns() - recordTime) / 1e9) > self.processTimerAvgStandard): 
                    self.processTimers['records'].pop(0); recordLength -= 1
                    if (recordLength == 0): break;
                else: break;
            #Calculate the average
            if (recordLength > 0):
                t_processLoop_Sum = 0; t_process_Sum = 0; t_processTk_Sum = 0
                readTime_Sum      = 0; readSize_Sum  = 0; readRate_Sum    = 0
                writeTime_Sum     = 0; writeSize_Sum = 0; writeRate_Sum   = 0
                for i in range (recordLength):
                    t_processLoop_Sum += self.processTimers['records'][i]['t_processLoop']; t_process_Sum  += self.processTimers['records'][i]['t_process']; t_processTk_Sum    += self.processTimers['records'][i]['t_processTk']
                    readTime_Sum      += self.processTimers['records'][i]['ipcb_readTime']; readSize_Sum   += self.processTimers['records'][i]['ipcb_readSize']; readRate_Sum   += self.processTimers['records'][i]['ipcb_readRate']
                    writeTime_Sum     += self.processTimers['records'][i]['ipcb_writeTime']; writeSize_Sum += self.processTimers['records'][i]['ipcb_writeSize']; writeRate_Sum += self.processTimers['records'][i]['ipcb_writeRate']
                self.processTimers['t_processLoop_avg']  = t_processLoop_Sum / recordLength; self.processTimers['t_process_avg']      = t_process_Sum / recordLength; self.processTimers['t_processTk_avg']    = t_processTk_Sum   / recordLength
                self.processTimers['ipcb_readTime_avg']  = readTime_Sum      / recordLength; self.processTimers['ipcb_readSize_avg']  = readSize_Sum  / recordLength; self.processTimers['ipcb_readRate_avg']  = readRate_Sum      / recordLength
                self.processTimers['ipcb_writeTime_avg'] = writeTime_Sum     / recordLength; self.processTimers['ipcb_writeSize_avg'] = writeSize_Sum / recordLength; self.processTimers['ipcb_writeRate_avg'] = writeRate_Sum     / recordLength
                self.processTimers['nRecords'] = recordLength; self.processTimers['updated'] = True
            else: self.processTimers['nRecords'] = 0
    #MANAGER PROCESS CONTROL END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        




    #MANAGER INTERNAL FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __resultInterpreter(self, pageName, objectName, result):
        def readResult(result):
            #Check if it is a general function call first
            if (type(result) == tuple):
                functionName = result[0]
                functionParam = result[1:]
                if functionName in self.generalFunctions.keys(): self.generalFunctions[functionName](pageName, objectName, functionParam)
            else:
                #If is a general function call, but has no parameter
                if result in self.generalFunctions.keys(): self.generalFunctions[result](pageName, objectName)
                #If not is a general function call, check for a registered object functions list
                elif ((pageName + "-" + objectName + "-" + result) in self.objectFunctions.keys()):
                    functionContent = self.objectFunctions[pageName + "-" + objectName + "-" + result]
                    if (functionContent is None): pass
                    else:
                        if (type(functionContent) is tuple): functionContent[0](self, functionContent[1])
                        else: functionContent(self)

        if (result is not None):
            if (type(result) == str):
                readResult(result)
            elif (type(result) == tuple):
                for resElement in result:
                    readResult(resElement)


    def __searchGUIO(self, mouseX, mouseY):
        newSelectedGUIO = None
        #GUIO Searching
        for objectName in self.pages[self.currentPage].keys():
            if (newSelectedGUIO is None): newSelectedGUIO = objectName
            else:
                if (self.pages[self.currentPage][newSelectedGUIO].layer < self.pages[self.currentPage][objectName].layer):
                    if (self.pages[self.currentPage][objectName].xPos < mouseX) and (mouseX < self.pages[self.currentPage][objectName].xPos + self.pages[self.currentPage][objectName].width) and \
                       (self.pages[self.currentPage][objectName].yPos < mouseY) and (mouseY < self.pages[self.currentPage][objectName].yPos + self.pages[self.currentPage][objectName].height): newSelectedGUIO = objectName

        #Post-GUIOSearch Object Grab & Released Handling
        #[0] None    -> None   : Do nothing
        #[1] None    -> Object : Send "Hovered" Signal to the Object
        #[2] Object  -> None   : Send "Escape" Signal to the Object
        #[3] ObjectA -> ObjectB: Send "Hovered" Signal to the ObjectB and Send "Escape" Signal to the ObjectA
        #[4] ObjectA -> ObjectA: Do nothing
        if (self.selectedGUIO is None): #[1] None -> Object
            if (newSelectedGUIO is not None): 
                self.selectedGUIO = newSelectedGUIO
                self.__resultInterpreter(self.currentPage, self.selectedGUIO, self.pages[self.currentPage][self.selectedGUIO].processUserInput("HOVERED"))
        else: #[2] Object -> None or [3] ObjectA -> ObjectB
            if (newSelectedGUIO is None): #[2]: Object -> None
                self.__resultInterpreter(self.currentPage, self.selectedGUIO, self.pages[self.currentPage][self.selectedGUIO].processUserInput("ESCAPED"))
                self.selectedGUIO = None; self.selectedGUIOLayer = None;
            elif (newSelectedGUIO != self.selectedGUIO): # [3]: ObjectA -> ObjectB
                self.__resultInterpreter(self.currentPage, self.selectedGUIO, self.pages[self.currentPage][self.selectedGUIO].processUserInput("ESCAPED"))
                self.selectedGUIO = newSelectedGUIO
                self.__resultInterpreter(self.currentPage, self.selectedGUIO, self.pages[self.currentPage][self.selectedGUIO].processUserInput("HOVERED"))

    def __postObjectActivationSearch(self):
        mousePos = self.tkE_userInput.getMousePos()
        mouseX = mousePos[0]; mouseY = mousePos[1]
        newSelectedGUIO = None
        #GUIO Searching
        for objectName in self.pages[self.currentPage].keys():
            if (newSelectedGUIO is None): newSelectedGUIO = objectName
            else:
                if (self.pages[self.currentPage][newSelectedGUIO].layer < self.pages[self.currentPage][objectName].layer):
                    if (self.pages[self.currentPage][objectName].xPos < mouseX) and (mouseX < self.pages[self.currentPage][objectName].xPos + self.pages[self.currentPage][objectName].width) and \
                       (self.pages[self.currentPage][objectName].yPos < mouseY) and (mouseY < self.pages[self.currentPage][objectName].yPos + self.pages[self.currentPage][objectName].height): newSelectedGUIO = objectName
        self.selectedGUIO = newSelectedGUIO
        if (self.selectedGUIO is not None): self.__resultInterpreter(self.currentPage, self.selectedGUIO, self.pages[self.currentPage][self.selectedGUIO].processUserInput("HOVERED"))

    #Auxillary Functions --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __valueFormatter(self, value, originalUnit, outputMode = "string"):
        newValue = value; newUnit = originalUnit
        if (originalUnit == "ns"):
            if   (value > pow(1000, 3)): newValue = newValue / pow(1000, 3); newUnit = "s"
            elif (value > pow(1000, 2)): newValue = newValue / pow(1000, 2); newUnit = "ms"
            elif (value > pow(1000, 1)): newValue = newValue / pow(1000, 1); newUnit = "us"
        elif (originalUnit == "Bytes"):
            if   (value > pow(1024, 3)): newValue = newValue / pow(1024, 3); newUnit = "GB"
            elif (value > pow(1024, 2)): newValue = newValue / pow(1024, 2); newUnit = "MB"
            elif (value > pow(1024, 1)): newValue = newValue / pow(1024, 1); newUnit = "KB"
        elif (originalUnit == "Bytes/s"):
            if   (value > pow(1024, 3)): newValue = newValue / pow(1024, 3); newUnit = "GB/s"
            elif (value > pow(1024, 2)): newValue = newValue / pow(1024, 2); newUnit = "MB/s"
            elif (value > pow(1024, 1)): newValue = newValue / pow(1024, 1); newUnit = "KB/s"
        if   (outputMode == "string"): return ("{:.3f} {:s}".format(newValue, newUnit))
        elif (outputMode == "value"): return (newValue, newUnit)
    #Auxillary Functions END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #MANAGER INTERNAL FUNCTIONS END -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





    #General Object Call Functions ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __GUIOSearchOn(self, pageName, objectName): self.searchGUIO = True; mousePos = self.tkE_userInput.getMousePos(); self.__searchGUIO(mousePos[0], mousePos[1])
    def __GUIOSearchOff(self, pageName, objectName): self.searchGUIO = False
    def __addUserInputSubscriber(self, pageName, objectName): 
        if not((pageName, objectName) in self.userInputSubscriber): 
            self.userInputSubscriber.append((pageName, objectName))
    def __removeUserInputSubscriber(self, pageName, objectName):
        if ((pageName, objectName) in self.userInputSubscriber): 
            self.userInputSubscriber.remove((pageName, objectName))
    #General Object Call Functions END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------










    #Auxillary Classes ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    class __timerFunction():
        def __init__(self, function = None, interval = 1000, repeat = True):
            self.function = function
            self.interval = interval * 1e6
            self.lastActivatedTime = 0
            self.lastDelayTime = 0
            self.repeat = repeat

        def process(self, managerInstance):
            currentTime = time.perf_counter_ns()
            timeElapsed = currentTime - self.lastActivatedTime
            if ((timeElapsed + self.lastDelayTime) > self.interval):
                self.lastActivatedTime = currentTime
                self.lastDelayTime = (timeElapsed + self.lastDelayTime) % self.interval
                self.function(managerInstance)
            return self.repeat

    #Auxillary Classes END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------










