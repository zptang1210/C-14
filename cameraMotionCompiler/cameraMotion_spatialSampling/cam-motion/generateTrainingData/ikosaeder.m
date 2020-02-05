function [ vertices ] = ikosaeder( frequency )
%IKOSAEDER Summary of this function goes here
%   Detailed explanation goes here


numVertices = 2*(1+5*((frequency-1)*((frequency-1)+1))/(2)) + frequency*5*(frequency+1);
numPlanes = 3*frequency + 1;
vertices = ones(3, numVertices);
angles = ones(2, numVertices);

theta_delta = 180/(frequency*3);
theta = 0;
begin = 1;
last_numVertices_sameTheta = 0; 
i = 0; % num of current layer, where all vertices have the same theta
t = 0;

while (i < frequency)
            
        numVertices_sameTheta = 5*i;
        
        angles(1, begin:(numVertices_sameTheta+last_numVertices_sameTheta+1)) = theta;
        angles(1, (numVertices-(numVertices_sameTheta+last_numVertices_sameTheta+1)+1):(numVertices-begin+1)) = 180 - theta;
        
        if i>0
            angles(2, begin:(numVertices_sameTheta+last_numVertices_sameTheta+1)) = 0 : 360/(i*5):359.9;
            angles(2, (numVertices-(numVertices_sameTheta+last_numVertices_sameTheta+1)+1):(numVertices-begin+1)) = -36 : 360/(i*5): 323.9;
        end
        
        begin = (numVertices_sameTheta+last_numVertices_sameTheta+1) + 1 ;
        
        last_numVertices_sameTheta = i*5 + last_numVertices_sameTheta;
    
        theta = theta_delta + theta;
        i = i+1;
    
end
while (i < numPlanes-frequency)
        
        angles(1, begin:begin+frequency*5-1) = theta;
        
        if(t==0)
            angles(2, begin:begin+frequency*5-1) = 0 : 360/(frequency*5):359;
            t = 1;
        else
            angles(2, begin:begin+frequency*5-1) = -36 : 360/(frequency*5): 323;
            t = 0;
        end
        
        begin = (begin+frequency*5) ;

        theta = theta_delta + theta;
        i = i+1;
    
end

vertices(1,:) = sind(angles(1,:)).*cosd(angles(2,:));
vertices(2,:) = sind(angles(1,:)).*sind(angles(2,:));
vertices(3,:) = cosd(angles(1,:));


% figure
% x = vertices(1,:);
% y = vertices(2,:);
% z = vertices(3,:);
% scatter3(x,y,z,'*')
% view(30,40)

end

