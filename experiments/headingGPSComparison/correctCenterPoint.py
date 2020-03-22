import sys
import matplotlib.pyplot as plt
from geographiclib.geodesic import Geodesic
sys.path.append('../../utils')
from parseMetadata_new import parseMetadata



def extractGPSInfo(metadataFilePath):
    with open(metadataFilePath, 'r') as fid:
        txt = fid.readlines()

    # direcrtly print the lines not starting with numerical character
    # print(txt[0])
    i = 1
    while txt[i][0].isdigit() == False:
        # print(txt[i])
        i+=1

    # process record
    info = []
    old_data_list = [''] * 9 
    while i < len(txt):
        splittedTxt = txt[i].split(' ')
        timestamp = int(splittedTxt[0])
        data_str = "".join(splittedTxt[1:])

        data_list = data_str.split(',')
        if data_list[0][0].isalpha():
            # print(i, '-', txt[i])
            pass
        else:
            if data_list != old_data_list:
                [lat_str, lon_str, alt_str, pit_str, rol_str, yaw_str,
                vx_str, vy_str, vz_str] = data_str.split(',')
                latitude = float(lat_str)
                longitude = float(lon_str)
                altitude = float(alt_str)
                pitch = float(pit_str)
                roll = float(rol_str)
                yaw = float(yaw_str)
                vx = float(vx_str)
                vy = float(vy_str)
                vz = float(vz_str)
                info.append((timestamp, None, latitude, longitude, altitude,
                            pitch, roll, yaw, vx, vy, vz))
                old_data_list = data_list

        i+=1
    
    return info

def extractLatLong(info):
    x, y = [], []
    for item in info:
        latitude, longtitude = item[2], item[3]
        x.append(latitude)
        y.append(longtitude)
    return x, y

def plotTrace2D(info, centerPoint):
    x, y = extractLatLong(info)
    #plt.axis('equal')
    plt.figure(figsize=(9, 9))
    plt.plot(y, x, c='black')
    plt.plot([centerPoint[1]], [centerPoint[0]], 'ro')
    plt.show()


def correctCenterPoint(metadataFilePath, startPoint, azimuth, radius, verbose=False):
    geodict = Geodesic.WGS84.Direct(startPoint[0], startPoint[1], azimuth, -radius)
    if verbose: print(geodict)
    centerPoint = geodict['lat2'], geodict['lon2']

    if verbose:
        info = extractGPSInfo(metadataFilePath)
        plotTrace2D(info, centerPoint)

    return centerPoint


if __name__ == '__main__':
    metadataFolder = './metadata/'
    metadataFile = 'DJI_0460_corrected.metadata'
    startPoint = (42.39406174172764,-72.73755380039054) # lat/lng
    azimuth = 333
    radius = 30

    centerPoint = correctCenterPoint(metadataFolder+metadataFile, startPoint, azimuth, radius, verbose=True)
    print((centerPoint[1], centerPoint[0]))
