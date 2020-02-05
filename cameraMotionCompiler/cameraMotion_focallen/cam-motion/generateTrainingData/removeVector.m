function [vectorListNew] = removeVector(vectorList, vector, angleThresh)

    % vectorList and vector are unit vectors!
    
    scalarProduct = vector(1).*vectorList(1,:) + vector(2).*vectorList(2,:) + vector(3).*vectorList(3,:); 
    deltaTheta_degree = acosd(scalarProduct);
    
    vectorListNew = vectorList(:,deltaTheta_degree>angleThresh);

end

