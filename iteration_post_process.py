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

os.system('cls' if os.name == 'nt' else 'clear')

print('''-------------------------------------------------------------
                 BINARY VQE - POST PROCESSING
-------------------------------------------------------------
    ''')

single = input('''
Select the operation to be performed:
    A) Post-processing of a single VQE run
    B) Post-processing of a multiple VQE run
Selection (default: B): ''')
single = True if single.upper() == "A" else False

average = input("\nSelect the number of average points (default: 10): ")
average = 10 if average == "" else int(average)

target_file = None
target = None
if input("\nDo you want to load a eigenvalue list file (y/n)? ").upper() == "Y":
    target_file = input("""    Select the file: """)
    if os.path.isfile(target_file)==True:
        myfile = open(target_file, 'r')
        lines = myfile.readlines()
        target = float((lines[1].split())[-1])
        print("     -> Target value: {}".format(target))
        myfile.close()
    else:
        print("""ERROR: Target file "{}" not found""".format(target_file))
        exit()

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
    data_file = open(filename + ".txt", 'w')
    for i, r in enumerate(data[0]):
        data_file.write("{}\t{}\n".format(r, data[1][i]))
    data_file.close()
    plotter.plot_vqe_statistic(filename + ".txt", bins=n_bins, save_plot=True, target=target, path=filename+".png")

