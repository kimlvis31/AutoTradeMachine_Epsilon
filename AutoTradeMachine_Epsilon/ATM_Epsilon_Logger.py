import time

class programLogger():
    def __init__(self, programStartTime):
        self.t_programStart = time.perf_counter_ns()
        self.t_processTimers = dict()
        self.msgs = list()
        self.msgs_maxN = 2000

    def printPMessage(self, msg, showTime = True, termPrint = True):
        msg = str(msg)
        if (showTime == True): displayMsg = "[{:s}] {:s}".format(self.__getCurrentProgramTime(), msg)
        else:                  displayMsg = msg
        if (termPrint == True): print(displayMsg)
        if (len(self.msgs) < self.msgs_maxN): self.msgs.append(displayMsg)
        else:                                 self.msgs.pop(0); self.msgs.append(displayMsg)
    def getPMessages(self): return self.msgs
    def getPMsgLength(self): return len(self.msgs)
    def clearPMessages(self): self.msgs.clear()

    def setProgramStartTime(self, newStartTime): self.t_programStart = newStartTime
    def getProgramStartTime(self): return self.t_programStart

    def __getCurrentProgramTime(self):
        currentProgramTime = time.perf_counter_ns() - self.t_programStart
        #day = 0; hour = 23; minute = 59; second = 59.9
        #currentProgramTime = 1e9 * (86400 * day + 3600 * hour + 60 * minute + second)
        if currentProgramTime >= (1e9 * 86400): #Bigger than an hour
            currentProgramTime = currentProgramTime / 1e9
            days    = int(currentProgramTime / (86400))
            hours   = int((currentProgramTime - (days * 86400)) / 3600)
            minutes = int((currentProgramTime - (days * 86400) - (hours * 3600)) / 60)
            seconds = currentProgramTime % (60)
            return ("{:d} Days {:d} Hours {:d} Min {:.3f} s".format(days, hours, minutes, seconds))
        elif currentProgramTime >= (1e9 * 3600): #Bigger than an hour
            currentProgramTime = currentProgramTime / 1e9
            hours   = int(currentProgramTime / (3600))
            minutes = int((currentProgramTime - (hours * 3600)) / 60)
            seconds = currentProgramTime % (60)
            return ("{:d} Hours {:d} Min {:.3f} s".format(hours, minutes, seconds))
        elif currentProgramTime >= (1e9 * 60): #Bigger than a minute
            currentProgramTime = currentProgramTime / 1e9
            minutes = int(currentProgramTime / 60)
            seconds = currentProgramTime % (60)
            return ("{:d} Min {:.3f} s".format(minutes, seconds))
        elif currentProgramTime >= 1e9: #Bigger than a second
            return ("{:.3f} s".format(currentProgramTime / 1e9))
        elif currentProgramTime >= 1e6: #Bigger than a milisecond
            return ("{:.3f} ms".format(currentProgramTime / 1e6))
        elif currentProgramTime >= 1e3: #Bigger than a microsecond
            return ("{:.3f} us".format(currentProgramTime / 1e3))
        else:
            return ("{:.3f} ns".format(currentProgramTime))