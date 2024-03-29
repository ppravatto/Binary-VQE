import numpy as np
import os, plotter, glob, readline

def complete(text, state):
    return (glob.glob(text+'*')+[None])[state]

readline.set_completer_delims(' \t\n;')
readline.parse_and_bind('tab: complete')
readline.set_completer(complete)

def get_converged_value(filename, average=10):
    real, imag = [], []
    datafile = open(filename, 'r')
    for line in datafile:
        data = line.split()
        real.append(float(data[0]))
        imag.append(float(data[1]))
    datafile.close()
    real_avg, imag_avg = 0, 0
    for i in range(average):
        real_avg += real[-1-i]
        imag_avg += imag[-1-i]
    return real_avg/average, imag_avg/average

def load_iteration_folder(path, average=10):
    if os.path.isdir(path)==False:
        print("ERROR: {} is not a valid path".format(path))
        exit()
    data = [[],[]]
    for filename in os.listdir(path):
        if filename.endswith(".txt"):
            file_path = path + "/" +filename
            print("Loading from path: {}".format(file_path))
            try:
                real, imag = get_converged_value(file_path, average)
            except:
                print(" -> ERROR: Unable to load file")
            else:
                data[0].append(real)
                data[1].append(imag)
        else:
            print("Skipping: {}".format(filename))
    return data

def load_parsed_files(path, root_name=""):
    data_avg = []
    comparison_data = [[],[],[]]
    for filename in os.listdir(path):
        data_list, avg = [], 0
        if filename.endswith(".txt") and filename.startswith(root_name):
            print(" -> Loading: {}".format(filename))
            filename = path + "/" + filename
            data_file = open(filename)
            for line in data_file:
                data = line.split()
                if "#" in line:
                    if data[0] == "#ORDER":
                        comparison_data[0].append(float(data[1]))
                    elif data[0] == "#TARGET":
                        comparison_data[1].append(float(data[1]))
                    else:
                        pass
                else:
                    data_list.append(float(data[0]))
            data_file.close()
            for element in data_list:
                avg += element/len(data_list)
            data_avg.append(avg)
            comparison_data[2].append(data_list)
        else:
            print(" -> Skipping: {}".format(filename))
    return comparison_data, data_avg


os.system('cls' if os.name == 'nt' else 'clear')

print('''-------------------------------------------------------------
                 BINARY VQE - POST PROCESSING
-------------------------------------------------------------
    ''')

input_buffer = input('''Select the operation to be performed:
    A) Post-processing of a single VQE run
    B) Post-processing of a multiple VQE run
    C) Compare different multiple VQE scans
    D) Compare different noise statistics
Selection (default: B): ''')

if input_buffer.upper() == "C":
    xlabel = input("\nSelect x label: ")
    xlabel = None if xlabel == "" else xlabel
    ylabel = input("Select y label for normal graph: ")
    ylabel = None if ylabel == "" else ylabel
    ylabel_shifted = input("Select y label for shifted graph: ")
    ylabel_shifted = None if ylabel_shifted == "" else ylabel_shifted
    ylabel ={"normal": ylabel, "shifted": ylabel_shifted}
    print("-------------------------------------------------------------\n")
    print("DATASET LOADING")
    path = input("Select post-processed data folder: ")
    if os.path.isdir(path)==False:
        print("ERROR: {} is not a valid path".format(path))
        exit()
    dataset_name = input("Select the data filename root (default: PostProc_Average_): ")
    dataset_name = dataset_name if dataset_name != "" else "PostProc_Average_"
    comparison_data, data_avg = load_parsed_files(path, root_name=dataset_name)
    for element in comparison_data[0]:
        if comparison_data[0].count(element) != 1:
            print("ERROR: {} entries found for order element {}".format(comparison_data.count(element), element))
            exit()
    print("-------------------------------------------------------------\n")
    sv_type = None
    sv_comparison_data = None
    if input("Do you want to load statevector files (y/n)? ").upper() == "Y":
        print("\nSTATEVECTOR DATASET LOADING")
        path = input("Select post-processed data folder: ")
        if os.path.isdir(path)==False:
            print("ERROR: {} is not a valid path".format(path))
            exit()
        dataset_name = input("Select the data filename root (default: PostProc_Average_): ")
        dataset_name = dataset_name if dataset_name != "" else "PostProc_Average_"
        sv_comparison_data, _ = load_parsed_files(path, root_name=dataset_name)
        for element in sv_comparison_data[0]:
            if sv_comparison_data[0].count(element) != 1:
                print("ERROR: {} entries found for order element {}".format(sv_comparison_data.count(element), element))
                exit()
        if len(sv_comparison_data[0]) != len(comparison_data[0]):
            print("ERROR: {} statevector data loaded, {} are required".format(len(sv_comparison_data[0]),len(comparison_data[0])))
            exit()
        for element in sv_comparison_data[0]:
            if comparison_data[0].count(element) != 1:
                print("ERROR: statevector data entry {} does not match".format(element))
                exit()
        for element in comparison_data[0]:
            if sv_comparison_data[0].count(element) != 1:
                print("ERROR: data entry {} does not match with statevector".format(element))
                exit()
        print("-------------------------------------------------------------\n")
        sv_type = input('''Select type of statevector data to be plotted:
    A) Average
    B) Min
    C) Both
Selection (default: B): ''')
        if sv_type.upper() == "C":
            sv_type = "both"
        elif sv_type.upper() == "A":
            sv_type = "average"
        else:
            sv_type = "min"
    plotter.plot_vqe_statistic_comparison(comparison_data, statevector=sv_comparison_data, statevector_type=sv_type, xlabel=xlabel, ylabel=ylabel, marker=data_avg)
