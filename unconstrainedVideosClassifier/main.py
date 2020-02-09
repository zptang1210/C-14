###
#   IMPORT
###
import json

from classifer import classifier
from fps_converter import *

###
#   LOAD DATA
###
with open('data.json') as json_file:
    videos = json.load(json_file)

###
#   LOOP VIDEOS
###
for video_i in range(len(videos)):
    print('Video {}'.format(video_i + 1))
    video = videos[video_i]
    results = classifier(
        video['compressed_cameramotion'],
        waypoints_framesskipped_converter(video['waypoints'], video['frames_skipped']),
        video['kml'],
        remove_start=video.get('remove_start', 0),
        remove_end=video.get('remove_end', 0))

    print(results['classification'])
