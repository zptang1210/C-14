function [ angleField, magnitudes ] = convertFlow(flow)

    [~, W, ~] = size(flow);

    angleField = atan2(flow(:,:,2), flow(:,:,1));
    angleField = angleField + pi;
    magnitudes = sqrt(flow(:, :, 1).^2 + flow(:, :, 2).^2);
    
    angleField = uint16(angleField .* 2^16/(2*pi));
    magnitudes = uint16(magnitudes .* 2^16/W);

end

