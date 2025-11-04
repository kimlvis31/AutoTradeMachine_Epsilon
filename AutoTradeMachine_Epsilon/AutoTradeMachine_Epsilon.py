#ATM Modules
import ATM_Epsilon_Logger
from ATM_Epsilon_Manager_AutoTrader      import manager_AutoTrader
from ATM_Epsilon_Manager_BinanceAPI      import manager_BinanceAPI
from ATM_Epsilon_Manager_DataAnalysis    import manager_DataAnalysis
from ATM_Epsilon_Manager_DataManagement  import manager_DataManagement
from ATM_Epsilon_Manager_GUI             import manager_GUI
from ATM_Epsilon_Manager_IPC             import manager_IPC
from ATM_Epsilon_Manager_IPC             import assistant_IPC
from ATM_Epsilon_Manager_SecurityControl import manager_SecurityControl

#Python Modules
import os
import multiprocessing
import time
import psutil
import types

path_PROJECT = os.path.dirname(os.path.realpath(__file__))

#IPC HANDLING FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def __DARHandler(m_MAIN, dataName):
    if dataName in m_MAIN['IPC_DARHANDLERDICTIONARY'].keys():
        if (type(m_MAIN['IPC_DARHANDLERDICTIONARY'][dataName]) == types.BuiltinFunctionType): return m_MAIN['IPC_DARHANDLERDICTIONARY'][dataName]()
        else:                                                                                 return m_MAIN['IPC_DARHANDLERDICTIONARY'][dataName]
    else: return None
def __FARHandler(m_MAIN, functionID, functionParams):
    if functionID in m_MAIN['IPC_FARHANDLERDICTIONARY'].keys():
        return m_MAIN['IPC_FARHANDLERDICTIONARY'][functionID](m_MAIN, functionParams)
#IPC HANDLING FUNCTIONS END ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#INTERNAL FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def __calculateProcessTimers(m_MAIN):
    if (m_MAIN['processTimersUpdateBuffer'] != None):
        ipcProcessingTimes = m_MAIN['IPC_ASSISTANT'].getProcessingTimes(mode = "returnAsValues")
        m_MAIN['processTimers']['records'].append({'recordTime': m_MAIN['processTimersUpdateBuffer'][0], 't_processLoop': m_MAIN['processTimersUpdateBuffer'][1],   't_process': m_MAIN['processTimersUpdateBuffer'][2],
                                                                                                         'ipcb_readTime':  ipcProcessingTimes['ipcb_r_readTime'],  'ipcb_readSize':  ipcProcessingTimes['ipcb_r_readSize'],  'ipcb_readRate':  ipcProcessingTimes['ipcb_r_readRate'],
                                                                                                         'ipcb_writeTime': ipcProcessingTimes['ipcb_t_writeTime'], 'ipcb_writeSize': ipcProcessingTimes['ipcb_t_writeSize'], 'ipcb_writeRate': ipcProcessingTimes['ipcb_t_writeRate']})
        recordLength = len(m_MAIN['processTimers']['records'])
        #Remove all the expired records
        while (True):
            recordTime = m_MAIN['processTimers']['records'][0]['recordTime']
            if (((time.perf_counter_ns() - recordTime) / 1e9) > m_MAIN['processTimerAvgStandard']): 
                m_MAIN['processTimers']['records'].pop(0); recordLength -= 1
                if (recordLength == 0): break;
            else: break;
        #Calculate the average
        if (recordLength > 0):
            t_processLoop_Sum = 0; t_process_Sum = 0
            readTime_Sum      = 0; readSize_Sum  = 0; readRate_Sum    = 0
            writeTime_Sum     = 0; writeSize_Sum = 0; writeRate_Sum   = 0
            for i in range (recordLength):
                t_processLoop_Sum += m_MAIN['processTimers']['records'][i]['t_processLoop']; t_process_Sum  += m_MAIN['processTimers']['records'][i]['t_process']
                readTime_Sum      += m_MAIN['processTimers']['records'][i]['ipcb_readTime']; readSize_Sum   += m_MAIN['processTimers']['records'][i]['ipcb_readSize']; readRate_Sum   += m_MAIN['processTimers']['records'][i]['ipcb_readRate']
                writeTime_Sum     += m_MAIN['processTimers']['records'][i]['ipcb_writeTime']; writeSize_Sum += m_MAIN['processTimers']['records'][i]['ipcb_writeSize']; writeRate_Sum += m_MAIN['processTimers']['records'][i]['ipcb_writeRate']
            m_MAIN['processTimers']['t_processLoop_avg']  = t_processLoop_Sum / recordLength; m_MAIN['processTimers']['t_process_avg']      = t_process_Sum / recordLength
            m_MAIN['processTimers']['ipcb_readTime_avg']  = readTime_Sum      / recordLength; m_MAIN['processTimers']['ipcb_readSize_avg']  = readSize_Sum  / recordLength; m_MAIN['processTimers']['ipcb_readRate_avg']  = readRate_Sum  / recordLength
            m_MAIN['processTimers']['ipcb_writeTime_avg'] = writeTime_Sum     / recordLength; m_MAIN['processTimers']['ipcb_writeSize_avg'] = writeSize_Sum / recordLength; m_MAIN['processTimers']['ipcb_writeRate_avg'] = writeRate_Sum / recordLength
            m_MAIN['processTimers']['nRecords'] = recordLength; m_MAIN['processTimers']['updated'] = True
        else: m_MAIN['processTimers']['nRecords'] = 0
