function generateTAFlowFT3D(set)
    rng default

    %FT3DPathLoad = '/local_scratch/pbideau/data/FlyingThings'; %'/mnt/nfs/work1/elm/rrmenon/shared_data';%'/scratch/clear/ptokmako/datasets/FlyingThings';
    %FT3DPathSave = '/local_scratch/pbideau/data/syntheticTrainingData/TRAIN_synthetic_unitVec_noise';%'/mnt/nfs/scratch1/pbideau/motionSegmentation/Tokmakov17/FlyingThings/TRAIN_trans_negPI_posPI';%'/home/piabideau/Desktop/gypsum/FlyingThings/TRAIN_trans_0_PI_puppenkiste';%'/mnt/nfs/scratch1/pbideau/motionSegmentation/Tokmakov17/FlyingThings/TRAIN_trans_negPI_posPI';
    
    FT3DPathLoad = '/mnt/nfs/work1/elm/rrmenon/shared_data';%'/local_scratch/pbideau/data/FlyingThings'; %'/mnt/nfs/work1/elm/rrmenon/shared_data';%'/scratch/clear/ptokmako/datasets/FlyingThings';
    FT3DPathSave = '/mnt/nfs/scratch1/pbideau/motionSegmentation/FlyingThings3D_deltaTheta_TRAIN';%'/local_scratch/pbideau/data/syntheticTrainingData/TRAIN_synthetic_unitVec_noise';%'/mnt/nfs/scratch1/pbideau/motionSegmentation/Tokmakov17/FlyingThings/TRAIN_trans_negPI_posPI';%'/home/piabideau/Desktop/gypsum/FlyingThings/TRAIN_trans_0_PI_puppenkiste';%'/mnt/nfs/scratch1/pbideau/motionSegmentation/Tokmakov17/FlyingThings/TRAIN_trans_negPI_posPI';
    splits = dir([FT3DPathLoad, '/frames_finalpass/', set]);
    
    frequency = 50;
    % generate set of translational directions using verices of an icosahedron
    [translationDir] = ikosaeder(frequency);
    
    %for i=3:length(splits)
    i = 3;
        videos = dir([FT3DPathLoad, '/frames_finalpass/', set, '/', splits(i).name]);
        for j = 3 : length(videos)
            convertSeq2AngleField(FT3DPathLoad, FT3DPathSave, [set, '/', splits(i).name '/', ...
                videos(j).name, '/left/'], translationDir);
            convertSeq2AngleField(FT3DPathLoad, FT3DPathSave, [set, '/', splits(i).name '/', ...
                videos(j).name, '/right/'], translationDir);
        end
    %end
end

function convertSeq2AngleField(FT3DPathLoad, FT3DPathSave, seqPath, translationDir)

    frames = dir([FT3DPathLoad, '/motion_labels_new/', seqPath]);
    mkdir([FT3DPathSave, '/flow_angles/', seqPath]);
    
    for i = 3 : length(frames)
        frame_name = frames(i).name;
        split = strsplit(frame_name, '.');
        gt_frame = imread([FT3DPathLoad, '/motion_labels_new/', seqPath, frame_name]);
        img_FT3D = imread([FT3DPathLoad, '/frames_finalpass/', seqPath, frame_name]);

        [height, width, ~] = size(gt_frame);
        
        % generate anglefield
        [angleField] = create_FT3D_flow(gt_frame, img_FT3D, translationDir, [height, width]); % [-1 1]
        
        % transform to uint16
        angleField = 0.5.*(angleField + 1); % [0 1]
        anglefield_1_uint16 = uint16(angleField(:,:,1) .* 2^16); % [0 2^16]
        anglefield_2_uint16 = uint16(angleField(:,:,2) .* 2^16);
        
        imwrite(anglefield_1_uint16, [FT3DPathSave, '/flow_angles/', seqPath, ...
            'angleField_u_', split{1}, '.png']);
        imwrite(anglefield_2_uint16, [FT3DPathSave, '/flow_angles/', seqPath, ...
            'angleField_v_', split{1}, '.png']);

    end

end
