function plotFishPlot(pdap, p, t, turn, titlestring, rays)

color = {[0 0.4470 0.7410], [0.8500 0.3250 0.0980],[0.4660 0.6740 0.1880], [0.9290 0.6940 0.1250], [0.4940 0.1840 0.5560]...
          [0.3010 0.7450 0.9330], [0.6350 0.0780 0.1840]};

if nargin < 6
   rays = zeros(2,2);
   rays(1,1) = -20;
   rays(1,2) = 72.8;
   rays(2,1) = -10;
   rays(2,2) = 153.1;
end
      
%xsim = (0:1E-2:2).*cos(72.8*pi/180).*cos(-20*pi/180);  % simulated arrival angle
%ysim = (0:1E-2:2).*sin(72.8*pi/180).*cos(-20*pi/180);
%zsim = (0:1E-2:2).*sin(-20*pi/180);

%xsim2 = (0:1E-2:2).*cos(153.1*pi/180).*cos(-10*pi/180);  % simulated arrival angle
%ysim2 = (0:1E-2:2).*sin(153.1*pi/180).*cos(-10*pi/180);
%zsim2 = (0:1E-2:2).*sin(-10*pi/180);      


xsim = (0:1E-2:2).*cos(rays(1,2)*pi/180).*cos(rays(1,1)*pi/180);  % simulated arrival angle
ysim = (0:1E-2:2).*sin(rays(1,2)*pi/180).*cos(rays(1,1)*pi/180);
zsim = (0:1E-2:2).*sin(rays(1,1)*pi/180);

xsim2 = (0:1E-2:2).*cos(rays(2,2)*pi/180).*cos(rays(2,1)*pi/180);  % simulated arrival angle
ysim2 = (0:1E-2:2).*sin(rays(2,2)*pi/180).*cos(rays(2,1)*pi/180);
zsim2 = (0:1E-2:2).*sin(rays(2,1)*pi/180);      
      


dataR = squeeze(sum(pdap,3));
dataR = dataR/max(max(abs(dataR)));
x = dataR.*cos(p+turn).*cos(t);
y = dataR.*sin(p+turn).*cos(t);
z = dataR.*sin(t);

figure
rad = sqrt(x.^2 + y.^2 + z.^2);
hSurf = surf(x, y, z, rad);

colormap(jet)
xlim([-1.2 1.2]);
ylim([-1.2 1.2]);
zlim([-1.2 1.2]);
%axis equal
view(110,40)
hold on
%     plot3(xx,yy,zz,'o','Color','r','MarkerFaceColor','r','LineWidth',0.75)
plot3(xsim,ysim,zsim,'o','Color',color{1},'MarkerFaceColor',color{1},'LineWidth',0.25)
plot3(xsim2,ysim2,zsim2,'o','Color',color{2},'MarkerFaceColor',color{2}','LineWidth',0.25)
plot3(-2:1E-2:2,0:0,0:0,'o','Color','k','MarkerFaceColor','k','LineWidth',0.25)
plot3(0:0,-2:1E-2:2,0:0,'o','Color','k','MarkerFaceColor','k','LineWidth',0.25)
plot3(0:0,0:0,-2:1E-2:2,'o','Color',color{3},'MarkerFaceColor',color{3},'LineWidth',0.25)
colorbar
%caxis([0 15E-4])
xlabel('X','FontSize',18);
ylabel('Y','FontSize',18);
title(titlestring,'FontSize',18);
hold off

end

