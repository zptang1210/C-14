# Video Processing

In this folder, we provide several methods to compress the video taken from drones in order to accelerate the verification speed.



* videoCompressor.py

  Compress each frame in the original video by a certain scale.

* patchExtractor.py

  Extract the patch in the central part of each frame and form a new video.

* skipFrames.py

  Skip frames in the original video.



extractFrames.py can extract each frame and generate image files. This is used to debug the optical flow. videoProcessor.py is the base class.



## How to use

Put the original video in the same folder, and use these video processors by using commands like this:

```python
python videoCompressor.py DJI_0179 20

python skipFrames.py DJI_0179 3

python patchExtractor.py DJI_0179 100 100
```

