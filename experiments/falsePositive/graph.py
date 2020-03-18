import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os

font = {'size': 14}
matplotlib.rc('font', **font)

dictionary = {}


def build_dictionary(path, is720=False):
    global dictionary
    for currentpath, folders, files in os.walk(path):
        for file in files:
            if file[:3] == 'log':
                print(os.path.join(currentpath, file))
                file_without_ext = os.path.splitext(file)[0]
                sampleRate, skipRate, resizeRate = list(map(float, file_without_ext.split('_')[1:]))

                if is720:
                    resizeRate = resizeRate * 3

                if not (sampleRate, skipRate, resizeRate) in dictionary:
                    dictionary[(sampleRate, skipRate, resizeRate)] = {}

                with open(os.path.join(currentpath, file)) as f:
                    lines = f.readlines()

                    previous_number = None
                    previous_video = None
                    previous_sampleRate = None
                    previous_resizeRate = None
                    previous_estYaw = None
                    previous_realYaw = None
                    previous_diff = None

                    for line in lines:
                        line = line.strip().split(' ')
                        if line[0] == '#': previous_number = line[1]
                        if line[0] == 'video': previous_video = line[1]
                        if line[0] == 'sampleRate': previous_sampleRate = line[1]
                        if line[0] == 'resizeRate': previous_resizeRate = line[1]
                        if line[0] == 'estYaw': previous_estYaw = line[1]
                        if line[0] == 'realYaw': previous_realYaw = line[1]
                        if line[0] == 'diff':
                            previous_diff = line[1]
                            if not (previous_video, previous_number) in dictionary[(sampleRate, skipRate, resizeRate)]:
                                dictionary[(sampleRate, skipRate, resizeRate)][(previous_video, previous_number)] = [
                                    {
                                        'estYaw': previous_estYaw,
                                        'realYaw': previous_realYaw,
                                        'diff': previous_diff
                                    }
                                ]
                            else:
                                dictionary[(sampleRate, skipRate, resizeRate)][
                                    (previous_video, previous_number)].append(
                                    {
                                        'estYaw': previous_estYaw,
                                        'realYaw': previous_realYaw,
                                        'diff': previous_diff
                                    })


######

build_dictionary('data/', False)

# Remove last hotpoint
for parameters, parameters_v in dictionary.items():
    for videos, videos_v in parameters_v.items():
        if len(dictionary[parameters][videos]) == 3:
            dictionary[parameters][videos] = dictionary[parameters][videos][:-1]


###########

def getyaws(skipRate_params=15, resizeRate_params=15, sampleRate_params=1):
    yaws = []

    for parameters, parameters_v in dictionary.items():
        sampleRate, skipRate, resizeRate = parameters
        print(sampleRate, skipRate, resizeRate)
        if skipRate == skipRate_params and resizeRate == resizeRate_params and sampleRate == sampleRate_params:
            for videos, videos_v in parameters_v.items():
                print(videos)
                for hotpoints in videos_v:
                    print(hotpoints)
                    yaws.append(float(hotpoints['diff']))
    return yaws


def getfalseNegative(skipRate_params=15, resizeRate_params=15, sampleRate_params=1, threshold=20):
    total_number_videos = 0
    total_of_true = 0

    for parameters, parameters_v in dictionary.items():
        sampleRate, skipRate, resizeRate = parameters

        #####  #####
        if skipRate == skipRate_params and resizeRate == resizeRate_params and sampleRate == sampleRate_params:
            for videos, videos_v in parameters_v.items():
                check = True
                for i_hotpoints, hotpoints in enumerate(videos_v):
                    if abs(float(hotpoints['diff'])) > threshold:
                        check = False
                total_number_videos += 1
                if check: total_of_true += 1

        # if skipRate == 10 and resizeRate == resizeRate_params and sampleRate == 0.8:
        #     for videos, videos_v in parameters_v.items():
        #         check = True
        #         for i_hotpoints, hotpoints in enumerate(videos_v):
        #             if abs(float(hotpoints['diff'])) > threshold:
        #                 print('###')
        #                 print(hotpoints)
        #                 print(i_hotpoints)
        #                 print(videos)
        #                 print(float(hotpoints['diff']))
        #                 check = False
        #         total_number_videos += 1
        #         if check: total_of_true += 1

    return 1 - total_of_true / total_number_videos


#### PLOT ####

fn = []
thresholds = np.arange(5, 50, 1)
sampleRates = [0.2, 0.4, 0.6, 0.8, 1]

for _ in thresholds:
    fn.append([])
    for _ in sampleRates:
        fn[-1].append(None)

for i, threshold in enumerate(thresholds):
    for j, sampleRate in enumerate(sampleRates):
        fn[i][j] = getfalseNegative(skipRate_params=15, resizeRate_params=12, sampleRate_params=sampleRate,
                                    threshold=threshold)
print(fn)

fn = np.array(fn).T
fig, ax = plt.subplots()
CS = ax.contour(thresholds, sampleRates, fn, [0, 0.02, 0.05, 0.1])

ax.clabel(CS, inline=1, fontsize=10)
plt.xlabel('Rotation error threshold (in degrees)')
plt.ylabel('Sampling rate')
plt.show()
# plt.savefig('graphs/fn_contrained.pdf')
