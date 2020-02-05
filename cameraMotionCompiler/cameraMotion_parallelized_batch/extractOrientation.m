function extractOrientation(argumentsFile, height, width, focallen_param)

    height = str2num(height);
    width = str2num(width);
    focallen_param = str2num(focallen_param);

    addpath(genpath('cam-motion'));

    arg_file_fid = fopen(strcat('./batchInfo/', argumentsFile), 'r');
    str_arg_num = fgetl(arg_file_fid);
    arg_num = str2double(str_arg_num);

    for i = 1:arg_num
        str_args = fgetl(arg_file_fid);
        splitted_args = regexp(str_args, ',', 'split');
        frameStart = str2double(splitted_args{1});
        frameEnd = str2double(splitted_args{2});
        ofFolderName = splitted_args{3};


        rotation_prev = [0 0 0];

        fid = fopen(strcat('./output/', ofFolderName, '.txt'), 'w');

        segmentation = zeros(height, width);
        focallength_px = width * focallen_param;
        for frameNum = frameStart:frameEnd
            fprintf('Calculating Orientation for FrameNum = %d ...', frameNum);
            floName = strcat(strcat('./extracted/', ofFolderName, '/flo', num2str(frameNum)), '.flo');
            while exist(floName, 'file') ~= 2
                ;
            end
            % D = dir(floName);
            % sizeoffile = D.bytes;
            % fprintf('sizeof', floName, sizeoffile);
            flow = readFlowFile(floName);
            
            [rotation_ABC, translation_UVW, fval] = CameraMotion(flow, segmentation, focallength_px, rotation_prev);
            
            fprintf(fid, 'frame %d:\nrotation: (%f,%f,%f)\ntranslation: (%f,%f,%f)\n', frameNum, ...
                    rotation_ABC(1), rotation_ABC(2), rotation_ABC(3), ...
                    translation_UVW(1), translation_UVW(2), translation_UVW(3));
            
            fprintf('Done!\n');
            rotation_prev = rotation_ABC;
        end

        fclose(fid);
    end

    fclose(arg_file_fid);
    exit;