#INTERNAL FUNCTIONS END -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#MAIN PROCESS ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def process_MAIN(m_MAIN):
    #IPC Control ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    m_MAIN['IPC_ASSISTANT'].readIPCB_R()
    for targetManager in m_MAIN['IPC_ASSISTANT'].atm_Managers:
        #Process DARs and send DARRs
        for DAR in m_MAIN['IPC_ASSISTANT'].getDARs(targetManager):  #DAR:  [0]: dataName, [1]: requestID, [2]: timeoutTrigger_result, [3]: nRetry_result
            m_MAIN['IPC_ASSISTANT'].sendDARR(targetManager, __DARHandler(m_MAIN, DAR[0]), DAR[1], timeoutTrigger = DAR[2], nRetry = DAR[3]) #Activate the requested function and Send FARR to the corresponding targetManager, attaching the requestID
        #Process FARs and send FARRs
        for FAR in m_MAIN['IPC_ASSISTANT'].getFARs(targetManager):  #FAR:  [0]: functionID, [1]: functionParameters, [2]: requestID, [3]: timeoutTrigger_result, [4]: nRetry_result
            m_MAIN['IPC_ASSISTANT'].sendFARR(targetManager, __FARHandler(m_MAIN, FAR[0], FAR[1]), FAR[2], timeoutTrigger = FAR[3], nRetry = FAR[4]) #Activate the requested function and Send FARR to the corresponding targetManager, attaching the requestID

    #m_MAIN['PROGRAMLOGGER'].printPMessage("TEST")

    m_MAIN['IPC_ASSISTANT'].patchIPCB_T() #Place near the end of the process, patch IPCB Data
    __calculateProcessTimers(m_MAIN)
    return m_MAIN['processRepeat']
#MAIN PROCESS END -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



#GENERAL MANAGER PROCESS ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def processManager(programLogger, p_DLT, atm_managerName, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T):
    #Manager Module Initialization
    atm_manager = None; atm_Managers.append("MAIN")
    if (atm_managerName == "AUTOTRADER"):        atm_manager = manager_AutoTrader(programLogger, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T)
    elif (atm_managerName == "BINANCEAPI"):      atm_manager = manager_BinanceAPI(programLogger, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T)
    elif (atm_managerName == "DATAANALYSIS"):    atm_manager = manager_DataAnalysis(programLogger, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T)
    elif (atm_managerName == "DATAMANAGEMENT"):  atm_manager = manager_DataManagement(programLogger, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T)
    elif (atm_managerName == "SECURITYCONTROL"): atm_manager = manager_SecurityControl(programLogger, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T)

    #Process Control Variables Initialization
    process_Continue = True
    loop_lastStart = time.perf_counter_ns()
    #Process Control
    while (process_Continue == True):
        loop_elapsed = time.perf_counter_ns() - loop_lastStart
        if (loop_elapsed > p_DLT): #If more time has passed than the DLT since the last loop start
            loop_lastStart = time.perf_counter_ns() #Re-set the loop timer
            process_start = time.perf_counter_ns() #Start Processing Time Counter
            process_Continue = atm_manager.process() #Start the Manager Process and retrieve the process status
            process_elapsed = time.perf_counter_ns() - process_start #Record Processing Time
            atm_manager.recordProcessTimers(loop_elapsed, process_elapsed) #Pass processing times to the manager
            #print("[{:s}] Last Loop Time: {:.3f} ms, Last Processing Time: {:.1f} us".format(atm_managerName, loop_elapsed / 1e6, process_elapsed / 1e3))
            delay = (p_DLT - process_elapsed) / 1e9 #Calculate the leftover time
            if (delay > 0): time.sleep(delay)       #If the processing time is less than the DLT, put the process to sleep for the leftover time
            
    #Termination Sequence

