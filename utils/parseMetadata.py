import re
from motion import motion
from command import command

class parseMetadata(object):

    __DroneFlyingStatusLabel = ['GimbalAttitudeAction', 'GoToAction', 'RecordVideoAction',
    'WaypointMission', 'NewHotpointAction', 'AircraftYawAction']

    __DroneProgrammingLabel = ['STARTING_POINT', 'STARTING_HEADING', 'CENTER_POINT', 
    'RESET_GIMBAL', 'START_RECORDING', 'IN_AND_OUT', 'START_HOTPOINT', 'STOP_RECORDING',
    'VIDEO_FILENAME']

    def __init__(self, metadataFilePath):
        self.filePath = metadataFilePath


    def parse(self):
        hotPointActionTimeList = list()
        hotpointCmdList = list()
        waypointActionTimeList = list()
        waypointCmdList = list()
        recordVideoTime = None
        with open(self.filePath, 'r') as fin:
            # read motion
            motionClass = self.__parseMotion(fin)

            while True:
                cmdString = fin.readline()
                if cmdString=='':
                    break
                else:
                    cmdString = cmdString.strip('\n')
                    if self.__isCommand(cmdString) == False:
                        continue
                
                cmdClass = self.__parseCommand(cmdString, fin)
                if cmdClass.cmd in parseMetadata.__DroneFlyingStatusLabel:
                    if cmdClass.cmd == 'RecordVideoAction':
                        if recordVideoTime==None: # only record the first RecordVideoAction
                            recordVideoTime = self.__parseRecordVideoAction(cmdClass)
                    elif cmdClass.cmd == 'NewHotpointAction':
                        hotPointActionTimeList.append(self.__parseHotPointActionTime(cmdClass))
                        hotpointCmdList.append(cmdClass)
                    elif cmdClass.cmd == 'WaypointMission':
                        waypointActionTimeList.append(self.__parseWayPointActionTime(cmdClass))
                        waypointCmdList.append(cmdClass)
                elif cmdClass.cmd in parseMetadata.__DroneProgrammingLabel:
                    pass
        
        return motionClass, recordVideoTime, hotPointActionTimeList, waypointActionTimeList, (hotpointCmdList, waypointCmdList)


    def __parseMotion(self, fin):
        fin.readline()
        blockChainNum = int(re.match(r'BlockNum: (\d+)', fin.readline().strip('\n')).group(1))
        hashCode = re.match(r'Hash: ([\w\d]+)', fin.readline().strip('\n')).group(1)
        innerRadius = int(re.match(r'Inner radius: (\d+)', fin.readline().strip('\n')).group(1))
        outerRadius = int(re.match(r'Outer radius: (\d+)', fin.readline().strip('\n')).group(1))
        motionAngle = []
        clockwiseDirect = []
        pattern = re.compile(r'Motion: Angle: (\d+) Clockwise: (\w+)')
        while True:
            tmpStr = fin.readline()
            if tmpStr == '\n':
                break
            else:
                tmpStr = tmpStr.strip('\n')
            result = pattern.match(tmpStr)
            motionAngle.append(int(result.group(1)))
            if result.group(2)=='true':
                clockwiseDirect.append(True)
            else:
                clockwiseDirect.append(False)

        # WARNING: droneAngle here is hardcoded, and is not read from the metadata! This will be fixed in the parser
        # for the new metadata format. Hard to fix in the old format.
        return motion(blockChainNum, hashCode, innerRadius, outerRadius, motionAngle, clockwiseDirect, droneAngle=50)


    def __parseCommand(self, cmdString, fin):
        # print(cmdString)
        cmdSplitted = cmdString.split(' ')
        timestamp = [int(cmdSplitted[0])] # starttime and endtime
        if cmdSplitted[1] in parseMetadata.__DroneFlyingStatusLabel:
            assert cmdSplitted[2]=='STARTED'
            cmd = cmdSplitted[1]
            interStatus = list()
            while True:
                tmpStr = fin.readline().strip('\n')
                tmpStrSplitted = tmpStr.split(' ')
                if tmpStrSplitted[1] == cmd and tmpStrSplitted[2] == 'PROGRESSED':
                    # timestamp.append(int(tmpStrSplitted[0]))
                    pass
                elif tmpStrSplitted[1] == cmd and tmpStrSplitted[2] == 'FINISHED':
                    timestamp.append(int(tmpStrSplitted[0]))
                    break
                else:
                    interStatus.append(tmpStr)
            cmdClass = command(timestamp, cmd, interStatus, None)

        elif cmdSplitted[1] in parseMetadata.__DroneProgrammingLabel:
            cmd = cmdSplitted[1]
            cmdClass = command(timestamp, cmd, None, cmd[2:])

        return cmdClass


    def __isCommand(self, cmdString):
        cmdSplitted = cmdString.split(' ')
        if cmdSplitted[1] in parseMetadata.__DroneFlyingStatusLabel or\
           cmdSplitted[1] in parseMetadata.__DroneProgrammingLabel:
            return True
        else:
            return False


    def __parseRecordVideoAction(self, cmdClass):
        return cmdClass.timestamp


    def __parseHotPointActionTime(self, cmdClass):
        return cmdClass.timestamp

    
    def __parseWayPointActionTime(self, cmdClass):
        return cmdClass.timestamp
    

def getMotionAngleDiff(a, b, clockwiseDirect):
    if clockwiseDirect == True:
        if a <= b:
            return b-a
        else:
            return 360-a+b
    else:
        if a <= b:
            return a+360-b
        else:
            return a-b



if __name__=='__main__':
    parser = parseMetadata('0179.metadata')
    motionClass, recordVideoTime, hotPointActionTimeList, waypointActionTimeList = parser.parse()
    print('motionAngle:', motionClass.motionAngle)
    print('clockwise', motionClass.clockwiseDirect)
    
    print('actual motion angle diff:')
    for i in range(len(motionClass.motionAngle)-1):
        print(getMotionAngleDiff(motionClass.motionAngle[i], motionClass.motionAngle[i+1], motionClass.clockwiseDirect[i+1]))
    
    print('recordVideoTime:', recordVideoTime)
    print('hotPointActionTimeList:', hotPointActionTimeList)    
    print('waypointActionTimeList:', waypointActionTimeList)