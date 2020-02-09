import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def request_yaw(framestamps, yaw, start, end):
    if start < framestamps[0] or end > framestamps[-1]:
        return None

    cumulative_yaw = 0
    for i_framestamp in range(1, len(framestamps)):

        if framestamps[i_framestamp - 1] >= end:
            break

        if framestamps[i_framestamp] > start:
            cumulative_yaw += (min(end, framestamps[i_framestamp]) - max(start, framestamps[i_framestamp - 1])) \
                              / (framestamps[i_framestamp] - framestamps[i_framestamp - 1]) \
                              * yaw[i_framestamp - 1]

    return cumulative_yaw


def compare_yaw(metadata_framestamps, yaw_metadata, step, yaw_cameramotion):
    print("metadata_framestamps", len(metadata_framestamps))
    if metadata_framestamps[0] > 0:
        print('framestamps[0] should be negative ({})'.format(metadata_framestamps[0]))

    # Create camera motion framestamps
    cameramotion_framestamps = list(range(0, (len(yaw_cameramotion) + 1) * step, step))

    # Remove negative timestamps and computing the first yaw
    for i_framestamp, framestamp in enumerate(metadata_framestamps):
        if framestamp <= 0:
            prev_framestamp = framestamp
        else:
            normed_yaw = yaw_metadata[i_framestamp - 1] / (framestamp - prev_framestamp)
            yaw_metadata[i_framestamp - 1] = normed_yaw * framestamp
            yaw_metadata = yaw_metadata[i_framestamp - 1:]
            metadata_framestamps[i_framestamp - 1] = 0
            metadata_framestamps = metadata_framestamps[i_framestamp - 1:]
            break

    errors = []
    start = metadata_framestamps[0]
    for i_metadata in range(1, len(metadata_framestamps)):
        end = metadata_framestamps[i_metadata]
        yaw_predicted = request_yaw(cameramotion_framestamps, yaw_cameramotion, start, end)
        if yaw_predicted is None: break
        #if abs(yaw_metadata[i_metadata - 1]) < 0.01:
        errors.append((yaw_predicted - yaw_metadata[i_metadata - 1]) / (
                    metadata_framestamps[i_metadata] - metadata_framestamps[i_metadata - 1]))
        start = end
    #plt.plot(metadata_framestamps[:-1], yaw_metadata)
    #plt.plot(list(range(0, len(yaw_cameramotion), step)), yaw_cameramotion)
    errors = np.array(errors)
    #plt.plot(errors)


    #return errors
    return (errors ** 2).mean(), (errors ** 2).std()


if __name__ == "__main__":
    r = request_yaw([0, 1, 2, 3], [1, 1, 1], 0, 3)
    assert r == 3, r

    r = request_yaw([0, 1, 2, 3], [1, 1, 1], 1, 3)
    assert r == 2, r

    r = request_yaw([0, 1, 2, 3], [1, 1, 1], 0.5, 0.75)
    assert r == 0.25, r

    r = request_yaw([0, 1, 2, 3], [1, 1, 1], 0.75, 1.25)
    assert r == 0.5, r

    r = request_yaw([0, 1, 2, 3], [2, 1, 2], 0.5, 2.5)
    assert r == 3, r
