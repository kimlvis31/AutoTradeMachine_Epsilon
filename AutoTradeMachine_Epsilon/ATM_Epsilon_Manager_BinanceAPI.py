from ATM_Epsilon_Manager_IPC import assistant_IPC

from pympler import asizeof
import time
import ccxt
import binance
import pythonBinance_enums
import os
import time
import types
import pprint
import ciso8601
from datetime import datetime
import math

MANAGERNAME = "BINANCEAPI"

path_PROJECT = os.path.dirname(os.path.realpath(__file__))
path_BINANCEAPI = os.path.join(path_PROJECT + r"\data\binanceAPI")

class manager_BinanceAPI:
    #MANAGER INITIALIZATION -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __init__(self, programLogger, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T):
        #Create Local Instance of Program Data Logger
        self.programLogger = programLogger
        self.programLogger.clearPMessages()
        
        #Send Initialization Start Message
        self.programLogger.printPMessage("INITIALIZING {:s} MANAGER...".format(MANAGERNAME))

        #Process Control Variables
        self.processRepeat = True
        self.processTimersUpdateBuffer = None
        self.processTimers = {'updated': False, 'records': list(), 't_processLoop_avg':  0, 't_process_avg':      0, 
                                                                   'ipcb_readTime_avg':  0, 'ipcb_readSize_avg':  0, 'ipcb_readRate_avg':  0,
                                                                   'ipcb_writeTime_avg': 0, 'ipcb_writeSize_avg': 0, 'ipcb_writeRate_avg': 0, 'nRecords': 0}
        self.processTimerAvgStandard = 1

        #Program Managers List Read
        self.atm_Managers = atm_Managers.copy(); self.atm_Managers.remove(MANAGERNAME)

        #IPC Assistant Initialization
        self.assistantIPC = assistant_IPC(programLogger, MANAGERNAME, self.atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T)
        self.darHanlderDictionary = {"DAR TEST": "[BINANCE API] DAR TEST SUCCESSFUL", "ATMMANAGERS": self.atm_Managers, "PTIMERS": self.processTimers, "PTIMERS_LASTRECORD": None, "PTIMERS_AVGSTANDARD": self.processTimerAvgStandard}
        self.farHanlderDictionary = dict(); self.__initializeFARs()
        self.IPCResultHandlers = dict()
        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_0_IPC ASSISTANT INITIALIZED"); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("IPC ASSISTANT INITIALIZED") #Process Status Report

        #API Management Data ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.ccxtBinance = ccxt.binance({'ratelimit': 1000})
        self.clientBinance = binance.Client()

        self.ccxtBinance_accountInfo = dict()
        self.connection_Status_BINANCE = False; self.connection_Market_LastCheckedTime  = time.time()
        self.connection_Status_ACCOUNT = False; self.connection_Account_LastCheckedTime = time.time()
        self.marketData = None
        
        self.ccxtBinance_spotWallet   = {'info': None, 'balances': dict(), 'updateTime': None}
        self.verifiedSpotSymbols = None
        self.ccxtBinance_futureWallet = {'info': None, 'balances': dict(), 'updateTime': None}
        
        #Initialize and Start Binance Threaded Websocket Manager Variables
        self.clientBinance_WebSocket = {'TWM': binance.ThreadedWebsocketManager(), 'streamNames': list(), 'subscriptionAppendQueue': list(), 'streamingSymbols': list()}
        self.clientBinance_WebSocket['TWM'].start()
        self.idToAPISymbol = {'SPOT': dict(), 'USDS-M': {'PERP': dict(), 'CQ': dict(), 'NQ': dict()}, 'COIN-M': {'PERP': dict(), 'CQ': dict(), 'NQ': dict()}}

        self.currnetHourRaw1ms = dict()
        self.lastHourRaw1ms = dict()
        self.retreiveLastHour = False

        #[0]: Open Time (int), [1]: Open Price (float), [2]: High Price (float), [3]: Low Price (float), [4]: Close Price (float), [5]: Traded Volume (float), [6]: Close Time (int), 
        #[7]: Quote Asset Volume (float), [8]: Number of Trade (int), [9]: Taker Buy Base Asset Volume (float), [10]: Taker Buy Quote Asset Volume (float)
        def klineStreamHandler_SPOT(msg):
            msgType = msg['e']
            if (msgType == 'kline'):
                symbolAPI = self.idToAPISymbol['SPOT'][msg['s']]
                kline = [msg['k']['t'], msg['k']['o'], msg['k']['h'], msg['k']['l'], msg['k']['c'], msg['k']['v'], msg['k']['T'], msg['k']['q'], msg['k']['n'], msg['k']['V'], msg['k']['Q'], 1]
                currentMinute = int((msg['k']['t'] / 60000) % 60)
                if   ((currentMinute == 0) and (len(self.currnetHourRaw1ms.keys()) == 60)): self.currnetHourRaw1ms[symbolAPI].clear()
                elif ((msg['k']['x'] == True) and (currentMinute == 59)): 
                    self.lastHourRaw1ms[symbolAPI] = self.currnetHourRaw1ms[symbolAPI].copy()
                    tID = self.assistantIPC.sendFAR("DATAMANAGEMENT", "RECORD_LASTHOUR_RAW1M", ("BINANCE", symbolAPI, self.lastHourRaw1ms[symbolAPI]))
                    def klineStreamHandler_SPOT_FARHandler(manager, result): pass
                    self.IPCResultHandlers[tID] = klineStreamHandler_SPOT_FARHandler
                self.currnetHourRaw1ms[symbolAPI][currentMinute] = kline

        def klineStreamHandler_USDS_M(msg):
            msgType = msg['e']
            if (msgType == 'continuous_kline'):
                contractType = msg['ct']
                if (contractType == "PERPETUAL"):         symbolAPI = self.idToAPISymbol['USDS-M']['PERP'][msg['ps']]
                elif (contractType == "CURRENT_QUARTER"): symbolAPI = self.idToAPISymbol['USDS-M']['CQ'][msg['ps']]
                elif (contractType == "NEXT_QUARTER"):    symbolAPI = self.idToAPISymbol['USDS-M']['NQ'][msg['ps']]
                kline = [msg['k']['t'], msg['k']['o'], msg['k']['h'], msg['k']['l'], msg['k']['c'], msg['k']['v'], msg['k']['T'], msg['k']['q'], msg['k']['n'], msg['k']['V'], msg['k']['Q'], 1]
                currentMinute = int((msg['k']['t'] / 60000) % 60)
                if   ((currentMinute == 0) and (len(self.currnetHourRaw1ms.keys()) == 60)): self.currnetHourRaw1ms[symbolAPI].clear()
                elif ((msg['k']['x'] == True) and (currentMinute == 59)): 
                    self.lastHourRaw1ms[symbolAPI] = self.currnetHourRaw1ms[symbolAPI].copy()
                    tID = self.assistantIPC.sendFAR("DATAMANAGEMENT", "RECORD_LASTHOUR_RAW1M", ("BINANCE", symbolAPI, self.lastHourRaw1ms[symbolAPI]))
                    def klineStreamHandler_SPOT_FARHandler(manager, result): pass
                    self.IPCResultHandlers[tID] = klineStreamHandler_SPOT_FARHandler
                self.currnetHourRaw1ms[symbolAPI][currentMinute] = kline

        def klineStreamHandler_COIN_M(msg):
            msgType = msg['e']
            if (msgType == 'continuous_kline'):
                contractType = msg['ct']
                if (contractType == "PERPETUAL"):         symbolAPI = self.idToAPISymbol['COIN-M']['PERP'][msg['ps']]
                elif (contractType == "CURRENT_QUARTER"): symbolAPI = self.idToAPISymbol['COIN-M']['CQ'][msg['ps']]
                elif (contractType == "NEXT_QUARTER"):    symbolAPI = self.idToAPISymbol['COIN-M']['NQ'][msg['ps']]
                kline = [msg['k']['t'], msg['k']['o'], msg['k']['h'], msg['k']['l'], msg['k']['c'], msg['k']['v'], msg['k']['T'], msg['k']['q'], msg['k']['n'], msg['k']['V'], msg['k']['Q'], 1]
                currentMinute = int((msg['k']['t'] / 60000) % 60)
                if   ((currentMinute == 0) and (len(self.currnetHourRaw1ms.keys()) == 60)): self.currnetHourRaw1ms[symbolAPI].clear()
                elif ((msg['k']['x'] == True) and (currentMinute == 59)): 
                    self.lastHourRaw1ms[symbolAPI] = self.currnetHourRaw1ms[symbolAPI].copy()
                    tID = self.assistantIPC.sendFAR("DATAMANAGEMENT", "RECORD_LASTHOUR_RAW1M", ("BINANCE", symbolAPI, self.lastHourRaw1ms[symbolAPI]))
                    def klineStreamHandler_SPOT_FARHandler(manager, result): pass
                    self.IPCResultHandlers[tID] = klineStreamHandler_SPOT_FARHandler
                self.currnetHourRaw1ms[symbolAPI][currentMinute] = kline

        #Pre-Registered API Keys
        self.PRKeys = dict()
        self.darHanlderDictionary["PRKeyList"] = self.PRKeys.keys()

        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_10_API MANAGEMENT DATA INITIALIZED"); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("API MANAGEMENT DATA INITIALIZED") #Process Status Report

        #Initial Market Connection Check
        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_15_CHECKING BINANCE MARKET CONNECTION..."); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("Checking BINANCE Market Connection...") #Process Status Report
        self.connection_Market_LastCheckedTime = time.time()
        self.connection_Account_LastCheckedTime = time.time()
        self.assistantIPC.sendPRD("ACCOUNTCONNECTIONSTATUS", (self.connection_Status_ACCOUNT, self.connection_Account_LastCheckedTime))

        #Connection Check
        try:
            self.ccxtBinance.fetch_ticker("BTC/USDT")
            self.connection_Status_BINANCE = True
            self.assistantIPC.sendPRD("MARKETCONNECTIONSTATUS", (self.connection_Status_ACCOUNT, self.connection_Market_LastCheckedTime))
            self.programLogger.printPMessage("BINANCE Market Connection Check Successful! [{:s}]".format(time.ctime(self.connection_Market_LastCheckedTime)))
            self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_20_LOADING BINANCE MARKET DATA"); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("Loading BINANCE Market Data...") #Process Status Report
            self.marketData = self.ccxtBinance.load_markets()
            self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_25_BINANCE MARKET DATA LOAD COMPLETE"); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("BINANCE Market Data Loaded!") #Process Status Report
            monthNow = datetime.now().month
            for assetDictKey in self.marketData.keys():
                if   (self.marketData[assetDictKey]['spot'] == True):                                                        
                    self.marketData[assetDictKey]['marketType'] = "SPOT"
                    if (self.marketData[assetDictKey]['active'] == True): self.idToAPISymbol['SPOT'][self.marketData[assetDictKey]['id']] = assetDictKey
                elif ((self.marketData[assetDictKey]['future'] == True) or (self.marketData[assetDictKey]['swap'] == True)): 
                    if (self.marketData[assetDictKey]['inverse'] == True):                                                   
                        self.marketData[assetDictKey]['marketType'] = "COIN-M"
                        if (self.marketData[assetDictKey]['active'] == True):
                            if ("-" in assetDictKey):
                                symbolSplit = assetDictKey.split("-")
                                symbolQuarter = int(symbolSplit[1][2:4]) / 3
                                if (math.ceil(monthNow/3) == symbolQuarter): self.idToAPISymbol['COIN-M']['CQ'][self.marketData[assetDictKey]['id'].split("_")[0]]   = assetDictKey
                                else:                                        self.idToAPISymbol['COIN-M']['NQ'][self.marketData[assetDictKey]['id'].split("_")[0]]   = assetDictKey
                            else:                                            self.idToAPISymbol['COIN-M']['PERP'][self.marketData[assetDictKey]['id'].split("_")[0]] = assetDictKey
                    else:                                                                                                        
                        self.marketData[assetDictKey]['marketType'] = "USDS-M"
                        if (self.marketData[assetDictKey]['active'] == True):
                            if ("-" in assetDictKey):
                                symbolSplit = assetDictKey.split("-")
                                symbolQuarter = int(symbolSplit[1][2:4]) / 3
                                if (math.ceil(monthNow/3) == symbolQuarter): self.idToAPISymbol['USDS-M']['CQ'][self.marketData[assetDictKey]['id'].split("_")[0]] = assetDictKey
                                else:                                        self.idToAPISymbol['USDS-M']['NQ'][self.marketData[assetDictKey]['id'].split("_")[0]] = assetDictKey
                            else:                                            self.idToAPISymbol['USDS-M']['PERP'][self.marketData[assetDictKey]['id']]             = assetDictKey
        except Exception as e: 
            self.programLogger.printPMessage("BINANCE MARKET Connection Check Failed [{:s}] <{:s}>".format(time.ctime(self.connection_Market_LastCheckedTime), str(e)))
            self.assistantIPC.sendPRD("MARKETCONNECTIONSTATUS", (self.connection_Status_BINANCE, self.connection_Market_LastCheckedTime, e))
        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_30_BINANCE MARKET CONNECTION SUCCESSFUL"); self.assistantIPC.patchIPCB_T() #Process Status Report

        #For project demonstration purposes, only Binance-Futures BTC/USDT Data is handled
        marketData = self.marketData
        self.marketData    = dict()
        self.idToAPISymbol = {'SPOT': dict(), 'USDS-M': {'PERP': dict(), 'CQ': dict(), 'NQ': dict()}, 'COIN-M': {'PERP': dict(), 'CQ': dict(), 'NQ': dict()}}
        for assetDictKey in marketData:
            if assetDictKey == 'BTC/USDT:USDT':
                self.marketData[assetDictKey] = marketData[assetDictKey]
                self.idToAPISymbol['USDS-M']['PERP'][self.marketData[assetDictKey]['id']] = assetDictKey


        #Market Registration Timestamp Check
        def __checkNewMRGT(self, symbol, counter, totalLen):
            self.programLogger.printPMessage("Checking Market Registration Timestamp '{:s}'...".format(symbol))
            counter += 1
            e1mStamp = "None"
            try:
                mrktRegTimeStamp_File = open(mrktRegTimeStamp_File_Dir, 'a')
                if (self.marketData[symbol]['active'] == True): 
                    self.marketData[symbol]['mrktRegTimeStamp'] = self.__checkMrktRegTimeStamp(symbol)
                    mrktRegTimeStamp_File.write("\n{:s},{:d}".format(symbol, self.marketData[symbol]['mrktRegTimeStamp']))
                else:                                                    
                    self.marketData[symbol]['mrktRegTimeStamp'] = None
                    mrktRegTimeStamp_File.write("\n{:s},None".format(symbol))
                e1mStamp = str(self.marketData[symbol]['mrktRegTimeStamp'])
                mrktRegTimeStamp_File.close()
            except Exception as e: self.programLogger.printPMessage("An error occured while attempting to check Market Registration TimeStamp for '{:s}' <{:s}>".format(symbol, str(e)))
            self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_{:d}_CHECKING MARKET REGISTRATION TIMESTAMP... [{:d} / {:d}]".format(int(counter / totalLen * 10 + 30), counter, totalLen)); self.assistantIPC.patchIPCB_T()
            self.programLogger.printPMessage("Market Registration Timestamp Check for '{:s}' Complete: <{:s}> [{:d} / {:d}]".format(symbol, e1mStamp, counter, totalLen))
            return counter

        if (self.connection_Status_BINANCE == True):
            self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_30_CHECKING MARKET REGISTRATION TIMESTAMP..."); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("Check Market Registration Timestamp...") #Process Status Report
            mrktRegTimeStamp_File_Dir = os.path.join(path_BINANCEAPI, 'mrktRegTStamp.bin')
            if (os.path.isfile(mrktRegTimeStamp_File_Dir)): #If 'mrktRegTimeStamp.bin' File Does Exist
                mrktRegTimeStamp_File = open(mrktRegTimeStamp_File_Dir)
                mrktRegTimeStamps = mrktRegTimeStamp_File.readlines()
                symbolsChecklist = list(self.marketData.keys())
                marketSymbolsLen = len(symbolsChecklist)
                for mrktRegTimeStamp in mrktRegTimeStamps:
                    try:
                        if (mrktRegTimeStamp != "\n"):
                            mrktRegTimeStampContents = mrktRegTimeStamp.strip().split(",")
                            symbol = mrktRegTimeStampContents[0]; timeStamp = mrktRegTimeStampContents[1]
                            if symbol in symbolsChecklist:
                                if (timeStamp == "None"): self.marketData[symbol]['mrktRegTimeStamp'] = None
                                else:                     self.marketData[symbol]['mrktRegTimeStamp'] = int(timeStamp)
                                symbolsChecklist.remove(symbol)
                    except Exception as e: self.programLogger.printPMessage("An error occured while reading 'mrktRegTStamp' dataline: <{:s}> <{:s}>".format(str(mrktRegTimeStamp), str(e)))
                mrktRegTimeStamp_File.close()
                totalLen = marketSymbolsLen; counter = totalLen - len(symbolsChecklist)
                for uncheckedSymbol in symbolsChecklist: __checkNewMRGT(self, uncheckedSymbol, counter, totalLen); counter += 1

            else: #If 'mrktRegTimeStamp.bin' File Does Not Exist
                mrktRegTimeStamp_File = open(mrktRegTimeStamp_File_Dir, 'w'); mrktRegTimeStamp_File.close()
                totalLen = len(self.marketData.keys()); counter = 0
                for assetDictKey in self.marketData.keys(): __checkNewMRGT(self, assetDictKey, counter, totalLen); counter += 1

        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_40_MARKET REGISTRATION TIMESTAMP CHECK COMPLETE!"); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("Market Registration Timestamp Check Complete!") #Process Status Report
        self.assistantIPC.sendPRD("MARKET", self.marketData);
        #API Management Data END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #Timer Functions --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_35_INITIALIZING TIMER FUNCTIONS..."); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("INITIALIZING TIMER FUNCTIONS") #Process Status Report
        #Timer Function Assignments
        self.timerFunctions = dict()

        #Check market connection every second
        def timerFunction_CHECKMARKETCONNECTION(manager):
            manager.connection_Market_LastCheckedTime = time.time()
            try:
                self.ccxtBinance.fetch_ticker("BTC/USDT")
                if (manager.connection_Status_BINANCE == False):
                    manager.connection_Status_BINANCE = True
                    manager.marketData = manager.ccxtBinance.load_markets(); manager.assistantIPC.sendPRD("MARKET", manager.marketData);
                manager.assistantIPC.sendPRD("MARKETCONNECTIONSTATUS", (manager.connection_Status_BINANCE, manager.connection_Market_LastCheckedTime))
                manager.programLogger.printPMessage("BINANCE Market Connection Check Successful! [{:s}]".format(time.ctime(manager.connection_Market_LastCheckedTime)), termPrint = False)
            except Exception as e:
                manager.marketData = None
                manager.connection_Status_BINANCE = False; manager.assistantIPC.sendPRD("MARKETCONNECTIONSTATUS",  (manager.connection_Status_BINANCE, manager.connection_Market_LastCheckedTime, e))
                manager.connection_Status_ACCOUNT = False; manager.assistantIPC.sendPRD("ACCOUNTCONNECTIONSTATUS", (manager.connection_Status_ACCOUNT, manager.connection_Market_LastCheckedTime, e))
                manager.programLogger.printPMessage("BINANCE Market Connection Check Failed [{:s}]".format(time.ctime(manager.connection_Market_LastCheckedTime)), termPrint = False)
        self.timerFunctions["CHECKMARKETCONNECTION"] = self.__timerFunction(function = timerFunction_CHECKMARKETCONNECTION, interval = 1000)

        #If account is connected, check account connection every 5 seconds and update balance information
        def timerFunction_CHECKACCOUNTCONNECTION(manager):
            manager.connection_Account_LastCheckedTime = time.time()
            if (manager.connection_Status_ACCOUNT == True):
                try:
                    balance_spot = manager.ccxtBinance.fetch_balance()
                    balance_futures = manager.ccxtBinance.fetch_balance(params = {'type': "future"})
                    #Localize data from fetch_balance
                    for symbol in self.verifiedSpotSymbols: self.ccxtBinance_spotWallet['balances'][symbol] = balance_spot[symbol]
                    del balance_spot['info']['balances']
                    self.ccxtBinance_spotWallet['info']       = balance_spot['info']
                    self.ccxtBinance_spotWallet['updateTime'] = balance_spot['timestamp']
                    for key in balance_futures.keys():
                        if (key != 'info') and (key != 'timestamp') and (key != 'datetime') and (key != 'free') and (key != 'used') and (key != 'total'): self.ccxtBinance_futureWallet['balances'][key] = balance_futures[key]
                    self.ccxtBinance_futureWallet['info']       = balance_futures['info']
                    self.ccxtBinance_futureWallet['updateTime'] = balance_futures['timestamp']
                    #Announce Connection Status & Check Time
                    manager.assistantIPC.sendPRD("ACCOUNTCONNECTIONSTATUS", (manager.connection_Status_ACCOUNT, manager.connection_Account_LastCheckedTime))
                    manager.assistantIPC.sendPRD("SPOTWALLET",     self.ccxtBinance_spotWallet)
                    manager.assistantIPC.sendPRD("FUTURESWALLET", self.ccxtBinance_futureWallet)
                    manager.programLogger.printPMessage("Account Connection Check Successful! [{:s}]".format(time.ctime(manager.connection_Account_LastCheckedTime)), termPrint = False)
                except Exception as e:
                    manager.connection_Status_ACCOUNT = False
                    manager.assistantIPC.sendPRD("ACCOUNTCONNECTIONSTATUS", (manager.connection_Status_ACCOUNT, manager.connection_Account_LastCheckedTime, e))
                    manager.programLogger.printPMessage("Account Connection Check Failed [{:s}]".format(time.ctime(manager.connection_Account_LastCheckedTime)), termPrint = False)
            return True
        self.timerFunctions["CHECKACCOUNTCONNECTION"] = self.__timerFunction(function = timerFunction_CHECKACCOUNTCONNECTION, interval = 5000)

        #Add websocket 3 kline subscriptions every second
        """ Removed for project demonstration stability
        #Add websocket 3 kline subscriptions every second
        def timerFunction_ADDWBKLINESUBSCRIPTION(manager):
            if (0 < len(manager.clientBinance_WebSocket['subscriptionAppendQueue'])):
                if (manager.connection_Status_BINANCE == True):
                    for i in range (min([3, len(manager.clientBinance_WebSocket['subscriptionAppendQueue'])])):
                        symbolAPI = manager.clientBinance_WebSocket['subscriptionAppendQueue'].pop(0)
                        marketType = manager.marketData[symbolAPI]['marketType']
                        if   (marketType == "SPOT"):   manager.__addKlineStream(symbol = symbolAPI, handlerFunction = klineStreamHandler_SPOT)
                        elif (marketType == "USDS-M"): manager.__addKlineStream(symbol = symbolAPI, handlerFunction = klineStreamHandler_USDS_M)
                        elif (marketType == "COIN-M"): manager.__addKlineStream(symbol = symbolAPI, handlerFunction = klineStreamHandler_COIN_M)
                return True
            else: return False
        self.timerFunctions["ADDWBKLINESUBSCRIPTION"] = self.__timerFunction(function = timerFunction_ADDWBKLINESUBSCRIPTION, interval = 1000)
        """
        
        def timerFunction_ANNOUNCURRENTHOURRAW1MS(manager):
            pass
            for symbol in self.currnetHourRaw1ms.keys():
                print("<{:s}> <{:.3f} KBytes>".format(symbol, asizeof.asizeof(self.currnetHourRaw1ms[symbol])/1024))
                for minute in self.currnetHourRaw1ms[symbol].keys():
                    print("   [{:d}]: {:s}".format(minute, str(self.currnetHourRaw1ms[symbol][minute])))
            print("\n\n\n")
        self.timerFunctions["ANNOUNCURRENTHOURRAW1MS"] = self.__timerFunction(function = timerFunction_ANNOUNCURRENTHOURRAW1MS, interval = 1000)
        
        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_40_TIMER FUNCTION INITIALIZATION COMPLETE!"); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("TIMER FUNCTIONS INITIALIZATION COMPLETE") #Process Status Report
        #Timer Functions END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #Send Initialization End Message
        self.programLogger.printPMessage("{:s} MANAGER INITIALIZATION COMPLETE!".format(MANAGERNAME))
        self.assistantIPC.sendPRD("PROC_STATUS", "ACTIVE", nRetry = "INF"); self.assistantIPC.patchIPCB_T() #Process Status Report
    #MANAGER INITIALIZATION END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        

        
    #MANAGER MAIN PROCESS ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def process(self):
        #IPC Control ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.assistantIPC.readIPCB_R() #Place at the beginning of the process, read IPCB Data
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

        #Timer Functions Processing
        for fID in self.timerFunctions.keys():
            if (self.timerFunctions[fID].process(self) == False): del self.timerFunctions[fID]

        self.assistantIPC.patchIPCB_T() #Place near the end of the process, patch IPCB Data
        self.__calculateProcessTimers() #Calculate 'process timer averages' and control number of records

        return self.processRepeat
    #MANAGER MAIN PROCESS END -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #MANAGER PROCESS CONTROL ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def recordProcessTimers(self, t_loop, t_process):
        self.processTimersUpdateBuffer = (time.perf_counter_ns(), t_loop, t_process)
    def __calculateProcessTimers(self):
        if (self.processTimersUpdateBuffer != None):
            ipcProcessingTimes = self.assistantIPC.getProcessingTimes(mode = "returnAsValues")
            self.processTimers['records'].append({'recordTime': self.processTimersUpdateBuffer[0], 't_processLoop': self.processTimersUpdateBuffer[1],       't_process': self.processTimersUpdateBuffer[2],
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
                t_processLoop_Sum = 0; t_process_Sum = 0
                readTime_Sum      = 0; readSize_Sum  = 0; readRate_Sum    = 0
                writeTime_Sum     = 0; writeSize_Sum = 0; writeRate_Sum   = 0
                for i in range (recordLength):
                    t_processLoop_Sum += self.processTimers['records'][i]['t_processLoop']; t_process_Sum  += self.processTimers['records'][i]['t_process']
                    readTime_Sum      += self.processTimers['records'][i]['ipcb_readTime']; readSize_Sum   += self.processTimers['records'][i]['ipcb_readSize']; readRate_Sum   += self.processTimers['records'][i]['ipcb_readRate']
                    writeTime_Sum     += self.processTimers['records'][i]['ipcb_writeTime']; writeSize_Sum += self.processTimers['records'][i]['ipcb_writeSize']; writeRate_Sum += self.processTimers['records'][i]['ipcb_writeRate']
                self.processTimers['t_processLoop_avg']  = t_processLoop_Sum / recordLength; self.processTimers['t_process_avg']      = t_process_Sum / recordLength
                self.processTimers['ipcb_readTime_avg']  = readTime_Sum      / recordLength; self.processTimers['ipcb_readSize_avg']  = readSize_Sum  / recordLength; self.processTimers['ipcb_readRate_avg']  = readRate_Sum  / recordLength
                self.processTimers['ipcb_writeTime_avg'] = writeTime_Sum     / recordLength; self.processTimers['ipcb_writeSize_avg'] = writeSize_Sum / recordLength; self.processTimers['ipcb_writeRate_avg'] = writeRate_Sum / recordLength
                self.processTimers['nRecords'] = recordLength; self.processTimers['updated'] = True
            else: self.processTimers['nRecords'] = 0
    #MANAGER PROCESS CONTROL END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #IPC HANDLING FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __DARHandler(self, dataName):
        if dataName in self.darHanlderDictionary.keys():
            if (type(self.darHanlderDictionary[dataName]) == types.BuiltinFunctionType): return self.darHanlderDictionary[dataName]()
            else:                                                                        return self.darHanlderDictionary[dataName]
        else: return None

    def __initializeFARs(self):
        def __FA_TESTFUNCTION(managerInstance, functionParams):
            try: return ("[BINANCE API] FAR TEST SUCCESSFUL with Function Params: " + str(functionParams))
            except Exception as e: print("ERROR OCCURED WHILE PROCESSING FUNCTION ACTIVATION RESULT", e)
        self.farHanlderDictionary["FAR TEST"] = __FA_TESTFUNCTION
        def __FA_GET_PRD(managerInstance, functionParams):
            prdFromManager = managerInstance.assistantIPC.getPRD(functionParams[0]).copy()
            for key in prdFromManager.keys():
                stringVer = str(prdFromManager[key])
                if len(stringVer) > functionParams[1]: prdFromManager[key] = stringVer[:functionParams[1]]
            return prdFromManager
        self.farHanlderDictionary["GET_PRD"] = __FA_GET_PRD
        def __FA_GET_IPCLOG(managerInstance, functionParams):
            return managerInstance.assistantIPC.getProcessLog()
        self.farHanlderDictionary["GET_IPCLOG"] = __FA_GET_IPCLOG
        def __FA_EDIT_PTIMERAVGSTANDARD(managerInstance, functionParams):
            self.processTimerAvgStandard = functionParams; return self.processTimerAvgStandard
        self.farHanlderDictionary["EDIT_PTIMERAVGSTANDARD"] = __FA_EDIT_PTIMERAVGSTANDARD
        def __FA_GET_PTIMER_AVG(managerInstance, functionParams):
            returnDict = {'t_processLoop_avg':  self.processTimers['t_processLoop_avg'], 
                          't_process_avg':      self.processTimers['t_process_avg'], 
                          'ipcb_readTime_avg':  self.processTimers['ipcb_readTime_avg'], 
                          'ipcb_readSize_avg':  self.processTimers['ipcb_readSize_avg'],
                          'ipcb_readRate_avg':  self.processTimers['ipcb_readRate_avg'], 
                          'ipcb_writeTime_avg': self.processTimers['ipcb_writeTime_avg'], 
                          'ipcb_writeSize_avg': self.processTimers['ipcb_writeSize_avg'], 
                          'ipcb_writeRate_avg': self.processTimers['ipcb_writeRate_avg'], 
                          'nRecords':           self.processTimers['nRecords']}
            return returnDict
        self.farHanlderDictionary["GET_PTIMERS_AVG"] = __FA_GET_PTIMER_AVG
        def __FA_GET_PTIMER_LAST(managerInstance, functionParams):
            self.processTimers['updated'] = False
            if (0 < self.processTimers['nRecords']): return self.processTimers['records'][-1]
            else                                   : return None
        self.farHanlderDictionary["GET_PTIMERS_LAST"] = __FA_GET_PTIMER_LAST
        def __FA_GET_IPC_TIDAVAILABILITY(managerInstance, functionParams):
            return (len(managerInstance.assistantIPC.TID_Availables), managerInstance.assistantIPC.TIDIssueLimit)
        self.farHanlderDictionary["GET_IPC_TIDAVAILABILITY"] = __FA_GET_IPC_TIDAVAILABILITY
        def __FA_GET_PLOG(managerInstance, functionParams):
            return self.programLogger.getPMessages()
        self.farHanlderDictionary["GET_PLOG"] = __FA_GET_PLOG




        #functionParams - [0]: API Key (Type: str-64), [1]: Secret Key (Type: str-64)
        def __FA_CONNECTAPI_byKey(managerInstance, functionParams):
            if (managerInstance.connection_Status_BINANCE == True):
                connectionResult = managerInstance.__connectAPI(functionParams[0], functionParams[1])
                return connectionResult
            else: return (False, time.time(), "market not conencted")
        self.farHanlderDictionary["CONNECTAPI_byKEY"] = __FA_CONNECTAPI_byKey

        #functionParams - [0]: PRID(Type: str), [1]: PRID Password(Type: str)
        def __FA_CONNECTAPI_byPRID(managerInstance, functionParams):
            if (managerInstance.connection_Status_BINANCE == True):
                prID = functionParams[0]; password = functionParams[1]
                if (password == managerInstance.PRKeys[prID][2]):
                    connectionResult = managerInstance.__connectAPI(managerInstance.PRKeys[prID][0], managerInstance.PRKeys[prID][1])
                    return connectionResult
                else: return (False, time.time(), "incorred password")
            else: return (False, time.time(), "market not conencted")
        self.farHanlderDictionary["CONNECTAPI_byPRID"] = __FA_CONNECTAPI_byPRID

        #functionParams - None
        def __FA_DISCONNECTAPI(managerInstance, functionParams):
            disconnectionResult = managerInstance.__disconnectAPI()
            return disconnectionResult
        self.farHanlderDictionary["DISCONNECTAPI"] = __FA_DISCONNECTAPI

        #functionParams - AssetSymbol(Type: str)
        def __FA_FETCH_TICKER(managerInstance, functionParams):
            return managerInstance.ccxtBinance.fetch_ticker(functionParams)
        self.farHanlderDictionary["FETCH_TICKER"] = __FA_FETCH_TICKER

        #Returns a day worth of '1m' interval klines of the specified asset
        #functionParams - [0]: AssetSymbol(Type: str), [1]: Since(Type:int, in seconds since epoch)
        def __FA_FETCH_KLINES(managerInstance, functionParams):
            if (managerInstance.marketData != None):
                if (managerInstance.connection_Status_BINANCE == True):
                    market = managerInstance.marketData[functionParams[0]]['marketType']; symbol_client = managerInstance.marketData[functionParams[0]]['id']
                    timeStamp_dayBegin = int(functionParams[1] / 86400) * 86400
                    timeStamp_todayBegin = int(time.time() / 86400) * 86400
                    #Receive Kline data from Binance
                    if   (market == "SPOT"):
                        klines1 = managerInstance.clientBinance.get_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = timeStamp_dayBegin * 1000, end_str = (timeStamp_dayBegin + 43200) * 1000, limit = 720)
                        klines2 = managerInstance.clientBinance.get_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = (timeStamp_dayBegin + 43200) * 1000, end_str = (timeStamp_dayBegin + 86400) * 1000, limit = 720)
                    elif (market == "USDS-M"):
                        klines1 = managerInstance.clientBinance.futures_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = timeStamp_dayBegin * 1000, end_str = (timeStamp_dayBegin + 43200) * 1000, limit = 720)
                        klines2 = managerInstance.clientBinance.futures_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = (timeStamp_dayBegin + 43200) * 1000, end_str = (timeStamp_dayBegin + 86400) * 1000, limit = 720)
                    elif (market == "COIN-M"): 
                        klines1 = managerInstance.clientBinance.futures_coin_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, startTime = (timeStamp_dayBegin -    60) * 1000, endTime = (timeStamp_dayBegin + 43140) * 1000, limit = 720)
                        klines2 = managerInstance.clientBinance.futures_coin_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, startTime = (timeStamp_dayBegin + 43140) * 1000, endTime = (timeStamp_dayBegin + 86340) * 1000, limit = 720)
                    klinesSum = klines1 + klines2
                    #Analyze Received Contents
                    firstDataTimestamp = managerInstance.marketData[functionParams[0]]['mrktRegTimeStamp'] / 1000
                    if (timeStamp_dayBegin < firstDataTimestamp): expectedDataLength = int(1440 - (firstDataTimestamp - timeStamp_dayBegin) / 60)
                    else: expectedDataLength = 1440
                    if (len(klinesSum) == expectedDataLength): #All of the data has been received successfully
                        for i in range (len(klinesSum)): klinesSum[i] += [1]
                        verificationCode = "C"
                    else: #The possible cases are: [1]: The current date and the data date are the same, [2]: Some data are missing
                        if (timeStamp_dayBegin == int(time.time() / 86400) * 86400): #The data from today is inevitably incomplete
                            for i in range (len(klinesSum)): klinesSum[i] += [1]
                            verificationCode = "i"
                        else: #There are some missing data
                            klineReadCounter = 0; newKlines = list()
                            for i in range (expectedDataLength): 
                                expectedTimeStamp = (timeStamp_dayBegin + 60 * i) * 1000
                                try:
                                    if ((klinesSum[klineReadCounter][0]) == expectedTimeStamp): newKlines.append(klinesSum[klineReadCounter] + [1]); klineReadCounter += 1
                                    else:                                                       newKlines.append([expectedTimeStamp, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                                except: newKlines.append([expectedTimeStamp, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                            klinesSum = newKlines
                            verificationCode = "comp"
                    return (functionParams[0], functionParams[1], functionParams[2], klinesSum, verificationCode)
                else: return (functionParams[0], functionParams[1], functionParams[2], "#MARKETCONFALSE#", None)
            else: return (functionParams[0], functionParams[1], functionParams[2], "#DNE_MARKET#", None)
        self.farHanlderDictionary["FETCH_KLINES"] = __FA_FETCH_KLINES

        #Returns a day worth of '1m' interval klines of the specified asset
        #functionParams - [0]: AssetSymbol(Type: str), [1]: Since(Type:int, in seconds since epoch)
        def __FA_FETCH_KLINES_1m(managerInstance, functionParams):
            if (managerInstance.marketData != None):
                if (managerInstance.connection_Status_BINANCE == True):
                    market = managerInstance.marketData[functionParams[0]]['marketType']; symbol_client = managerInstance.marketData[functionParams[0]]['id']
                    timeStamp_minuteBegin = int(functionParams[1] / 60) * 60
                    #Receive Kline data from Binance
                    if   (market == "SPOT"):   kline = managerInstance.clientBinance.get_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = timeStamp_minuteBegin * 1000, end_str = (timeStamp_minuteBegin + 59) * 1000, limit = 720)[0]
                    elif (market == "USDS-M"): kline = managerInstance.clientBinance.futures_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = timeStamp_minuteBegin * 1000, end_str = (timeStamp_minuteBegin + 59) * 1000, limit = 720)[0]
                    elif (market == "COIN-M"): kline = managerInstance.clientBinance.futures_coin_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, startTime = (timeStamp_minuteBegin - 1) * 1000, endTime = (timeStamp_minuteBegin + 59) * 1000, limit = 720)[0]
                    return (functionParams[0], functionParams[1], functionParams[2], kline)
                else: return (functionParams[0], functionParams[1], functionParams[2], "#MARKETCONFALSE#")
            else: return (functionParams[0], functionParams[1], functionParams[2], "#DNE_MARKET#")
        self.farHanlderDictionary["FETCH_KLINES_1m"] = __FA_FETCH_KLINES_1m

        #Add a data stream subscription
        #functionParams - [0]: AssetSymbol(Type: str)
        def __FA_ADD_DATASTREAMSUBSCRIPTION(managerInstance, functionParams):
            symbolAPI = functionParams
            if (managerInstance.marketData[symbolAPI]['active'] == True): 
                managerInstance.clientBinance_WebSocket['subscriptionAppendQueue'].append(symbolAPI)
                return True
            else: return "#SNA#" #Symbol Not Active
        self.farHanlderDictionary["ADD_DATASTREAMSUBSCRIPTION"] = __FA_ADD_DATASTREAMSUBSCRIPTION
        
        #Remove a data stream subscription
        #functionParams - [0]: AssetSymbol(Type: str)
        def __FA_REMOVE_DATASTREAMSUBSCRIPTION(managerInstance, functionParams):
            symbolAPI = functionParams
            if (symbolAPI in managerInstance.clientBinance_WebSocket['streamingSymbols']):
                targetIndex = managerInstance.clientBinance_WebSocket['streamingSymbols'].index(symbolAPI)
                streamName = managerInstance.clientBinance_WebSocket['streamNames'][targetIndex]
                try: managerInstance.clientBinance_WebSocket['TWM'].stop_socket(streamName)
                except Exception as e: print(e)
                managerInstance.clientBinance_WebSocket['streamingSymbols'].remove(symbolAPI)
                managerInstance.clientBinance_WebSocket['streamNames'].remove(streamName)
                del managerInstance.currnetHourRaw1ms[symbolAPI]
                del managerInstance.lastHourRaw1ms[symbolAPI]
                return True
            else: return "#SNS#" #Symbol Not Subscribed
        self.farHanlderDictionary["REMOVE_DATASTREAMSUBSCRIPTION"] = __FA_REMOVE_DATASTREAMSUBSCRIPTION

    def __FARHandler(self, functionID, functionParams):
        if functionID in self.farHanlderDictionary.keys():
            return self.farHanlderDictionary[functionID](self, functionParams)
    #IPC HANDLING FUNCTIONS END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


    
    #MANAGER INTERNAL FUNCTIONS ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __connectAPI(self, apiKey, secretKey):
        currentTime = time.time()
        ccxtBinance = ccxt.binance(config = {'apiKey': apiKey, 'secret': secretKey})
        #ccxtBinance = ccxt.binance(config = {'apiKey': apiKey, 'secret': secretKey})
        try:
            """
            ['info']
                ['makerCommission']
                ['takerCommission']
                ['buyerCommission']
                ['sellerCommission']
                ['commissionRates']
                ['canTrade']
                ['canWithdraw']
                ['canDeposit']
                ['brokered']
                ['requireSelfTradePrevention']
                ['preventSor']
                ['updateTime']
                ['accountType']
                ['balances']
                ['permissions']
                ['uid']
            [SYMBOL_0]: ['free', 'used', 'total']
              .
              .
              .
            [SYMBOL_N]: ['free', 'used', 'total']
            ['timestamp']: 
            ['datetime']:  
            ['free']:  [SYMBOL_0, ..., SYMBOL_0]
            ['used']:  [SYMBOL_0, ..., SYMBOL_0]
            ['total']: [SYMBOL_0, ..., SYMBOL_0]
            """
            balance_spot = ccxtBinance.fetch_balance()
            """
            ['info']:
                ['feeTier']
                ['canTrade']
                ['canDeposit']
                ['canWithdraw']
                ['tradeGroupId']
                ['updateTime']
                ['multiAssetsMargin']
                ['totalInitialMargin']
                ['totalMaintMargin']
                ['totalWalletBalance']
                ['totalUnrealizedProfit']
                ['totalMarginBalance']
                ['totalPositionInitialMargin']
                ['totalOpenOrderInitialMargin']
                ['totalCrossWalletBalance']
                ['totalCorssUnPnl']
                ['availableBalance']
                ['maxWithdrawAmount']
                ['assets']
                ['positions']
            [SYMBOL_0]: ['free', 'used', 'total']
              .
              .
              .
            [SYMBOL_N]: ['free', 'used', 'total']
            ['timestamp']: None
            ['datetime']:  None
            ['free']:  [SYMBOL_0, ..., SYMBOL_0]
            ['used']:  [SYMBOL_0, ..., SYMBOL_0]
            ['total']: [SYMBOL_0, ..., SYMBOL_0]
            """
            balance_futures = ccxtBinance.fetch_balance(params = {'type': "future", 'ratelimit': 1000})

            #Multi-Source Verification of the SPOT symbols
            self.programLogger.printPMessage("Verifying Currency Symbols")
            symbolsFromInfo = list()
            for element in balance_spot['info']['balances']: symbolsFromInfo.append(element['asset'])
            symbolsFromMain = list()
            for key in balance_spot.keys():
                if (key != 'info') and (key != 'timestamp') and (key != 'datetime') and (key != 'free') and (key != 'used') and (key != 'total'): symbolsFromMain.append(key)
            symbolsFromFree = list(balance_spot['free'].keys()); symbolsFromUsed = list(balance_spot['used'].keys()); symbolsFromTotal = list(balance_spot['total'].keys())
            self.programLogger.printPMessage("{:d} symbols found from keyword 'info:balances'".format(len(symbolsFromInfo)))
            self.programLogger.printPMessage("{:d} symbols found from keyword 'mainDict'".format(len(symbolsFromMain)))
            self.programLogger.printPMessage("{:d} symbols found from keyword 'free'".format(len(symbolsFromFree)))
            self.programLogger.printPMessage("{:d} symbols found from keyword 'used'".format(len(symbolsFromUsed)))
            self.programLogger.printPMessage("{:d} symbols found from keyword 'free'".format(len(symbolsFromTotal)))
            sources = (('info:balances', symbolsFromInfo), ('mainDict', symbolsFromMain), ('free', symbolsFromFree), ('used', symbolsFromUsed), ('total', symbolsFromTotal))
            testSymbols = dict()
            verifiedSymbols = list()
            for source in sources:
                for symbol in source[1]:
                    if (symbol in testSymbols): testSymbols[symbol][0] += 1; testSymbols[symbol][1].append(source[0])
                    else:                       testSymbols[symbol] = [1, [source[0]]]
                    if (testSymbols[symbol][0] == 5): verifiedSymbols.append(symbol); del testSymbols[symbol]
            if (0 < len(testSymbols)):
                self.programLogger.printPMessage("{:d} Multi-Source Verification Failed Symbols Found".format(len(testSymbols)))
                for key in testSymbols.keys(): self.programLogger.printPMessage("   [{:s}] from {:s}".format(key, str(testSymbols[key])))
            self.programLogger.printPMessage("{:d} Multi-Source Verified Symbols Will be Used".format(len(verifiedSymbols)))
            self.verifiedSpotSymbols = verifiedSymbols
            
            #Localize data from fetch_balance
            for symbol in self.verifiedSpotSymbols: self.ccxtBinance_spotWallet['balances'][symbol] = balance_spot[symbol]
            del balance_spot['info']['balances']
            self.ccxtBinance_spotWallet['info']       = balance_spot['info']
            self.ccxtBinance_spotWallet['updateTime'] = balance_spot['timestamp']
            
            for key in balance_futures.keys():
                if (key != 'info') and (key != 'timestamp') and (key != 'datetime') and (key != 'free') and (key != 'used') and (key != 'total'): self.ccxtBinance_futureWallet['balances'][key] = balance_futures[key]
            self.ccxtBinance_futureWallet['info']       = balance_futures['info']
            self.ccxtBinance_futureWallet['updateTime'] = balance_futures['timestamp']

            self.ccxtBinance = ccxtBinance
            self.connection_Status_ACCOUNT = True
            self.assistantIPC.sendPRD("ACCOUNTCONNECTIONSTATUS", (self.connection_Status_ACCOUNT, currentTime))
            self.assistantIPC.sendPRD("SPOTWALLET",     self.ccxtBinance_spotWallet)
            self.assistantIPC.sendPRD("FUTURESWALLET", self.ccxtBinance_futureWallet)
            self.programLogger.printPMessage("BINANCE API ACCOUNT CONNECTION SUCCESSFUL")
            return (True, currentTime)
        except Exception as e:
            self.programLogger.printPMessage("BINANCE API ACCOUNT CONNECTION FAILED");
            return (False, currentTime, e)
        
    #Reset the connected account API
    def __disconnectAPI(self):
        currentTime = time.time()
        self.connection_Status_ACCOUNT = False
        self.assistantIPC.sendPRD("ACCOUNTCONNECTIONSTATUS", (self.connection_Status_ACCOUNT, currentTime))
        self.ccxtBinance = ccxt.binance()
        self.programLogger.printPMessage("BINANCE API ACCOUNT DISCONNECTED");
        return (True, currentTime)
    
    #Check Market Registration Timestamp of the given symbol
    def __checkMrktRegTimeStamp(self, symbol):
        symbol_client = self.marketData[symbol]['id']
        market = self.marketData[symbol]['marketType']
        if (market == "SPOT"):
            tDate_beg = "2017-07-01"
            tDate_end = datetime.fromtimestamp(time.mktime(ciso8601.parse_datetime(tDate_beg).timetuple()) + 86400 * 30).strftime("%Y-%m-%d")
            while (True):
                earliest1d = self.clientBinance.get_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1DAY, start_str = tDate_beg, end_str = tDate_end)
                if (0 < len(earliest1d)): break
                else: tDate_beg = tDate_end; tDate_end = datetime.fromtimestamp(time.mktime(ciso8601.parse_datetime(tDate_beg).timetuple()) + 86400 * 30).strftime("%Y-%m-%d")
            earliest1dTimeStamp = earliest1d[0][0]
            klines1 = self.clientBinance.get_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = earliest1dTimeStamp,            end_str = earliest1dTimeStamp + 43200000, limit = 720)
            klines2 = self.clientBinance.get_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = earliest1dTimeStamp + 43200000, end_str = earliest1dTimeStamp + 86400000, limit = 720)
            day1mKlines = klines1 + klines2
            earliest1m = day1mKlines[0][0]
        elif (market == "USDS-M"):
            tDate_beg = "2019-08-30"
            tDate_end = datetime.fromtimestamp(time.mktime(ciso8601.parse_datetime(tDate_beg).timetuple()) + 86400 * 30).strftime("%Y-%m-%d")
            while (True):
                earliest1d = self.clientBinance.futures_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1DAY, start_str = tDate_beg, end_str = tDate_end)
                if (0 < len(earliest1d)): break
                else: tDate_beg = tDate_end; tDate_end = datetime.fromtimestamp(time.mktime(ciso8601.parse_datetime(tDate_beg).timetuple()) + 86400 * 30).strftime("%Y-%m-%d")
            earliest1dTimeStamp = earliest1d[0][0]
            klines1 = self.clientBinance.futures_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = earliest1dTimeStamp,            end_str = earliest1dTimeStamp + 43200000, limit = 720)
            klines2 = self.clientBinance.futures_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = earliest1dTimeStamp + 43200000, end_str = earliest1dTimeStamp + 86400000, limit = 720)
            day1mKlines = klines1 + klines2
            earliest1m = day1mKlines[0][0]
        elif (market == "COIN-M"):
            tDate_beg = 1567123200
            tDate_end = 1567123200 + 86400 * 30
            while (True):
                earliest1d = self.clientBinance.futures_coin_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1DAY, startTime = (tDate_beg - 1) * 1000, endTime = (tDate_end - 1) * 1000)
                if (0 < len(earliest1d)): break
                else: tDate_beg = tDate_end; tDate_end = tDate_beg + 86400 * 30
                time.sleep(0.1)
            earliest1dTimeStamp = earliest1d[0][0]
            klines1 = self.clientBinance.futures_coin_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, startTime = earliest1dTimeStamp -    60000, endTime = earliest1dTimeStamp + 43140000, limit = 720)
            klines2 = self.clientBinance.futures_coin_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, startTime = earliest1dTimeStamp + 43140000, endTime = earliest1dTimeStamp + 86340000, limit = 720)
            day1mKlines = klines1 + klines2
            earliest1m = day1mKlines[0][0]
        return earliest1m

    #Add a k-line stream
    def __addKlineStream(self, symbol, handlerFunction):
        symbol_client = self.marketData[symbol]['id']
        market = self.marketData[symbol]['marketType']
        currentTimeStamp = int(time.time())
        currentHour = int(time.time()/3600); lastHour = currentHour - 1
        #SPOT
        if (market == "SPOT"): 
            streamName = self.clientBinance_WebSocket['TWM'].start_kline_socket(callback = handlerFunction, symbol = symbol_client)
            klines_lastHour = self.clientBinance.get_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = lastHour*3600000, end_str = currentHour*3600000, limit = 60)
            klines_currentHour = self.clientBinance.get_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = currentHour*3600000, end_str = currentTimeStamp * 1000, limit = 60)
        #USDS-M
        elif (market == "USDS-M"):
            if ("_" in symbol_client):
                #Seems to be not receiving any data from binance, disable for now
                """
                symbolSplit = symbol_client.split("_")
                symbolPass = symbolSplit[0]
                if (symbolSplit[1] == "PERP"): quarterType = pythonBinance_enums.ContractType.PERPETUAL
                else:
                    monthNow = datetime.now().month
                    symbolQuarter = int(symbolSplit[1][2:4]) / 3
                    if (math.ceil(monthNow/3) == symbolQuarter): quarterType = pythonBinance_enums.ContractType.CURRENT_QUARTER
                    else:                                        quarterType = pythonBinance_enums.ContractType.NEXT_QUARTER
                streamName = self.clientBinance_WebSocket['TWM'].start_kline_futures_socket(callback = handlerFunction, symbol = symbolPass, futures_type = pythonBinance_enums.FuturesType.USD_M, contract_type = quarterType)
                """
                return False
            else: streamName = self.clientBinance_WebSocket['TWM'].start_kline_futures_socket(callback = handlerFunction, symbol = symbol_client)
            klines_lastHour = self.clientBinance.futures_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = lastHour*3600000, end_str = currentHour*3600000, limit = 60)
            klines_currentHour = self.clientBinance.futures_historical_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = currentHour*3600000, end_str = currentTimeStamp * 1000, limit = 60)
        #COIN-M
        elif (market == "COIN-M"):
            symbolSplit = symbol_client.split("_")
            symbolPass = symbolSplit[0]
            if (symbolSplit[1] == "PERP"): quarterType = pythonBinance_enums.ContractType.PERPETUAL
            else:
                monthNow = datetime.now().month
                symbolQuarter = int(symbolSplit[1][2:4]) / 3
                if (math.ceil(monthNow/3) == symbolQuarter): quarterType = pythonBinance_enums.ContractType.CURRENT_QUARTER
                else:                                        quarterType = pythonBinance_enums.ContractType.NEXT_QUARTER
            streamName = self.clientBinance_WebSocket['TWM'].start_kline_futures_socket(callback = handlerFunction, symbol = symbolPass, futures_type = pythonBinance_enums.FuturesType.COIN_M, contract_type = quarterType)
            klines_lastHour = self.clientBinance.futures_coin_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = lastHour*3600000-60000, end_str = currentHour*3600000-60000, limit = 60)
            klines_currentHour = self.clientBinance.futures_coin_klines(symbol = symbol_client, interval = binance.Client.KLINE_INTERVAL_1MINUTE, start_str = currentHour*3600000-60000, end_str = currentTimeStamp*1000-60000, limit = 60)
        #streamName = self.clientBinance_WebSocket['TWM'].start_kline_socket(callback = handlerFunction, symbol = symbol_client)
        
        self.clientBinance_WebSocket['streamNames'].append(streamName)
        self.clientBinance_WebSocket['streamingSymbols'].append(symbol)
        self.lastHourRaw1ms[symbol] = dict()
        self.currnetHourRaw1ms[symbol] = dict()
        for i in range (len(klines_lastHour)): self.lastHourRaw1ms[symbol][int((klines_lastHour[i][0] / 60000) % 60)] = klines_lastHour[i][:-1] + [1]
        for i in range (len(klines_currentHour)): self.currnetHourRaw1ms[symbol][int((klines_currentHour[i][0] / 60000) % 60)] = klines_currentHour[i][:-1] + [1]
        
        print(len(self.clientBinance_WebSocket['streamNames']), symbol, streamName, market)
    #MANAGER INTERNAL FUNCTIONS END -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------






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
                if (self.function is not None): 
                    try: self.function(managerInstance)
                    except Exception as e: print("An error occurred while executing a timerFunction <{:s}> <{:s}>".format(str(self.function), str(e)))
            return self.repeat
    #Auxillary Classes END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------