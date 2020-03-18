import json
import math
import copy
import random
from shutil import copyfile

from convertCameraCoordFrameToDroneUnconstrained import convertCameraCoordFrameToDrone
from parseComputedMotion import *
from convertKMLToDroneCoord import convertKMLToDroneCoord
from waypoints_fps_converter import waypoints_fps_converter


def binary_classifier(angle_errors, translation_errors, rotation_threshold=30, translation_threshold=35):
    final_classification = True
    #print(rotation_threshold, translation_threshold)
    for angle_error in angle_errors:
        if angle_error < -rotation_threshold or angle_error > rotation_threshold:
            final_classification = False
            break

    if final_classification == True:
        for translation_error in translation_errors:
            if translation_error < -translation_threshold or translation_error > translation_threshold:
                final_classification = False
                break

    return final_classification


def classifier(cameraMotion, waypoints, kml, remove_start=0, remove_end=0):
    # Get all camera motion from video
    parser = parseComputedMotion(cameraMotion)
    frame, orientation_camera_motion, translation_camera_motion = parser.parse()

    # convertKMLToDroneCoord
    rotations_kml, translations_kml, droneCameraAngles_kml, waypoints_kml = convertKMLToDroneCoord(kml)

    ### REMOVE TO THE START ###
    rotations_kml = rotations_kml[remove_start:]
    translations_kml = translations_kml[remove_start:]
    droneCameraAngles_kml = droneCameraAngles_kml[remove_start:]

    for i in range(len(waypoints_kml)):
        waypoints_kml[i] = max(0, waypoints_kml[i] - remove_start)
    ###

    ### REMOVE TO THE END ###
    rotations_kml = rotations_kml[:len(rotations_kml) - remove_end]
    translations_kml = translations_kml[:len(translations_kml) - remove_end]
    droneCameraAngles_kml = droneCameraAngles_kml[:len(droneCameraAngles_kml) - remove_end]

    for i in range(len(waypoints_kml)):
        waypoints_kml[i] = min(len(rotations_kml) - 1, waypoints_kml[i])
    ###

    # Checkpoints annotated in the video
    waypoints_video = waypoints

    if len(waypoints_video) != len(waypoints_kml):
        print('len(waypoints_video) ', len(waypoints_video))
        print('len(waypoints_kml) ', len(waypoints_kml))
        exit()

    translations_video = [[], [], []]
    rotations_video = [[], [], []]

    angle_errors = []
    translation_errors = []
    translations_angle_kml_segments = []
    yaw_kml_segments = []
    yaw_video_segments = []

    # Segment by segment
    for i in range(1, len(waypoints_video)):

        # Calculate interpolation of the angle between the drone and the camera for the video
        n_frames_video = waypoints_video[i] - waypoints_video[i - 1]
        n_frames_kml = waypoints_kml[i] - waypoints_kml[i - 1]

        droneCameraAngle_video = np.interp(
            #np.arange(0, n_frames_kml+1, n_frames_kml / n_frames_video),  # New x
            np.arange(0, n_frames_kml+1, n_frames_kml / n_frames_video),  # New x
            np.arange(0, n_frames_kml),  # Old x
            droneCameraAngles_kml[waypoints_kml[i - 1]:waypoints_kml[i]]  # Old y
        ).tolist()

        converter = convertCameraCoordFrameToDrone(orientation_camera_motion[waypoints_video[i - 1]:waypoints_video[i]],
                                                   translation_camera_motion[waypoints_video[i - 1]:waypoints_video[i]])

        #if len(droneCameraAngle_video) > len(orientation_camera_motion[waypoints_video[i - 1]:waypoints_video[i]]):
        #    droneCameraAngle_video = droneCameraAngle_video[:-1]

        # Get rotation and translation from the video for this segment
        rotations_video_segment, translations_video_segment = converter.convert(droneCameraAngle_video, plot=False)

        # Get rotation from kml for this segment
        rotations_kml_segment = rotations_kml[waypoints_kml[i - 1]:waypoints_kml[i]]



        ######
        #   OLD ANGLE ERROR
        ######
        angle_error = (rotations_video_segment.sum(axis=0)[1] * 180 / np.pi) - (
                rotations_kml_segment.sum(axis=0)[1] * 180 / np.pi)

        if angle_error < -180:
            angle_error += 360

        if angle_error > 180:
            angle_error -= 360

        yaw_kml_segments.append(rotations_kml_segment.sum(axis=0)[1] * 180 / np.pi)
        yaw_video_segments.append(rotations_video_segment.sum(axis=0)[1] * 180 / np.pi)



        ######
        #   NEW ANGLE ERROR
        ######
        # rotations_kml_new, translations_kml_new = convertKMLToVerifier(kml)
        #
        #
        # angle_error = rotations_video_segment.sum(axis=0)[1] * 180 / np.pi - rotations_kml_new[i-1]
        # if angle_error < -180:
        #     angle_error += 360
        # if angle_error > 180:
        #     angle_error -= 360
        #



        #########################################

        angle_errors.append((angle_error).tolist())

        # Translation error
        # translation_errors.append((np.mean(translations_video_segment, axis=0) - np.mean(
        #    translations_kml[waypoints_kml[i - 1]:waypoints_kml[i]], axis=0)).tolist())

        # print('######')
        # print(len(translations_video_segment))
        # print(len(translations_kml[waypoints_kml[i - 1]:waypoints_kml[i]]))
        # print('*******')


        translation_video_segment = np.sum(translations_video_segment, axis=0)
        translation_kml_segment = np.sum(translations_kml[waypoints_kml[i - 1]:waypoints_kml[i]], axis=0)
        # translation_kml_segment = translations_kml[waypoints_kml[i - 1]:waypoints_kml[i]]

        translation_video_segment_normalized = translation_video_segment / np.sqrt(
            translation_video_segment[0] ** 2 + translation_video_segment[1] ** 2 + translation_video_segment[2] ** 2)
        translation_kml_segment_normalized = translation_kml_segment / np.sqrt(
            translation_kml_segment[0] ** 2 + translation_kml_segment[1] ** 2 + translation_kml_segment[2] ** 2)

        translation_error = math.degrees(
            np.arccos(np.dot(translation_video_segment_normalized, translation_kml_segment_normalized)))
        normal = [0, -1, 0]

        if np.dot(normal, np.cross(translation_kml_segment_normalized, translation_video_segment_normalized)) > 0:
            translation_error = - translation_error

        translations_angle_kml_segments.append(translation_kml_segment_normalized)


        # exit()
        translation_errors.append(translation_error)
        # translation_errors.append().tolist())

        # Save translation and rotation if we don't want to recompute
        for i, _ in enumerate(translations_video):
            translations_video[i] += translations_video_segment[:, i].tolist()
            rotations_video[i] += rotations_video_segment[:, i].tolist()

    # Mean error for the entire video rotation and translation

    translations_kml = np.transpose(translations_kml)
    rotations_kml = np.transpose(rotations_kml)


    # Binary classification
    classification = binary_classifier(angle_errors, translation_errors)

    return {
        'translations_video': translations_video,
        'rotations_video': rotations_video,
        'translations_kml': translations_kml,
        'translations_angle_kml': translations_angle_kml_segments,
        'rotations_kml': rotations_kml,
        'yaw_kml': yaw_kml_segments,
        'yaw_video': yaw_video_segments,
        'waypoints_kml': waypoints_kml,
        'angle_errors': angle_errors,
        'translation_errors': translation_errors,
        'classification': classification
    }


if __name__ == "__main__":

    # Save in case of I delete everything...
    copyfile("data.json", "data_save.json")

    with open('data.json') as f:
        data = json.load(f)

    VIDEO_NUMBER = 5

    for i in range(len(data[VIDEO_NUMBER]['cameramotion'])):

        CAMERAMOTION_NUMBER = i

        cameraMotion = data[VIDEO_NUMBER]['cameramotion'][CAMERAMOTION_NUMBER]['path']
        waypoints = waypoints_fps_converter(data[VIDEO_NUMBER]['waypoints'],
                                            data[VIDEO_NUMBER]['cameramotion'][0]['fps'],
                                            data[VIDEO_NUMBER]['cameramotion'][CAMERAMOTION_NUMBER]['fps'])

        results = []
        for kml in data[VIDEO_NUMBER]['kml']:
            results.append(classifier(cameraMotion, waypoints, kml)['results'])

        data[VIDEO_NUMBER]['cameramotion'][CAMERAMOTION_NUMBER]['results'] = results

        # print(results)

        with open('data.json', 'w') as json_file:
            json.dump(data, json_file)
