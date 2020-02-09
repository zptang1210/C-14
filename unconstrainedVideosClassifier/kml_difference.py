from bs4 import BeautifulSoup as Soup
import geopy.distance


def get_waypoints(kml_file):
    with open(kml_file) as data:
        kml = Soup(data, 'lxml-xml')

    folders = kml.findAll('Folder')[-3]
    placemarks = folders.findAll('Placemark')

    waypoints = []

    for placemark in placemarks:
        waypoints.append(list(map(float, placemark.coordinates.text.split(',')[0:2])))

    return waypoints


def kml_difference(kml1, kml2):
    waypoints_kml1 = get_waypoints(kml1)

    waypoints_kml2 = get_waypoints(kml2)

    if len(waypoints_kml1) != len(waypoints_kml2):
        print('The number of waypoints should be the same'.format(len(waypoints_kml1), len(waypoints_kml2)))
        exit()

    distances = []

    for i in range(len(waypoints_kml1)):

        if waypoints_kml1[i] != waypoints_kml2[i]:
            distances.append(geopy.distance.distance((waypoints_kml1[i][1], waypoints_kml1[i][0]),
                                                     (waypoints_kml2[i][1], waypoints_kml2[i][0])).m)

    if len(distances) > 1:
        print('Multiple waypoints differ')
        exit()

    return distances


def kml_difference_2(kml1, kml2):
    waypoints_kml1 = get_waypoints(kml1)

    waypoints_kml2 = get_waypoints(kml2)

    if len(waypoints_kml1) != len(waypoints_kml2):
        print('The number of waypoints should be the same'.format(len(waypoints_kml1), len(waypoints_kml2)))
        exit()

    distances = []

    for i in range(len(waypoints_kml1)):

        if waypoints_kml1[i] != waypoints_kml2[i]:
            distances.append(geopy.distance.distance((waypoints_kml1[i][1], waypoints_kml1[i][0]),
                                                     (waypoints_kml2[i][1], waypoints_kml2[i][0])).m)

    if len(distances) > 1:
        print('Multiple waypoints differ')
        exit()

    return distances