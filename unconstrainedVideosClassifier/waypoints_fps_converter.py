def waypoints_fps_converter(waypoints, fps_from, fpm_to):
    return [round(fpm_to / fps_from * waypoint) for waypoint in waypoints]
