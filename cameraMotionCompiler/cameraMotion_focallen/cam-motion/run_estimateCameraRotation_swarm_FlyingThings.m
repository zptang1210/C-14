function [  ] = run_estimateCameraRotation_swarm_FlyingThings( id, pathFlow, pathTXT, pathSave, pathSaveFlow, pathSegmentation, pathGroundtruthMotion, N_THREADS )

maxNumCompThreads(str2num(N_THREADS));
j = str2num(id);

fileID = fopen(pathTXT);
C = textscan(fileID, '%s\n');
fclose(fileID);
path_root = C{1,1}{j};

rotation_prev = [0 0 0];

C = strsplit(path_root, '/');
pathFlow = sprintf('%s/%s', pathFlow, path_root);
pathSave = sprintf('%s/%s', pathSave, path_root);
pathSegmentation = sprintf('%s/%s', pathSegmentation,path_root);
pathGroundtruthMotion = sprintf('%s/%s/%s/%s', pathGroundtruthMotion, C{1,1}, C{1,2}, C{1,3});

numFrames = length(dir(pathFlow))-2;

% directories off all frames
pathFlow_frames = dir(pathFlow); 
pathSegmentation_frames = dir(pathSegmentation);

mkdir(pathSave)
mkdir(sprintf('%s/%s/%s', pathSaveFlow, 'gtCamMotion-gtFocalL', path_root))
mkdir(sprintf('%s/%s/%s', pathSaveFlow, 'estCamMotion-estFocalL', path_root))
mkdir(sprintf('%s/%s/%s', pathSaveFlow, 'gtCamMotion-gtFocalL-negPi-posPi', path_root))
mkdir(sprintf('%s/%s/%s', pathSaveFlow, 'estCamMotion-estFocalL-negPi-posPi', path_root))

fileID = fopen(sprintf('%sestCam_ours.txt', pathSave), 'w');
fileID_gt = fopen(sprintf('%sgt.txt', pathSave), 'w');

fidAngle_est = fopen([sprintf('%s/estCamMotion-estFocalL-negPi-posPi/%s', pathSaveFlow, path_root), 'minmax.txt'], 'w');
fidAngle_gt = fopen([sprintf('%s/gtCamMotion-gtFocalL-negPi-posPi/%s', pathSaveFlow, path_root), 'minmax.txt'], 'w');

error_endPoint_video = zeros(numFrames, 1);
error_endPoint_trans = zeros(numFrames, 1);
rotation_ABC_gt = zeros(numFrames, 3);
rotation_ABC = zeros(numFrames, 3);
translation_UVW_gt = zeros(numFrames, 3);
translation_UVW = zeros(numFrames, 3);

