function plotAzPap(times, azPdap, az, preTitle)

figure
contourf(times, az, azPdap,'LineStyle','none')
hold on

colormap(jet)
colorbar

xlabel('Delay, \tau (ns)','FontSize',16);
ylabel('Azimuth Angle, \phi','FontSize',16);
titlestring = {strcat(preTitle, 'Azimuthal Power-Angle-Profile')}; % Loaded Wall  No Loading
title(titlestring,'FontSize',18);
hold off


end

