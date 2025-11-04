import queue
from ATM_Epsilon_Manager_IPC import assistant_IPC

import numpy
import time
import types
import os
import pprint
import win32api
import datetime
import shutil
from pympler import asizeof

MANAGERNAME = "DATAMANAGEMENT"

path_PROJECT = os.path.dirname(os.path.realpath(__file__))
path_DM = os.path.join(path_PROJECT + r"\data\dm")


class manager_DataManagement:
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
        self.darHanlderDictionary = {"DAR TEST": "[DATA MANAGEMENT] DAR TEST SUCCESSFUL", "ATMMANAGERS": self.atm_Managers, "PTIMERS": self.processTimers, "PTIMERS_AVGSTANDARD": self.processTimerAvgStandard}
        self.farHanlderDictionary = dict(); self.__initializeFARs()
        self.IPCResultHandlers = dict()
        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_0_IPC ASSISTANT INITIALIZED"); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("IPC ASSISTANT INITIALIZED") #Process Status Report
        
        #Data Management Variables
        self.sds = {'BINANCE': dict()}

        self.dm_DBConnected = False
        self.dm_DBDir = None
        self.dm_DBVolume = {'total': None, 'free': None, 'used': None}

        self.dm_raw1mDownloadQueue_Binance = list()
        self.dm_raw1mDownloadQueue_available_Binance = True

        currentTime = time.time()
        self.dm_DB_LastUpdatedDay    = int(currentTime / 86400)
        self.dm_DB_LastUpdatedHour   = int(currentTime / 3600)
        self.dm_DB_LastUpdatedMinute = int(currentTime / 60)

        #Data Type List
        self.dTypeList = ['raw1m', 'sklc', 'mklc']

        #Read DMI (Database Management Instruction) File
        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_5_READING DATABASE MANAGEMENT INSTRUCTIONS"); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("READING DATABASE MANAGEMENT INSTRUCTIONS") #Process Status Report
        dmi_file = open(os.path.join(path_DM, "dmi.bin"))
        tempLines = dmi_file.readlines()
        self.dmi = {'driveName' :  None,
                    'autoCorruptionRemoval': None,
                    'SDS_BINANCE': list()}
        acceptables = ("driveName", "SDS_BINANCE")
        for line in tempLines:
            try:
                words = line.split("="); key = words[0].strip(); content = words[1].strip()
                if (key in acceptables):
                    if   (key == "SDS_BINANCE"):           self.dmi["SDS_BINANCE"].append(content)
                    elif (key == "autoCorruptionRemoval"): 
                        if (content == "True"):            self.dmi["autoCorruptionRemoval"] = True
                        else:                              self.dmi["autoCorruptionRemoval"] = False
                    else:                                  self.dmi[key] = content
            except: pass
        dmi_file.close()
        self.__saveDMI()
        pprint.pprint(self.dmi)
        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_10_DATABASE MANAGEMENT INSTRUCTIONS READ COMPLETE"); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("DATABASE MANAGEMENT INSTRUCTIONS READ COMPLETE") #Process Status Report
        
        #Check if the DB drive specified in DMI exists
        drives = win32api.GetLogicalDriveStrings().split("\000")[:-1]
        for i in range (len(drives)):
            driveName = win32api.GetVolumeInformation(drives[i])[0]
            if (self.dmi['driveName'] == driveName): 
                self.dm_DBConnected = True
                self.dm_DBDir = drives[i]
                break
                     
        #Initialize self.sds['BINANCE']
        mrktRegTStamp_FileDir = os.path.join(path_PROJECT, "data/binanceAPI/mrktRegTStamp.bin")
        if (os.path.isfile(mrktRegTStamp_FileDir) == True):
            mrktRegTStamp_File = open(mrktRegTStamp_FileDir); fileLines = mrktRegTStamp_File.readlines(); mrktRegTStamp_File.close()
            mrktRegTStamps = dict()
            for line in fileLines:
                try:
                    contents = line.split(",")
                    mrktRegTStamps[contents[0]] = int(contents[1])
                except: pass

        """
        for symbolAPI in self.dmi["SDS_BINANCE"]:
            symbolDIR = symbolAPI.strip().replace("/", "%").replace(":", "&")
            if (self.dm_DBConnected == True): symbolDBDir = os.path.join(self.dm_DBDir, "binance", symbolDIR)
            else:                             symbolDBDir = None
            self.sds["BINANCE"][symbolAPI] = {'symbolDIR': symbolDIR, 'dir': symbolDBDir, 'dataStatus': {'density': None, 'packetStatus_raw1m': dict(), 'analysis': dict()}, 'mrktRegTimeStamp': mrktRegTStamps.get(symbolAPI, None)}
            marketRegistrationDay = int(self.sds["BINANCE"][symbolAPI]['mrktRegTimeStamp'] / 86400000); lastestCompletedDay = int(time.time() / 86400)
            for i in range (marketRegistrationDay, lastestCompletedDay + 1): self.sds["BINANCE"][symbolAPI]['dataStatus']['packetStatus_raw1m'][i * 86400] = False
            self.__analyzeSymbolData_BINANCE(symbolAPI)
            tID = self.assistantIPC.sendFAR("BINANCEAPI", "ADD_DATASTREAMSUBSCRIPTION", symbolAPI, nRetry = "INF")
            def ADD_DATASTREAMSUBSCRIPTION_FARHandler(manager, result): print("SDS BINANCE WEBSOCKET STREAMING SUBSCRIPTION RESULT:", result)
            self.IPCResultHandlers[tID] = ADD_DATASTREAMSUBSCRIPTION_FARHandler
        """
                
        #print("\n<sds>")
        #pprint.pprint(self.sds)
        #print()

        #Timer Function Assignments
        self.timerFunctions = dict()

        #Once new hour begins, update the DB kline data
        def timerFunction_UPDATERTRIGGERCHECK(manager):
            if (manager.dm_DBConnected == True): #Check if the DB path still exists and Download Queue Exists
                if (os.path.isdir(manager.dm_DBDir)):
                    try:
                        currentTime = time.time()
                        currentDay    = int(currentTime / 86400)
                        currentHour   = int(currentTime / 3600)
                        currentMinute = int(currentTime / 60)

                        if (currentDay    != manager.dm_DB_LastUpdatedDay):    self.__dailyUpdate();    manager.dm_DB_LastUpdatedDay  = currentDay
                        if (currentHour   != manager.dm_DB_LastUpdatedHour):   self.__hourlyUpdate();   manager.dm_DB_LastUpdatedHour = currentHour
                        if (currentMinute != manager.dm_DB_LastUpdatedMinute): print("MINUTELY UPDATER TRIGGERED"); manager.dm_DB_LastUpdatedMinute = currentMinute

                    except Exception as e: manager.programLogger.printPMessage("An Error Occured While Attempting to Update the Database <{:s}>".format(str(e))) #Process Status Report
                else:
                    manager.dm_DBConnected = False
                    manager.programLogger.printPMessage("Database Update Failed <DB Connection Lost>")
        self.timerFunctions["UPDATEDRTRIGGERCHECK"] = self.__timerFunction(function = timerFunction_UPDATERTRIGGERCHECK, interval = 1000)
        
        #Process 'raw1m' download queue
        def timerFunction_PROCESS_RAW1MDOWNLOADQUEUE(manager):
            if ((manager.dm_DBConnected == True) and (manager.assistantIPC.getPRD("BINANCEAPI", "MARKETCONNECTIONSTATUS") != None)):
                #Process 'raw1m' Download Queue for 'BINANCE'
                if ((0 < len(manager.dm_raw1mDownloadQueue_Binance)) and (manager.dm_raw1mDownloadQueue_available_Binance == True) and (manager.assistantIPC.getPRD("BINANCEAPI", "MARKETCONNECTIONSTATUS")[0] == True)):
                    queueContent = manager.dm_raw1mDownloadQueue_Binance.pop(0)
                    self.dm_raw1mDownloadQueue_available_Binance = False
                    tID = manager.assistantIPC.sendFAR("BINANCEAPI", "FETCH_KLINES", (queueContent[0], queueContent[1], queueContent[2]))
                    def timerFunction_PROCESS_RAW1MDOWNLOADQUEUE_FARHandler0(manager, result):
                        symbol = result[0]; timestamp = result[1]; klineDataList = result[3]; verificationCode = result[4]
                        if (symbol in self.sds["BINANCE"].keys()): #Check if the symbol has not been removed from SDS
                            if ((result[3] == "#DNE_MARKET#") or (result[2] == "#MARKETCONFALSE#")): #If the request result is a FA failure, append back the queue
                                manager.dm_raw1mDownloadQueue_Binance.append((result[0], result[1], result[2]))
                            else: #If the request result is a success, save the result appropriately
                                fileName = "{:s}_{:d}_{:s}.bin".format(manager.sds["BINANCE"][symbol]['symbolDIR'], timestamp, verificationCode)
                                fileDir = os.path.join(manager.sds["BINANCE"][symbol]['dir'], 'raw1m', fileName)
                                file = open(fileDir, 'w')
                                for klineData in klineDataList: 
                                    #[0]: Open Time (int), [1]: Open Price (float), [2]: High Price (float), [3]: Low Price (float), [4]: Close Price (float), [5]: Traded Volume (float), [6]: Close Time (int), 
                                    #[7]: Quote Asset Volume (float), [8]: Number of Trade (int), [9]: Taker Buy Base Asset Volume (float), [10]: Taker Buy Quote Asset Volume (float), [11]: Original
                                    file.write("{:d} {:.12f} {:.12f} {:.12f} {:.12f} {:.12f} {:d} {:.12f} {:d} {:.12f} {:.12f} {:d}\n".\
                                        format(int(klineData[0]), float(klineData[1]), float(klineData[2]), float(klineData[3]), float(klineData[4]), float(klineData[5]), int(klineData[6]),
                                                float(klineData[7]), int(klineData[8]), float(klineData[9]), float(klineData[10]), int(klineData[12])))
                                file.close()
                                self.sds["BINANCE"][symbol]['dataStatus']['packetStatus_raw1m'][timestamp] = True
                                #Density Edit
                                if (result[2] == "new"): self.sds["BINANCE"][symbol]['dataStatus']['density'] += 100 / len(self.sds["BINANCE"][symbol]['dataStatus']['packetStatus_raw1m'].keys())
                                print("{:.3f} %".format(self.sds["BINANCE"][symbol]['dataStatus']['density']), symbol)
                        self.dm_raw1mDownloadQueue_available_Binance = True
                    manager.IPCResultHandlers[tID] = timerFunction_PROCESS_RAW1MDOWNLOADQUEUE_FARHandler0

                #Process 'raw1m' Download Queue for 'Other Markets'
                #Currently Empty
        self.timerFunctions["PROCESS_RAW1MDOWNLOADQUEUE"] = self.__timerFunction(function = timerFunction_PROCESS_RAW1MDOWNLOADQUEUE, interval = 1000)

        #Check Database Connection Every 100ms
        def timerFunction_CHECKDBCONNECTION(manager):
            connectionCheckTime = time.time()
            if (self.dm_DBDir == None): #If dm_DBDir is None, DB Search during initialization was failed, so keep looking for one
                #Check if the DB drive specified in DMI exists
                drives = win32api.GetLogicalDriveStrings().split("\000")[:-1]
                for i in range (len(drives)):
                    driveName = win32api.GetVolumeInformation(drives[i])[0]
                    if (self.dmi['driveName'] == driveName): self.dm_DBConnected = True; self.dm_DBDir = drives[i]; break #DB is found
                #Do this now that the DB is found
                if (self.dm_DBConnected == True):
                    for symbolAPI in self.sds["BINANCE"].keys(): self.sds["BINANCE"][symbolAPI]['dir'] = os.path.join(self.dm_DBDir, "binance", self.sds["BINANCE"][symbolAPI]['symbolDIR']); self.__analyzeSymbolData_BINANCE(symbolAPI) #Add symbolDBDir and analyze data contents
                    self.__getDBVolume() #Get Connected DB Volume
                    #Announce the DB and updated SDS info via PRD
                    self.assistantIPC.sendPRD("DBCONNECTION", (self.dm_DBConnected, self.dm_DBDir, connectionCheckTime), nRetry = "INF")
                    self.assistantIPC.sendPRD("DBVOLUME", self.dm_DBVolume, nRetry = "INF")
                    self.assistantIPC.sendPRD("SDS", self.sds, nRetry = "INF")

            else: #If the dm_DBDir does exist, keep checking if the direction still exists
                if (os.path.isdir(self.dm_DBDir)): #Connected -> Connected
                    self.__getDBVolume()
                    self.assistantIPC.sendPRD("DBCONNECTION", (self.dm_DBConnected, self.dm_DBDir, connectionCheckTime), nRetry = 0)
                    self.assistantIPC.sendPRD("DBVOLUME", self.dm_DBVolume, nRetry = 0)
                else: #Connected -> Disconnected
                    self.dm_DBDir = None; self.dm_DBConnected = False
                    for symbolAPI in self.sds["BINANCE"].keys(): self.sds["BINANCE"][symbolAPI]['dir'] = None
                    self.dm_DBVolume = {'total': None, 'free': None, 'used': None}
                    #Announce the DB and updated SDS info via PRD
                    self.assistantIPC.sendPRD("DBCONNECTION", (self.dm_DBConnected, self.dm_DBDir, connectionCheckTime), nRetry = "INF")
                    self.assistantIPC.sendPRD("DBVOLUME", self.dm_DBVolume, nRetry = "INF")
                    self.assistantIPC.sendPRD("SDS", self.sds, nRetry = "INF")
        self.timerFunctions["CHECKDBCONNECTION"] = self.__timerFunction(function = timerFunction_CHECKDBCONNECTION, interval = 1000)
        
        #Announce Post-Initialization Data
        self.assistantIPC.sendPRD("DMI_DBDRIVENAME",  self.dmi['driveName'], nRetry = "INF")
        self.assistantIPC.sendPRD("DBCONNECTION", (self.dm_DBConnected, self.dm_DBDir, time.time()), nRetry = "INF")
        self.assistantIPC.sendPRD("DBVOLUME", self.dm_DBVolume, nRetry = "INF")
        self.assistantIPC.sendPRD("SDS", self.sds, nRetry = "INF")

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
                self.processTimers['ipcb_readTime_avg']  = readTime_Sum      / recordLength; self.processTimers['ipcb_readSize_avg']  = readSize_Sum  / recordLength; self.processTimers['ipcb_readRate_avg']  = readRate_Sum      / recordLength
                self.processTimers['ipcb_writeTime_avg'] = writeTime_Sum     / recordLength; self.processTimers['ipcb_writeSize_avg'] = writeSize_Sum / recordLength; self.processTimers['ipcb_writeRate_avg'] = writeRate_Sum     / recordLength
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
            try: return ("[DATA MANAGEMENT] FAR TEST SUCCESSFUL with Function Params: " + str(functionParams))
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

        #Append a data symbol to SDS&DMI
        def __FA_APPEND_SDS_BINANCE(managerInstance, functionParams):
            '''
            #functionParams = 'symbolAPI'
            '''
            symbolAPI = functionParams[0]
            mrktRegTimeStamp = functionParams[1]
            #Generate symbolDIR and symbolDBDir accordingly to the DB connection Status
            symbolDIR = symbolAPI.strip().replace("/", "%").replace(":", "&")
            if (managerInstance.dm_DBConnected == True): symbolDBDir = os.path.join(managerInstance.dm_DBDir, "binance", symbolDIR)
            else:                                        symbolDBDir = None
            #Update the SDS and DMI data
            managerInstance.sds["BINANCE"][symbolAPI] = {'symbolDIR': symbolDIR, 'dir': symbolDBDir, 'dataStatus': {'density': None, 'packetStatus_raw1m': dict(), 'analysis': dict()}, 'mrktRegTimeStamp': mrktRegTimeStamp}
            marketRegistrationDay = int(managerInstance.sds["BINANCE"][symbolAPI]['mrktRegTimeStamp'] / 86400000); lastestCompletedDay = int(time.time() / 86400)
            for i in range (marketRegistrationDay, lastestCompletedDay + 1): self.sds["BINANCE"][symbolAPI]['dataStatus']['packetStatus_raw1m'][i * 86400] = False
            managerInstance.__analyzeSymbolData_BINANCE(symbolAPI)
            #Send subcription append FAR to 'BINANCE API'
            tID = self.assistantIPC.sendFAR("BINANCEAPI", "ADD_DATASTREAMSUBSCRIPTION", symbolAPI, nRetry = "INF")
            def ADD_DATASTREAMSUBSCRIPTION_FARHandler(manager, result): print("SDS BINANCE WEBSOCKET STREAMING SUBSCRIPTION RESULT:", result)
            self.IPCResultHandlers[tID] = ADD_DATASTREAMSUBSCRIPTION_FARHandler
            managerInstance.dmi['SDS_BINANCE'].append(symbolAPI)
            managerInstance.__saveDMI()
            #Announce the updated SDS via PRD
            managerInstance.assistantIPC.sendPRD("SDS", managerInstance.sds, nRetry = "INF")
            #Return the result
            return (True, "SDS Appending Successful '{:s}'".format(symbolAPI))
        self.farHanlderDictionary["APPEND_SDS_BINANCE"] = __FA_APPEND_SDS_BINANCE

        #Remove a data symbol from SDS&DMI
        def __FA_REMOVE_SDS_BINANCE(managerInstance, functionParams):
            '''
            #functionParams = 'symbolAPI'
            '''
            symbolAPI = functionParams
            #If symbolAPI exists within the SDS, remove it from SDS and DMI, then save the DMI file and announce the updated SDS via PRD -> Return 'True' to indicate successful removal
            if symbolAPI in managerInstance.sds["BINANCE"].keys():
                del managerInstance.sds["BINANCE"][symbolAPI]
                managerInstance.dmi["SDS_BINANCE"].remove(symbolAPI)
                managerInstance.assistantIPC.sendPRD("SDS", managerInstance.sds, nRetry = "INF")
                managerInstance.__saveDMI()
                newQueue = list()
                for i in range (len(managerInstance.dm_raw1mDownloadQueue_Binance)):
                    queue = managerInstance.dm_raw1mDownloadQueue_Binance.pop(0)
                    if (queue[0] != symbolAPI): newQueue.append(queue)
                managerInstance.dm_raw1mDownloadQueue_Binance = newQueue
                #Send subsription removal FAR to 'BINANCEAPI'
                tID = self.assistantIPC.sendFAR("BINANCEAPI", "REMOVE_DATASTREAMSUBSCRIPTION", symbolAPI, nRetry = "INF")
                def REMOVE_DATASTREAMSUBSCRIPTION_FARHandler(manager, result): print("SDS BINANCE WEBSOCKET STREAMING UNSUBSCRIPTION RESULT:", result)
                self.IPCResultHandlers[tID] = REMOVE_DATASTREAMSUBSCRIPTION_FARHandler
                #Return the result
                return (True, "SDS Removal Successful '{:s}'".format(symbolAPI))
            #If symbolAPI does not exist within the SDS -> Return 'False' to indicate failed removal
            else: return (False, "SDS Removal Failed - Symbol Does Not Exist in SDS")
        self.farHanlderDictionary["REMOVE_SDS_BINANCE"] = __FA_REMOVE_SDS_BINANCE

        #Record Last Hour Data
        def __FA_RECORD_LASTHOUR_RAW1M(managerInstance, functionParams):
            '''
            #functionParams[0] = 'market'
            #functionParams[1] = 'symbolAPI'
            #functionParams[2] = 'klines'
            '''
            market     = functionParams[0]
            symbolAPI  = functionParams[1]
            klinesDict = functionParams[2]
            currentHour = int(time.time()/3600)

            pprint.pprint(klinesDict)

            if (market == "BINANCE"):
                fileName = "{:s}_{:d}_i.bin".format(managerInstance.sds["BINANCE"][symbolAPI]['symbolDIR'], int(time.time()/86400)*86400)
                fileDir = os.path.join(managerInstance.sds["BINANCE"][symbolAPI]['dir'], 'raw1m', fileName)
                if ((currentHour % 24) == 0): #New Day Start
                    file = open(fileDir, 'w')
                    for minute in klinesDict.keys():
                        klineData = klinesDict[minute]
                        #[0]: Open Time (int), [1]: Open Price (float), [2]: High Price (float), [3]: Low Price (float), [4]: Close Price (float), [5]: Traded Volume (float), [6]: Close Time (int), 
                        #[7]: Quote Asset Volume (float), [8]: Number of Trade (int), [9]: Taker Buy Base Asset Volume (float), [10]: Taker Buy Quote Asset Volume (float), [11]: Original
                        file.write("{:d} {:.12f} {:.12f} {:.12f} {:.12f} {:.12f} {:d} {:.12f} {:d} {:.12f} {:.12f} {:d}\n".\
                            format(int(klineData[0]), float(klineData[1]), float(klineData[2]), float(klineData[3]), float(klineData[4]), float(klineData[5]), int(klineData[6]),
                                   float(klineData[7]), int(klineData[8]), float(klineData[9]), float(klineData[10]), int(klineData[11])))
                    file.close()
                else: #Current Day File Edit
                    newContent = list()
                    file = open(fileDir)
                    currentContents = file.readlines()
                    for ccLine in currentContents:
                        timestamp_Hr = int(int(ccLine.strip().split(" ")[0]) / 3600000)
                        if (timestamp_Hr == currentHour - 1): break
                        else: newContent.append(ccLine)
                    file.close()
                    file = open(fileDir, 'w')
                    for line in newContent: file.write(line)
                    for minute in klinesDict.keys():
                        klineData = klinesDict[minute]
                        #[0]: Open Time (int), [1]: Open Price (float), [2]: High Price (float), [3]: Low Price (float), [4]: Close Price (float), [5]: Traded Volume (float), [6]: Close Time (int), 
                        #[7]: Quote Asset Volume (float), [8]: Number of Trade (int), [9]: Taker Buy Base Asset Volume (float), [10]: Taker Buy Quote Asset Volume (float), [11]: Original
                        file.write("{:d} {:.12f} {:.12f} {:.12f} {:.12f} {:.12f} {:d} {:.12f} {:d} {:.12f} {:.12f} {:d}\n".\
                            format(int(klineData[0]), float(klineData[1]), float(klineData[2]), float(klineData[3]), float(klineData[4]), float(klineData[5]), int(klineData[6]),
                                    float(klineData[7]), int(klineData[8]), float(klineData[9]), float(klineData[10]), int(klineData[11])))
                    file.close()
            return True
        self.farHanlderDictionary["RECORD_LASTHOUR_RAW1M"] = __FA_RECORD_LASTHOUR_RAW1M

    def __FARHandler(self, functionID, functionParams):
        if functionID in self.farHanlderDictionary.keys():
            return self.farHanlderDictionary[functionID](self, functionParams)
    #IPC HANDLING FUNCTIONS END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





    #Auxillary Functions --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #Get Current Database disk usage data and save 'total', 'used', and 'free' space
    def __getDBVolume(self):
        diskUsage = shutil.disk_usage(self.dm_DBDir)
        self.dm_DBVolume['total'] = diskUsage[0]; self.dm_DBVolume['used'] = diskUsage[1]; self.dm_DBVolume['free'] = diskUsage[2]

    #Save the DMI data in the path_DM, as a file names 'dmi.bin'
    def __saveDMI(self):
        dmi_file = open(os.path.join(path_DM, "dmi.bin"), 'w')
        dmi_file.write("driveName = {:s}".format(self.dmi['driveName']))
        dmi_file.write("\nautoCorruptionRemoval = {:s}".format(str(self.dmi['autoCorruptionRemoval'])))
        for symbolAPI in self.dmi['SDS_BINANCE']: dmi_file.write("\nSDS_BINANCE = {:s}".format(symbolAPI))
        dmi_file.close()

    #Identify the 'raw1m' and analysis files for the given symbol existing in the Database
    def __analyzeSymbolData_BINANCE(self, symbolAPI):
        if (os.path.isdir(self.sds["BINANCE"][symbolAPI]['dir']) == True): #If the expected directory already exists, analyze the data content within
            symbolDBDir_raw1m    = os.path.join(self.sds["BINANCE"][symbolAPI]['dir'], 'raw1m')
            symbolDBDir_analysis = os.path.join(self.sds["BINANCE"][symbolAPI]['dir'], 'analysis')
            #'raw1m' Content Check
            if (os.path.isdir(symbolDBDir_raw1m)): 
                if (self.sds["BINANCE"][symbolAPI]['mrktRegTimeStamp'] == None): self.sds["BINANCE"][symbolAPI]['dataStatus']['density'] = 0
                else:
                    unrecognizableFiles = list()
                    filesInFolder = os.listdir(symbolDBDir_raw1m)
                    n_testPass = 0
                    for fileName in filesInFolder:
                        try:
                            #Analyze the file name
                            fileNameSplit = fileName.split(".");         fileType = fileNameSplit[1]
                            fileNameSplit = fileNameSplit[0].split("_"); fileSymbol = fileNameSplit[0]; fileTimeStamp = int(fileNameSplit[1]); fileVerificationCode = fileNameSplit[2]
                            #File Name Check
                            if ((fileType == "bin") and                                                                          #Type Check
                                (fileSymbol == self.sds["BINANCE"][symbolAPI]['symbolDIR']) and                                  #Symbol Check
                                (fileTimeStamp in self.sds["BINANCE"][symbolAPI]['dataStatus']['packetStatus_raw1m'].keys()) and #Timestamp Check
                                (fileVerificationCode == "comp") or (fileVerificationCode == "C")):                              #Verification Code Check ['i']: Incomplete, redownload needed, ['c']: Compensated, missing data compensated, ['C']: Complete
                                self.sds["BINANCE"][symbolAPI]['dataStatus']['packetStatus_raw1m'][fileTimeStamp] = True; n_testPass += 1
                            else: unrecognizableFiles.append(os.path.join(symbolDBDir_raw1m, fileName))
                        except: unrecognizableFiles.append(os.path.join(symbolDBDir_raw1m, fileName))
                    self.sds["BINANCE"][symbolAPI]['dataStatus']['density'] = n_testPass / len(self.sds["BINANCE"][symbolAPI]['dataStatus']['packetStatus_raw1m'].keys()) * 100
                    #Append all the empty data to the 'raw1m' download queue in reverse order (most recent first)
                    timeStamps = list(self.sds["BINANCE"][symbolAPI]['dataStatus']['packetStatus_raw1m'].keys()); timeStamps.sort()
                    for i in range (len(timeStamps)):
                        reverseIndex = len(timeStamps) - i - 1
                        if (reverseIndex == len(timeStamps)-1):
                            if (self.sds["BINANCE"][symbolAPI]['dataStatus']['packetStatus_raw1m'][timeStamps[reverseIndex]] == False): self.dm_raw1mDownloadQueue_Binance.append((symbolAPI, timeStamps[reverseIndex], "new"))
                            else:                                                                                                       self.dm_raw1mDownloadQueue_Binance.append((symbolAPI, timeStamps[reverseIndex], "edit"))
                        else:
                            if (self.sds["BINANCE"][symbolAPI]['dataStatus']['packetStatus_raw1m'][timeStamps[reverseIndex]] == False): self.dm_raw1mDownloadQueue_Binance.append((symbolAPI, timeStamps[reverseIndex], "new"))
                    #If 'autoCorruptionRemoval' is True, delete all the corrupt & unrecognizable data
                    if (self.dmi['autoCorruptionRemoval'] == True):
                        for fileDir in unrecognizableFiles: os.remove(fileDir)
                    return True
            else: 
                os.mkdir(symbolDBDir_raw1m)
                self.sds["BINANCE"][symbolAPI]['dataStatus']['density'] = 0
                for timeStamp in self.sds["BINANCE"][symbolAPI]['dataStatus']['packetStatus_raw1m'].keys(): self.dm_raw1mDownloadQueue_Binance.append((symbolAPI, timeStamp, "new"))
            #Analysis Content Check
            if (os.path.isdir(symbolDBDir_analysis)): pass
            else: os.mkdir(symbolDBDir_analysis)
            return True
        else: #If the exepcted directory does not exist (usually when the subscription name has just been added), create the path and initialize the 'range' value within 'self.sds["BINANCE"][symbolAPI]'
            os.mkdir(self.sds["BINANCE"][symbolAPI]['dir'])
            os.mkdir(os.path.join(self.sds["BINANCE"][symbolAPI]['dir'], 'raw1m'))
            os.mkdir(os.path.join(self.sds["BINANCE"][symbolAPI]['dir'], 'analysis'))
            self.sds["BINANCE"][symbolAPI]['dataStatus']['density'] = 0
            for timeStamp in self.sds["BINANCE"][symbolAPI]['dataStatus']['packetStatus_raw1m'].keys(): self.dm_raw1mDownloadQueue_Binance.append((symbolAPI, timeStamp, "new"))
            return True
        
    def __hourlyUpdate(self):
        pass
        
    def __dailyUpdate(self):
        pass

    #Auxillary Functions END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





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