#GENERAL MANAGER PROCESS END ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#GUI MANAGER PROCESS --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def processManager_GUI(programLogger, p_DLT, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T):
    #Manager Module Initialization
    atm_Managers.append("MAIN")
    m_GUI = manager_GUI(programLogger, atm_Managers, IPCB_R, IPCB_T, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessID_R, IPCBStatusFlag_AccessID_T)
    
    #Process Control Variables Initialization
    p_CVs = {'p_Continue': True, 'l_lastStart': time.perf_counter_ns()}

    #Process Control
    def m_GUI_mainer0():
        p_CVs['l_elapsed'] = time.perf_counter_ns() - p_CVs['l_lastStart']
        if (p_CVs['l_elapsed'] > p_DLT): #If more time has passed than the DLT since the last loop start
            p_CVs['l_lastStart'] = time.perf_counter_ns() #Re-set the loop timer
            p_CVs['p_start']     = time.perf_counter_ns() #Start Processing Time Counter
            p_CVs['p_Continue']  = m_GUI.process() #Start the Manager Process and retrieve the process status
            p_CVs['p_elapsed']   = time.perf_counter_ns() - p_CVs['p_start'] #Record processing time
            p_CVs['p_Tk_start']  = time.perf_counter_ns() #Start Tk Processing Time Counter
            m_GUI.window.after_idle(m_GUI_mainer1) #Make a reservation of function call for 'm_GUI_mainer1()' once the Tk goes to idle
        else:
            m_GUI.window.after_idle(m_GUI_mainer0) #If the timer has not been expired yet, repeat the loop once the Tk goes to idle
    def m_GUI_mainer1():
        p_CVs['p_Tk_elapsed'] = time.perf_counter_ns() - p_CVs['p_Tk_start'] #Start Tk Processing Time Counter
        m_GUI.recordProcessTimers(p_CVs['l_elapsed'], p_CVs['p_elapsed'], p_CVs['p_Tk_elapsed']) #Pass processing times to the manager
        #print("[{:s}] Last Loop Time: {:.3f} ms, Last Processing Time: {:.1f} us, Last Tk Processing Time: {:.1f} us, Total Processing Time: {:.1f} us".format("GUI", p_CVs['l_elapsed'] / 1e6, p_CVs['p_elapsed'] / 1e3, p_CVs['p_Tk_elapsed'] / 1e3, (p_CVs['p_elapsed'] + p_CVs['p_Tk_elapsed']) / 1e3))
        if (p_CVs['p_Continue'] == True): m_GUI_mainer0() #If the manager process returned true, repeat the process
        else: m_GUI.window.destroy()                      #If the manager process returned false, destory the window, entering 'Termination Sequence' below

    m_GUI.window.after(1, m_GUI_mainer0) #Start the process loop after one second
    m_GUI.window.mainloop() #Start Tk mainloop

    #Termination Sequence

#GUI MANAGER PROCESS END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#IPC MANAGER PROCESS --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def processManager_IPC(programLogger, p_DLT, atm_Managers, IPCBs, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessIDs):
    #Manager Module Initialization
    atm_Managers.append("MAIN")
    m_IPC = manager_IPC(programLogger, atm_Managers, IPCBs, IPCBStatusFlag_shmName, IPCBStatusFlag_AccessIDs)

    #Process Control Variables Initialization
    process_Continue = True
    loop_lastStart = time.perf_counter_ns()
    #Process Control
    while (process_Continue == True):
        loop_elapsed = time.perf_counter_ns() - loop_lastStart
        if (loop_elapsed > p_DLT): #If more time has passed than the DLT since the last loop start
            loop_lastStart = time.perf_counter_ns() #Re-set the loop timer
            process_start = time.perf_counter_ns() #Start Processing Time Counter
            process_Continue = m_IPC.process() #Start the Manager Process and retrieve the process status
            process_elapsed = time.perf_counter_ns() - process_start #Record Processing Time
            m_IPC.recordProcessTimers(loop_elapsed, process_elapsed) #Pass processing times to the manager
            #print("[{:s}] Last Loop Time: {:.3f} ms, Last Processing Time: {:.1f} us".format("IPC", loop_elapsed / 1e6, process_elapsed / 1e3))
            delay = (p_DLT - process_elapsed) / 1e9 #Calculate the leftover time
            if (delay > 0): time.sleep(delay)       #If the processing time is less than the DLT, put the process to sleep for the leftover time

    #Termination Sequence
            
