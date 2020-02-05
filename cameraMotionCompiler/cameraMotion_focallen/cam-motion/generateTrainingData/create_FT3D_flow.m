function [anglefield] = create_FT3D_flow(segmentation_FT3D, img_FT3D, translationDir, size_output)

    height = size_output(1);
    width = size_output(2);
    
    % focal length (assuming f [in mm]/ CCD width [in mm] = 1)
    f = width;

    xmin = floor(-(width)/2);
    xmax = floor((width)/2);
    ymin = floor(-(height)/2);
    ymax = floor((height)/2);
    x_comp = repmat( xmin:xmax, height, 1);
    x_comp(:, width/2 + 1) = [];
    y_comp = repmat( (ymin:ymax).', 1, width);
    y_comp(height/2 + 1, :) = [];
    
    regions = bwlabeln(segmentation_FT3D);
    region_label = unique(regions);
    
    % region mask
    regions = repmat(regions, [1,1,numel(region_label)]);
    region_label = repmat(reshape(region_label, [1,1,numel(region_label)]), [height, width, 1]);
    region_mask = (regions==region_label);
    
    anglefield_1 = zeros(height, width, size(region_label,3));
    anglefield_2 = zeros(height, width, size(region_label,3));
    
    % STATIC BACKGROUND
    % Choose randomly translational directions UVW for each region
    idx = randi([1, size(translationDir,2)], 1, 1);
    % generate anglefields
    UVW = translationDir(:,idx);
    anglefield_1(:,:,1) = -UVW(1)*f + x_comp.*UVW(3);
    anglefield_2(:,:,1) = -UVW(2)*f + y_comp.*UVW(3);
    
    % remove translational directions that are closer than deltaThresh=10 to
    % the background motion direction
    %translationDirNew = removeVector(translationDir, UVW, 10);
    
    % MOVING OBJECTS
    % dilate object region to avoid object boundaries due to later smoothing
    se = strel('square',100);
    dilated_region_mask = imdilate(region_mask(:,:,2:end),se);
    
    % loop over each object
    for i = 2:(size(region_label,3))

        object_i = superpixels(img_FT3D, randi(10), 'Compactness', 100);
        object_i = object_i.*dilated_region_mask(:,:,i-1);
        
        % Choose randomly translational directions UVW for each region
        idx = randi([1, size(translationDir,2)], numel(unique(object_i)), 1);
        
        % generate anglefields
        UVW = reshape(translationDir(:,idx),[3,1,numel(unique(object_i))]);
        y_comp_rep = repmat(y_comp, [1,1,numel(unique(object_i))]);
        x_comp_rep = repmat(x_comp, [1,1,numel(unique(object_i))]);
    
        object_anglefield_1 = repmat(-UVW(1,1,:)*f, [height, width, 1]) + x_comp_rep.*repmat(UVW(3,1,:), [height, width, 1]);
        object_anglefield_2 = repmat(-UVW(2,1,:)*f, [height, width, 1]) + y_comp_rep.*repmat(UVW(3,1,:), [height, width, 1]);
        object_anglefield_1 = object_anglefield_1./sqrt(object_anglefield_1.^2 + object_anglefield_2.^2);
        object_anglefield_2 = object_anglefield_2./sqrt(object_anglefield_1.^2 + object_anglefield_2.^2);
        
        % region mask
        object_regions = repmat(object_i, [1,1,numel(unique(object_i))]);
        object_region_label = repmat(reshape(unique(object_i), [1,1,numel(unique(object_i))]), [height, width, 1]);
        object_region_mask = (object_regions==object_region_label);
        object_anglefield_1 = object_anglefield_1.*object_region_mask;
        object_anglefield_2 = object_anglefield_2.*object_region_mask;
        anglefield_1(:,:,i) = sum(object_anglefield_1(:,:,1:end),3);
        anglefield_2(:,:,i) = sum(object_anglefield_2(:,:,1:end),3);
        
        anglefield_1(:,:,i) = imgaussfilt(anglefield_1(:,:,i), 50);
        anglefield_2(:,:,i) = imgaussfilt(anglefield_2(:,:,i), 50);
        
    end
    
    anglefield_1 = anglefield_1.*region_mask;
    anglefield_2 = anglefield_2.*region_mask;

    anglefield_1 = sum(anglefield_1(:,:,1:end),3);
    anglefield_2 = sum(anglefield_2(:,:,1:end),3);
    
    anglefield(:,:,1) = anglefield_1;
    anglefield(:,:,2) = anglefield_2;
    anglefield(:,:,1) = anglefield(:,:,1)./sqrt(anglefield(:,:,1).^2 + anglefield(:,:,2).^2);
    anglefield(:,:,2) = anglefield(:,:,2)./sqrt(anglefield(:,:,1).^2 + anglefield(:,:,2).^2);
    
    % add Gaussian noise
    anglefield(:,:,1) = anglefield(:,:,1)+ 0.1.*randn(size(anglefield(:,:,1)));
    anglefield(:,:,2) = anglefield(:,:,2)+ 0.1.*randn(size(anglefield(:,:,2)));
    anglefield(:,:,1) = anglefield(:,:,1)./sqrt(anglefield(:,:,1).^2 + anglefield(:,:,2).^2);
    anglefield(:,:,2) = anglefield(:,:,2)./sqrt(anglefield(:,:,1).^2 + anglefield(:,:,2).^2);

end