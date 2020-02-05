function [  ] = run_estimateCameraRotation_davis( id, pathFlow, pathFrames, pathSave, pathSaveFlow, pathSegmentation, N_THREADS )

maxNumCompThreads(str2num(N_THREADS));

[j, s] = ind2sub([50, 5], str2num(id));

j=j+2;

scale_list = [0.6 0.8 1 1.2 1.4];
scale = scale_list(s);

%j = str2num(id);

nameVideos = dir(pathFrames);
name = nameVideos(j).name;

rotation_prev = [0 0 0];

pathFrames = sprintf('%s/%s', pathFrames, name);
pathFlow = sprintf('%s/%s', pathFlow, name);
pathSave = sprintf('%s-%02d/%s', pathSave, scale*10, name);
pathSegmentation = sprintf('%s/%s', pathSegmentation, name);


numFrames = length(dir(pathFlow))-2;

% directories off all frames
pathFrames_frames = dir(pathFrames);
pathFlow_frames = dir(pathFlow); 
pathSegmentation_frames = dir(pathSegmentation);


mkdir(pathSave)
mkdir(sprintf('%s/estCamMotion-estFocalL-%02d/%s', pathSaveFlow, scale*10, name))
mkdir(sprintf('%s/estCamMotion-estFocalL-%02d-negPi-posPi/%s', pathSaveFlow, scale*10, name))
%mkdir(sprintf('%s/%s/%s', pathSaveFlow, 'origFlow', name))
%mkdir(sprintf('%s/%s/%s', pathSaveFlow, 'origFlow-negPi-posPi', name))

fileID = fopen(sprintf('%s/%s_estCam_ours.txt', pathSave, name), 'w');

rotation_ABC = zeros(numFrames, 3);
translation_UVW = zeros(numFrames, 3);






for i = 1 : numFrames

    % path ground truth optical flow
    path_flow = sprintf('%s/%s', pathFlow, pathFlow_frames(i+2).name);

    % load motion segmentation
    path_segmentation = sprintf('%s/%s', pathSegmentation, pathSegmentation_frames(i+2).name);

    
    
    
    
    % read groundtruth optical flow
    flow = readFlowFile(path_flow);
    %load(path_flow);
    %flow = uv;

    % read motion segmentation
    segmentation = imread(path_segmentation);
    segmentation = segmentation./max(max(segmentation));
    
    
    [height, width] = size(segmentation);
    se = strel('disk', 10); mask_big = imdilate(double(segmentation), se);
    segmentation = mask_big;
    
    focallength = scale*width;

    % estimate camera motion, given groundtruth flow and groundtruth
    % focallength
    [ rotation_ABC(i,:), translation_UVW(i,:) ] = CameraMotion( flow, segmentation, focallength, rotation_prev);
    rotation_prev = rotation_ABC(i,:);
    
    % save rotation compensated flow as .flo file
    [xImg, yImg] = getPixels( zeros(height, width) );
    
    flow_estimated_Img = getRotofOF3D( rotation_ABC(i,:), xImg, yImg, focallength, flow);
    writeFlowFile(flow_estimated_Img, sprintf('%s/estCamMotion-estFocalL-%02d/%s/%05d.flo', pathSaveFlow, scale*10, name, i));

    
    %writeFlowFile(flow, sprintf('%s/origFlow/%s/%05d.flo', pathSaveFlow, name, i ));

    % save rotation compensated flow as angle and magnitude seperately
    [anglefield_uint16, magnitude_uint16] = convertFlow(flow_estimated_Img);
    imwrite(anglefield_uint16, sprintf('%s/estCamMotion-estFocalL-%02d-negPi-posPi/%s/angleField_%05d.png', pathSaveFlow, scale*10, name, i));
    imwrite(magnitude_uint16, sprintf('%s/estCamMotion-estFocalL-%02d-negPi-posPi/%s/magField_%05d.png', pathSaveFlow, scale*10, name, i));

    %[anglefield_uint16, magnitude_uint16] = convertFlow(flow);
    %imwrite(anglefield_uint16, sprintf('%s/origFlow-negPi-posPi/%s/angleField_%05d.png', pathSaveFlow, name, i));
    %imwrite(magnitude_uint16, sprintf('%s/origFlow-negPi-posPi/%s/magField_%05d.png', pathSaveFlow, name, i));
    
    % write estimated rotation to .txt file
    formatSpec = '%4.0f -> %4.0f: camera rotation: [%f %f %f], camera translation: [%f %f %f], f = %f\n';
    fprintf(fileID, formatSpec, i, i+1, rotation_ABC(i,:), translation_UVW(i, :), focallength);

end

fclose(fileID);

% generate video
%createVideo(pathFrames_frames, pathFlow_frames, rotation_ABC, rotation_ABC_gt, focallength, pathSave, pathTransFlow);

end
