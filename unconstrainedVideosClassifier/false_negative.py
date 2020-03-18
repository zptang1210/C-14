###
#   IMPORT
###
import numpy as np
import json
import matplotlib
import matplotlib.pyplot as plt

from classifer import classifier, binary_classifier
from fps_converter import *

###
#   MATPLOTLIB PARAMS
###
font = {'size': 14}
matplotlib.rc('font', **font)

###
#   CONSTANTS
###
PITCH = 0
YAW = 1
ROLL = 2

Y = 0
Z = 1
X = 2

###
#   LOAD DATA
###
with open('data.json') as json_file:
    videos = json.load(json_file)[:10]

all_angle_errors = []
all_translation_errors = []

rotation_thresholds = np.arange(20, 50, 0.5)
translation_thresholds = np.arange(20, 50, 0.5)

# Initialize binary_acc to 0's
binary_acc = np.zeros((len(rotation_thresholds), len(translation_thresholds)))

for video_i in range(len(videos)):
    print('Video {}'.format(video_i + 1))
    video = videos[video_i]
    results = classifier(
        video['compressed_cameramotion'],
        waypoints_framesskipped_converter(video['waypoints'], video['frames_skipped']),
        video['kml'],
        remove_start=video.get('remove_start', 0),
        remove_end=video.get('remove_end', 0))

    for i in range(len(rotation_thresholds)):
        for j in range(len(translation_thresholds)):
            binary_acc[i][j] += int(
                not binary_classifier(results['angle_errors'], results['translation_errors'],
                                      rotation_threshold=rotation_thresholds[i],
                                      translation_threshold=translation_thresholds[j]))

binary_acc = np.array(binary_acc).T.astype(float) / len(videos)

print(binary_acc)
print(len(binary_acc))
fig, ax = plt.subplots()
print(rotation_thresholds)
print(translation_thresholds)
CS = ax.contour(rotation_thresholds, translation_thresholds, binary_acc, np.arange(0, 0.4, 0.1))
ax.clabel(CS, inline=1, fontsize=10)
plt.xlabel('Rotation error threshold in (degrees)')
plt.ylabel('Angle between translation vectors \n threshold (in degrees)')
plt.show()
# plt.savefig('graph18.pdf', bbox_inches = "tight")
