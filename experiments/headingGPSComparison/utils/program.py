class program:

    def __init__(self, cmd):
        self.cmd = cmd
        self.absoluteAngles = [angle for angle, clockwise in cmd]
        self.isClockwise = [clockwise for angle, clockwise in cmd]
        del self.isClockwise[0] # the first item is invalid
        self.numAngles = len(self.isClockwise)
        self.travelledAngles = self.__getTravelledAngles()

    
    def __str__(self):
        string = 'program'
        for angle, direction in self.cmd:
            string += ('_' + str(angle) + '_' + str(direction))
        return string


    def __getTravelledAngles(self):
        travelledAngles = []
        for i in range(self.numAngles):
            a = program.getTravelledAngles(self.absoluteAngles[i], self.absoluteAngles[i+1], self.isClockwise[i])
            travelledAngles.append(a)
        
        return travelledAngles


    @staticmethod
    def getTravelledAngles(a, b, isClockwise):
        if isClockwise == True:
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
    droneProgram = program(((295, None), (165, False), (90, False), (173, False), (278, True)))
    print(droneProgram.isClockwise)
    print(droneProgram.travelledAngles)