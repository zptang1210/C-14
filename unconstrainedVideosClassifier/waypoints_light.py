###
#   IMPORT
###
import math
import json
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

from classifer import classifier
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

# Keep track of all results for graph
all_angle_errors = []
all_translation_errors = []

for video_i in range(len(videos)):
    print('Video {}'.format(video_i + 1))
    video = videos[video_i]
    results = classifier(
        video['compressed_cameramotion'],
        waypoints_framesskipped_converter(video['waypoints'], video['frames_skipped']),
        video['kml'],
        remove_start=video.get('remove_start', 0),
        remove_end=video.get('remove_end', 0))

    translations_video = results['translations_video']
    rotations_video = results['rotations_video']
    translations_kml = results['translations_kml']


    for i in range(len(translations_kml[0])):
       norm = math.sqrt(translations_kml[0][i] ** 2 + translations_kml[1][i] ** 2  + translations_kml[2][i] ** 2)
       translations_kml[0][i] = translations_kml[0][i] / norm
       translations_kml[1][i] = translations_kml[1][i] / norm
       translations_kml[2][i] = translations_kml[2][i] / norm


    rotations_kml = results['rotations_kml']
    waypoints_kml = results['waypoints_kml']
    angle_errors = results['angle_errors']
    translation_errors = results['translation_errors']
    yaw_kml = results['yaw_kml']
    yaw_video = results['yaw_video']


    all_angle_errors  = all_angle_errors + angle_errors
    all_translation_errors += translation_errors

    rotations_video = rotations_framesskipped_converter(rotations_video, frames_skipped)

    print(angle_errors)
    print(translation_errors)
    print(results['classification'])

    ###
    #   FIGURE AND SUBPLOTS
    ###
    # figure = plt.figure()
    # ax_compressed_rotations = figure.add_subplot('221')
    # ax_ideal_rotations = figure.add_subplot('222')
    # ax_compressed_translations = figure.add_subplot('223')
    # ax_ideal_translations = figure.add_subplot('224')
    #
    # ###
    # #   ax_compressed_rotations
    # ###
    # ax_compressed_rotations.plot(rotations_video[YAW], label='yaw')
    # ax_compressed_rotations.ticklabel_format(axis='y', style='sci', scilimits=(-2, 2))
    # ax_compressed_rotations.set_title("Compressed Video", pad=18)
    # ax_compressed_rotations.legend()
    # first_waypoint = waypoints_framesskipped_converter(waypoints, frames_skipped)[0]
    # for vert in waypoints_framesskipped_converter(waypoints, frames_skipped):
    #    ax_compressed_rotations.axvline(x=(vert - first_waypoint), color='darkred')
    # #ax_compressed_rotations.set_ylim([-0.007, 0.008])
    #
    # ###
    # #   ax_ideal_rotations
    # ###
    # ax_ideal_rotations.plot(rotations_kml[YAW], label='yaw')
    # ax_ideal_rotations.ticklabel_format(axis='y', style='sci', scilimits=(-2, 2))
    # ax_ideal_rotations.set_title("Litchi", pad=18)
    # ax_ideal_rotations.legend()
    # ax_ideal_rotations.set_xlabel('Frames')
    # for vert in waypoints_kml:
    #     ax_ideal_rotations.axvline(x=vert, color='darkred')
    # #ax_ideal_rotations.set_ylim([-0.007, 0.008])
    #
    # ###
    # #   ax_compressed_translations
    # ###
    #
    # ax_compressed_translations.plot(translations_video[X], label='x')
    # ax_compressed_translations.plot(translations_video[Y], label='y')
    # ax_compressed_translations.plot(translations_video[Z], label='z')
    # ax_compressed_translations.legend()
    # ax_compressed_translations.set_xlabel('Frames')
    # first_waypoint = waypoints_framesskipped_converter(waypoints, frames_skipped)[0]
    # for vert in waypoints_framesskipped_converter(waypoints, frames_skipped):
    #    ax_compressed_translations.axvline(x=(vert - first_waypoint), color='darkred')
    # #ax_compressed_translations.set_xlim([20, 30])
    # #ax_compressed_translations.set_ylim([-1.2, 1.2])
    #
    # ###
    # #   ax_ideal_translations
    # ###
    # ax_ideal_translations.plot(translations_kml[X], label='x')
    # ax_ideal_translations.plot(translations_kml[Y], label='y')
    # ax_ideal_translations.plot(translations_kml[Z], label='z')
    # ax_ideal_translations.legend()
    # for vert in waypoints_kml:
    #    ax_ideal_translations.axvline(x=vert, color='darkred')
    # #ax_ideal_translations.set_xlim([265, 370])
    # #ax_ideal_translations.set_ylim([-1.2, 1.2])
    #
    # ###
    # #   GRAPH PARAMS
    # ###
    # plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    # figure.suptitle('Video {}'.format(VIDEO + 1), size=15, y=0.98)
    # #plt.savefig('graphs/video{}.png'.format(VIDEO))
    # plt.show()


# print(sorted(all_translation_errors))
# print(sorted(all_angle_errors))
# exit()
##### ANGLE ERRORS DISTRIBUTION ######


kwargs = dict(hist=True, kde_kws={'linewidth': 2, 'shade': True})
sns.distplot(all_angle_errors, rug=True, kde=False, norm_hist=False, color="mediumseagreen", **kwargs)

plt.xlim(-50, 50)
plt.xlabel('Angle error in degrees in rotation')
#plt.title('Angle errors distribution (Litchi)')
plt.legend()
#plt.savefig('graph14.pdf')
plt.show()
################

# kwargs = dict(hist=True, kde_kws={'linewidth': 2, 'shade': True})
# sns.distplot(all_translation_errors, rug=True, kde=False, norm_hist=False, color="mediumseagreen", **kwargs)
# plt.xlim(-50, 50)
# #plt.title('Translation errors distribution (Litchi)')
# plt.xlabel('Angle error in degree between translation vectors')
# plt.legend()
# #plt.show()
# plt.savefig('graph14_translation.pdf')


#######








