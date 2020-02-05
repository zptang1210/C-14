function [ TransAngle, dif, invert] = chooseTrans( idx, TransOF_ideal, RotadjustedAF )

    %select translational anglefield with smalles difference in Angle
    TransAngle_1 = anglefield(TransOF_ideal);
    TransAngle_2 = mod(TransAngle_1+pi, 2*pi);

    dif_1 = abs( RotadjustedAF(idx) - TransAngle_1(idx) );
    dif_1 = min( dif_1, abs(2*pi-dif_1));

    if sum(sum(dif_1)) < numel(dif_1)*pi/2 
        TransAngle = TransAngle_1;
        dif = dif_1;
        invert = 1;
    else     
        TransAngle = TransAngle_2;
        dif = pi-dif_1;
        invert = -1;
    end

end

