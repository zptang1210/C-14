import math
import numpy as np
from bs4 import BeautifulSoup as Soup
import geopy.distance
import matplotlib.pyplot as plt


def convertKMLToDroneCoord(file, FPS=30):
    with open(file) as data:
        kml = Soup(data, 'lxml-xml')  # Parse as XML

    # Get the checkpoints
    checkpoints = kml.findAll('Folder')[-1]
    checkpoints = [checkpoint.text for checkpoint in checkpoints.findAll('Camera')]

    # Get the <gx:Tour>
    tour = kml.find('gx:Tour')

    # Get all <gx:FlyTo>
    flyTos = tour.findAll('gx:FlyTo')

    # Camera Translations
    xs = []
    ys = []
    zs = []

    # Camera Rotations
    rolls = []
    pitchs = []
    yaws = []

    droneCameraAngle = []

    previous_latitude = None
    previous_longitude = None
    previous_altitude = None
    previous_tilt = None
    previous_heading = None

    waypoints = []

    # Integrals

    x_integ = [0]
    y_integ = [0]
    z_integ = [0]

    roll_integ = [0]
    pitch_integ = [0]
    yaw_integ = [0]

    # For each checkpoint
    for i_flyTo, flyTo in enumerate(flyTos):

        # First checkpoint
        if i_flyTo == 0:
            previous_latitude = float(flyTo.find('latitude').text)
            previous_longitude = float(flyTo.find('longitude').text)
            previous_altitude = float(flyTo.find('altitude').text)
            previous_tilt = float(flyTo.find('tilt').text)
            previous_heading = float(flyTo.find('heading').text)

        else:
            duration = round(float(flyTo.find('gx:duration').text) * FPS)

            latitude = float(flyTo.find('latitude').text)
            longitude = float(flyTo.find('longitude').text)
            altitude = float(flyTo.find('altitude').text)
            tilt = float(flyTo.find('tilt').text)
            heading = float(flyTo.find('heading').text)

            # dz is daltitude
            dz = (altitude - previous_altitude) / duration

            # dx is dlongitude in meter
            dx = geopy.distance.distance((previous_latitude, longitude),
                                         (previous_latitude, previous_longitude)).m / duration
            # Recover the sign
            if (longitude - previous_longitude) != 0:
                dx *= (longitude - previous_longitude) / abs((longitude - previous_longitude))

            # dy is dlatitude in meter
            dy = geopy.distance.distance((latitude, previous_longitude),
                                         (previous_latitude, previous_longitude)).m / duration
            # Recover the sign
            if (latitude - previous_latitude) != 0:
                dy *= (latitude - previous_latitude) / abs((latitude - previous_latitude))

            unchanged_tilt = tilt

            # The angle difference should be at most 180 otherwise we can rotate in the other direction
            if abs(heading - previous_heading) > 180:
                if heading > previous_heading:
                    previous_heading += 360
                else:
                    heading += 360
            if abs(tilt - previous_tilt) > 180:
                if tilt > previous_tilt:
                    previous_tilt += 360
                else:
                    tilt += 360

            for i_frame in range(duration):
                # droneCameraAngle.append(90 - unchanged_tilt)
                # Heading at each frame in rad
                interpolated_heading = math.radians(
                    (previous_heading * (duration - 1 - i_frame) + heading * i_frame) / (duration - 1))

                # Tilt at each frame in rad
                interpolated_tilt = math.radians(
                    (previous_tilt * (duration - 1 - i_frame) + tilt * i_frame) / (duration - 1))

                # Rotation matrix around y
                R_y = np.array(
                    [[np.cos(interpolated_tilt - math.pi / 2), 0, np.sin(interpolated_tilt - math.pi / 2)], [0, 1, 0],
                     [-np.sin(interpolated_tilt - math.pi / 2), 0, np.cos(interpolated_tilt - math.pi / 2)]])
                # Rotation matrix around z
                R_z = np.array(
                    [[np.cos(interpolated_heading - math.pi / 2), -np.sin(interpolated_heading - math.pi / 2), 0],
                     [np.sin(interpolated_heading - math.pi / 2), np.cos(interpolated_heading - math.pi / 2), 0],
                     [0, 0, 1]])

                # Apply rotation matrix

                r = R_z.dot([dx, dy, dz])

                xs.append(r[0])
                # We need a minus if we want z to point up
                ys.append(-r[1])
                zs.append(-r[2])

                # zs.append(dz)

                x_integ[-1] += xs[-1]
                y_integ[-1] += ys[-1]
                z_integ[-1] += zs[-1]

                rolls.append(math.cos(math.pi / 2) * ((heading - previous_heading) / duration))

                roll_integ[-1] += rolls[-1]

                # DroneCameraAngle
                droneCameraAngle.append(math.pi / 2 - interpolated_tilt)

            # pitchs += [(tilt - previous_tilt) / duration] * duration
            pitchs += [0] * duration
            yaws += [(heading - previous_heading) / duration * math.pi / 180] * duration

            pitch_integ[-1] += (0) * duration
            yaw_integ[-1] += ((heading - previous_heading) / duration * math.pi / 180) * duration

            previous_latitude = latitude
            previous_longitude = longitude
            previous_altitude = altitude
            previous_tilt = tilt
            previous_heading = heading

        # Check if it is a checkpoint
        if flyTo.find('Camera').text in checkpoints:
            waypoints.append(len(droneCameraAngle))

            x_integ.append(0)
            y_integ.append(0)
            z_integ.append(0)

            roll_integ.append(0)
            pitch_integ.append(0)
            yaw_integ.append(0)

    # Normalize
    # max_ = max(xs + ys + zs)
    # min_ = min(xs + ys + zs)
    # xs = [(x - min_) / (max_ - min_) * 2 - 1 for x in xs]
    # ys = [(y - min_) / (max_ - min_) * 2 - 1 for y in ys]
    # zs = [(z - min_) / (max_ - min_) * 2 - 1 for z in zs]

    ####################### HERE #######################

    # for i in range(len(xs)):
    #    norm = math.sqrt(xs[i] ** 2 + ys[i] ** 2  + zs[i] ** 2)
    #    xs[i] = xs[i] / norm
    #    ys[i] = ys[i] / norm
    #    zs[i] = zs[i] / norm

    #######################      #######################

    '''

    plt.figure('Relative Rotation in Drone Frame of Reference')
    plt.subplot(311)
    plt.plot(pitchs, label='A-pitch')
    plt.plot(yaws, label='B-yaw')
    plt.plot(rolls, label='C-roll')
    plt.legend()
    plt.xlabel('time (in frame)')
    plt.ylabel('rotation (in rad/frame)')
    plt.ylim(-.006, .006)

    # plt.figure('Relative Translation in Drone Frame of Reference')
    plt.subplot(312)
    plt.plot(xs, label='X')
    plt.plot(ys, label='Y')
    plt.plot(zs, label='Z')
    plt.legend()
    plt.xlabel('time')
    plt.ylabel('translation')
    #plt.ylim(-1.1, 1.1)
    # plt.show()

    plt.subplot(313)
    plt.plot(droneCameraAngle, label='droneCameraAngle (in rad)')

    for line in waypoints:
        plt.axvline(x=line)

    plt.legend()
    plt.xlabel('time')
    plt.ylabel('droneCameraAngle')
    plt.show()

    '''

    return np.array([pitchs, yaws, rolls]).transpose((1, 0)), np.array([ys, zs, xs]).transpose((1, 0)), np.array(
        droneCameraAngle), np.array(waypoints)


if __name__ == '__main__':
    print('convertKMLTodroneCoord')
    ori, translation, droneCameraAngle, waypoints = convertKMLToDroneCoord(
        '/Users/fabien/Documents/amherst/fall19/cs696/litchi_missions/Sunrise in Waterbury.kml')
    print(len(ori[0]))
    print(len(translation[0]))
