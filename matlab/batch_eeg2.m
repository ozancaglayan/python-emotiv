function [output_args] = batch_eeg2(filename)
load(filename);

[dname, fname, ext] = fileparts(filename);
[dname, dataset_name, ext] = fileparts(dname);

% Setup parameters for preprocessing
cfg = [];
cfg.standardize = 'yes';
cfg.demean = 'yes';
cfg.hpfilter = 'yes';
cfg.hpfreq = 8;
dataPP = ft_preprocessing(cfg, data);

% Setup parameters for frequency analysis
cfg.output = 'pow';
cfg.method = 'mtmfft';
cfg.taper = 'hanning';
cfg.keeptrials = 'yes';
freqs = ft_freqanalysis(cfg, dataPP);

% Channel index's
chan_idx = [find(strcmp(data.label, 'O1')) find(strcmp(data.label, 'O2'))];
nr_chans = length(chan_idx);
n_trials = double(n_trials);

fig = figure(1);
set(fig,'numbertitle', 'off', 'name', dataset_name);
suptitle(dataset_name);

% Start plotting
for i = 1:n_trials
    % Plot raw data
    
    subplot(n_trials*2, nr_chans, ((i - 1) * nr_chans) + 1);
    for c = 1:nr_chans
        plot(dataPP.time{i}, dataPP.trial{i}(c, :));
        title(['Channel ' data.label{c}]);
    end   
    
    % Plot spectrum
    subplot(n_trials*2, nr_chans, ((i - 1) * nr_chans) + 2);
    for c = 1:nr_chans
        plot(freqs.freq, squeeze(freqs.powspctrm(i, c, :)), 'r');
        title(['Spectrum ' data.label{c}]);
    end
end
end