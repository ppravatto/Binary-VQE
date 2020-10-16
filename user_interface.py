import time, os, ast, shutil
from datetime import datetime

def get_user_input(VQE_statistic_flag=False, auto_flag=False):

    config_data = {}
    config_data["auto_flag"] = auto_flag
    os.system('cls' if os.name == 'nt' else 'clear')

    print('''-------------------------------------------------------------
                        BINARY VQE
-------------------------------------------------------------
    ''')
    input_buffer = input("""Select the Hamiltonian matrix file (default: "VQE.txt"): """)
    input_buffer = "VQE.txt" if input_buffer == "" else input_buffer
    if auto_flag==False and os.path.isfile(input_buffer)==False:
        print("ERROR: {} datafile not found\n".format(input_buffer))
        exit()
    config_data["VQE_file"] = input_buffer

    input_buffer = input("    -> Select matrix element threshold: (default: 0): " )
    input_buffer = 0 if input_buffer == "" else float(input_buffer)
    config_data["VQE_threshold"] = input_buffer

    contracted_name = ""

    while True:
        input_buffer = input('''
    Variational form: RyRz
        -> Entangler type: 
            F) Full entanglement between qubits
            L) Linear entanglement between qubits
        Selection (default: F): ''')
        if input_buffer.upper() == "F" or input_buffer.upper() == "":
            input_buffer = "full"
            contracted_name += "F"
            break
        elif input_buffer.upper() == "L":
            input_buffer = "linear"
            contracted_name += "L"
            break
        else:
            print("ERROR: {} is not a valid entry".format(input_buffer))
    config_data["VQE_entanglement"] = input_buffer

    input_buffer = input("    -> Select the variational form depth (default: 1): ")
    input_buffer = 1 if input_buffer == "" else int(input_buffer)
    contracted_name += str(input_buffer) + "_"
    config_data["VQE_depth"] = input_buffer

    while True:
        input_buffer = input('''
    Expectation value:
        -> Criteria type:
            D) Direct
            G) Graph coloring sorted
        Selection (default: D): ''')
        if input_buffer.upper() == "D" or input_buffer == "":
            input_buffer = "direct"
            contracted_name += "D"
            break
        elif input_buffer.upper() == "G":
            input_buffer = "graph_coloring"
            contracted_name += "G"
            break
        else:
            print("ERROR: {} is not a valid entry".format(input_buffer))
    config_data["VQE_exp_val_method"] = input_buffer
            
    while True:
        input_buffer = input('''
    Optimizer:
        -> Optimizer type:
            N) Nelder-Mead
            C) COBYLA
            L) SLSQP
            S) SPSA
        Selection: ''')
        if input_buffer.upper() == "N":
            input_buffer = "Nelder-Mead"
            contracted_name += "N"
            break
        elif input_buffer.upper() == "C":
            input_buffer = "COBYLA"
            contracted_name += "C"
            break
        elif input_buffer.upper() == "L":
            input_buffer = "SLSQP"
            contracted_name += "L"
            break
        elif input_buffer.upper() == "S":
            input_buffer = "SPSA"
            contracted_name += "S"
            break
        else:
            print("ERROR: {} is not a valid entry".format(input_buffer))
    config_data["VQE_optimizer"] = input_buffer
    contracted_name += "_"

    input_buffer = input("    -> Maximum number of iterations (default: 400): ")
    input_buffer = 400 if input_buffer == "" else int(input_buffer)
    config_data["VQE_max_iter"] = input_buffer

    opt_options = {}
    if config_data["VQE_optimizer"] == "SPSA":
        input_buffer = None
        if input("    -> Do you want to define custom coefficents for SPSA (y/n)? ").upper() == "Y":
            print("       Select the parameters (Press enter to select the default value):")
            for i in range(5):
                label = 'c' + str(i)
                buffer = input("        " + label + ": ")
                if buffer != "":
                    opt_options[label] = float(buffer)
    else:
        input_buffer = input("    -> Optimizer tolerance (default: 1e-6): ")
        input_buffer = 1e-6 if input_buffer == "" else float(input_buffer)
    config_data["opt_options"] = opt_options
    config_data["VQE_tol"] = input_buffer


    VQE_shots = 1
    VQE_quantum_device = None
    while True:
        VQE_backend = input('''
    Backend:
        -> Simulators:
            Q) QASM simulator
            S) Statevector simulator
        Selection: ''')
        if VQE_backend.upper() == "Q":
            contracted_name += "Q"
            VQE_backend = "qasm_simulator"
            VQE_shots = input("    qasm_simulator number of shots (default: 8192): ")
            VQE_shots = 8192 if VQE_shots == "" else int(VQE_shots)
            if VQE_shots%1000 == 0:
                contracted_name += str(int(VQE_shots/1000))
                contracted_name += "k"
            else:
                contracted_name += str(VQE_shots)
            VQE_error_mitigation = False
            if input("    Do you want to import a noise model from IBMQ device (y/n)? ").upper() == "Y":
                IBMQ_device_file = open("IBMQ_devices", 'r')
                IBMQ_device_list = IBMQ_device_file.readlines()
                IBMQ_device_file.close()
                for i, line in enumerate(IBMQ_device_list):
                    device_data = line.split()
                    print("""        {}) '{}' - ({} qubits)""".format(chr(65+i), device_data[0], device_data[1]))
                VQE_quantum_device = input("    Selection (default: ibmq_16_melbourne): ").upper()
                search_flag = False
                for i, line in enumerate(IBMQ_device_list):
                    if VQE_quantum_device == chr(65+i):
                        VQE_quantum_device = (line.split())[0]
                        search_flag = True
                        break
                if search_flag == False:
                    VQE_quantum_device = 'ibmq_16_melbourne'
                print("     -> Selected device: {}\n".format(VQE_quantum_device))
                if  input("    Do you want to apply qiskit error mitigation algorithm (y/n)? ").upper() == "Y":
                    VQE_error_mitigation = True
                config_data["VQE_error_mitigation"] = VQE_error_mitigation
            break
        elif VQE_backend.upper() == "S":
            contracted_name += "S"
            VQE_backend = "statevector_simulator"
            break
        else:
            print("ERROR: {} is not a valid backend".format(VQE_backend))

    config_data["VQE_shots"] = VQE_shots
    config_data["VQE_backend"] = VQE_backend
    config_data["VQE_quantum_device"] = VQE_quantum_device
    config_data["contracted_name"] = contracted_name

    print("\nOther options:")
    input_buffer = None
    if input("    -> Do you want to load a eigenvalue list file (y/n)? ").upper() == "Y":
        input_buffer = input("""         Select the file (default: "eigval_list.txt"): """)
        input_buffer = "eigval_list.txt" if input_buffer == "" else input_buffer
    config_data["target_file"] = input_buffer

    if config_data["target_file"] != None and auto_flag==False:
        if os.path.isfile(input_buffer)==True:
            myfile = open(config_data["target_file"], 'r')
            lines = myfile.readlines()
            config_data["target"] = float((lines[1].split())[-1])
            print("         -> Target value: {}\n".format(config_data["target"]))
            myfile.close()
        else:
            print("""ERROR: Target file "{}" not found""".format(config_data["target_file"]))
            exit()

    statistic_flag = False
    if VQE_statistic_flag == True:
        VQE_num_samples = input("         Select number of VQE run to accumulate (default: 500): ")
        VQE_num_samples = 500 if VQE_num_samples == "" else int(VQE_num_samples)
        VQE_num_bins = input("         Select number of bins (default: 25): ")
        VQE_num_bins = 25 if VQE_num_bins == "" else int(VQE_num_bins)
        config_data["VQE_num_samples"] = VQE_num_samples
        config_data["VQE_num_bins"] = VQE_num_bins
    elif VQE_backend != "statevector_simulator":
        if input("    -> Do you want to accumulate converged value statistic (y/n)? ").upper() == "Y":
            statistic_flag = True
            num_samples = input("         Select number of samples (default: 1000): ")
            num_samples = 1000 if num_samples == "" else int(num_samples)
            num_bins = input("         Select number of bins (default: 50): ")
            num_bins = 50 if num_bins == "" else int(num_bins)
            config_data["num_samples"] = num_samples
            config_data["num_bins"] = num_bins
    config_data["VQE_statistic_flag"] = VQE_statistic_flag  
    config_data["statistic_flag"] = statistic_flag

    simulator_options = {}
    if VQE_statistic_flag == True:
        simulator_options = {
            "method": "automatic",
            "max_parallel_threads": 1,
            "max_parallel_experiments": 1,
            "max_parallel_shots": 1
        }
    else:
        if config_data["VQE_exp_val_method"] == "direct":
            if input("    -> Do you want to run a parallel simulation (y/n)? ").upper() == "Y":
                threads = 0
            else:
                threads = 1
        if config_data["VQE_exp_val_method"] == "direct":
            simulator_options = {
                "method": "automatic",
                "max_parallel_threads": threads,
                "max_parallel_experiments": threads,
                "max_parallel_shots": 1
            }
        else:
            simulator_options = {
                "method": "automatic"
            }
    config_data["simulator_options"] = simulator_options
    print("-------------------------------------------------------------\n")
    return config_data

