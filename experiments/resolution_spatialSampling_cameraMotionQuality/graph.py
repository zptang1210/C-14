import sys
import matplotlib
from pathlib import Path

sys.path.append('../utils/')
from GPSrpyxyz import *
from compareyaw import compare_yaw

font = {'size': 14}
matplotlib.rc('font', **font)

# Video target
video = 'DJI_0179'
metadataFilePath = f'../unconstrainedVideosClassifier/metadata/{video}.metadata'

compressions = [2, 5, 10, 15, 20, 25, 30]
spatialsamplings = [3, 5, 7, 9, 11, 13, 15]

# results
results = [[] for _ in spatialsamplings]
results_timing = [[] for _ in spatialsamplings]


def get_total_timing(file):
    file_timing = open(file, "r")
    timings = file_timing.readlines()
    timings = [float(timing.split(':')[1].strip()) for timing in timings]
    return sum(timings)


def compute_MSE(arr1, arr2):
    print(arr2.shape)
    arr2 = arr2[:, 1]
    arr1 = arr1[:-3, 1]
    return ((arr1 - arr2) ** 2).mean(axis=0)


info = extractGPSInfo(metadataFilePath)
timestamp, pitch, roll, yaw, vx, vy, vz = extractPitchRollYawXYZ(info)
framestamp, timeFrameDict = timestampToFramestamp(metadataFilePath, timestamp)

v_world_list, v_body_list, x_axis_body_list, y_axis_body_list, z_axis_body_list = convertXYZToBodyFrame(framestamp,
                                                                                                        pitch,
                                                                                                        roll,
                                                                                                        yaw,
                                                                                                        vx,
                                                                                                        vy,
                                                                                                        vz,
                                                                                                        plot=False)

_, x_axis_camera_list, y_axis_camera_list, z_axis_camera_list = convertXYZFromBodyToCamera(framestamp,
                                                                                           50.0,
                                                                                           v_world_list,
                                                                                           x_axis_body_list,
                                                                                           y_axis_body_list,
                                                                                           z_axis_body_list,
                                                                                           plot=False)

yaw_metadata, pitch_metadata, roll_metadata = getRPYInCameraFrame(framestamp, x_axis_camera_list, y_axis_camera_list,
                                                                  z_axis_camera_list, plot=False)

for i in range(len(framestamp)):
    if framestamp[i] >= 0:
        start = i
        break

print("len(x_axis_camera_list)", len(x_axis_camera_list))
print("len(yaw_metadata)", len(yaw_metadata))
print("len(framestamp)", len(framestamp))

target_orientation_camera_motion = [pitch_metadata, yaw_metadata, roll_metadata]

target_orientation_camera_motion = np.array([*zip(*target_orientation_camera_motion)])

# Loop
for compression in compressions:

    for j, spatialsampling in enumerate(spatialsamplings):
        # file_name = video + '__compressed_' + str(compression) + '__spatialSampling_' + str(spatialsampling) + '.txt'
        file_name = 'res_cm_' + video + '__compressed_' + str(compression) + '__spatialSampling_' + str(
            spatialsampling) + '.txt'
        file_name_timing = 'res_cm_' + video + '__compressed_' + str(compression) + '__spatialSampling_' + str(
            spatialsampling) + '_timing.txt'

        cameraMotion1 = Path(
            'cm_resolution_data/1/' + file_name)
        cameraMotion2 = Path(
            'cm_resolution_data/2/' + file_name)
        #cameraMotion3 = Path(
        #    'cm_resolution_data/3/' + file_name)
        # cameraMotion = Path('/Users/fabien/Documents/amherst/fall19/cs696/droneCAPTCHA/temp/newresult/' + file_name)
        # if not cameraMotion.exists():
        #   print('{} does not exist'.format(cameraMotion))

        parser = parseComputedMotion(cameraMotion1)
        frame, orientation_camera_motion, translation_camera_motion = parser.parse()
        m1, _ = compare_yaw(framestamp, yaw_metadata, 1, orientation_camera_motion[:, 1])

        parser = parseComputedMotion(cameraMotion2)
        frame, orientation_camera_motion, translation_camera_motion = parser.parse()
        m2, _ = compare_yaw(framestamp, yaw_metadata, 1, orientation_camera_motion[:, 1])

        #parser = parseComputedMotion(cameraMotion3)
        #frame, orientation_camera_motion, translation_camera_motion = parser.parse()
        #m3, _ = compare_yaw(framestamp, yaw_metadata, 1, orientation_camera_motion[:, 1])

        results[j].append((m1 + m2) / 2)

        timing1 = get_total_timing(
            'cm_resolution_data/1/' + file_name_timing)
        timing2 = get_total_timing(
            'cm_resolution_data/2/' + file_name_timing)
        #timing3 = get_total_timing(
        #    'cm_resolution_data/3/' + file_name_timing)

        average_timing = (timing1 + timing2) / 2

        results_timing[j].append(average_timing / 60)


def compression_to_resolution(compressions):
    resolutions = []
    x4k = 3840
    y4k = 2160
    for compression in compressions:
        resolutions.append('{}x{}'.format(int(x4k / compression), int(y4k / compression)))
    return resolutions


######## GRAPHS


fig, ax1 = plt.subplots()

for i, result in enumerate(results):
    plt.plot(compressions, result, label=str(spatialsamplings[i]))

plt.set_cmap('CMRmap')
ax1.set_ylabel('yaw MSE')
ax1.set_ylim(bottom=0)
# ax1.set_xlabel('Video resolution')
ax1.ticklabel_format(axis='y', style='sci', scilimits=(-2, 2))

leg = ax1.legend(loc='lower left', prop={'size': 9}, ncol=2)
leg.set_title("Spatial sampling", prop={'size': 10})
leg._legend_box.align = "center"

print(compressions)
print(compression_to_resolution(compressions))

# leg = plt.legend(title="Spacial sampling")
# leg._legend_box.align = "left"
# plt.title('MSE of yaw with respect to metadata')
# plt.show()
# plt.savefig('graph2.pdf')

############


ax2 = ax1.twinx()

print(results_timing)
for i, result in enumerate(results_timing):
    print(result)
    print(str(spatialsamplings[i]))
    plt.plot(compressions, result, '--', label=str(spatialsamplings[i]))

# plt.figure(figsize=())
ax2.set_ylabel('Time of optical flow + Camera motion\n(in minutes)')
ax2.set_ylim(bottom=0)
ax2.set_yscale('log')
ax2.set_yticks([15, 30, 60, 120, 300, 600, 1000])
ax2.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax2.set_xlabel('Video resolution')
# ax2.ticklabel_format(axis='y', style='plain')

ax1.set_xticks(compressions)
ax1.set_xticklabels(compression_to_resolution(compressions), rotation=45, horizontalalignment="right")
ax1.tick_params(axis="x", labelsize=11)

# #plt.title('Time of optical flow + Camera motion')
# plt.savefig('graph2_timing.pdf')


# ax2.set_xticklabels(compression_to_resolution(compressions))
# print(compression_to_resolution(compressions))
# ax1.set_xticklabels(compression_to_resolution(compressions), rotation=45)
#
# ax1.tick_params(axis="x", labelsize=9)

plt.axis('tight')

# plt.show()
plt.savefig('graphs/cm_resolution_benchmark.pdf', bbox_inches="tight")
