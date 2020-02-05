function [ f ] = plotEPE( error_endPoint_video, error_endPoint_trans, video_name, i )

    f =figure('visible', 'off');

    plot(error_endPoint_video, 'g', 'LineWidth', 1);
    hold on

    plot(error_endPoint_trans, 'b', 'LineWidth', 1)

    legend('rotation-EPE', 'translation-EPE');

    legend boxoff

    %   add title and axis labels
    title(video_name)
    xlabel('frame')
    ylabel('End-Point-Error')

end
