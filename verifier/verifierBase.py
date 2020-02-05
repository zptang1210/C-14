from abc import abstractmethod

class verifierBase(object):

    def __init__(self, rawVideoName, metadataName, droneProgram):
        self.rawVideoName = rawVideoName
        self.metadataName = metadataName
        self.droneProgram = droneProgram
    
    @abstractmethod
    def isMatch(self):
        pass
