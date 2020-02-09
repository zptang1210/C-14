import sys
import matplotlib
from pathlib import Path

sys.path.append('../utils/')
from GPSrpyxyz import *
from compareyaw import compare_yaw


font = {'size'   : 14}
matplotlib.rc('font', **font)


# Video target
video = 'DJI_0179'
metadataFilePath = f'../unconstrainedVideosClassifier/metadata/{video}.metadata'
video = 'skip_CM_' + video

reduce = [1, 2, 3, 5, 10, 15, 30, 60, 90]

compression = 12
spatialsampling = 7

# results

results = []
results_std = []
results_timing = []



def get_total_timing(file):
    file_timing = open(file, "r")
    timings = file_timing.readlines()
    timings = [float(timing.split(':')[1].strip()) for timing in timings]
    return sum(timings)



def compute_error(target, arr, step, window):
    # Correct small errors
    smaller = min(target.shape[0], arr.shape[0])
    target = target[:smaller]
    arr = arr[:smaller]

    errors = []

    for i in range(0, len(arr), window):
        error = 0
        print(i)
        if i < len(arr) - window:
            for j in range(window):
                error += (arr[i + j] - target[i + j])

        errors.append(error / window)

    errors =  np.array(errors)

    return ((errors) ** 2).mean(axis=0)


def compute_MSE(arr1, arr2):
    smaller = min(arr1.shape[0], arr2.shape[0])
    print(arr1.shape[0])
    print(arr2.shape[0])
    arr1 = arr1[:smaller]
    arr2 = arr2[:smaller]
    print(arr1.shape[0])
    print(arr2.shape[0])

    plt.plot(arr1[:, 1])
    plt.plot(arr2[:, 1])
    plt.show()

    # return np.sum(((arr1[:1] - arr2[:1]) ** 2).mean(axis=0)) #/ arr1.shape[1]
    return ((arr1 - arr2) ** 2).mean(axis=0)[1]  # / arr1.shape[1]




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

v_camera_list, x_axis_camera_list, y_axis_camera_list, z_axis_camera_list = convertXYZFromBodyToCamera(framestamp,
                                                                                                       50.0,
                                                                                                       v_world_list,
                                                                                                       x_axis_body_list,
                                                                                                       y_axis_body_list,
                                                                                                       z_axis_body_list,
                                                                                                       plot=False)



yaw_metadata, pitch_metadata, roll_metadata = getRPYInCameraFrame(framestamp, x_axis_camera_list, y_axis_camera_list,
                                                                  z_axis_camera_list, plot=False)







target_orientation_camera_motion = [pitch_metadata, yaw_metadata, roll_metadata]
target_orientation_camera_motion = np.array([*zip(*target_orientation_camera_motion)])

# Loop
for reduc in reduce:
    file_name = video + '__compressed_12__reduce_' + str(reduc) + '__spatialSampling_7.txt'

    cameraMotion1 = Path('cm_skipframe_data/1/' + file_name)
    cameraMotion2 = Path('cm_skipframe_data/2/' + file_name)
    cameraMotion3 = Path('cm_skipframe_data/3/' + file_name)

    parser = parseComputedMotion(cameraMotion1)
    frame, orientation_camera_motion, translation_camera_motion = parser.parse()
    print(yaw_metadata)
    m1, _ = compare_yaw(framestamp, yaw_metadata, reduc, orientation_camera_motion[:, 1])

    parser = parseComputedMotion(cameraMotion2)
    frame, orientation_camera_motion, translation_camera_motion = parser.parse()
    m2, _ = compare_yaw(framestamp, yaw_metadata, reduc, orientation_camera_motion[:, 1])

    parser = parseComputedMotion(cameraMotion3)
    frame, orientation_camera_motion, translation_camera_motion = parser.parse()
    m3, _ = compare_yaw(framestamp, yaw_metadata, reduc, orientation_camera_motion[:, 1])


    results.append((m1 + m2 + m3) / 3)

    file_name_timing = video + '__compressed_12__reduce_' + str(reduc) + '__spatialSampling_7_timing.txt'



    timing1 = get_total_timing(
        'cm_skipframe_data/1/' + file_name_timing)

    timing2 = get_total_timing(
        'cm_skipframe_data/2/' + file_name_timing)

    timing3 = get_total_timing(
        'cm_skipframe_data/3/' + file_name_timing)

    average_timing = (timing1 + timing2 + timing3) / 3

    results_timing.append(average_timing / 60)





def skipped_format(skipped):
    FPS = 30
    return ['{:.1f}'.format(FPS / s).rstrip('0').rstrip('.') for s in skipped]


kwargs = dict(capsize=2, elinewidth=1.1, linewidth=0.6, ms=7)



def compression_to_resolution(compressions):
    resolutions = []
    x4k = 3840
    y4k = 2160
    for compression in compressions:
        resolutions.append('{}x{}'.format(int(x4k / compression), int(y4k / compression)))
    return resolutions




fig, ax1 = plt.subplots()

plt.plot(skipped_format(reduce), results)


ax1.set_ylabel('yaw MSE')
ax1.set_ylim(bottom=0)
ax1.set_xlabel('Video frame rate')
ax1.ticklabel_format(axis='y', style='sci', scilimits=(-2, 2))




ax2 = ax1.twinx()

plt.plot(skipped_format(reduce), results_timing, '--')


ax2.set_ylabel('Time of optical flow + Camera motion \n (in minutes)')
ax2.set_ylim(bottom=0)
ax2.set_xlabel('Video frame rate')
ax2.ticklabel_format(axis='y', style='sci', scilimits=(-2, 2))

plt.xticks(np.arange(len(reduce)), skipped_format(reduce))


plt.show()
plt.savefig('graphs/cm_skipframe_benchmark.pdf', bbox_inches = "tight")

