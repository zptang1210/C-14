import os
import sys
import json
current_folder_path = os.path.split(os.path.realpath(__file__))[0] + '/'
sys.path.append(current_folder_path + '../../videoProcessing/')
from skipFrames import skipFrames
from videoCompressor import videoCompressor


# 720p
data0403 = ('DJI_0403', 'DJI_0403_corrected', ((214, None), (57, False), (248, False)), '720p')
data0410 = ('DJI_0410', 'DJI_0410', ((214, None), (57, False), (248, False)), '720p')
data0411 = ('DJI_0411', 'DJI_0411', ((173, None), (65, False), (205, True)), '720p')
data0412 = ('DJI_0412', 'DJI_0412_corrected', ((173, None), (65, False), (205, True)), '720p')

data0404 = ('DJI_0404', 'DJI_0404_corrected', ((43, None), (10, False), (179, False)), '720p')

data0400 = ('DJI_0400', 'DJI_0400', ((125, None), (39, False), (344, True)), '720p')
data0402 = ('DJI_0402', 'DJI_0402', ((56, None), (347, True), (183, False)), '720p')

# 4k
data0460 = ('DJI_0460', 'DJI_0460_corrected', ((333, None), (182, True), (22, True)), '4k')
data0459 = ('DJI_0459', 'DJI_0459_corrected', ((50, None), (142, True), (249, False)), '4k')

data0443 = ('DJI_0443', 'DJI_0443', ((63, None), (346, False), (128, False)), '4k')
data0439 = ('DJI_0439', 'DJI_0439', ((125, None), (177, True), (114, False)), '4k')

data0447 = ('DJI_0447', 'DJI_0447_corrected', ((7, None), (217, True), (327, True)), '4k')

data0494 = ('DJI_0494', 'DJI_0494', ((93, None), (321, True), (337, False), (228, True), (288, True)), '4k')
data0495 = ('DJI_0495', 'DJI_0495', ((244, None), (173, False), (221, True), (311, True), (277, True)), '4k')
data0496 = ('DJI_0496', 'DJI_0496', ((186, None), (53, False), (80, False), (137, False), (305, False)), '4k')

data0488 = ('DJI_0488', 'DJI_0488', ((286, None), (215, True), (310, True), (184, True), (59, False)), '4k')
data0489 = ('DJI_0489', 'DJI_0489', ((78, None), (194, True), (272, True), (135, True), (315, False)), '4k')
data0490 = ('DJI_0490', 'DJI_0490', ((307, None), (147, True), (77, False), (28, False), (220, False)), '4k')
data0491 = ('DJI_0491', 'DJI_0491', ((267, None), (89, True), (143, True), (41, True), (301, True)), '4k')

data0508 = ('DJI_0508', 'DJI_0508', ((104, None), (289, True), (292, False), (114, False), (23, True)), '4k')
data0504 = ('DJI_0504', 'DJI_0504', ((161, None), (29, True), (122, False), (249, True), (328, False)), '4k')

data0498 = ('DJI_0498', 'DJI_0498', ((176, None), (216, True), (240, False), (77, False), (4, True)), '4k')
data0497 = ('DJI_0497', 'DJI_0497', ((346, None), (80, True), (176, True), (196, False), (171, True)), '4k')

data0502 = ('DJI_0502', 'DJI_0502', ((174, None), (48, False), (94, True), (240, False), (34, False)), '4k')
data0501 = ('DJI_0501', 'DJI_0501', ((85, None), (53, False), (24, False), (56, False), (209, False)), '4k')
data0500 = ('DJI_0500', 'DJI_0500', ((32, None), (13, True), (197, False), (258, True), (42, False)), '4k')

dataset = [data0403, data0410, data0411, data0412, data0404, data0400, data0402, 
           data0460, data0459, data0443, data0439, data0447, data0494, data0495, data0496, 
           data0488, data0489, data0490, data0491, data0508, data0498, data0497, 
           data0502, data0501, data0500]


videoNameList = [d[0] for d in dataset]
metadataList = [d[1] for d in dataset]
programList = [d[2] for d in dataset]
videoTypeList = [d[3] for d in dataset]



def compressVideo(rawVideoName, compressParam):
    resizeNum = compressParam['resize']
    skipFrameNum = compressParam['skipFrames']

    if resizeNum == 1 and skipFrameNum == 1:
        videoName = rawVideoName
    else:
        tempVideoName = rawVideoName
        if skipFrameNum != 1:
            compressor = skipFrames(tempVideoName, inputPath='../../PWCNET_ORIEXTRACTOR/videos/')
            tempVideoName = compressor.process(skipFrameNum, outputPath='../../PWCNET_ORIEXTRACTOR/videos/') 
        if resizeNum != 1:
            compressor = videoCompressor(tempVideoName, inputPath='../../PWCNET_ORIEXTRACTOR/videos/')
            tempVideoName = compressor.process(resizeNum, outputPath='../../PWCNET_ORIEXTRACTOR/videos/')
        videoName = tempVideoName   
    return videoName




if __name__=='__main__':
    sampleParam = {'hotpointSampleLength': 1, 'hotpointSampleRate': 0.6, 'waypointSampleLength': 1, 'waypointMaxSampleNum': 5}
    compressParam_720p = {'resize': 4, 'skipFrames': 15}
    compressParam_4k = {'resize': 12, 'skipFrames': 15}

    # compress videos
    compressedVideoNameDict = {}
    for videoName, videoType in zip(videoNameList, videoTypeList):
        compressParam = compressParam_4k if videoType=='4k' else compressParam_720p
        compressedVideoName = compressVideo(videoName, compressParam)
        compressedVideoNameDict[videoName] = compressedVideoName

    with open('compressedVideoNameDict.json', 'w') as fout:
        json.dump(compressedVideoNameDict, fout)
