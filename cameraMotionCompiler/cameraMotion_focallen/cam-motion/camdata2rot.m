function [ rotAngle, R, Tc, f ] = camdata2rot( camdata_1, camdata_2)
% N: extrinsic matrix
% M: intrisic matrix

    row = [0 0 0 1];
    [M1,N1] = cam_read(camdata_1);
    [M2,N2] = cam_read(camdata_2);
    
    N2 = [N2; row];
    N1 = [N1; row];
    
    %R = N2/N1;
    R =  N2 * inv(N1); % +
    %R = N1 * inv(N2); % -

    Tc = R(1:3, 4);
    Rc = R(1:3, 1:3);
    
    rotAngle(1) = atan2(Rc(3,2), Rc(3,3));
	rotAngle(2) = atan2(-Rc(3,1), sqrt(Rc(3,2)*Rc(3,2) + Rc(3,3)*Rc(3,3)));
	rotAngle(3) = atan2(Rc(2,1), Rc(1,1));
    %{
    R_x = [1 0 0; 0 cos(rotAngle(1)) -sin(rotAngle(1)); 0 sin(rotAngle(1)) cos(rotAngle(1))];
    R_z = [cos(rotAngle(2)) 0 sin(rotAngle(2)); 0 1 0; -sin(rotAngle(2)) 0 cos(rotAngle(2))];
    R_y = [cos(rotAngle(3)) -sin(rotAngle(3)) 0; sin(rotAngle(3)) cos(rotAngle(3)) 0; 0 0 1];
    rotationMatrix1 = R_x * R_y * R_z;
    sum(sum(abs(Rc-rotationMatrix1)))

    rotationMatrix2 = R_x * R_z * R_y;
    sum(sum(abs(Rc-rotationMatrix2)))

    rotationMatrix3 = R_y * R_x * R_z;
    sum(sum(abs(Rc-rotationMatrix3)))

    rotationMatrix4 = R_y * R_z * R_x;
    sum(sum(abs(Rc-rotationMatrix4)))

    rotationMatrix5 = R_z * R_y * R_x;
    sum(sum(abs(Rc-rotationMatrix5)))

    rotationMatrix6 = R_z * R_x * R_y;
    sum(sum(abs(Rc-rotationMatrix6)))
%}
   
    f = M2(1,1);

end

