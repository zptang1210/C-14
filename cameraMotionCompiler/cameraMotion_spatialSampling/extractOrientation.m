function extractOrientation(ofFolderName, frameStart, frameEnd, height, width, spatialSamplingRate, focallen_param)

    frameStart = str2num(frameStart);
    frameEnd = str2num(frameEnd);
    height = str2num(height);
    width = str2num(width);
    spatialSamplingRate = str2num(spatialSamplingRate);
    focallen_param = str2num(focallen_param);

    addpath(genpath('cam-motion'));

    rotation_prev = [0 0 0];

    fid = fopen(strcat('./output/', ofFolderName, '.txt'), 'w');

    segmentation = zeros(height, width);
    focallength_px = width * focallen_param;
    for frameNum = frameStart:frameEnd
        fprintf('Calculating Orientation for FrameNum = %d ...', frameNum);
        floName = strcat(strcat('./extracted/', ofFolderName, '/flo', num2str(frameNum)), '.flo');
        flow = readFlowFile(floName);
        
        [rotation_ABC, translation_UVW, fval] = CameraMotion(flow, segmentation, focallength_px, rotation_prev, spatialSamplingRate);
        
        fprintf(fid, 'frame %d:\nrotation: (%f,%f,%f)\ntranslation: (%f,%f,%f)\n', frameNum, ...
                rotation_ABC(1), rotation_ABC(2), rotation_ABC(3), ...
                translation_UVW(1), translation_UVW(2), translation_UVW(3));
        
        fprintf('Done!\n');
        rotation_prev = rotation_ABC;
    end

    fclose(fid);
    exit;
