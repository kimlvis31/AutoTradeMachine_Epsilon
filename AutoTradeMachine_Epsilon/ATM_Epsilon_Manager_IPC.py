from tkinter import CURRENT
import ATM_Epsilon_Logger

import time
import multiprocessing
import random
import os
from pympler import asizeof
import types

#IPC MANAGER CLASS ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class manager_IPC:
    #MANAGER INITIALIZATION -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __init__(self, programLogger, atm_Managers, IPCBs, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessIDs):
        #Create Local Instance of Program Data Logger
        self.programLogger = programLogger
        self.programLogger.clearPMessages()
        
        #Send Initialization Start Message
        self.programLogger.printPMessage("INITIALIZING IPC MANAGER...")

        #Process Control Variables
        self.processRepeat = True
        self.processTimersUpdateBuffer = None
        self.processTimers = {'updated': False, 'records': list(), 't_processLoop_avg':  0, 't_process_avg':      0, 
                                                                   'ipcb_readTime_avg':  0, 'ipcb_readSize_avg':  0, 'ipcb_readRate_avg':  0,
                                                                   'ipcb_writeTime_avg': 0, 'ipcb_writeSize_avg': 0, 'ipcb_writeRate_avg': 0, 'nRecords': 0}
        self.processTimerAvgStandard = 1

        #Program Managers List
        self.atm_Managers = atm_Managers
        
        #Create local access to IPCBs and IPCB Status Flag
        self.IPCBs = IPCBs
        self.IPCBStatusFlag_AccessIDs = IPCBStatusFlag_AccessIDs
        self.IPCBStatusFlagMemory = multiprocessing.shared_memory.SharedMemory(name = IPCBStatusFlag_shmName)
        self.IPCBStatusFlag = self.IPCBStatusFlagMemory.buf

        #Create Temporary Data Storages
        self.receivedMessages = dict()
        self.reDirectedMessages = dict()
        for managerName in self.atm_Managers: 
            self.receivedMessages[managerName] = dict()
            self.reDirectedMessages[managerName] = dict()
        self.emptyBufferSize = asizeof.asizeof(self.receivedMessages)

        #Manager Control Variables
        self.SHOW_PROCESSINGTIME = False
        self.IPCB_COM_TIMEOUT = 1
        
        #IPC Assistant Initialization
        self.assistantIPC = assistant_IPC(programLogger, "IPC", self.atm_Managers, IPCBs["IPC_R"], IPCBs["IPC_T"], IPCBStatusFlag_shmName, IPCBStatusFlag_AccessIDs["IPC_R"], IPCBStatusFlag_AccessIDs["IPC_T"])
        self.darHanlderDictionary = {"DAR TEST": "[IPC] DAR TEST SUCCESSFUL", "ATMMANAGERS": self.atm_Managers, "PTIMERS": self.processTimers, "PTIMERS_AVGSTANDARD": self.processTimerAvgStandard}
        self.farHanlderDictionary = dict(); self.__initializeFARs()
        self.IPCResultHandlers = dict()
        
        #Timer Function Assignments
        self.timerFunctions = dict()

        self.programLogger.printPMessage("IPC MANAGER INITIALIZATION COMPLETE!")
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

        #Timer Functions Processing
        for fID in self.timerFunctions.keys():
            if (self.timerFunctions[fID].process(self) == False): del self.timerFunctions[fID]
                
        self.assistantIPC.patchIPCB_T() #Place near the end of the process, patch IPCB Data
        self.__calculateProcessTimers() #Calculate 'process timer averages' and control number of records





        proc_timer0 = time.perf_counter_ns()
        #IPCB_R Collection and Data Localizing ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        proc_timer1 = time.perf_counter_ns()
        
        tempManagerNameList = self.atm_Managers.copy()
        timeout_timer = time.time()
        while (len(tempManagerNameList) != 0):
            managerName = tempManagerNameList.pop(0)
            IPCBName    = managerName + "_T"
            if (self.__isIPCBAvailable(IPCBName)):          #If the correspoding manager's IPCB is available, process the IPCB
                self.__raiseIPCBStatusFlag(IPCBName)                               #Raise the IPCB Status Flag to indicate it is being processed
                self.receivedMessages[managerName] = self.IPCBs[IPCBName].copy()   #Copy from the IPCB_T
                self.IPCBs[IPCBName].clear()                                      #Empty the IPCB_T has the data has been localized
                self.__lowerIPCBStatusFlag(IPCBName)                               #lower the IPCB Status Falg to indicate it is now available
            else: tempManagerNameList.append(managerName) #If the correspoding manager's IPCB is not available, move the manager name to the back of the list
            if ((time.time() - timeout_timer) > self.IPCB_COM_TIMEOUT): #Time-Out Control - Activated when reading from IPCB takes more than 'IPCB_COM_TIMEOUT'
                self.programLogger.printPMessage("IPCB READ TIMEOUT OCCURED: Please Check the IPCB_T for the following managers {:s}".format(str(tempManagerNameList))); break;
        copyingT = (time.perf_counter_ns() - proc_timer1) / 1e3
        receivedMessagesSize = asizeof.asizeof(self.receivedMessages) - self.emptyBufferSize
        #IPCB_R Collection and Data Localizing END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        #Localized Data Re-directing --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        """
        MSG CONTENT DESCRIPTION - SENDER END
            PRD (Pre-Registered Data):
                [0]: DATA NAME
                [1]: DATA CONTENT
            DAR (Data Request):
                [0]: RECEIVER
                [1]: DATA NAME
            DARR (Data Request Result):
                [0]: RECEIVER
                [1]: DATA CONTENT
                [2]: REQUEST ID
            FAR (Function Activation Result):
                [0]: RECEIVER
                [1]: FUNCTION ID
                [2]: FUNCTION PARAMETERS
            FARR (Function Activation Result):
                [0]: RECEIVER
                [1]: FUNCTION RESULT
                [2]: REQUEST ID

        MSG CONTENT DESCRIPTION - RECEIVER END
            PRD (Pre-Registered Data):
                [0]: DATA NAME
                [1]: DATA CONTENT
            DAR (Data Request):
                [0]: DATA NAME
            DARR (Data Request Result):
                [0]: DATA CONTENT
                [1]: REQUEST ID
            FAR (Function Activation Result):
                [0]: FUNCTION ID
                [1]: FUNCTION PARAMETERS
            FARR (Function Activation Result):
                [0]: FUNCTION RESULT
                [1]: REQUEST ID
        """
        proc_timer1 = time.perf_counter_ns()

        for sender in self.receivedMessages.keys():
            for msgKey in self.receivedMessages[sender].keys():
                msgType = msgKey.split("-")[1]
                transID = msgKey.split("-")[2]
                #PRD MESSEAGE HANDLING ----------------------------------------------------------------------------------------------------------------------------------------------------------------
                if (msgType == "PRD"):
                #    [KEY]: SENDER-"PRD"-SENDERTRANSID, [0]: RECEIVER, [1]: DATANAME, [2]: DATACONTENT 
                # -> [KEY]: SENDER-"PRD"-SENDERTRANSID, [0]: DATANAME, [1]: DATACONTENT to receivers
                # -> [KEY]: SENDER-"TRC"
                    if (self.receivedMessages[sender][msgKey][0] == "ALL"): #If the destination is 'ALL'
                        for targetManager in self.atm_Managers: #To all the other managers except itself, send refined PRD message
                            if (targetManager != sender): self.reDirectedMessages[targetManager][msgKey] = [self.receivedMessages[sender][msgKey][1], self.receivedMessages[sender][msgKey][2]]
                    else: self.reDirectedMessages[self.receivedMessages[sender][msgKey][0]][msgKey] = [self.receivedMessages[sender][msgKey][1], self.receivedMessages[sender][msgKey][2]]
                    if (self.receivedMessages[sender][msgKey][1] == "IPCLOG"): self.reDirectedMessages[sender]["IPC-TRC-" + transID] = "IPCLOG"
                    else:                                                      self.reDirectedMessages[sender]["IPC-TRC-" + transID] = None
                #DAR MESSEAGE HANDLING ----------------------------------------------------------------------------------------------------------------------------------------------------------------
                elif (msgType == "DAR"):  
                    self.reDirectedMessages[self.receivedMessages[sender][msgKey][0]][msgKey] = [self.receivedMessages[sender][msgKey][1], self.receivedMessages[sender][msgKey][2], self.receivedMessages[sender][msgKey][3]]
                #    [KEY]: SENDER-"DAR"-SENDERTRANSID, [0]: RECEIVER, [1]: DATANAME, [2]: Result Timeout Trigger, [3]: Result nRetry
                # -> [KEY]: SENDER-"DAR"-SENDERTRANSID, [0]: DATANAME, [1]: Result Timeout Trigger, [2]: Result nRetry
                #DARR MESSEAGE HANDLING ---------------------------------------------------------------------------------------------------------------------------------------------------------------
                elif (msgType == "DARR"): 
                    self.reDirectedMessages[self.receivedMessages[sender][msgKey][0]][msgKey] = [self.receivedMessages[sender][msgKey][1], self.receivedMessages[sender][msgKey][2]]
                    self.reDirectedMessages[sender]["IPC-TRC-" + transID] = None
                #    [KEY]: SENDER-"DARR"-SENDERTRANSID, [0]: RECEIVER,    [1]: DATACONTENT, [2]: REQUESTID
                # -> [KEY]: SENDER-"DARR"-SENDERTRANSID, [0]: DATACONTENT, [1]: REQUESTID
                #FAR MESSEAGE HANDLING ----------------------------------------------------------------------------------------------------------------------------------------------------------------
                elif (msgType == "FAR"):  
                    self.reDirectedMessages[self.receivedMessages[sender][msgKey][0]][msgKey] = [self.receivedMessages[sender][msgKey][1], self.receivedMessages[sender][msgKey][2], self.receivedMessages[sender][msgKey][3], self.receivedMessages[sender][msgKey][4]]
                #    [KEY]: SENDER-"FAR"-SENDERTRANSID, [0]: RECEIVER,   [1]: FUNCTIONID, [2]: FUNCTIONPARAMETERS, [3]: Result Timeout Trigger, [4]: Result nRetry
                # -> [KEY]: SENDER-"FAR"-SENDERTRANSID, [0]: FUNCTIONID, [1]: FUNCTION PARAMETERS, [2]: Result Timeout Trigger, [3]: Result nRetry
                #FARR MESSEAGE HANDLING ---------------------------------------------------------------------------------------------------------------------------------------------------------------
                elif (msgType == "FARR"): 
                    self.reDirectedMessages[self.receivedMessages[sender][msgKey][0]][msgKey] = [self.receivedMessages[sender][msgKey][1], self.receivedMessages[sender][msgKey][2]]
                    self.reDirectedMessages[sender]["IPC-TRC-" + transID] = None
                #    [KEY]: SENDER-"FARR"-SENDERTRANSID, [0]: RECEIVER,       [1]: FUNCTIONRESULT, [2]: REQUESTID
                # -> [KEY]: SENDER-"FARR"-SENDERTRANSID, [0]: FUNCTIONRESULT, [1]: REQUESTID

        redirectingT = (time.perf_counter_ns() - proc_timer1) / 1e3
        
        #Localized Data Re-directing END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #Re-directed Localized Data Patching to IPCB_T --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        proc_timer1 = time.perf_counter_ns()
        
        tempManagerNameList = self.atm_Managers.copy()
        timeout_timer = time.time()
        while (len(tempManagerNameList) != 0):
            managerName = tempManagerNameList.pop(0)
            IPCBName    = managerName + "_R"
            if (self.__isIPCBAvailable(IPCBName)):          #If the correspoding manager's IPCB is available, process the IPCB
                self.__raiseIPCBStatusFlag(IPCBName)                                #Raise the IPCB Status Flag to indicate it is being processed
                self.IPCBs[IPCBName].update(self.reDirectedMessages[managerName])   #Upload the re-directed messages to IPCB_R
                self.__lowerIPCBStatusFlag(IPCBName)                                #lower the IPCB Status Falg to indicate it is now available
            else: tempManagerNameList.append(managerName) #If the correspoding manager's IPCB is not available, move the manager name to the back of the list
            if ((time.time() - timeout_timer) > self.IPCB_COM_TIMEOUT): #Time-Out Control - Activated when reading from IPCB takes more than 'IPCB_COM_TIMEOUT'
                self.programLogger.printPMessage("IPCB WRITE TIMEOUT OCCURED: Please Check the IPCB_R for the following managers {:s}".format(str(tempManagerNameList))); break;
            
        #Reset the local temporary message storage
        for manager in self.atm_Managers:
            self.receivedMessages[manager].clear()
            self.reDirectedMessages[manager].clear()

        patchingT = (time.perf_counter_ns() - proc_timer1) / 1e3
        #Re-directed Localized Data Patching to IPCB_T END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        totalProcessingT = (time.perf_counter_ns() - proc_timer0) / 1e3

        if (self.SHOW_PROCESSINGTIME):
            dataProcessingRate = receivedMessagesSize / totalProcessingT * 1e6
            if receivedMessagesSize > (1024 * 1024): receivedMessagesSize = receivedMessagesSize / 1024 / 1024; receivedMessagesSizeUnit = "MB";
            else:                                    receivedMessagesSize = receivedMessagesSize / 1024;        receivedMessagesSizeUnit = "KB";
            if   dataProcessingRate > (1024 * 1024 * 1024): dataProcessingRate = dataProcessingRate / 1024 / 1024 / 1024; dataProcessingRateUnit = "GB/s"
            elif dataProcessingRate > (1024 * 1024):        dataProcessingRate = dataProcessingRate / 1024 / 1024;        dataProcessingRateUnit = "MB/s"
            elif dataProcessingRate > (1024):               dataProcessingRate = dataProcessingRate / 1024;               dataProcessingRateUnit = "KB/s"
            else:                                                                                                         dataProcessingRateUnit = "Bytes/s"
            print("<INTER-PROCESSES COMMUNICATION REPORT>")
            print("   Total Processing Time: {:.3f} us [{:.3f} {:s}] [{:.3f} {:s}]".format(totalProcessingT, receivedMessagesSize, receivedMessagesSizeUnit, dataProcessingRate, dataProcessingRateUnit))
            print("      DATA LOCALIZATION:   {:.3f} us".format(copyingT))
            print("      MESSAGE REDIRECTING: {:.3f} us".format(redirectingT))
            print("      MESSAGE PATCHING:    {:.3f} us".format(patchingT))

        return self.processRepeat
    #MANAGER MAIN PROCESS END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
    #MANAGER PROCESS CONTROL END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def __isIPCBAvailable(self, IPCBName): return (self.IPCBStatusFlag[self.IPCBStatusFlag_AccessIDs[IPCBName]] == 0)
    def __raiseIPCBStatusFlag(self, IPCBName): self.IPCBStatusFlag[self.IPCBStatusFlag_AccessIDs[IPCBName]] = 1
    def __lowerIPCBStatusFlag(self, IPCBName): self.IPCBStatusFlag[self.IPCBStatusFlag_AccessIDs[IPCBName]] = 0





    #IPC HANDLING FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __DARHandler(self, dataName):
        if dataName in self.darHanlderDictionary.keys():
            if (type(self.darHanlderDictionary[dataName]) == types.BuiltinFunctionType): return self.darHanlderDictionary[dataName]()
            else:                                                                        return self.darHanlderDictionary[dataName]
        else: return None

    def __initializeFARs(self):
        def __FA_TESTFUNCTION(managerInstance, functionParams):
            try: return ("[IPC] FAR TEST SUCCESSFUL with Function Params: " + str(functionParams))
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

    def __FARHandler(self, functionID, functionParams):
        if functionID in self.farHanlderDictionary.keys():
            return self.farHanlderDictionary[functionID](self, functionParams)
    #IPC HANDLING FUNCTIONS END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------






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
#IPC MANAGER CLASS END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




















#IPC ASSISTANT CLASS --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class assistant_IPC:
    def __init__(self, programLogger, managerName, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T):
        #Program Data
        self.programLogger = programLogger
        self.managerName = managerName
        self.atm_Managers = atm_Managers;

        #Create local access to IPCBs and IPCB Status Flag
        self.IPCB_R = IPCB_R
        self.IPCB_T = IPCB_T
        self.IPCBStatusFlag_AccessID_R = IPCBStatusFlag_AccessID_R
        self.IPCBStatusFlag_AccessID_T = IPCBStatusFlag_AccessID_T
        self.IPCBStatusFlagMemory = multiprocessing.shared_memory.SharedMemory(name = IPCBStatusFlag_shmName)
        self.IPCBStatusFlag = self.IPCBStatusFlagMemory.buf
        
        #Local Messages Storage
        self.PRD_IN   = dict() #Pre-registered Data from other managers
        self.DAR_IN   = dict() #Data Request Queue
        self.DARR_IN  = dict() #Data Request Result Queue
        self.FAR_IN   = dict() #Function Activation Request Queue
        self.FARR_IN  = dict() #Function Activation Request Result Queue

        self.PRD_OUT  = dict() #Pre-registered Data to send to other managers
        self.DAR_OUT  = dict() #Data Request Queue
        self.DARR_OUT = dict() #Data Request Result Queue
        self.FAR_OUT  = dict() #Function Activation Request Queue
        self.FARR_OUT = dict() #Function Activation Request Result Queue

        for atmManager in self.atm_Managers:
            self.PRD_IN[atmManager]   = dict()
            self.DAR_IN[atmManager]   = dict()
            self.DARR_IN[atmManager]  = dict()
            self.FAR_IN[atmManager]   = dict()
            self.FARR_IN[atmManager]  = dict()

        #Latest IPC Communication Data
        self.t_IPCB_R_Localization = 0
        self.t_IPCB_R_DataAnalysis = 0
        self.t_IPCB_R_ReadTotal    = 0
        self.ds_IPCB_R_ReadSize    = 0
        self.t_IPCB_T_Preparation  = 0
        self.t_IPCB_T_Patch        = 0
        self.t_IPCB_T_WriteTotal   = 0
        self.ds_IPCB_T_WriteSize   = 0

        #Result Reception Variables
        self.receptionDict  = dict()
        self.TIDIssueLimit  = 5000
        self.TID_Availables = list(range(0, self.TIDIssueLimit))
        #self.TID_Issued[transID] = [[0]: Message Type, [1]: Message Content, [2]: PatchedTime, [3]: Time-Out Trigger, [4]:Retry Counter, [5]: Numbers to Retry]
        self.TID_Issued = dict()
        self.TID_Completed  = list()

        #Development Settings
        self.processLog = list()
        self.processLogLimit = 1000
        self.processLogUpdated = False
        self.printMessages = False;

    #Process-Cycle Functions --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def readIPCB_R(self):
        proc_timer0 = time.perf_counter_ns()
        if (self.__isIPCBAvailable(self.IPCBStatusFlag_AccessID_R)): #If the IPCB_R is accessible
            #IPCB_R Messages Localization -------------------------------------------------------------------------------------------------------------------------------------------------------------
            proc_timer1 = time.perf_counter_ns()

            self.__raiseIPCBStatusFlag(self.IPCBStatusFlag_AccessID_R) #Raise the IPCB_R Status Flag to indicate that it is being processed
            IPCB_Read = self.IPCB_R.copy()                             #Localize the data from shared memory
            self.IPCB_R.clear()                                        #Empty the IPCB_R as the data has been localized
            self.__lowerIPCBStatusFlag(self.IPCBStatusFlag_AccessID_R) #Lower the IPCB_R Status Flag to indicate that it is now accessible
            
            self.t_IPCB_R_Localization = (time.perf_counter_ns() - proc_timer1) / 1e3
            self.ds_IPCB_R_ReadSize = asizeof.asizeof(IPCB_Read)
            #IPCB_R Messages Localization END ---------------------------------------------------------------------------------------------------------------------------------------------------------

            #Localized IPCB_R Messages Interpretation and Local Re-location ---------------------------------------------------------------------------------------------------------------------------
            proc_timer1 = time.perf_counter_ns()

            for msgID in IPCB_Read.keys():
                msgIDContents = msgID.split("-"); #IPC RELAY MESSAGE: {[0]: SENDER, [1]: msgType, [2]: SENDERREQUESTID}
                if (msgIDContents[1] == "PRD"):    #At PRD_IN[SENDER], add:  [KEY]: DATANAME, [ITEM]: DATACONTENT
                    self.PRD_IN[msgIDContents[0]][IPCB_Read[msgID][0]] = IPCB_Read[msgID][1]
                    if (IPCB_Read[msgID][0] != "IPCLOG"): self.__recordProcessLog("PRD FROM '{:s}'! [Data]: {:s}, [Content]: {:s}".format(msgIDContents[0], IPCB_Read[msgID][0], str(IPCB_Read[msgID][1])))
                elif (msgIDContents[1] == "DAR"):  #At DAR_IN[SENDER], add:  [KEY]: RECEIVALINDEX, [ITEM]: ([0]: DATANAME, [1]: SENDERREQUESTID, [2]: Result Timeout Trigger, [3]: Result nRetry)
                    self.DAR_IN[msgIDContents[0]][len(self.DAR_IN[msgIDContents[0]])] = (IPCB_Read[msgID][0], msgIDContents[2], IPCB_Read[msgID][1], IPCB_Read[msgID][2])
                    self.__recordProcessLog("DAR FROM '{:s}'! [Data]: {:s}, [tID]: {:s}".format(msgIDContents[0], IPCB_Read[msgID][0], msgIDContents[2]))
                elif (msgIDContents[1] == "DARR"): #At DARR_IN[SENDER], add: [KEY]: RECEIVALINDEX, [ITEM]: ([0]: DATACONTENT, [1]: REQUESTID)
                    transID = int(IPCB_Read[msgID][1])
                    if (transID in self.receptionDict): 
                        self.receptionDict[transID] = IPCB_Read[msgID][0] #Save the result to the appropriate reception position
                        self.TID_Completed.append(transID)
                    self.__recordProcessLog("DARR FROM '{:s}'! [Content]: {:s}, [tID]: {:d}".format(msgIDContents[0], str(IPCB_Read[msgID][0]), transID))
                elif (msgIDContents[1] == "FAR"):  #At FAR_IN[SENDER], add:  [KEY]: RECEIVALINDEX, [ITEM]: ([0]: FUNCTIONID,  [1]: FUNCTIONPARAMETERS, [2]:SENDERREQUESTID, [3]: Result Timeout Trigger, [4]: Result nRetry)
                    self.FAR_IN[msgIDContents[0]][len(self.FAR_IN[msgIDContents[0]])] = (IPCB_Read[msgID][0], IPCB_Read[msgID][1], msgIDContents[2], IPCB_Read[msgID][2], IPCB_Read[msgID][3])
                    self.__recordProcessLog("FAR FROM '{:s}'! [fID]: {:s}, [fParams]: {:s}, [tID]: {:s}".format(msgIDContents[0], IPCB_Read[msgID][0], str(IPCB_Read[msgID][1]), msgIDContents[2]))
                elif (msgIDContents[1] == "FARR"): #At FARR_IN[SENDER], add: [KEY]: RECEIVALINDEX, [ITEM]: ([0]: DATACONTENT, [1]: REQUESTID)
                    transID = int(IPCB_Read[msgID][1])
                    if (transID in self.receptionDict):
                        self.receptionDict[transID] = IPCB_Read[msgID][0] #Save the result to the appropriate reception position
                        self.TID_Completed.append(transID)
                    self.__recordProcessLog("FARR FROM '{:s}'! [fResult]: {:s}, [tID]: {:d}".format(msgIDContents[0], str(IPCB_Read[msgID][0]), transID))
                elif (msgIDContents[1] == "TRC"):
                    transID = int(msgIDContents[2])
                    self.TID_Availables.append(transID)
                    del self.TID_Issued[transID]
                    if (IPCB_Read[msgID] != "IPCLOG"): self.__recordProcessLog("TRC RECEIVED! [trcID]: {:d}".format(transID))

            #TID Timeout Check & Dispose and Re-post Attempt
            expiredTIDs = list()
            currentTime = time.perf_counter_ns()
            for tID in self.TID_Issued.keys():
                if ((self.TID_Issued[tID][2] != None) and (self.TID_Issued[tID][3] < (currentTime - self.TID_Issued[tID][2]))): #If tID timeout has occured
                    if ((self.TID_Issued[tID][5] == "INF") or (self.TID_Issued[tID][4] < self.TID_Issued[tID][5])): #Check if tID needs to be re-queued
                        msgType = self.TID_Issued[tID][0]
                        contentAsString = str(self.TID_Issued[tID][1]); stringRepLimit = 50
                        if (stringRepLimit < len(contentAsString)): contentAsString = contentAsString[:stringRepLimit] + "..."
                        self.__recordProcessLog("TID REPOST ATTEMPTED [{:d}]: ({:s}, {:s}, {:d}, {:d}, {:d}, {:s})".format(tID, msgType, contentAsString, self.TID_Issued[tID][2], self.TID_Issued[tID][3], self.TID_Issued[tID][4] + 1, str(self.TID_Issued[tID][5])))
                        print("TID REPOST ATTEMPTED [{:d}]: ({:s}, {:s}, {:d}, {:d}, {:d}, {:s})".format(tID, msgType, contentAsString, self.TID_Issued[tID][2], self.TID_Issued[tID][3], self.TID_Issued[tID][4] + 1, str(self.TID_Issued[tID][5])))
                        self.TID_Issued[tID][4] += 1
                        if   (msgType == "PRD"):  self.PRD_OUT[tID]  = self.TID_Issued[tID][1]
                        elif (msgType == "DAR"):  self.DAR_OUT[tID]  = self.TID_Issued[tID][1]
                        elif (msgType == "DARR"): self.DARR_OUT[tID] = self.TID_Issued[tID][1]
                        elif (msgType == "FAR"):  self.FAR_OUT[tID]  = self.TID_Issued[tID][1]
                        elif (msgType == "FARR"): self.FARR_OUT[tID] = self.TID_Issued[tID][1]
                    else:
                        msgType = self.TID_Issued[tID][0]
                        contentAsString = str(self.TID_Issued[tID][1]); stringRepLimit = 50
                        if (stringRepLimit < len(contentAsString)): contentAsString = contentAsString[:stringRepLimit] + "..."
                        self.__recordProcessLog("TID TIMEOUT DISPOSED [{:d}]: ({:s}, {:s}, {:d}, {:d}, {:d}, {:s})".format(tID, msgType, contentAsString, self.TID_Issued[tID][2], self.TID_Issued[tID][3], self.TID_Issued[tID][4], str(self.TID_Issued[tID][5])))
                        print("TID TIMEOUT DISPOSED [{:d}]: ({:s}, {:s}, {:d}, {:d}, {:d}, {:s})".format(tID, msgType, contentAsString, self.TID_Issued[tID][2], self.TID_Issued[tID][3], self.TID_Issued[tID][4], str(self.TID_Issued[tID][5])))
                        if   (msgType == "PRD"):  self.TID_Availables.append(tID);           expiredTIDs.append(tID)
                        elif (msgType == "DAR"):  self.receptionDict[tID] = "#TIDDISPOSED#"; self.TID_Completed.append(tID)
                        elif (msgType == "DARR"): self.TID_Availables.append(tID);           expiredTIDs.append(tID)
                        elif (msgType == "FAR"):  self.receptionDict[tID] = "#TIDDISPOSED#"; self.TID_Completed.append(tID)
                        elif (msgType == "FARR"): self.TID_Availables.append(tID);           expiredTIDs.append(tID)
            for tID in expiredTIDs: del self.TID_Issued[tID]

            self.t_IPCB_R_DataAnalysis = (time.perf_counter_ns() - proc_timer1)
        self.t_IPCB_R_ReadTotal = (time.perf_counter_ns() - proc_timer0)
            #Localized IPCB_R Messages Interpretation and Local Re-location END -----------------------------------------------------------------------------------------------------------------------

    #Local PRD_IN[manager] Format - [KEY]: DATA NAME, [ITEM]: DATA CONTENT
    #PRD Data is stored even after read
    def getPRD(self, targetManager, dataName = None):
        if targetManager in self.atm_Managers: 
            if dataName is None: return self.PRD_IN[targetManager]
            else: return self.PRD_IN[targetManager].get(dataName, None)
        else: return None
    #Local PRD_OUT[transID] = (dataName, dataContent)
    def sendPRD(self, dataName, dataContent, targetManager = "ALL", timeoutTrigger = 10000, nRetry = 3):
        transID = self.__issueTID()
        if (transID is not None):
            self.TID_Issued[transID] = ["PRD", (targetManager, dataName, dataContent), None, int(timeoutTrigger * 1e6), 0, nRetry]
            self.PRD_OUT[transID] = (targetManager, dataName, dataContent)
            contentAsString = str(dataContent)
            stringRepLimit = 50
            if (stringRepLimit < len(contentAsString)): contentAsString = contentAsString[:stringRepLimit] + "..."
            self.__recordProcessLog("PRD Registered! <[{:d}]:{:s}-{:s}>".format(transID, dataName, contentAsString))
        else:
            self.__recordProcessLog("PRDReg Rejected - tID Limit Reached")
    #Local DAR_IN[manager] Format - [KEY]: RECEIVALINDEX, [ITEM]: ([0]: DATA NAME, [1]: REQUEST ID)
    #Return the list of DARs as a tuple, return an empty tuple if no DAR exsits, DAR Data is removed upon reading
    def getDARs(self, targetManager):
        if (targetManager in self.atm_Managers) and (len(self.DAR_IN[targetManager]) > 0): 
            data = tuple(self.DAR_IN[targetManager].values())
            self.DAR_IN[targetManager].clear()
            return data
        else: return tuple()
    #Local DARR_OUT[transID] = (targetManager, dataContent, requestID)
    def sendDARR(self, targetManager, dataContent, requestID, timeoutTrigger, nRetry):
        transID = self.__issueTID()
        if (transID is not None):
            self.TID_Issued[transID] = ["DARR", (targetManager, dataContent, requestID), None, int(timeoutTrigger * 1e6), 0, nRetry]
            self.DARR_OUT[transID] = (targetManager, dataContent, requestID)
            contentAsString = str(dataContent)
            stringRepLimit = 50
            if (stringRepLimit < len(contentAsString)): contentAsString = contentAsString[:stringRepLimit] + "..."
            self.__recordProcessLog("DARR Registered! <[{:d}]:{:s}>".format(transID, contentAsString))
        else:
            self.__recordProcessLog("DARRReg Rejected - tID Limit Reached")
    #Local DARR_IN[manager] Format - [KEY]: RECEIVALINDEX, [ITEM]: ([0]: DATA CONTENT, [1]: REQUEST ID)
    def sendDAR(self, targetManager, dataName, timeoutTrigger = 10000, nRetry = 3, timeoutTrigger_result = 1000, nRetry_result = 3):
        transID = self.__issueTID()
        if (transID is not None): 
            self.TID_Issued[transID] = ["DAR", [targetManager, dataName, timeoutTrigger_result, nRetry_result], None, int(timeoutTrigger * 1e6), 0, nRetry]
            self.DAR_OUT[transID] = [targetManager, dataName, timeoutTrigger_result, nRetry_result]
            self.__recordProcessLog("DAR Registered! <[{:d}]:{:s}>".format(transID, str(self.DAR_OUT[transID])))
            return transID
        else:  
            self.__recordProcessLog("DARReg Rejected - tID Limit Reached")
            return None
    #Local FAR_IN[manager] Format - [KEY]: RECEIVALINDEX, [ITEM]: ([0]: FUNCTION ID, [1]: REQUEST ID)
    #Return the list of FARs as a tuple, return an empty tuple if no DAR exsits, FAR Data is removed upon reading
    def getFARs(self, targetManager):
        if (targetManager in self.atm_Managers) and (len(self.FAR_IN[targetManager]) > 0): 
            data = tuple(self.FAR_IN[targetManager].values())
            self.FAR_IN[targetManager].clear()
            return data
        else: return tuple()
    #Local FARR_OUT[transID] = (targetManager, functionResult, requestID)
    def sendFARR(self, targetManager, functionResult, requestID, timeoutTrigger, nRetry):
        transID = self.__issueTID()
        if (transID is not None):
            self.TID_Issued[transID] = ["FARR", (targetManager, functionResult, requestID), None, int(timeoutTrigger * 1e6), 0, nRetry]
            self.FARR_OUT[transID] = (targetManager, functionResult, requestID)
            contentAsString = str(functionResult)
            stringRepLimit = 50
            if (stringRepLimit < len(contentAsString)): contentAsString = contentAsString[:stringRepLimit] + "..."
            self.__recordProcessLog("FARR Registered! <[{:d}]:{:s}>".format(transID, contentAsString))
        else:
            self.__recordProcessLog("FARRreg Rejected - tID Limit Reached")
    #Local FARR_IN[manager] Format - [KEY]: RECEIVALINDEX, [ITEM]: ([0]: FUNCTION RESULT, [1]: REQUEST ID)
    def sendFAR(self, targetManager, functionID, functionParameters, timeoutTrigger = 10000, nRetry = 3, timeoutTrigger_result = 1000, nRetry_result = 3):
        transID = self.__issueTID()
        if (transID is not None): 
            self.TID_Issued[transID] = ["FAR", [targetManager, functionID, functionParameters, timeoutTrigger_result, nRetry_result], None, int(timeoutTrigger * 1e6), 0, nRetry]
            self.FAR_OUT[transID] = [targetManager, functionID, functionParameters, timeoutTrigger_result, nRetry_result]; 
            contentAsString = str(functionParameters)
            stringRepLimit = 50
            if (stringRepLimit < len(contentAsString)): contentAsString = contentAsString[:stringRepLimit] + "..."
            self.__recordProcessLog("FAR Registered! <[{:d}]:{:s}>".format(transID, contentAsString))
            return transID
        else:  
            self.__recordProcessLog("FARRg Rejected - tID Limit Reached")
            return None

    #Given a recptionID, return the received result if the result has arrived, or return '#NYR#' if the result has not been received yet
    def getResult(self, transID):
        if transID in self.TID_Completed: #Check if the result has arrived
            del self.TID_Issued[transID]
            self.TID_Completed.remove(transID)  #Remove the transID from the completed result list
            self.TID_Availables.append(transID) #Append the released transID back to the TID_Availables list
            return self.receptionDict.pop(transID)     #Remove the element associated with the transID
        else: return "#NYR#" #Not Yet Received

    def patchIPCB_T(self):
        proc_timer0 = time.perf_counter_ns()
        #

        #IPCB_T Messages Preparation for Sending ------------------------------------------------------------------------------------------------------------------------------------------------------
        proc_timer1 = time.perf_counter_ns()
        IPCB_Write = dict()
        #Appending PRD_OUT
        for tID in self.PRD_OUT: #Message Content: [key]: MANAGERNAME-"PRD"-ANNOUCEMENTID, [0]: RECEIVER, [1]: DATA NAME, [2]: DATA CONTENT
            IPCB_Write[self.managerName + "-PRD-" + str(tID)] = (self.PRD_OUT[tID][0], self.PRD_OUT[tID][1], self.PRD_OUT[tID][2]);                                             self.TID_Issued[tID][2] = time.perf_counter_ns()
        #Appending DAR_OUT
        for tID in self.DAR_OUT: #Message Content: [Key]: MANAGERNAME-"DAR"-REQUESTID, [0]: RECEIVER, [1]: DATA NAME, [2]: Result Timeout Trigger, [3]: Result nRetry
            IPCB_Write[self.managerName + "-DAR-" + str(tID)] = [self.DAR_OUT[tID][0], self.DAR_OUT[tID][1], self.DAR_OUT[tID][2], self.DAR_OUT[tID][3]];                       self.TID_Issued[tID][2] = time.perf_counter_ns()
        #Appending DARR_OUT
        for tID in self.DARR_OUT: #Message Content: [Key]: MANAGERNAME-"DARR"-REQUESTID, [0]: RECEIVER, [1]: DATA CONTENT, [2]: REQUESTID
            IPCB_Write[self.managerName + "-DARR-" + str(tID)] = [self.DARR_OUT[tID][0], self.DARR_OUT[tID][1], self.DARR_OUT[tID][2]];                                         self.TID_Issued[tID][2] = time.perf_counter_ns()
        #Appending FAR_OUT
        for tID in self.FAR_OUT: #Message Content: [Key]: MANAGERNAME-"FAR"-REQUESTID, [0]: RECEIVER, [1]: DATA NAME, [2]: FUNCTION PARAMETERS, [3]: Result Timeout Trigger, [4]: Result nRetry
            IPCB_Write[self.managerName + "-FAR-" + str(tID)] = [self.FAR_OUT[tID][0], self.FAR_OUT[tID][1], self.FAR_OUT[tID][2], self.FAR_OUT[tID][3], self.FAR_OUT[tID][4]]; self.TID_Issued[tID][2] = time.perf_counter_ns()
        #Appending FAR_OUT
        for tID in self.FARR_OUT: #Message Content: [Key]: MANAGERNAME-"FARR"-REQUESTID, [0]: RECEIVER, [1]: DATA CONTENT, [2]: REQUESTID
            IPCB_Write[self.managerName + "-FARR-" + str(tID)] = [self.FARR_OUT[tID][0], self.FARR_OUT[tID][1], self.FARR_OUT[tID][2]];                                         self.TID_Issued[tID][2] = time.perf_counter_ns()

        self.t_IPCB_T_Preparation = (time.perf_counter_ns() - proc_timer0)
        self.ds_IPCB_R_WriteSize = asizeof.asizeof(IPCB_Write)
        #IPCB_T Messages Preparation for Sending END --------------------------------------------------------------------------------------------------------------------------------------------------

        if (self.__isIPCBAvailable(self.IPCBStatusFlag_AccessID_T)):
            proc_timer1 = time.perf_counter_ns()
            self.__raiseIPCBStatusFlag(self.IPCBStatusFlag_AccessID_T) #Raise the IPCB_T Status Flag to indicate that it is being processed
            self.IPCB_T.update(IPCB_Write)                             #Upload the re-directed messages to IPCB_T
            self.__lowerIPCBStatusFlag(self.IPCBStatusFlag_AccessID_T) #Lower the IPCB_T Status Flag to indicate that it is now accessible
            self.t_IPCB_T_Patch = (time.perf_counter_ns() - proc_timer1)
        
            #Reset the local temporary buffers
            self.PRD_OUT.clear()
            self.DAR_OUT.clear()
            self.DARR_OUT.clear()
            self.FAR_OUT.clear()
            self.FARR_OUT.clear()

        #Function Timer Record
        self.t_IPCB_T_WriteTotal = (time.perf_counter_ns() - proc_timer0)

    def getProcessingTimes(self, mode = "print"):
        dataReadProcessingRate  = self.ds_IPCB_R_ReadSize  / self.t_IPCB_R_ReadTotal  * 1e9
        dataWriteProcessingRate = self.ds_IPCB_R_WriteSize / self.t_IPCB_T_WriteTotal * 1e9
        
        if (mode == "returnAsValues"):
            returnDict = {'ipcb_r_readTime':  self.t_IPCB_R_ReadTotal,
                          'ipcb_r_readSize':  self.ds_IPCB_R_ReadSize,
                          'ipcb_r_readRate':  dataReadProcessingRate,
                          'ipcb_t_writeTime': self.t_IPCB_T_WriteTotal,
                          'ipcb_t_writeSize': self.ds_IPCB_R_WriteSize,
                          'ipcb_t_writeRate': dataWriteProcessingRate}
            return returnDict
        else:
            if   self.ds_IPCB_R_ReadSize > (1024 * 1024): self.ds_IPCB_R_ReadSize = self.ds_IPCB_R_ReadSize / 1024 / 1024; readSizeUnit = "MB"
            elif self.ds_IPCB_R_ReadSize > 1024:          self.ds_IPCB_R_ReadSize = self.ds_IPCB_R_ReadSize / 1024;        readSizeUnit = "KB"
            else:                                                                                                          readSizeUnit = "Bytes"
            if   self.ds_IPCB_R_WriteSize > (1024 * 1024): self.ds_IPCB_R_WriteSize = self.ds_IPCB_R_WriteSize / 1024 / 1024; writeSizeUnit = "MB"
            elif self.ds_IPCB_R_WriteSize > 1024:          self.ds_IPCB_R_WriteSize = self.ds_IPCB_R_WriteSize / 1024;        writeSizeUnit = "KB"
            else:                                                                                                             writeSizeUnit = "Bytes"
            if   dataReadProcessingRate > (1024 * 1024 * 1024):  dataReadProcessingRate = dataReadProcessingRate / 1024 / 1024 / 1024;   dataReadProcessingRateUnit = "GB/s"
            elif dataReadProcessingRate > (1024 * 1024):         dataReadProcessingRate = dataReadProcessingRate / 1024 / 1024;          dataReadProcessingRateUnit = "MB/s"
            elif dataReadProcessingRate > (1024):                dataReadProcessingRate = dataReadProcessingRate / 1024;                 dataReadProcessingRateUnit = "KB/s"
            else:                                                                                                                        dataReadProcessingRateUnit = "Bytes/s"
            if   dataWriteProcessingRate > (1024 * 1024 * 1024): dataWriteProcessingRate = dataWriteProcessingRate / 1024 / 1024 / 1024; dataWriteProcessingRateUnit = "GB/s"
            elif dataWriteProcessingRate > (1024 * 1024):        dataWriteProcessingRate = dataWriteProcessingRate / 1024 / 1024;        dataWriteProcessingRateUnit = "MB/s"
            elif dataWriteProcessingRate > (1024):               dataWriteProcessingRate = dataWriteProcessingRate / 1024;               dataWriteProcessingRateUnit = "KB/s"
            else:                                                                                                                        dataWriteProcessingRateUnit = "Bytes/s"
            if (mode == "print"):
                self.programLogger.printPMessage("[{:s} IPC REPORT] \
                                                  \n   IPCB_R READ TOTAL:    {:.3f} us [{:.3f} {:s}] [{:.3f} {:s}] \
                                                  \n      DATA LOCALIZATION: {:.3f} us \
                                                  \n      DATA ANALYSIS:     {:.3f} us \
                                                  \n   IPCB_T WRITE TOTAL:   {:.3f} us [{:.3f} {:s}] [{:.3f} {:s}] \
                                                  \n      DATA PREPARATION:  {:.3f} us \
                                                  \n      DATA PATCH:        {:.3f} us".format(self.managerName, 
                                                                                               self.t_IPCB_R_ReadTotal / 1e3, self.ds_IPCB_R_ReadSize, readSizeUnit, dataReadProcessingRate, dataReadProcessingRateUnit,
                                                                                               self.t_IPCB_R_Localization / 1e3, 
                                                                                               self.t_IPCB_R_DataAnalysis / 1e3, 
                                                                                               self.t_IPCB_T_WriteTotal / 1e3, self.ds_IPCB_R_WriteSize, writeSizeUnit, dataWriteProcessingRate, dataWriteProcessingRateUnit,
                                                                                               self.t_IPCB_T_Preparation / 1e3,
                                                                                               self.t_IPCB_T_Patch / 1e3))
            elif (mode == "returnAsString"):
                returnDict = {'ipcb_r_readTime':  "{:.3f} us".format(self.t_IPCB_R_ReadTotal),
                              'ipcb_r_readSize':  "{:.3f} {:s}".format(self.ds_IPCB_R_ReadSize, readSizeUnit),
                              'ipcb_r_readRate':  "{:.3f} {:s}".format(dataReadProcessingRate, dataReadProcessingRateUnit),
                              'ipcb_t_writeTime': "{:.3f} us".format(self.t_IPCB_T_WriteTotal),
                              'ipcb_t_writeSize': "{:.3f} {:s}".format(self.ds_IPCB_R_WriteSize, writeSizeUnit),
                              'ipcb_t_writeRate': "{:.3f} {:s}".format(dataWriteProcessingRate, dataWriteProcessingRateUnit)}
                return returnDict

    def getProcessLog(self): self.processLogUpdated = False; return self.processLog
    def newProcessLogAvailable(self): return self.processLogUpdated

    def __isIPCBAvailable(self, IPCBStatusFlag_AccessID): return (self.IPCBStatusFlag[IPCBStatusFlag_AccessID] == 0)
    def __raiseIPCBStatusFlag(self, IPCBStatusFlag_AccessID): self.IPCBStatusFlag[IPCBStatusFlag_AccessID] = 1
    def __lowerIPCBStatusFlag(self, IPCBStatusFlag_AccessID): self.IPCBStatusFlag[IPCBStatusFlag_AccessID] = 0
    def __issueTID(self):
        if (len(self.TID_Availables) > 0):
            transID = self.TID_Availables.pop(0)
            self.receptionDict[transID] = None
            return transID
        else: 
            return None
    def __recordProcessLog(self, msg):
        if (self.printMessages == True): self.programLogger.printPMessage("[{:s} - IPC ASSISTANT] ".format(self.managerName) + msg)
        self.processLog.append((time.perf_counter_ns() - self.programLogger.getProgramStartTime(), msg))
        nOverstackedMsgs = len(self.processLog) - self.processLogLimit
        for i in range (nOverstackedMsgs): self.processLog.pop(0)
        self.processLogUpdated = True
    #Process-Cycle Functions End ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
#IPC ASSISTANT CLASS END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

