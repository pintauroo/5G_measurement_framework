close all
clear all
clc

% Paths to data
main_folder = '../tcp_wireless_kpi';
oai_data_subfolder = '.';

oai_var_names = ["tmbuf", "RNTI", "UENum", "ul_thr_ue", "dl_thr_ue", "ph", "pcmax",...
    "avg_rsrp", "num_rsrp_meas", "cqi", "pucch_snrx10", "pusch_snrx10", "raw_rssi",...
    "ri1", "pmi_x1", "pmi_x2", "dlerrors", "pucch0_DTX", "dl_bler_statsbler", ...
    "dl_bler_statsmcs", "dltotal_bytes", "ulsch_DTX", "ulerrors", "ul_bler_statsbler",...
    "ul_bler_statsmcs", "ulsch_total_bytes_scheduled", "ultotal_bytes", "dlrounds", ...
    "ulrounds", "cwnd_values", "inflight", "rtt", "sending_rate", "throughput", ...
    "retransmissions_interval"];

% var_of_interest = { 'avg_rsrp', 'dl_bler_statsbler', 'dl_bler_statsmcs',...
%     'cwnd_values', 'rtt', 'throughput'};

var_of_interest = { 'avg_rsrp', 'ul_bler_statsbler', 'ul_bler_statsmcs',...
    'cwnd_values', 'rtt', 'throughput'};

oai_data_all = get_oai_tcp_data(main_folder,oai_data_subfolder);

%%

conf_map = struct('two_streams',[1,2],...
                  'DL_106',[3,7],...
                  'UL_106',[5,9],...
                  'DL_24',[4,8,11,14],...
                  'UL_24',[6,10,12,13,15]);

conf_names = convertCharsToStrings({oai_data_all(:).conf_name});
conf_names_of_interest_tag = 'UL_24';
conf_names_of_interest_idx = conf_map.(conf_names_of_interest_tag);
conf_names_of_interest = conf_names(conf_names_of_interest_idx);

data = [];
group_label = [];

for c = 1 : numel(conf_names_of_interest)
    data_tmp = oai_data_all(conf_names_of_interest_idx(c));
    conf_name_array = repmat(string(data_tmp.conf_name), size(data_tmp.data,1), 1); 
    data_tmp = data_tmp.data(:,ismember(data_tmp.data.Properties.VariableNames, var_of_interest));
    group_label = [group_label; conf_name_array];
    data = [data; data_tmp];
    

    for v = 1 : numel(var_of_interest)
        figure(v)
        x = data_tmp(:,ismember(data_tmp.Properties.VariableNames, var_of_interest{v}));
        x = rmmissing(x);
        if numel(x)
            cdfplot(x{:,:})
            hold on
            grid on
            xlabel(var_of_interest{v})
            legend(conf_names_of_interest)
        end
    end
end

xnames = var_of_interest;

figure
gplotmatrix(data{:,:},[],group_label,[],[],8,[],[],xnames)

% these idxs must be selected to identify KPIs from var_of_interest
idx1 = 2;
idx2 = 6;

figure
gscatter(data{:,idx1},data{:,idx2},group_label,[],[],8,[],xnames(idx1),xnames(idx2))
legend(conf_names_of_interest)
grid on

figure
scatterhist(data{:,idx1},data{:,idx2},'Group',group_label,'Kernel','on','Location','SouthEast',...
    'Direction','out',...
    'LineWidth',[2,2,2,2,2],'Marker','+od.s','MarkerSize',[4,4,4,4,4]);