def initialize_execution(config_data):
    start_date = datetime.now()
    contracted_date = start_date.strftime("%d%m_%H%M%S")
    folder = contracted_date + "_" + config_data["contracted_name"]
    os.mkdir(folder)
    config_data["base_folder"] = folder
    config_data["date"] = start_date.strftime("%d/%m/%Y")
    config_data["time"] = start_date.strftime("%H:%M:%S")
    if config_data["VQE_statistic_flag"] == True:
        iteration_folder = config_data["base_folder"] + "/iterations"
        os.mkdir(iteration_folder)
        config_data["iteration_folder"] = iteration_folder
    else:
        config_data["iteration_folder"] = config_data["base_folder"]
    if config_data["target_file"] != None and config_data["auto_flag"]==True:
        if os.path.isfile(config_data["target_file"])==True:
            myfile = open(config_data["target_file"], 'r')
            lines = myfile.readlines()
            config_data["target"] = float((lines[1].split())[-1])
            myfile.close()
        else:
            print("""ERROR: Target file "{}" not found""".format(config_data["target_file"]))
            exit()
    return config_data

def finalize_execution(config_data):
    VQE_copy_file = "./" + config_data["base_folder"] + "/" + config_data["VQE_file"]
    shutil.copyfile(config_data["VQE_file"], VQE_copy_file)
    if config_data["target_file"] != None:
        target_copy_file = "./" + config_data["base_folder"] + "/" + config_data["target_file"]
        shutil.copyfile(config_data["target_file"], target_copy_file)

