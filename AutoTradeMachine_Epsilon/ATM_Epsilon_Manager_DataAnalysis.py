from ATM_Epsilon_Manager_IPC import assistant_IPC

import time
import sys
import timeit
import numpy
import time
import types
import pprint

MANAGERNAME = "DATAANALYSIS"

class manager_DataAnalysis:
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
        self.darHanlderDictionary = {"DAR TEST": "[DATA ANALYSIS] DAR TEST SUCCESSFUL", "ATMMANAGERS": self.atm_Managers, "PTIMERS": self.processTimers, "PTIMERS_AVGSTANDARD": self.processTimerAvgStandard}
        self.farHanlderDictionary = dict(); self.__initializeFARs()
        self.IPCResultHandlers = dict()
        self.assistantIPC.sendPRD("PROC_STATUS", "INITIALIZING_0_IPC ASSISTANT INITIALIZED"); self.assistantIPC.patchIPCB_T(); self.programLogger.printPMessage("IPC ASSISTANT INITIALIZED") #Process Status Report
        
        #Timer Function Assignments
        self.timerFunctions = dict()

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
            try: return ("[DATA ANALYSIS] FAR TEST SUCCESSFUL with Function Params: " + str(functionParams))
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
                    except Exception as e: print(e)
            return self.repeat

    #Auxillary Classes END --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------