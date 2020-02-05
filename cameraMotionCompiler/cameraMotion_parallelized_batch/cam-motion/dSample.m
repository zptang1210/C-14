function [idx_down ] = dSample(region, n, h, w)

	idx = 1:h*w;
	idx = reshape(idx, h, w);

	start = floor(n/2);
	idx_down = idx(start:n:end, start:n:end);

	idx_down = ismember(idx_down, region).*idx_down;
	idx_down(idx_down==0)=[];
	idx_down = reshape(idx_down, numel(idx_down), 1);

end

