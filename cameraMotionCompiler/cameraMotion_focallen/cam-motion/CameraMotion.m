function [ rotation_ABC, translation_UVW, fval ] = CameraMotion( OF, segmentation, focallength_px, R)
% INPUT: OF             optical flow (heightxwidthx2 matrix)
%        u, v           values of the optical flow OF(:,:,1) and OF(:,:,2), 
%                       which belong to a single motion like background.
%                       Pixels of a moving object for example a car are not
%                       included.
%        row, col       position
%                       Example: pixel position of u is (row,col, 1)
%        mask           binary (heightxwidth)-matrix. 
%                       1 if optical flow at this position belongs
%                       to a single motion like backround otherwise 0.
%        height, width  size of optical flow
%
% OUTPUT: TransAngle    ideal translational anglefield, which discribes
%                       the pure camera motion (motion of the static
%                       background)
%         RotadjustedOF observed translational flow field 
%                       (observed optical flow - ideal rotational flow)          
%         RotadjustedAF anglefield of RotadjustedOF  
%         dif           angledifference between anglefield of RotadjustedOF
%                       TransAngle
%         pE            pseudo projection error

    [x_comp_idx_all, y_comp_idx_all] = getPixels( segmentation );
    [height, width] = size(segmentation);

    idx_motionComponent = find(~segmentation);
    
    uv_all = OF(cat(3, idx_motionComponent, idx_motionComponent+numel(segmentation)));

    % down sample flow
    idx_motionComponent_downSampled = dSample(idx_motionComponent, 5, height, width);
    uv = OF(cat(3, idx_motionComponent_downSampled, idx_motionComponent_downSampled+height*width));

    x_shift = width/2-0.5;
    y_shift = height/2-0.5;

    xM = repmat( 0:(width-1), height, 1);
    yM = repmat( [0:(height-1)].', 1, width);
    x = xM-x_shift;
    y = yM-y_shift;

    x_comp_idx = x(idx_motionComponent_downSampled);
    y_comp_idx = y(idx_motionComponent_downSampled);

        %C = {uv_all};
        %x_comp_idx_cell = {x_comp_idx};
        %y_comp_idx_cell = {y_comp_idx};
        
    fval_prev = realmax;
    
    %for i = 1:length(C)
        
        %uv = C{i};
        %x_comp_idx = x_comp_idx_cell{i};
        %y_comp_idx = y_comp_idx_cell{i};
        %--------------------------------------------------------------------------
        % rotations only
        %--------------------------------------------------------------------------
        % rotation_ABC_closedForm = Rotation( uv(:,1), uv(:,2), x_comp_idx, y_comp_idx, focallength_px);
        f_rotation = @(x)fcn_to_minimize_rotation(x, uv, x_comp_idx, y_comp_idx, focallength_px);
        x0 = [0 0 0]; 
        options = optimoptions('fminunc','Display','iter-detailed', 'FiniteDifferenceType', 'central', ...
            'FiniteDifferenceStepSize', eps^(1/3), 'OptimalityTolerance', 1e-8);
        [rotation_ABC_fixedTrans, ~] = fminunc( f_rotation, x0, options);

        %--------------------------------------------------------------------------
        % gradient decent over rotations
        %--------------------------------------------------------------------------   

        f_rotation = @(x)fcn_to_minimize(x, uv, x_comp_idx, y_comp_idx, focallength_px);% 1e-2);
        x0 = [0 0 0]; 
        options = optimoptions('fminunc','Display','iter-detailed', 'FiniteDifferenceType', 'central', ...
            'FiniteDifferenceStepSize', eps^(1/3), 'OptimalityTolerance', 1e-8);%, eps^(1/3));
        [rotation_ABC_1, ~] = fminunc( f_rotation, x0, options); 

        x0 = rotation_ABC_fixedTrans; 
        [rotation_ABC_2, ~] = fminunc( f_rotation, x0, options); 

        x0 = R; 
        [rotation_ABC_3, ~] = fminunc( f_rotation, x0, options);

        disp(size(x_comp_idx_all))
        disp(size(x_comp_idx))
        disp(size(uv_all))
        disp(size(uv))
        fval_1 = fcn_to_minimize( rotation_ABC_1, uv_all, x_comp_idx_all, y_comp_idx_all, focallength_px );
        fval_2 = fcn_to_minimize( rotation_ABC_2, uv_all, x_comp_idx_all, y_comp_idx_all, focallength_px );
        fval_3 = fcn_to_minimize( rotation_ABC_3, uv_all, x_comp_idx_all, y_comp_idx_all, focallength_px );
        
        if fval_1<fval_2
            fval = fval_1;
            rotation_ABC = rotation_ABC_1;
        else
            fval = fval_2;
            rotation_ABC = rotation_ABC_2;
        end

        if fval_3<fval
            fval = fval_3;
            rotation_ABC = rotation_ABC_3;
        end
        
        if fval_prev>fval
            fval_prev = fval;
            rotation_ABC_best = rotation_ABC;
        end
    
    %end  
    
    rotation_ABC = rotation_ABC_best;
    
    % subtract of camera rotation and estimate translation
    RotadjustedOF_comp = getRotofOF3D( rotation_ABC, x_comp_idx, y_comp_idx, focallength_px, uv); 
    [translation_UVW] = Translation( RotadjustedOF_comp(:,:,1), RotadjustedOF_comp(:,:,2), x_comp_idx, y_comp_idx, focallength_px);
   
    % translational optical flow
    TransOF_ideal(:,:,1) = -translation_UVW(1).*focallength_px + x_comp_idx .* translation_UVW(3);
    TransOF_ideal(:,:,2) = -translation_UVW(2).*focallength_px + y_comp_idx .* translation_UVW(3);
    
    % direction of translational optical flow (anglefield)
    RotadjustedAF = anglefield(RotadjustedOF_comp);
    [~, ~, invert] = ...
    chooseTrans( 1:numel(RotadjustedAF), TransOF_ideal, RotadjustedAF );
    translation_UVW = translation_UVW*invert;
    
    %{
    f_camera = @(x)fcn_to_minimize_6DOF(x, uv, x_comp_idx, y_comp_idx, focallength_px);
    A = [];
    b = [];
    Aeq = [];
    beq = [];
    lb =[];
    ub = [];
    nonlcon = @unitspheresurface;
    x0 = [rotation_ABC, translation_UVW];%[0 0 0 0 0 0]; 
    options = optimoptions('fmincon','Display','iter-detailed', 'FiniteDifferenceType', 'central', ...
        'FiniteDifferenceStepSize', eps^(1/3), 'OptimalityTolerance', 1e-8);%, eps^(1/3));
    [rotation_ABC_1, fval] = fmincon( f_camera, x0, A, b, Aeq, beq, lb, ub, nonlcon, options);
    
    rotation_ABC = rotation_ABC_1(1:3);
    translation_UVW = rotation_ABC_1(4:6);
    %}
end
