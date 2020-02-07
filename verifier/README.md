# Verifier

This is the verifier of C-14. It verifies if the video and its corresponding metadata matches the constrained flight plan. An example of using this verifier is shown as below:

```python
with open('threshold.json', 'r') as fin:
  threshold = json.load(fin)
sampleParam = {'hotpointSampleLength': 1, 'hotpointSampleRate': 0.6, 'waypointSampleLength': 1, 'waypointMaxSampleNum': 5}
compressParam = {'resize': 4, 'skipFrames': 15}

data0411 = ('DJI_0411', 'DJI_0411', program(((173, None), (65, False), (205, True))))
videoName, metadataName, plan = data0411
v = verifier(videoName, metadataName, plan, threshold, sampleParam, compressParam)
flag = v.verify(disableAutoCompression=False)
```

*threshold.json* stores the threshold we use to determine if the video and the plan match. 

*sampleParam* controls the number of samples we draw from each hotpoint and each fly in/out.

*compressParam* controls the compression of the video (if *disableAutoCompression* is set to True, this argument is of no effect).



