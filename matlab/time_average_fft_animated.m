% Channel combination labels
labels = {'o1', 'o2', 'o1-o2', 'o1-p7', 'o1-p8', 'o2-p7', 'o2-p8', 'o1-avg', 'o2-avg'};

% +1 for overall results
results = zeros(n_trials + 1, length(labels));

for t=1:n_trials
    % Fetch channels
    o1 = detrend(data.trial{t}(find(strcmp(data.label, 'O1')),:));
    o2 = detrend(data.trial{t}(find(strcmp(data.label, 'O2')),:));
    p7 = detrend(data.trial{t}(find(strcmp(data.label, 'P7')),:));
    p8 = detrend(data.trial{t}(find(strcmp(data.label, 'P8')),:));

    % Common average
    com_avg = (o1 + o2 + p7 + p8) / 4;
    
    % Channel combinations
    chans = [o1' o2' (o1-o2)' (o1-p7)' (o1-p8)' (o2-p7)' (o2-p8)' (o1-com_avg)' (o2-com_avg)'];
    
    % Trial cue as lowercase
    cue = strtrim(lower(cues(t,:)));

    % Convert frequencies to numbers
    left_freq = str2double(freq_left);
    right_freq = str2double(freq_right);

    % Data points to be summed up for scoring (f, 2*f-1, 2*f, 2*f+1)
    left_scores = [left_freq left_freq*2-1 left_freq*2 left_freq*2+1];
    right_scores = [right_freq right_freq*2-1 right_freq*2 right_freq*2+1];

    for j=1:length(chans(1,:))
        avg = zeros(1,bs);
        d = chans(:,j)';
        lefts = 0;
        rights = 0;
        fprintf(1, '\n\nChannel is: %s\n', labels{j});

        for i=1:length(d)/bs
            avg = avg + d((i-1)*bs + 1:i*bs);
            %f = abs(real(fft(avg / i))); % Pure FFT
            
            % Burg with order=32
            [Pxx, f] = pburg(avg, 32, 1:1:64, 128);
            Pxx = 10*log10(Pxx);
            %plot(f, Pxx);
            
            % Calculate scores
            fl_mean = sum(Pxx(left_scores)) / length(left_scores);
            fr_mean = sum(Pxx(right_scores)) / length(right_scores);
            if fl_mean > fr_mean
                lefts = lefts + 1;
            else
                rights = rights + 1;
            end
            fprintf(1, 'Trial %d (Cue: %s (%sHz)): Left->%.2f Right->%.2f\n', t, cue, eval(['freq_' cue]), fl_mean, fr_mean);
        end
        
        fprintf(1, 'Left %d, Right %d for cue %s\n', lefts, rights, cue);
        if (lefts > rights && strcmp(cue, 'left')) || (rights > lefts && strcmp(cue, 'right'))
            % Correctly classified
            results(t, j) = 1;
        end

        %display('Press a button to continue.');
        %waitforbuttonpress;
    end
end

for j=1:length(chans(1,:))
    results(n_trials + 1, j) = sum(results(1:n_trials, j)) / double(n_trials);
    fprintf(1, 'Chan: %s, Classification Rate: %.2f\n', labels{j}, results(end, j));
end