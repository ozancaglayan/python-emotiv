t = 4;
avg = zeros(1,bs);
o1 = detrend(data.trial{t}(1,:)); o2 = detrend(data.trial{t}(2,:)); d = o1 - o2;
for i=1:length(d)/bs
avg = avg + d((i-1)*bs + 1:i*bs);
f = abs(real(fft(avg / i)));
plot(f(1:64));
ylim([0 250]);
fl_mean = mean(f(str2num(freq_left)-1:str2num(freq_left)+1));
fr_mean = mean(f(str2num(freq_right)-1:str2num(freq_right)+1));
fprintf(1, 'Trial %d (Cue: %s): Left->%.2f Right->%.2f\n', t, cues(t,:), fl_mean, fr_mean);
pause(2);
end
