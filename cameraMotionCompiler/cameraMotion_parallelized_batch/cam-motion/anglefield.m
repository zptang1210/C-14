function [ angleImage ] = anglefield(opticalflow)

    magn = sqrt(opticalflow(:,:,1).^2 + opticalflow(:,:,2).^2);

    mask = opticalflow(:,:,2)<0;
    angleImage = (acos(opticalflow(:,:,1)./(magn+eps))) .* (mask.*2-1) + abs(mask-1)*2*pi;

end

