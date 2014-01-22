function [ output_args ] = burg_plots(filename, trial, pburg_order)

% Load the data
load(filename);

% Channel labels
chan_labels = {'O1', 'O2', 'O1-O2', 'AVG'};

fs = 128;

if nargin < 3
    % Default order is 8
    pburg_order = 8;
    if nargin < 2
        trial = 1;
    end
end

stitle = filename;
if ~exist('raw', 'var')
    % FieldTrip style dataset recording.
    display('Found dataset format.');
    raw = data.trial{trial};
    [~, stitle, ~] = fileparts(fileparts(filename));
    stitle = [stitle ' ' cues(trial,:) eval(['freq_' lower(cues(trial,:))]) 'Hz'];
end
stitle = strrep(stitle, '_', '-');

peaks = false;

% Pre-process channels
o1 = detrend(raw(find(strcmp(data.label, 'O1')),:));
o2 = detrend(raw(find(strcmp(data.label, 'O2')),:));
dif = o1 - o2;
avg = (o1 + o2) / 2;

% Channel data
chan_data = [o1' o2' dif' avg'];
n_rows = 5;
n_cols = 4;

h = figure;

% Plot raw data
for j = 1:n_cols
    subplot(n_rows, n_cols, j);
    plot(chan_data(:, j));
    grid on;
    title(['Raw ' chan_labels{j}]);
end

% Plot full pburg
for j = 1:n_cols
    subplot(n_rows, n_cols, j + n_cols);
    [Pxx, F] = pburg(chan_data(:, j), pburg_order, 1:1:64, fs);
    Pxx = 10*log10(Pxx);
    plot(F, Pxx); hold on;

    % Mark the mean of spectrum
    m_Pxx = mean(Pxx(7:48));
    line('XData', [0 80], 'YData', [m_Pxx m_Pxx], 'Color', 'm');

    if peaks
        [pks, locs] = findpeaks(Pxx, 'minpeakdistance', 3);

        for l=1:length(locs)
            text(locs(l), Pxx(locs(l)), ['\rightarrow' int2str(locs(l))], 'FontSize', 12, 'Rotation', 75);
        end

        plot(locs, Pxx(locs), 'k^', 'markerfacecolor', [1 0 0]); hold off;
    end
    grid on;
    title(['Burg PSD ' chan_labels{j}]);
end

% Plot spectral average of 1 second (128) blocks
for j = 1:n_cols
    subplot(n_rows, n_cols, j + 2*n_cols);
    
    fs
    j
    [Pxx, F] = pburg(chan_data(1:fs, j), pburg_order, 1:1:64, fs);
    
    n_blocks = (length(chan_data(:, j)) / fs);
    
    for b = 1:n_blocks - 1
        block = chan_data((b*fs) + 1:b*fs + fs, j);
        [n_Pxx, ~] = pburg(block, pburg_order, 1:1:64, fs);
        Pxx = Pxx + n_Pxx;
    end
    Pxx = 10*log10(Pxx);
    plot(F, Pxx); hold on;
    
    % Mark the mean of spectrum
    m_Pxx = mean(Pxx(7:48));
    line('XData', [0 80], 'YData', [m_Pxx m_Pxx], 'Color', 'm');

    if peaks
        [pks, locs] = findpeaks(Pxx, 'minpeakdistance', 3);
    
        for l=1:length(locs)
            text(locs(l), Pxx(locs(l)), ['\rightarrow' int2str(locs(l))], 'FontSize', 12, 'Rotation', 75);
        end

        plot(locs, Pxx(locs), 'k^', 'markerfacecolor', [1 0 0]); hold off;
    end
    grid on;
    title(['Avg. Burg ' chan_labels{j}]);
end

% Plot spectral average of 1 second (128) detrended blocks
for j = 1:n_cols
    subplot(n_rows, n_cols, j + 3*n_cols);
    
    [Pxx, F] = pburg(chan_data(1:fs, j), pburg_order, 1:1:64, fs);
    
    n_blocks = (length(chan_data(:, j)) / fs);
    
    for b = 1:n_blocks - 1
        block = detrend(chan_data((b*fs) + 1:b*fs + fs, j));
        [n_Pxx, ~] = pburg(block, pburg_order, 1:1:64, fs);
        Pxx = Pxx + n_Pxx;
    end
    Pxx = 10*log10(Pxx);
    plot(F, Pxx); hold on;
    
    % Mark the mean of spectrum
    m_Pxx = mean(Pxx(7:48));
    line('XData', [0 80], 'YData', [m_Pxx m_Pxx], 'Color', 'm');
    hold on; grid on;

    if peaks
        [pks, locs] = findpeaks(Pxx, 'minpeakdistance', 3);
    
        for l=1:length(locs)
            text(locs(l), Pxx(locs(l)), ['\rightarrow' int2str(locs(l))], 'FontSize', 12, 'Rotation', 75);
        end

        plot(locs, Pxx(locs), 'k^', 'markerfacecolor', [1 0 0]); hold off;
    end
    title(['Avg. Burg (detrended) ' chan_labels{j}]);
end

% Plot pburg for time locked averaged signal
for j = 1:n_cols
    subplot(n_rows, n_cols, j + 4*n_cols);
    
    block_size = 2*fs;
    
    block = chan_data(1:block_size, j);
    n_blocks = (length(chan_data(:, j)) / block_size);
    
    for b = 1:n_blocks - 1
        block = block + chan_data((b*block_size) + 1:b*block_size + block_size, j);
    end
    
    [Pxx, F] = pburg(block/n_blocks, pburg_order, 1:1:64, fs);
    Pxx = 10*log10(Pxx);
    plot(F, Pxx); hold on;
    
    % Mark the mean of spectrum
    m_Pxx = mean(Pxx(7:48));
    line('XData', [0 80], 'YData', [m_Pxx m_Pxx], 'Color', 'm');

    if peaks
        [pks, locs] = findpeaks(Pxx, 'minpeakdistance', 3);
    
        for l=1:length(locs)
            text(locs(l), Pxx(locs(l)), ['\rightarrow' int2str(locs(l))], 'FontSize', 12, 'Rotation', 75);
        end

        plot(locs, Pxx(locs), 'k^', 'markerfacecolor', [1 0 0]); hold off;
    end
    grid on;
    title(['Time-locked avg Burg ' chan_labels{j}]);
end

suptitle(stitle);

% Save as pdf
% the last two parameters of 'Position' define the figure size
width = 16.54;
height = 11.69;
set(h, 'PaperUnits', 'inches');
set(h, 'PaperSize', [width height]);
set(h, 'PaperPositionMode', 'manual');
set(h, 'PaperPosition', [0 0 width height]);

%saveas(h, ['pdfs/' strrep(filename, '.mat', '.pdf')]);