def save_report(config_data, real, imag, path=None):
    folder = config_data["base_folder"] if path==None else path
    report_file = folder + "/" + config_data["contracted_name"] + "_report.txt"
    report = open(report_file, 'w')
    report.write("Date: {}\n".format(config_data["date"]))
    report.write("Time: {}\n\n".format(config_data["time"]))
    report.write("VQE SETTINGS:\n")
    report.write("Entangler type: {}, depth: {}\n".format(config_data["VQE_entanglement"], config_data["VQE_depth"]))
    report.write("Expectation value computation method: {}".format(config_data["VQE_exp_val_method"]))
    report.write("Optimizer: {}, Max Iter: {}\n".format(config_data["VQE_optimizer"], config_data["VQE_max_iter"]))
    if config_data["VQE_optimizer"] != "SPSA":
        report.write("Tol: {}\n".format(config_data["VQE_tol"]))
    else:
        report.write("\n")
    report.write("Backend: {}, Shots: {}\n\n".format(config_data["VQE_backend"], config_data["VQE_shots"]))
    if config_data["VQE_quantum_device"] != None:
        error_mitigation_flag = "YES" if config_data["VQE_error_mitigation"] == True else "NO"
        report.write("Noise model: {}, Error mitigation: {}".format(config_data["VQE_quantum_device"], error_mitigation_flag))
    report.write("SYSTEM DATA:\n")
    report.write("Number of basis functions: {}, Qubits count: {}\n".format(config_data["M"], config_data["N"]))
    report.write("Non-zero matrix elements: {} of {}, Threshold: {}\n".format(config_data["num_integrals"], config_data["M"]**2, config_data["VQE_threshold"]))
    report.write("Total number of post rotations: {}\n\n".format(config_data["num_post_rot"]))
    if config_data["VQE_statistic_flag"] == True:
        report.write("VQE STATISTIC SAMPLING:\n")
        report.write("Number of samples: {}\n".format(config_data["VQE_num_samples"]))
    else:
        report.write("CALCULATION DATA:\n")
    report.write("Expectation value: Real part: {}, Imag part: {}\n".format(real, imag))
    if config_data["target_file"] != None:
        rel_error = (real-config_data["target"])/config_data["target"]
        report.write("Theoretical value: {}, Relative Error: {}\n".format(config_data["target"], rel_error))
    report.write("Runtime: {}s\n".format(config_data["runtime"]))
    report.close()

def get_pruned_type(variable):
    type_str = str(type(variable))
    data = type_str.split(" ")
    return data[1].strip(">").strip("'")

def save_dictionary_to_file(dictionary, filename):
    myfile = open(filename, 'w')
    for key, value in dictionary.items():
        myfile.write("{}\t{}\t{}\n".format(key, value, get_pruned_type(value)))
    myfile.close()

def load_dictionary_from_file(filename):
    dictionary = {}
    myfile = open(filename, 'r')
    for line in myfile:
        data = line.split('\t')
        buffer = data[1].strip("'")
        data[2] = data[2].strip('\n')
        if data[2] == "bool":
            buffer = True if buffer=="True" else False
        elif data[2] == "int":
            buffer = int(buffer)
        elif data[2] == "float":
            buffer = float(buffer)
        elif data[2] == "dict":
            buffer = ast.literal_eval(buffer)
        elif data[2] == "NoneType":
            buffer = None
        dictionary[str(data[0])] = buffer
    myfile.close()
    return dictionary
