

t = 1;
figure;hold all;

plot_i = 1:2:14;
for i=1:7
    subplot(7,2,plot_i(i));
    plot(data.time{t}, data.trial{t}(i,:));
    title(data.label{i});
end

plot_i = 14:-2:2;
for i=14:-1:8
    subplot(7,2,plot_i(i-7));
    plot(data.time{t}, data.trial{t}(i,:));
    title(data.label{i});
end
