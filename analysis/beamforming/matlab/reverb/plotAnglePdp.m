function plotAnglePdp(times, hThetaTauS)

color = {[0 0.4470 0.7410], [0.8500 0.3250 0.0980],[0.4660 0.6740 0.1880], [0.9290 0.6940 0.1250], [0.4940 0.1840 0.5560]...
          [0.3010 0.7450 0.9330], [0.6350 0.0780 0.1840]};
      
plotData = abs(hThetaTauS).^2;      
%plotMaxY = 1.1*max(max(plotData));
      
figure
plot(times,plotData(1,:),'LineWidth',2)
hold on
plot(times,plotData(2,:),'LineWidth',2)
hold on
% Because matlab is cool
lims = ylim;
plotMaxY = lims(2);

plot([3.53,3.53],[0,plotMaxY],'Color',color{1},'LineWidth',1)
hold on
plot([5.82,5.82],[0,plotMaxY],'Color',color{2},'LineWidth',1)
hold on
ylim(lims);
xlabel('Delay, \tau (ns)','FontSize',16);
ylabel('Relative Power','FontSize',16);
%titlestring = {'PDAP, Z-Dipole, 400 MHz BW, \Deltaf = 20 MHz, Sim09'}; % Loaded Wall  No Loading

legend('LOS', 'NLOS')

end

