function oai_data_all = get_oai_tcp_data(main_folder,oai_data_subfolder)

% All configurations
exp_config_folders = dir(fullfile(main_folder,oai_data_subfolder));

% Remove non_data folders 
name_tmp = convertCharsToStrings({exp_config_folders(:).name});
exp_config_folders(ismember(name_tmp,{'.','..','.DS_Store'})) = [];

oai_data_all = struct('conf_name',[],'data',[]);

for f = 1 : numel(exp_config_folders)
    conf_name = fullfile(exp_config_folders(f).folder,exp_config_folders(f).name);

    ue_data_in_folder = dir(conf_name);
    ue_data_in_folder = ue_data_in_folder(3:end);

    oai_data = [];

    for ud = 1 : numel(ue_data_in_folder)
        data_tmp = import_oai_tcp_file(fullfile(ue_data_in_folder(ud).folder,ue_data_in_folder(ud).name));
        % data_tmp = rmmissing(data_tmp);
        oai_data = [oai_data; data_tmp];
    end

    oai_data_all(f).conf_name = exp_config_folders(f).name;
    oai_data_all(f).data = oai_data;

end

end