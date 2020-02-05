function [ ] = createVideo(dirFrames, dirFlow, rotation_ABC, rotation_ABC_gt, focallength, dirVideo, pathTransFlow)%SegmentationCell, TransIdealCell, TransCell, dirVideo, depthCell)
% INPUT: SegmentationCell segmentations (numx1 cell array)     
%        firstidxOF       number of first frame (mostly 1)    
%        lastidxOF        number of last frame-1 
%        video            video name, for example 'forest'
%        imageformate     formate of the frame, for example '.png'
%        dirVideo         directory where video will be saved


%videoname  = sprintf('%s_rndStartSGD_%03d.%s', video, focallength_sensorwidth,  'avi');
outputVideo = VideoWriter(fullfile(dirVideo, sprintf('video_2.avi')));
outputVideo.FrameRate = 15;
open(outputVideo);
numFrames = length(rotation_ABC);

%origImg = imread(sprintf('%s/frame_%04d.png', dirFrames, 1));
origImg = imread(sprintf('%s/%s', dirFrames(3).folder, dirFrames(3).name));
[height, width, ~] = size(origImg);

x_shift = width/2-0.5;
y_shift = height/2-0.5;
xM = repmat( 0:(width-1), height, 1);
yM = repmat( [0:(height-1)].', 1, width);
x = xM-x_shift;
y = yM-y_shift;

for i = 1:numFrames
    
    %origImg = imread(sprintf('%s/frame_%04d.png', dirFrames, i));
    origImg = imread(sprintf('%s/%s', dirFrames(i+2).folder, dirFrames(i+2).name));
    
    flow = readFlowFile(sprintf('%s/%s', dirFlow(i+2).folder, dirFlow(i+2).name));
    %load(sprintf('%s/%s', dirFlow(i+2).folder, dirFlow(i+2).name));
    %flow = uv;
 
    flow_compensated = getRotofOF3D( rotation_ABC(i,:), x(:), y(:), focallength, flow);
    flow_compensated_gt = getRotofOF3D( rotation_ABC_gt(i,:), x(:), y(:), focallength, flow);
        
    % compute translational anglefiled
    flow_compensated = flow_compensated./sqrt(flow_compensated(:,:,1).^2 + flow_compensated(:,:,2).^2);
    flow_compensated_gt = flow_compensated_gt./sqrt(flow_compensated_gt(:,:,1).^2 + flow_compensated_gt(:,:,2).^2);
    
    frame = [im2uint8(origImg) uint8(flowToColor(flow)); uint8(flowToColor(flow_compensated)) uint8(flowToColor(flow_compensated_gt))];
    writeVideo(outputVideo, frame);
    
end

close(outputVideo);

end