for i = 1 : numFrames

    % path ground truth optical flow
    path_flow = sprintf('%s%s', pathFlow, pathFlow_frames(i+2).name);

    % load motion segmentation
    path_segmentation = sprintf('%s%s', pathSegmentation, pathSegmentation_frames(i+2).name);

    % load camera matrices
    cam_path = sprintf('%s/camera_data_%s.txt', pathGroundtruthMotion, C{1,4});
    cam_data = dlmread(cam_path);
    
    camdata_1 = cam_data(i, :);
    camdata_1 = reshape(camdata_1, 4, 4)';
    camdata_2 = cam_data(i+1, :);
    camdata_2 = reshape(camdata_2, 4, 4)';

    % read groundtruth optical flow
    flow = readFlowFile(path_flow);
    %[flow, ~] = parsePfm(path_flow);
    %flow = flow(:,:,1:2);

    % read motion segmentation
    segmentation = imread(path_segmentation);
    segmentation = segmentation./max(max(segmentation));

    [height, width] = size(segmentation);
    
    % ---------------------------------------------------------------------
    % compute ground truth camera motion between two frames:
    % FlyingThings3D
    %----------------------------------------------------------------------
    motion_matrix_gt = inv(camdata_2) * camdata_1;
    
    % gt focallength
    focallength_gt = -1050.0;

    % frame t+1: move 3D points (camera coordinate system) according to camera motion
    translation_UVW_gt(i,:) = motion_matrix_gt(1:3, 4);
    rotation_matrix = motion_matrix_gt(1:3,1:3);
    rotation_ABC_gt(i, 1) = -atan2(rotation_matrix(3,2), rotation_matrix(3,3));
	rotation_ABC_gt(i, 2) = atan2(-rotation_matrix(3,1), sqrt(rotation_matrix(3,2)*rotation_matrix(3,2) + rotation_matrix(3,3)*rotation_matrix(3,3)));
	rotation_ABC_gt(i, 3) = -atan2(rotation_matrix(2,1), rotation_matrix(1,1));

    % estimate camera motion, given groundtruth flow and groundtruth
    % focallength
    focallength = width;
    [ rotation_ABC(i,:), translation_UVW(i,:) ] = CameraMotion( flow, segmentation, focallength, rotation_prev);
    rotation_prev = rotation_ABC(i,:);

    % rotation: compute end-point-error (EPE)
    [xImg, yImg] = getPixels( zeros(size(segmentation)) );
    idx_motionComponent = find(~segmentation);

    
    flow_estimated_Img = getRotofOF3D( rotation_ABC(i,:), xImg, yImg, focallength, flow);
    flow_estimated = flow_estimated_Img(cat(3, idx_motionComponent, idx_motionComponent+numel(segmentation)));
    writeFlowFile(flow_estimated_Img, sprintf('%s/estCamMotion-estFocalL/%s/%s', pathSaveFlow, path_root, pathFlow_frames(i+2).name));

    flow_gt_Img = getRotofOF3D( rotation_ABC_gt(i,:), xImg, yImg, focallength_gt, flow);
    flow_gt = flow_gt_Img(cat(3, idx_motionComponent, idx_motionComponent+numel(segmentation)));
    writeFlowFile(flow_gt_Img, sprintf('%s/gtCamMotion-gtFocalL/%s/%s', pathSaveFlow, path_root, pathFlow_frames(i+2).name));
    
    B = strsplit(pathFlow_frames(i+2).name, '.');
    [minAngle, maxAngle, min_magnitude, max_magnitude] = convertFlow(flow_estimated_Img, sprintf('%s/estCamMotion-estFocalL-negPi-posPi/%s', pathSaveFlow, path_root), B{1,1});
    fprintf(fidAngle_est, '%f %f %f %f\n', minAngle, maxAngle, min_magnitude, ...
        max_magnitude);
    [minAngle, maxAngle, min_magnitude, max_magnitude] = convertFlow(flow_gt_Img,  sprintf('%s/gtCamMotion-gtFocalL-negPi-posPi/%s', pathSaveFlow, path_root), B{1,1});
    fprintf(fidAngle_gt, '%f %f %f %f\n', minAngle, maxAngle, min_magnitude, ...
        max_magnitude);

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
    formatSpec = '%4.0f -> %4.0f: camera rotation: [%f %f %4f], camera translation: [%f %f %f], f = %f, EPE-rotation: %f, EPE-translation: %f\n';
    fprintf(fileID, formatSpec, i, i+1, rotation_ABC(i,:), translation_UVW(i, :), focallength, error_endPoint_video(i), error_endPoint_trans(i));
    fprintf(fileID_gt, formatSpec, i, i+1, rotation_ABC_gt(i,:), translation_UVW_gt(i, :), focallength, error_endPoint_video(i), error_endPoint_trans(i));

end

fclose(fileID);
fclose(fileID_gt);
fclose(fidAngle_est);
fclose(fidAngle_gt);

% End-Point-Error for each video sequence
%error_endPoint_SINTEL(j) = sum(error_endPoint_video)./numel(error_endPoint_video);
% plot End-Point-Error for each video sequence
f1 = plotEPE( error_endPoint_video, error_endPoint_trans, '', j );
saveas(f1, sprintf('%s/cameraMotion-EPE.png', pathSave))

% plot camera rotations for each video sequence
M = sqrt(translation_UVW_gt(:,1).^2 + translation_UVW_gt(:,2).^2 + translation_UVW_gt(:,3).^2);
translation_UVW_gt = translation_UVW_gt./M;
f2 = plotCameraRotations( rotation_ABC_gt, rotation_ABC, translation_UVW_gt, -translation_UVW, '', j );
saveas(f2, sprintf('%s/cameraMotion.png', pathSave))

% generate video
%createVideo(pathFrames_frames, pathFlow_frames, rotation_ABC, rotation_ABC_gt, focallength, pathSaveFlow);

%end

end

