function [output_args] = batch_eeg(filename)

if nargin < 1
    filename = [pwd '/dataset.mat'];
    display(filename);
end

load(filename);

[dname, fname, ext] = fileparts(filename);
[dname, dataset_name, ext] = fileparts(dname);

% Channel index's
chan_idx = [find(strcmp(data.label, 'O1')) find(strcmp(data.label, 'O2'))];
nr_chans = length(chan_idx);
nr_cols = (nr_chans + 2);
n_trials = double(n_trials);

% Setup parameters for preprocessing
cfg = [];
%cfg.standardize = 'yes';
%cfg.detrend = 'yes';
%cfg.hpfilter = 'yes';
cfg.reref='yes';
cfg.refchannel='O1';
cfg.bpfreq = [10 45];
cfg.bpfilter='yes';

dataPP = ft_preprocessing(cfg, data);

% Setup parameters for frequency analysis
cfg.output = 'pow';
cfg.method = 'mtmfft';
cfg.taper = 'hanning';
cfg.keeptrials = 'yes';

freqs = ft_freqanalysis(cfg, dataPP);

fig = figure(1);
set(fig,'numbertitle', 'off', 'name', dataset_name);
suptitle(strrep(dataset_name, '_', ' '));

% Start plotting
for i = 1:n_trials
    % Plot raw data
    subplot_order = (nr_cols * (i - 1)) + 1;
    
    for c = 1:nr_chans
        subplot(n_trials, nr_cols, subplot_order);
        plot(dataPP.time{i}, dataPP.trial{i}(c, :));
        title(['Channel ' data.label{c} ' (' cues(i, :) ')'], 'Interpreter', 'none');
        subplot_order = subplot_order + 1;
    end   
    
    % Plot spectrum
    for c = 1:nr_chans
        subplot(n_trials, nr_cols, subplot_order);
        plot(freqs.freq, squeeze(freqs.powspctrm(i, c, :)), 'r');
        title(['Spectrum ' data.label{c}]);
        subplot_order = subplot_order + 1;
    end
end
end