elif input_buffer.upper() == "D":
    path = input("Select noise data folder: ")
    if os.path.isdir(path)==False:
        print("ERROR: {} is not a valid path".format(path))
        exit()
    dataset_tail = input("Select the data filename tail (default: _noise.txt): ")
    dataset_tail = dataset_tail if dataset_tail != "" else "_noise.txt"
    bins = input("Select number of bins (default: 50): ")
    bins = 50 if bins == "" else int(bins)
    noise_plotter = plotter.Plot_VQE_stats(bins=bins, alpha=0.75)
    for filename in os.listdir(path):
        if filename.endswith(dataset_tail):
            legend = None
            path_to_file = path + "/" + filename
            print(" -> Loading: {}".format(filename))
            data_file = open(path_to_file)
            for line in data_file:
                data = line.split()
                if "#" in line:
                    legend = line.strip("#\n")
                    print(legend)
            data_file.close()
            noise_plotter.add_datafile(path_to_file, label=legend)
        else:
            print(" -> Skipping: {}".format(filename))
    noise_plotter.plot()    
    
else:
    average = input("\nSelect the number of average points (default: 10): ")
    average = 10 if average == "" else int(average)

    single = True if input_buffer.upper() == "A" else False

    collect_info = False
    if single == False:
        input_buffer = input("\nDo you want to save information for a multiple comparison (y/n)?")
        collect_info = True if input_buffer.upper() == "Y" else False

    target_file = None
    target = None
    if collect_info == False:
        if input("\nDo you want to load a eigenvalue list file (y/n)? ").upper() == "Y":
            target_file = input("""    Select eigenvalue list file: """)
    else:
        target_file = input("""Select eigenvalue list file: """)
    
    if target_file != None:
        if os.path.isfile(target_file)==True:
            myfile = open(target_file, 'r')
            lines = myfile.readlines()
            target = float((lines[1].split())[-1])
            print("     -> Target value: {}".format(target))
            myfile.close()
        else:
            print("""ERROR: Target file "{}" not found""".format(target_file))
            exit()

    user_label = None
    if collect_info == True:
        user_label = float(input("""Select an ordering label for the comparison: """))
    
    if single==True:
        path = input("\nEnter the path to the iteration filename: ")
        if os.path.isfile(path)==False:
            print("ERROR: {} is not a valid filename".format(path))
            exit()
        real, imag = get_converged_value(path, average=average)
        plotter.plot_convergence(path, target=target, save_plot=True, path="PostProc_Conv.png")
        print("CONVERGED VALUE:")
        print("Real part: ", real)
        print("Imaginary part: ", imag)
        if(target != None):
            print("Relative error: {}".format((real-target)/target))
    else:
        n_bins = input("Select the nuber of bins (default: 50): ")
        n_bins = 50 if n_bins == "" else int(n_bins)
        path = input("Enter the path to the iterations folder:")
        if os.path.isdir(path)==False:
            print("ERROR: {} is not a valid folder".format(path))
            exit()
        data = load_iteration_folder(path, average=average)
        filename = "PostProc_Average_{}".format(average)
        if collect_info == True:
            filename += "_" + str(user_label)
        data_file = open(filename + ".txt", 'w')
        if collect_info == True:
            data_file.write("#ORDER\t{}\n".format(user_label))
            data_file.write("#TARGET\t{}\n".format(target))
        for i, r in enumerate(data[0]):
            data_file.write("{}\t{}\n".format(r, data[1][i]))
        data_file.close()
        plotter.plot_vqe_statistic(filename + ".txt", bins=n_bins, save_plot=True, target=target, path=filename+".png")

