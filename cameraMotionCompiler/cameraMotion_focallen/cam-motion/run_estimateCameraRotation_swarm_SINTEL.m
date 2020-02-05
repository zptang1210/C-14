function [  ] = run_estimateCameraRotation_swarm_SINTEL( id, pathFlow, pathFrames, pathSave, pathSaveFlow, pathSegmentation, pathGroundtruthMotion, N_THREADS )

maxNumCompThreads(str2num(N_THREADS));
j = str2num(id);

nameVideos = dir(pathFrames);
name = nameVideos(j).name;

rotation_prev = [0 0 0];

pathFrames = sprintf('%s/%s', pathFrames, name);
pathFlow = sprintf('%s/%s', pathFlow, name);
pathSave = sprintf('%s/%s', pathSave, name);
pathSegmentation = sprintf('%s/%s', pathSegmentation, name);
pathGroundtruthMotion = sprintf('%s/%s', pathGroundtruthMotion, name);

numFrames = length(dir(pathFlow))-2;

% directories off all frames
pathFrames_frames = dir(pathFrames);
pathFlow_frames = dir(pathFlow); 
pathSegmentation_frames = dir(pathSegmentation);
pathGroundtruthMotion_frames = dir(pathGroundtruthMotion);

mkdir(pathSave)
mkdir(sprintf('%s/%s/%s', pathSaveFlow, 'gtCamMotion-gtFocalL', name))
mkdir(sprintf('%s/%s/%s', pathSaveFlow, 'estCamMotion-estFocalL', name))
mkdir(sprintf('%s/%s/%s', pathSaveFlow, 'gtCamMotion-gtFocalL-negPi-posPi', name))
mkdir(sprintf('%s/%s/%s', pathSaveFlow, 'estCamMotion-estFocalL-negPi-posPi', name))

fileID = fopen(sprintf('%s/%s_estCam_ours.txt', pathSave, name), 'w');
fileID_gt = fopen(sprintf('%s/%s_gt.txt', pathSave, name), 'w');

error_endPoint_video = zeros(numFrames, 1);
error_endPoint_trans = zeros(numFrames, 1);
rotation_ABC_gt = zeros(numFrames, 3);
rotation_ABC = zeros(numFrames, 3);
translation_UVW_gt = zeros(numFrames, 3);
translation_UVW = zeros(numFrames, 3);