#IPC MANAGER PROCESS END ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------









#PROGRAM LIFE-CYCLE ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    #Record Program Start Time and Initialize Program Logger
    PROGRAMSTARTTIME = time.perf_counter_ns()
    programLogger = ATM_Epsilon_Logger.programLogger(PROGRAMSTARTTIME)
    programLogger.printPMessage("ATM_EPSILON STARTED! [{:s}]".format(time.ctime()))

    #Get System Information
    n_CORES = os.cpu_count()
    print("   AVAILABLE CPU PROCESSORS: {:d}".format(n_CORES))

    #Define the program managers and settings
    atm_Managers = ["AUTOTRADER", "BINANCEAPI", "DATAANALYSIS", "DATAMANAGEMENT", "GUI", "SECURITYCONTROL", "IPC"]
     #Minimum Loop Time [in miliseconds]
    p_DLT = {"MAIN":            10 * 1e6,
             "IPC":             10 * 1e6,
             "AUTOTRADER":      10 * 1e6,
             "BINANCEAPI":      50 * 1e6,
             "DATAANALYSIS":    10 * 1e6,
             "DATAMANAGEMENT":  10 * 1e6,
             "GUI":             10 * 1e6,
             "SECURITYCONTROL": 10 * 1e6}

    #Create Shared Memory Dictionaries for IPCB and IPCB Status Flag
    mpManager = multiprocessing.Manager()
    IPCBs = dict()
    IPCBStatusFlag_AccessIDs = dict()
    IPCBs["MAIN_R"] = mpManager.dict() #For Receival
    IPCBs["MAIN_T"] = mpManager.dict() #For Transmission
    IPCBStatusFlag_AccessIDs["MAIN_R"] = 0; IPCBStatusFlag_AccessIDs["MAIN_T"] = 1 #IPCBStatusFlagAccessIDs for MAIN Process
    accessID_IssueIndex = 2
    for managerType in atm_Managers:
        IPCBs[managerType + "_R"] = mpManager.dict() #For Receival
        IPCBs[managerType + "_T"] = mpManager.dict() #For Transmission
        IPCBStatusFlag_AccessIDs[managerType + "_R"] = accessID_IssueIndex; accessID_IssueIndex += 1;
        IPCBStatusFlag_AccessIDs[managerType + "_T"] = accessID_IssueIndex; accessID_IssueIndex += 1;
    IPCBStatusFlagMemory = multiprocessing.shared_memory.SharedMemory(name = "ATM_EPSILON_IPCBStatusFlagMemory", create = True, size = len(IPCBs))
    IPCBStatusFlag = IPCBStatusFlagMemory.buf

    #Create Processes
    processes = dict()
    for managerType in atm_Managers:
        if   (managerType == "IPC"): processes[managerType] = multiprocessing.Process(name = "IPC", target = processManager_IPC, 
                                                                                      args = (programLogger, p_DLT["IPC"],
                                                                                              atm_Managers, 
                                                                                              IPCBs, 
                                                                                              IPCBStatusFlagMemory.name, 
                                                                                              IPCBStatusFlag_AccessIDs))
        elif (managerType == "GUI"): processes[managerType] = multiprocessing.Process(name = "GUI", target = processManager_GUI, 
                                                                                      args = (programLogger, p_DLT["GUI"],
                                                                                              atm_Managers, 
                                                                                              IPCBs[managerType + "_R"], IPCBs[managerType + "_T"], 
                                                                                              IPCBStatusFlagMemory.name, 
                                                                                              IPCBStatusFlag_AccessIDs[managerType + "_R"], IPCBStatusFlag_AccessIDs[managerType + "_T"]))
        else:                        processes[managerType] = multiprocessing.Process(name = managerType, target = processManager, 
                                                                                      args = (programLogger, p_DLT[managerType],
                                                                                              managerType, 
                                                                                              atm_Managers, 
                                                                                              IPCBs[managerType + "_R"], IPCBs[managerType + "_T"], 
                                                                                              IPCBStatusFlagMemory.name, 
                                                                                              IPCBStatusFlag_AccessIDs[managerType + "_R"], IPCBStatusFlag_AccessIDs[managerType + "_T"]))
    programLogger.printPMessage("ATM_EPSILON STARTED!")
        
    #Main Process Control Variables and Management Data Initialization
    p_CVs_MAIN = {'p_Continue': True, 'l_lastStart': time.perf_counter_ns()}

    def __initializeFARs():
        farDictionary = dict()
        def __FA_TESTFUNCTION(m_MAIN, functionParams):
            try: return ("[MAIN] FAR TEST SUCCESSFUL with Function Params: " + str(functionParams))
            except Exception as e: print("ERROR OCCURED WHILE PROCESSING FUNCTION ACTIVATION RESULT", e)
        farDictionary["FAR TEST"] = __FA_TESTFUNCTION
        def __FA_GET_PRD(m_MAIN, functionParams):
            prdFromManager = m_MAIN['IPC_ASSISTANT'].getPRD(functionParams[0])
            for key in prdFromManager.keys():
                stringVer = str(prdFromManager[key])
                if len(stringVer) > functionParams[1]: prdFromManager[key] = stringVer[:functionParams[1]]
            return prdFromManager
        farDictionary["GET_PRD"] = __FA_GET_PRD
        def __FA_GET_IPCLOG(m_MAIN, functionParams):
            return m_MAIN['IPC_ASSISTANT'].getProcessLog()
        farDictionary["GET_IPCLOG"] = __FA_GET_IPCLOG
        def __FA_GET_IPC_TIDAVAILABILITY(m_MAIN, functionParams): 
            return (len(m_MAIN['IPC_ASSISTANT'].TID_Availables), m_MAIN['IPC_ASSISTANT'].TIDIssueLimit)
        farDictionary["GET_IPC_TIDAVAILABILITY"] = __FA_GET_IPC_TIDAVAILABILITY
        def __FA_EDIT_PTIMERAVGSTANDARD(m_MAIN, functionParams):
            m_MAIN['processTimerAvgStandard'] = functionParams; return m_MAIN['processTimerAvgStandard']
        farDictionary["EDIT_PTIMERAVGSTANDARD"] = __FA_EDIT_PTIMERAVGSTANDARD
        def __FA_GET_PTIMER_AVG(m_MAIN, functionParams):
            returnDict = {'t_processLoop_avg':  m_MAIN['processTimers']['t_processLoop_avg'], 
                          't_process_avg':      m_MAIN['processTimers']['t_process_avg'], 
                          'ipcb_readTime_avg':  m_MAIN['processTimers']['ipcb_readTime_avg'], 
                          'ipcb_readSize_avg':  m_MAIN['processTimers']['ipcb_readSize_avg'],
                          'ipcb_readRate_avg':  m_MAIN['processTimers']['ipcb_readRate_avg'], 
                          'ipcb_writeTime_avg': m_MAIN['processTimers']['ipcb_writeTime_avg'], 
                          'ipcb_writeSize_avg': m_MAIN['processTimers']['ipcb_writeSize_avg'], 
                          'ipcb_writeRate_avg': m_MAIN['processTimers']['ipcb_writeRate_avg'], 
                          'nRecords':           m_MAIN['processTimers']['nRecords']}
            return returnDict
        farDictionary["GET_PTIMERS_AVG"] = __FA_GET_PTIMER_AVG
        def __FA_GET_PTIMER_LAST(m_MAIN, functionParams):
            m_MAIN['processTimers']['updated'] = False
            if (0 < m_MAIN['processTimers']['nRecords']): return m_MAIN['processTimers']['records'][-1]
            else                                        : return None
        farDictionary["GET_PTIMERS_LAST"] = __FA_GET_PTIMER_LAST
        def __FA_GET_PTIMER_AVGSTANDARD(m_MAIN, functionParams):
            return m_MAIN['processTimerAvgStandard']
        farDictionary["GET_PTIMERS_AVGSTANDARD"] = __FA_GET_PTIMER_AVGSTANDARD
        def __FA_GET_PLOG(m_MAIN, functionParams):
            return m_MAIN['PROGRAMLOGGER'].getPMessages()
        farDictionary["GET_PLOG"] = __FA_GET_PLOG

        return farDictionary

    m_MAIN = {'IPC_ASSISTANT': assistant_IPC(programLogger, "MAIN", atm_Managers, IPCBs["MAIN_R"], IPCBs["MAIN_T"], IPCBStatusFlagMemory.name, IPCBStatusFlag_AccessIDs["MAIN_R"], IPCBStatusFlag_AccessIDs["MAIN_T"]),
              'IPC_DARHANDLERDICTIONARY': {"DAR TEST": "[MAIN] DAR TEST SUCCESSFUL", "ATMMANAGERS": atm_Managers},
              'IPC_FARHANDLERDICTIONARY': __initializeFARs(),
              'PROGRAMLOGGER': programLogger,
              'processRepeat': True,
              'processTimersUpdateBuffer': None,
              'processTimers': {'updated': False, 'records': list(), 't_processLoop_avg':  0, 't_process_avg':      0, 
                                                                     'ipcb_readTime_avg':  0, 'ipcb_readSize_avg':  0, 'ipcb_readRate_avg':  0,
                                                                     'ipcb_writeTime_avg': 0, 'ipcb_writeSize_avg': 0, 'ipcb_writeRate_avg': 0, 'nRecords': 0},
              'processTimerAvgStandard': 1}

    #Start Processes
    programLogger.printPMessage("STARTING PROCESSES...")
    processes["IPC"].start()
    programLogger.printPMessage("   PROCESS STARTED! [IPC]")
    procStatus_IPC = None
    while (procStatus_IPC != "ACTIVE"): m_MAIN['IPC_ASSISTANT'].readIPCB_R(); procStatus_IPC = m_MAIN['IPC_ASSISTANT'].getPRD("IPC", "PROC_STATUS")

    processes["GUI"].start()
    programLogger.printPMessage("   PROCESS STARTED! [GUI]")
    procStatus_GUI = None
    while (procStatus_GUI != "ACTIVE"): m_MAIN['IPC_ASSISTANT'].readIPCB_R(); procStatus_GUI = m_MAIN['IPC_ASSISTANT'].getPRD("GUI", "PROC_STATUS")

    for managerName in processes.keys():
        if ((managerName != "GUI") and (managerName != "IPC")):
            processes[managerName].start()
            programLogger.printPMessage("   PROCESS STARTED! [{:s}]".format(managerName))
            
    m_MAIN['IPC_ASSISTANT'].sendPRD("PROC_STATUS", "ACTIVE"); m_MAIN['IPC_ASSISTANT'].patchIPCB_T() #Process Status Report
    #Main Process Loop
    programLogger.printPMessage("   MAIN PROCESS LOOP STARTED!")
    while (p_CVs_MAIN['p_Continue'] == True):
        p_CVs_MAIN['l_elapsed'] = time.perf_counter_ns() - p_CVs_MAIN['l_lastStart'] 
        if (p_CVs_MAIN['l_elapsed'] > p_DLT["MAIN"]):
            p_CVs_MAIN['l_lastStart'] = time.perf_counter_ns() #Re-set the loop timer
            p_CVs_MAIN['p_start'] = time.perf_counter_ns() #Start Processing Time Counter
            p_CVs_MAIN['p_Continue'] = process_MAIN(m_MAIN) #Start the MAIN Process and retrieve the process status
            p_CVs_MAIN['p_elapsed'] = time.perf_counter_ns() - p_CVs_MAIN['p_start'] #Record Processing Time
            m_MAIN['processTimersUpdateBuffer'] = (time.perf_counter_ns(), p_CVs_MAIN['l_elapsed'], p_CVs_MAIN['p_elapsed']) #Pass processing times to the MAIN data dictionary
            #print("[{:s}] Last Loop Time: {:.3f} ms, Last Processing Time: {:.3f} us".format("MAIN", p_CVs_MAIN['l_elapsed'] / 1e6, p_CVs_MAIN['p_elapsed'] / 1e3))
            delay = (p_DLT["MAIN"] - p_CVs_MAIN['p_elapsed']) / 1e9 #Calculate the leftover time
            if (delay > 0): time.sleep(delay); #If the processing time is less than the DLT, put the process to sleep for the leftover time

    #Wait For Processes Termination
    for process in processes.values():
        process.join()

#PROGRAM LIFE-CYCLE END -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------










