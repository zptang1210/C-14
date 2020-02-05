function [ rotation_ABC ] = Rotation( u, v, x, y, focallength_px)

    % -------------------------------------------------------------------------
    % closed form solution to compute the camera rotation
    % ATTENTION: only works accuratly if rotation angles ABC are small!!!
    % -------------------------------------------------------------------------

    a = sum(sum( 1/focallength_px*x.^2.*y.^2 + (y.^2+1).*(focallength_px+1/focallength_px.*y.^2) ));
    b = sum(sum(  (x.^2+1).*(focallength_px+1/focallength_px*x.^2)  ));
    c = sum(sum( x.^2 + y.^2 ));
    d = - sum(sum( x.*y .* (1/focallength_px*x.^2 + 1/focallength_px*y.^2 + 1/focallength_px + focallength_px) ));
    e = - sum(sum( y ));
    f = sum(sum( x ));
    g = - sum(sum( focallength_px * x ));
    h = - sum(sum( focallength_px * y ));
    
    k = sum(sum( u.*x.*y + v.*(y.^2+1) ));
    l = - sum(sum( u.*(x.^2+1) + v.*x.*y ));
    m = sum(sum( u.*y - v.*x ));

    n = [k; l; m];
    M = [a d f; d b e; g h c];

    rotation_ABC = M\n;

end

