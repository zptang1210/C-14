function [ z ] = depth( x, y, translation_UVW, flowTrans, f )

    if sum(translation_UVW(1,:)==0)==3
        z = ones(size(x));
    else
        z = sqrt( ((-translation_UVW(1)*f+x.*translation_UVW(3)).^2 + ...
            (-translation_UVW(2)*f+y.*translation_UVW(3)).^2)...
            ./ (flowTrans(:,:,1).^2 + flowTrans(:,:,2).^2));
    end

end