for i = 1 : numFrames

    % path ground truth optical flow
    path_flow = sprintf('%s/%s', pathFlow, pathFlow_frames(i+2).name);

    % load motion segmentation
    path_segmentation = sprintf('%s/%s', pathSegmentation, pathSegmentation_frames(i+2).name);

    % load camera matrices
    camdata_1 = sprintf('%s/%s', pathGroundtruthMotion, pathGroundtruthMotion_frames(i+2).name);
    camdata_2 = sprintf('%s/%s', pathGroundtruthMotion, pathGroundtruthMotion_frames(i+3).name);

    % read groundtruth optical flow
    flow = readFlowFile(path_flow);
    %load(path_flow);
    %flow = uv;
    %pathFlow_frames(i+2).name = strrep(pathFlow_frames(i+2).name, 'mat', 'flo');

    % read motion segmentation
    segmentation = imread(path_segmentation);
    segmentation = segmentation./max(max(segmentation));

    [height, width] = size(segmentation);

    % compute ground truth camera motion between two frames
    [ rotation_ABC_gt(i,:), ~, translation_UVW_gt(i,:), focallength_gt ] = camdata2rot( camdata_1, camdata_2);
    focallength = width;

    % estimate camera motion, given groundtruth flow and groundtruth
    % focallength
    [ rotation_ABC(i,:), translation_UVW(i,:) ] = CameraMotion( flow, segmentation, focallength, rotation_prev);
    rotation_prev = rotation_ABC(i,:);
    
    % save rotation compensated flow as .flo file
    [xImg, yImg] = getPixels( zeros(height, width) );
    
    flow_estimated_Img = getRotofOF3D( rotation_ABC(i,:), xImg, yImg, focallength, flow);
    writeFlowFile(flow_estimated_Img, sprintf('%s/estCamMotion-estFocalL/%s/%05d.flo', pathSaveFlow, name, i));
     
    flow_gt_Img = getRotofOF3D( rotation_ABC_gt(i,:), xImg, yImg, focallength_gt, flow);
    writeFlowFile(flow_gt_Img, sprintf('%s/gtCamMotion-gtFocalL/%s/%05d.flo', pathSaveFlow, name, i ));

    % save rotation compensated flow as angle and magnitude seperately
    [anglefield_uint16, magnitude_uint16] = convertFlow(flow_estimated_Img);
    imwrite(anglefield_uint16, sprintf('%s/estCamMotion-estFocalL-negPi-posPi/%s/angleField_%05d.png', pathSaveFlow, name, i));
    imwrite(magnitude_uint16, sprintf('%s/estCamMotion-estFocalL-negPi-posPi/%s/magField_%05d.png', pathSaveFlow, name, i));

    [anglefield_uint16, magnitude_uint16] = convertFlow(flow_gt_Img);
    imwrite(anglefield_uint16, sprintf('%s/gtCamMotion-gtFocalL-negPi-posPi/%s/angleField_%05d.png', pathSaveFlow, name, i));
    imwrite(magnitude_uint16, sprintf('%s/gtCamMotion-gtFocalL-negPi-posPi/%s/magField_%05d.png', pathSaveFlow, name, i));
    
    % rotation: compute end-point-error (EPE)
    idx_motionComponent = find(~segmentation);
    flow_estimated = flow_estimated_Img(cat(3, idx_motionComponent, idx_motionComponent+numel(segmentation)));
    flow_gt = flow_gt_Img(cat(3, idx_motionComponent, idx_motionComponent+numel(segmentation)));

    error_endPoint_video(i) = endPointError( flow_gt, flow_estimated, width )*100;

    % translation: compute end-point-error (EPE)
    magnitude = sqrt(flow_gt_Img(:,:,1).^2+flow_gt_Img(:,:,2).^2);
    flow_trans_estimated_Img = zeros(numel(xImg),2);
    flow_trans_estimated_Img(:,1) = -translation_UVW(i,1).*focallength + xImg .* translation_UVW(i,3);
    flow_trans_estimated_Img(:,2) = -translation_UVW(i,2).*focallength + yImg .* translation_UVW(i,3);
    magnitude_estimated = sqrt(flow_trans_estimated_Img(:,1).^2 + flow_trans_estimated_Img(:,2).^2);
    flow_trans_estimated_Img = flow_trans_estimated_Img./magnitude_estimated;
    flow_trans_estimated_Img(isnan(flow_trans_estimated_Img)) = 0;
    flow_trans_estimated_Img = reshape(flow_trans_estimated_Img, [height, width, 2]);
    flow_trans_estimated_Img = flow_trans_estimated_Img.*magnitude;
    flow_trans_estimated = flow_trans_estimated_Img(cat(3, idx_motionComponent, idx_motionComponent+numel(segmentation)));

    error_endPoint_trans(i) = endPointError( flow_gt, reshape(flow_trans_estimated, [height*width-sum(sum(segmentation)), 1, 2]), width )*100; 

    % write estimated rotation to .txt file
    formatSpec = '%4.0f -> %4.0f: camera rotation: [%f %f %f], camera translation: [%f %f %f], f = %f, EPE-rotation: %f, EPE-translation: %f\n';
    fprintf(fileID, formatSpec, i, i+1, rotation_ABC(i,:), translation_UVW(i, :), focallength, error_endPoint_video(i), error_endPoint_trans(i));
    fprintf(fileID_gt, formatSpec, i, i+1, rotation_ABC_gt(i,:), translation_UVW_gt(i, :), focallength, error_endPoint_video(i), error_endPoint_trans(i));

end

fclose(fileID);
fclose(fileID_gt);

% End-Point-Error for each video sequence
%error_endPoint_SINTEL(j) = sum(error_endPoint_video)./numel(error_endPoint_video);
% plot End-Point-Error for each video sequence
f1 = plotEPE( error_endPoint_video, error_endPoint_trans, name, j );
saveas(f1, sprintf('%s/cameraMotion-EPE.png', pathSave))

% plot camera rotations for each video sequence
M = sqrt(translation_UVW_gt(:,1).^2 + translation_UVW_gt(:,2).^2 + translation_UVW_gt(:,3).^2);
translation_UVW_gt = translation_UVW_gt./M;
f2 = plotCameraRotations( rotation_ABC_gt, rotation_ABC, translation_UVW_gt, -translation_UVW, name, j );
saveas(f2, sprintf('%s/cameraMotion.png', pathSave))

% generate video
createVideo(pathFrames_frames, pathFlow_frames, rotation_ABC, rotation_ABC_gt, focallength, pathSaveFlow);


end


