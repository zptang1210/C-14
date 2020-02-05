function [ f ] = plotCameraRotations( rotation_ABC_gt, rotation_ABC, translation_UVW_gt, translation_UVW, video_name, i )

    f = figure('visible', 'off');
    
    subplot(2,1,1)
    
    A = plot(rotation_ABC_gt(:,1), 'g', 'LineWidth', 3); 
    hold on

    plot(rotation_ABC(:,1), 'g', 'LineWidth', 1);
    hold on

    B = plot(rotation_ABC_gt(:,2), 'r', 'LineWidth', 3);
    hold on

    plot(rotation_ABC(:,2), 'r', 'LineWidth', 1)
    hold on

    C = plot(rotation_ABC_gt(:,3), 'b', 'LineWidth', 3);
    hold on

    plot(rotation_ABC(:,3), 'b', 'LineWidth', 1)
    %hold on
    
    %plot(magnitude, 'c', 'LineWidth', 1)

    legend('A - groundtruth', 'A - estimated', 'B - groundtruth', 'B - estimated', ...
        'C - groundtruth', 'C - estimated');

    legend boxoff

    %   add title and axis labels
    title('camera rotation')
    xlabel('frame')
    ylabel('rotation in rad')
    %ylabel('translation (unit vector)')

    A.Color(4) = 0.2;
    B.Color(4) = 0.2;
    C.Color(4) = 0.2;
    
    subplot(2,1,2)
    
    A = plot(translation_UVW_gt(:,1), 'g', 'LineWidth', 3); 
    hold on

    plot(translation_UVW(:,1), 'g', 'LineWidth', 1);
    hold on

    B = plot(translation_UVW_gt(:,2), 'r', 'LineWidth', 3);
    hold on

    plot(translation_UVW(:,2), 'r', 'LineWidth', 1)
    hold on

    C = plot(translation_UVW_gt(:,3), 'b', 'LineWidth', 3);
    hold on

    plot(translation_UVW(:,3), 'b', 'LineWidth', 1)

    legend('U - groundtruth', 'U - estimated', 'V - groundtruth', 'V - estimated', ...
        'W - groundtruth', 'W - estimated');

    legend boxoff

    %   add title and axis labels
    title('camera translation')
    xlabel('frame')
    ylabel('translation (unit vector)')

    A.Color(4) = 0.2;
    B.Color(4) = 0.2;
    C.Color(4) = 0.2;

end

