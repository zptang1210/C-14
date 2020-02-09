def waypoints_fps_converter(waypoints, fps_from, fpm_to):
    return [round(fpm_to / fps_from * waypoint) for waypoint in waypoints]


def waypoints_framesskipped_converter(waypoints, frames_skipped):
    return [round(waypoint / frames_skipped) for waypoint in waypoints]


def rotations_fps_converter(rotations, fps_from, fpm_to):
    for i, rotation in enumerate(rotations):
        for j, value in enumerate(rotation):
            rotations[i][j] = rotations[i][j] * fpm_to / fps_from
    return rotations


def rotations_framesskipped_converter(rotations, frames_skipped):
    for i, rotation in enumerate(rotations):
        for j, value in enumerate(rotation):
            rotations[i][j] = rotations[i][j] / frames_skipped
    return rotations
