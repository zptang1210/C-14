function [ epe ] = endPointError( flow_gt, flow_estimated, norm_factor )

    flow_gt_norm = flow_gt./norm_factor;
    flow_estimated_norm = flow_estimated./norm_factor;
    
    flow_dif = flow_gt_norm - flow_estimated_norm;
    magnitude = sqrt(flow_dif(:,:,1).^2 + flow_dif(:,:,2).^2);
    
    epe = sum(sum(magnitude))./numel(magnitude);

end

