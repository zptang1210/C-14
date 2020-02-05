function [ I_filtered ] = filterAngleImg( I_orig, filter, mask )

    [filter_size, ~] = size(filter);
    pad = floor(filter_size/2);
    
    [h, w] = size(I_orig);
    
    [row,col] = find(mask);
    a = max(1, min(row)-pad);
    b = min(max(row)+pad, h);
    c = max(1, min(col)-pad);
    d = min(w, max(col)+pad);
    
    I = I_orig(a:b, c:d);
    
    [I_height, I_width] = size(I);
    
    I_filtered = I;%zeros(I_height, I_width);
    %I = padarray(I, [pad pad], 0, 'both');
    
    for i = (pad+1):(I_width-pad)
        for j = (pad+1):(I_height-pad)
            
            center_point = I(j,i);
            I_crop = I((j-pad):(j-pad+filter_size-1),(i-pad):(i-pad+filter_size-1));
            
            angle_dif = center_point - I_crop;
            
            angle_dif(angle_dif<-pi) = 2*pi + angle_dif(angle_dif<-pi);
            angle_dif(angle_dif>pi) = angle_dif(angle_dif>pi) - 2*pi;
            
            I_filtered(j, i) = center_point - sum(sum(filter .* angle_dif));
            
        end
    end

    I_filtered(I_filtered>pi)= I_filtered(I_filtered>pi) - 2*pi;
    I_filtered(I_filtered<-pi) = I_filtered(I_filtered<-pi) + 2*pi;
    
    I_orig(a:b, c:d) = I_filtered;
    I_filtered = I_orig;

end

