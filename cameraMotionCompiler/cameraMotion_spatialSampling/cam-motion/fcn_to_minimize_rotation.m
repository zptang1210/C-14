function [ avgError, Error ] = fcn_to_minimize_rotation( rotation_ABC, uv, x, y, f )

TransOF = getRotofOF3D( rotation_ABC, x, y, f, uv);

% magnitude of translational optical flow
magn = sqrt((TransOF(:,:,1)/f).^2 + (TransOF(:,:,2)/f).^2);%ones(size(TransOF));%

Error = magn;
numPixels = numel(TransOF)/2;
avgError = sum(sum(Error))/numPixels;

end
