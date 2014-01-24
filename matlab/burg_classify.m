function [ results, header ] = burg_classify(block_size, range)
    % Bring workspace variables
    data = evalin('base', 'data');
    n_trials = double(evalin('base', 'n_trials'));
    cues = evalin('base', 'cues');
    freq_left = evalin('base', 'freq_left');
    freq_right = evalin('base', 'freq_right');
        
    if nargin < 2
        % Range is not given
        range = 1:length(data.trial{1}(1,:));
    end
    
    do_plots = false;
    
    if block_size == 0
        block_size = length(data.trial{1}(1,:));
    end
    
    % Channel combination labels
    labels = {'o1', 'o2', 'o1-o2', 'o1-p7', 'o1-p8', 'o2-p7', 'o2-p8', 'o1-avg', 'o2-avg'};

    % +1 for overall results
    results = zeros(n_trials + 1, length(labels));
    
    % final averages
    final_pxx = zeros(n_trials, 64, length(labels));
    
    % 5Hz Highpass filter
    Wn = 5 / 64;
    [b, a] = butter(9, Wn, 'high');
    
    % N_FFT for FFT based averaging
    n_fft = 128;

    % Convert frequencies to numbers
    left_freq = str2double(freq_left);
    right_freq = str2double(freq_right);

    % Data points to be summed up for scoring (f, 2*f-1, 2*f, 2*f+1)
    if left_freq < 20
        left_scores = [left_freq left_freq*2-1 left_freq*2 left_freq*2+1];
    else
        left_scores = [left_freq-1 left_freq left_freq+1];
    end
    if right_freq < 20
        right_scores = [right_freq right_freq*2-1 right_freq*2 right_freq*2+1];
    else
        right_scores = [right_freq-1 right_freq right_freq+1];
    end

    for t=1:n_trials
        % Fetch channels and high-pass filter them
        o1 = filtfilt(b, a, data.trial{t}(find(strcmp(data.label, 'O1')),range));
        o2 = filtfilt(b, a, data.trial{t}(find(strcmp(data.label, 'O2')),range));
        p7 = filtfilt(b, a, data.trial{t}(find(strcmp(data.label, 'P7')),range));
        p8 = filtfilt(b, a, data.trial{t}(find(strcmp(data.label, 'P8')),range));
        
        % Resting data
        r_o1 = filtfilt(b, a, data.rest{t}(find(strcmp(data.label, 'O1')),:));
        r_o2 = filtfilt(b, a, data.rest{t}(find(strcmp(data.label, 'O2')),:));
        r_p7 = filtfilt(b, a, data.rest{t}(find(strcmp(data.label, 'P7')),:));
        r_p8 = filtfilt(b, a, data.rest{t}(find(strcmp(data.label, 'P8')),:));
        
        % Detrend channels
        %o1 = detrend(o1); r_o1 = detrend(r_o1);
        %o2 = detrend(o2); r_o2 = detrend(r_o2);
        %p7 = detrend(p7); r_p7 = detrend(r_p7);
        %p8 = detrend(p8); r_p8 = detrend(r_p8);

        % Common average of 4 channels
        com_avg = (o1 + o2 + p7 + p8) / 4;
        r_com_avg = (r_o1 + r_o2 + r_p7 + r_p8) / 4;

        % Channel combinations
        chans = [o1' o2' (o1-o2)' (o1-p7)' (o1-p8)' (o2-p7)' (o2-p8)' (o1-com_avg)' (o2-com_avg)'];
        r_chans = [r_o1' r_o2' (r_o1-r_o2)' (r_o1-r_p7)' (r_o1-r_p8)' (r_o2-r_p7)' (r_o2-r_p8)' (r_o1-r_com_avg)' (r_o2-r_com_avg)'];
        
        % Trial cue as lowercase
        cue = strtrim(lower(cues(t,:)));
        freq_cue = eval(['freq_' cue]);

        for j=1:length(chans(1,:))
            %avg_raw = zeros(1,block_size);
            avg_burg = zeros(1, 64);
            r_avg_burg = zeros(1, 64);
            avg_fft = zeros(1, n_fft);
            d = detrend(chans(:,j)');
            r_d = r_chans(:,j)';
            lefts = 0;
            rights = 0;
            fprintf(1, '\n\nChannel is: %s, variance: %.2f\n', labels{j}, var(d));
            
            iterations = floor(length(d)/block_size);

            for i=1:iterations
                % Time window averaging
                %avg = avg + d((i-1)*block_size + 1:i*block_size);
                
                % Burg spectral averaging
                block = d((i-1)*block_size + 1:i*block_size);
                %r_block = r_d((i-1)*block_size + 1:i*block_size);
                [n_Pxx, f] = pburg(block, 64, 1:1:64, 128);
                avg_burg = avg_burg + n_Pxx;
                
                % FFT spectral averaging
                F = abs(real(fft(block, n_fft)));
                avg_fft = avg_fft + F;

                Pxx = (avg_burg / i);
                %Pxx = avg_fft / i; % FFT
                if do_plots
                    plot(f, Pxx);grid on; ylim([-40, 40]);
                    set(gca, 'XTick', 1:2:64);
                    title(['Trial ' int2str(t) ' Electrode:' labels{j} ' Cue: ' cue ' ' freq_cue 'Hz (Averaging window: ' int2str(block_size) ')']);              
                    pause(1);
                end

                % Calculate scores
                %Pxx = 10*log10(Pxx);
                fl_mean = sum(Pxx(left_scores)) / length(left_scores);
                fr_mean = sum(Pxx(right_scores)) / length(right_scores);
                if fl_mean > fr_mean
                    lefts = lefts + 1;
                else
                    rights = rights + 1;
                end
                fprintf(1, 'Trial %d (Cue: %s (%sHz)): [%d/%d] Left-> %.2f (%d) Right-> %.2f (%d)\n', t, cue, freq_cue, i, iterations, fl_mean, lefts, fr_mean, rights);
            end
            
            % Record averaged PSD for further usage
            final_pxx(t, :, j) = Pxx;
            
            fprintf(1, 'Left %d, Right %d for cue %s\n', lefts, rights, cue);
            
            if (lefts > rights && strcmp(cue, 'left')) || (rights > lefts && strcmp(cue, 'right'))
                % Correctly classified
                results(t, j) = 1;
            end

        end
    end

    % Calculate total scores for each channel comb
    for j=1:length(chans(1,:))
        results(n_trials + 1, j) = sum(results(1:n_trials, j)) / double(n_trials);
    end

    % Sort classfication rates
    [~, i] = sort(results(end, :), 'descend');
    results = results(:, i);
    header = labels(i);

    for j=1:length(chans(1,:))
        % Print if classification rate > %50
        if results(end, j) > 0.50
            fprintf(1, 'Chan: %s, Classification Rate: %.2f\n', header{j}, results(end, j));
        end
    end

    h = figure;
    
    % Find the channel which maximizes classification rate
    max_chan_label = strtrim(header{1});
    max_chan_rate = results(end, 1);
    max_chan_idx = find(strcmp(labels, max_chan_label));
    max_chan_data = chans(:, max_chan_idx)';
    
    left_bound = min(left_freq, right_freq) - 2;
    right_bound = (max(left_freq, right_freq)*2) + 2;
    
    for i=1:n_trials
        cue = strtrim(lower(cues(i,:)));
        freq_cue = eval(['freq_' cue]);
        
        is_correct = results(i, 1);
        if is_correct
            color = 'b';
        else
            color = 'r';
        end
        
        % Plot maximum performance channel for each trial
        subplot(6, 2, 2*i - 1);
        plot(data.time{i}(range), max_chan_data);
        ylabel('$Amplitude$', 'Interpreter', 'latex');
        title(['(Trial ' num2str(i) ') EEG Signal'], 'Interpreter', 'latex');

        subplot(6, 2, 2*i);
        plot(left_bound:right_bound, final_pxx(i, left_bound:right_bound, max_chan_idx), color);
        %hold on;
        %plot(left_scores, final_pxx(i, left_scores, max_chan_idx), 'o', 'color', 'g');
        %plot(right_scores, final_pxx(i, right_scores, max_chan_idx), '^');
        set(gca, 'XTick', left_bound:2:right_bound);
        grid on;
        ylabel('$Power/Hz$', 'Interpreter', 'latex');
        
        title(['Averaged PSD (Attended $f=' freq_cue 'Hz$)'], 'Interpreter' ,'latex');
    end
    xlabel('Frequency ($Hz$)', 'Interpreter', 'latex');
    subplot(6, 2, 2*n_trials - 1);
    xlabel('Time (s)', 'Interpreter', 'latex');
    
        
    % Save as pdf
    % the last two parameters of 'Position' define the figure size
    
    width = 16.54;
    height = 11.69;
    set(h, 'PaperUnits', 'inches');
    set(h, 'PaperSize', [width height]);
    set(h, 'PaperPositionMode', 'manual');
    set(h, 'PaperPosition', [0 0 width height]);
    
    s_title = ['\parbox[b]{4.2in}{\centering ', num2str(length(range)/block_size), ' seconds (Channel ', upper(max_chan_label), ') - Averaging Window: ', num2str(block_size/128), ' seconds ', ...
               'Classification Rate: \%', num2str(100*max_chan_rate, '%.2f'), '}'];
    suptitle(s_title);

    saveas(h, 'results.pdf');
end

