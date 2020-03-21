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
        hotpointActionTimeList = list()
        hotpointCmdList = list()
        waypointActionTimeList = list()
        waypointCmdList = list()
        recordVideoTime = None
        with open(self.filePath, 'r') as fin:
            # read motion
            motionClass, centerPoint = self.__parseMotion(fin)

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
                        hotpointActionTimeList.append(self.__parseHotpointActionTime(cmdClass))
                        hotpointCmdList.append(cmdClass)
                    elif cmdClass.cmd == 'WaypointMission':
                        waypointActionTimeList.append(self.__parseWaypointActionTime(cmdClass))
                        waypointCmdList.append(cmdClass)
                elif cmdClass.cmd in parseMetadata.__DroneProgrammingLabel:
                    pass
        
        return motionClass, centerPoint, hotpointCmdList


    def __parseMotion(self, fin):
        # extract init info
        blockChainNum = re.match(r'[\d]+ BlockNum ([\w-]+)', fin.readline().strip('\n')).group(1)
        hashCode = re.match(r'[\d]+ Hash ([\w-]+)', fin.readline().strip('\n')).group(1)
        innerRadius = int(re.match(r'[\d]+ Inner radius: (\d+)', fin.readline().strip('\n')).group(1))
        outerRadius = int(re.match(r'[\d]+ Outer radius: (\d+)', fin.readline().strip('\n')).group(1))
        startingPoint = re.match(r'[\d]+ STARTING_POINT ([\w]+)', fin.readline().strip('\n')).group(1)
        centerPoint_pattern = re.match(r'[\d]+ CENTER_POINT {"longitude":([-\d.]+),"latitude":([-\d.]+)}', fin.readline().strip('\n'))
        centerPoint = float(centerPoint_pattern.group(1)), float(centerPoint_pattern.group(2))
        droneAngle = abs(int(re.match(r'[\d]+ RESET_GIMBAL ([-\d]+)', fin.readline().strip('\n')).group(1)))
        startMotionAngle = int(re.match(r'[\d]+ Motion: Angle: (\d+)', fin.readline().strip('\n')).group(1))
        yaw = int(re.match(r'[\d]+ YAW ([-\d]+)', fin.readline().strip('\n')).group(1))
        
        assert re.match(r'[\d]+ (\w+)', fin.readline().strip('\n')).group(1) == 'START_RECORDING'
        motionAngle_pattern = re.compile(r'[\d]+ Motion: Angle: (\d+) (\w+)')
        motionAngle = [startMotionAngle]
        clockwiseDirect = [False]

        while True:
            tmpStr = fin.readline().strip('\n')
            cmd  = re.match('[\d]+ ([:\w]+).*', tmpStr).group(1)
            if cmd == 'IN_AND_OUT':
                pass
            elif cmd == 'Motion:':
                result = motionAngle_pattern.match(tmpStr)
                motionAngle.append(int(result.group(1)))
                if result.group(2)=='true':
                    clockwiseDirect.append(True)
                else:
                    clockwiseDirect.append(False)               
            elif cmd == 'STOP_RECORDING':
                break
        
        # print(re.match(r'[\d]+ ([\w ]+)', fin.readline().strip('\n')).group(1) == 'TIMELINE STARTED')

        return motion(blockChainNum, hashCode, innerRadius, outerRadius, motionAngle, clockwiseDirect, droneAngle), centerPoint


    def __parseCommand(self, cmdString, fin):
        # print(cmdString)
        cmdSplitted = cmdString.split(' ')
        timestamp = [int(cmdSplitted[0])] # starttime and endtime
        if cmdSplitted[1] in parseMetadata.__DroneFlyingStatusLabel:
            assert cmdSplitted[2].upper() == 'STARTED'
            cmd = cmdSplitted[1]
            interStatus = list()
            while True:
                tmpStr = fin.readline().strip('\n')
                tmpStrSplitted = tmpStr.split(' ')
                if tmpStrSplitted[1] == cmd and tmpStrSplitted[2].upper() == 'PROGRESSED':
                    # timestamp.append(int(tmpStrSplitted[0]))
                    pass
                elif tmpStrSplitted[1] == cmd and tmpStrSplitted[2].upper() == 'FINISHED':
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


    def __parseHotpointActionTime(self, cmdClass):
        return cmdClass.timestamp

    
    def __parseWaypointActionTime(self, cmdClass):
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
    parser = parseMetadata('new.metadata')
    motionClass, recordVideoTime, hotpointActionTimeList, waypointActionTimeList = parser.parse()
    print('motionAngle:', motionClass.motionAngle)
    print('clockwise', motionClass.clockwiseDirect)
    
    print('actual motion angle diff:')
    for i in range(len(motionClass.motionAngle)-1):
        print(getMotionAngleDiff(motionClass.motionAngle[i], motionClass.motionAngle[i+1], motionClass.clockwiseDirect[i+1]))
    
    print('recordVideoTime:', recordVideoTime)
    print('hotpointActionTimeList:', hotpointActionTimeList)    
    print('waypointActionTimeList:', waypointActionTimeList)