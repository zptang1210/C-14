###
#   IMPORT
###
import numpy as np
import os
import math
import json
import matplotlib
import matplotlib.pyplot as plt

from kml_difference import kml_difference
from classifer import classifier
from fps_converter import *

###
#   MATPLOTLIB PARAMS
###
font = {'size'   : 14}
matplotlib.rc('font', **font)


###
#   LOAD DATA
###
fake_dir = '/Users/fabien/Documents/amherst/fall19/cs696/fake_kml/'
real_dir = '/Users/fabien/Documents/amherst/fall19/cs696/litchi_missions/'

with open('data.json') as json_file:
    videos = json.load(json_file)[:10]

data_rotation_true = []
data_translation_true = []
data_classification_true = []

data_rotation_false = []
data_translation_false = []
data_classification_false = []

for filename in os.listdir(fake_dir):
    print(filename)
    realname = filename.split('_')[0]
    video_number = int(realname[5:]) - 1  # Remove "video"
    differences = kml_difference(real_dir + realname + '.kml', fake_dir + filename)

    # Get video

    compressed_cameramotion = videos[video_number]['compressed_cameramotion']
    kml = videos[video_number]['kml']
    waypoints = videos[video_number]['waypoints']
    frames_skipped = videos[video_number]['frames_skipped']
    remove_start = 0
    remove_end = 0
    if 'remove_start' in videos[video_number]:
        remove_start = videos[video_number]['remove_start']

    if 'remove_end' in videos[video_number]:
        remove_end = videos[video_number]['remove_end']

    ######## FAKE ########

    results_fake = classifier(
        compressed_cameramotion,  # path to camera motion
        waypoints_framesskipped_converter(waypoints, frames_skipped),  # Annotated video waypoints
        fake_dir + filename,  # Path to kml
        remove_start=remove_start,
        remove_end=remove_end)

    rotations_kml_fake = results_fake['yaw_kml']
    translation_kml_fake = results_fake['translations_angle_kml']
    classification = results_fake['classification']

    if classification:
        data_classification_true.append(classification)
    else:
        data_classification_false.append(classification)

    ######## REAL ########

    results_real = classifier(
        compressed_cameramotion,  # path to camera motion
        waypoints_framesskipped_converter(waypoints, frames_skipped),  # Annotated video waypoints
        real_dir + realname + '.kml',  # Path to kml
        remove_start=remove_start,
        remove_end=remove_end)

    rotations_kml_real = results_real['yaw_kml']
    translation_kml_real = results_real['translations_angle_kml']


    ##### Translations #####

    max_translation_error = 0

    for i in range(len(translation_kml_fake)):
        translation_error = math.degrees(
            np.arccos(np.dot(translation_kml_fake[i], translation_kml_real[i])))

        max_translation_error = max(max_translation_error, translation_error)

    if classification:
        data_translation_true.append(max_translation_error)
    else:
        data_translation_false.append(max_translation_error)

    ##### Rotations #####

    def max_rotation(rotations1, rotations2):

        max_rot = 0

        for i in range(len(rotations1)):

            error = rotations1[i] - rotations2[i]

            if error < -180:
                error += 360

            if error > 180:
                error -= 360

            max_rot = max(max_rot, abs(error))

        return max_rot


    max_rotation_error = max_rotation(rotations_kml_fake, rotations_kml_real)

    if classification:
        data_rotation_true.append(max_rotation_error)
    else:
        data_rotation_false.append(max_rotation_error)


true_negative = plt.scatter(data_rotation_false, data_translation_false, marker='8', color='green')
false_positive = plt.scatter(data_rotation_true, data_translation_true, marker='x', color='red', )

plt.legend((true_negative, false_positive), ('True negative', 'False positive'))


plt.xlabel('Yaw rotation angle error (in degrees)')
plt.ylabel('Translation vector angle error \n (in degrees)')
#sns.regplot(x=data_x, y=data_y, logistic=True)
#lt.yticks([0, 0.25, 0.5, 0.75, 1], ['True \n Negative', '0.25', '0.5', '0.75', 'False \n Positive'])
# plt.scatter(data_x, data_y)
#plt.xlabel('Distance in meters')
#plt.savefig('graph15.pdf', bbox_inches = "tight")
plt.show()
# for all file in folder:
#
#     kml_difference(kml, kml)
