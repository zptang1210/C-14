function [ avgError ] = fcn_to_minimize( rotation_ABC, uv, x, y, f )

TransOF = getRotofOF3D( rotation_ABC, x, y, f, uv);
%RotOF = getRotofOF( rotation_ABC, x, y, f);
%TransOF = uv + RotOF;
% direction of translational optical flow (anglefield)
RotadjustedAF = anglefield(TransOF);
% magnitude of translational optical flow
magn = sqrt((TransOF(:,:,1)/f).^2 + (TransOF(:,:,2)/f).^2);%ones(size(TransOF));%

%--------------------------------------------------------------------------
%translational component (Berthold Horn, Robot Vision, p.409)
%--------------------------------------------------------------------------
%f_translation = @(x0)fcn_to_minimize_translation(x0, uv, x, y, f);% 1e-2);
%x0 = [0 0 0];%Translation( TransOF(:,:,1), TransOF(:,:,2), x, y, f); 
%options = optimoptions('fminunc', 'FiniteDifferenceType', 'central', ...
%        'FiniteDifferenceStepSize', eps^(1/3), 'OptimalityTolerance', 1e-8);%, eps^(1/3));
%[translation_UVW, fval] = fminunc( f_translation, x0, options);

[translation_UVW] = Translation( TransOF(:,:,1), TransOF(:,:,2), x, y, f);

% -------------------------------------------------------------------------
% check correct direction of translation_UVW
% -------------------------------------------------------------------------
TransOF_ideal(:,:,1) = -translation_UVW(1).*f + x .* translation_UVW(3);
TransOF_ideal(:,:,2) = -translation_UVW(2).*f + y .* translation_UVW(3);

[~, dif, ~] = ...
chooseTrans( 1:numel(RotadjustedAF), TransOF_ideal, RotadjustedAF );
    
Error = pi.*magn.*(dif/180);
numPixels = numel(TransOF)/2;
avgError = sum(sum(Error))/numPixels;

end

