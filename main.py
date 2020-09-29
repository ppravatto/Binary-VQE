import binary_vqe as bm
import plotter as myplt
import numpy as np
import time, os
from datetime import datetime

os.system('cls' if os.name == 'nt' else 'clear')

print('''-------------------------------------------------------------
                        BINARY VQE
-------------------------------------------------------------
''')

VQE_file = input("""Select the Hamiltonian matrix file (default: "VQE.txt"): """)
VQE_file = "VQE.txt" if VQE_file == "" else VQE_file
if os.path.isfile(VQE_file)==False:
    print("ERROR: {} datafile not found\n".format(VQE_file))
    exit()

VQE_threshold = input("    -> Select matrix element threshold: (default: 0): " )
VQE_threshold = 0 if VQE_threshold == "" else float(VQE_threshold)

contracted_name = ""

while True:
    VQE_entanglement = input('''
Variational form: RyRz
    -> Entangler type: 
           F) Full entanglement between qubits
           L) Linear entanglement between qubits
       Selection (default: F): ''')
    if VQE_entanglement.upper() == "F" or VQE_entanglement.upper() == "":
        VQE_entanglement = "full"
        contracted_name += "F"
        break
    elif VQE_entanglement.upper() == "L":
        VQE_entanglement = "linear"
        contracted_name += "L"
        break
    else:
        print("ERROR: {} is not a valid entry".format(VQE_entanglement))

VQE_depth = input("    -> Select the variational form depth (default: 1): ")
VQE_depth = 1 if VQE_depth == "" else int(VQE_depth)
contracted_name += str(VQE_depth)
contracted_name += "_"

while True:
    VQE_exp_val_method = input('''
Expectation value:
    -> Criteria type:
        D) Direct
        G) Graph coloring sorted
    Selection (default: D): ''')
    if VQE_exp_val_method.upper() == "D" or VQE_exp_val_method == "":
        VQE_exp_val_method = "direct"
        break
    elif VQE_exp_val_method.upper() == "G":
        VQE_exp_val_method = "graph_coloring"
        break
    else:
        print("ERROR: {} is not a valid entry".format(VQE_exp_val_method))
        
        
while True:
    VQE_optimizer = input('''
Optimizer:
    -> Optimizer type:
        N) Nelder-Mead
        C) COBYLA
        L) SLSQP
        S) SPSA
    Selection: ''')
    if VQE_optimizer.upper() == "N":
        VQE_optimizer = "Nelder-Mead"
        contracted_name += "N"
        break
    elif VQE_optimizer.upper() == "C":
        VQE_optimizer = "COBYLA"
        contracted_name += "C"
        break
    elif VQE_optimizer.upper() == "L":
        VQE_optimizer = "SLSQP"
        contracted_name += "L"
        break
    elif VQE_optimizer.upper() == "S":
        VQE_optimizer = "SPSA"
        contracted_name += "S"
        break
    else:
        print("ERROR: {} is not a valid entry".format(VQE_optimizer))

contracted_name += "_"

VQE_max_iter = input("    -> Maximum number of iterations (default: 400): ")
VQE_max_iter = 400 if VQE_max_iter == "" else int(VQE_max_iter)

opt_options = {}
if VQE_optimizer == "SPSA":
    VQE_tol = None
    if input("    -> Do you want to define custom coefficents for SPSA (y/n)? ").upper() == "Y":
        print("       Select the parameters (Press enter to select the default value):")
        for i in range(5):
            label = 'c' + str(i)
            buffer = input("        " + label + ": ")
            if buffer != "":
                opt_options[label] = float(buffer)
else:
    VQE_tol = input("    -> Optimizer tolerance (default: 1e-6): ")
    VQE_tol = 1e-6 if VQE_tol == "" else float(VQE_tol)
   
VQE_shots = 1
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
        VQE_quantum_device = None
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
        break
    elif VQE_backend.upper() == "S":
        contracted_name += "S"
        VQE_backend = "statevector_simulator"
        break
    else:
        print("ERROR: {} is not a valid backend".format(VQE_backend))

print("\nOther options:")
target_file = None
if input("    -> Do you want to load a eigenvalue list file (y/n)? ").upper() == "Y":
    target_file = input("""         Select the file (default: "eigval_list.txt"): """)
    target_file = "eigval_list.txt" if target_file == "" else target_file
    if os.path.isfile(target_file)==False:
        print("ERROR: {} datafile not found\n".format(target_file))
        exit()

statistic_flag = False
if VQE_backend != "statevector_simulator":
    if input("    -> Do you want to accumulate converged value statistic (y/n)? ").upper() == "Y":
        statistic_flag = True
        num_samples = input("         Select number of samples (default: 1000): ")
        num_samples = 1000 if num_samples == "" else int(num_samples)
        num_bins = input("         Select number of bins (default: 50): ")
        num_bins = 50 if num_bins == "" else int(num_bins)

if VQE_exp_val_method == "direct":
    if input("    -> Do you want to run a parallel simulation (y/n)? ").upper() == "Y":
        threads = 0
    else:
        threads = 1

print("-------------------------------------------------------------\n")

target = None
if target_file != None:
    myfile = open(target_file, 'r')
    lines = myfile.readlines()
    target = float((lines[1].split())[-1])
    print("Target: {}".format(target))
    myfile.close()

while True:
    start_date = datetime.now()
    contracted_date = start_date.strftime("%d%m_%H%M%S")
    folder = contracted_date + "_" + contracted_name
    os.mkdir(folder)

    #Run a VQE calculation
    if VQE_exp_val_method == "direct":
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

    start_time = time.time()
    vqe = bm.BIN_VQE(VQE_file, method=VQE_exp_val_method, verbose=True, depth=VQE_depth)
    vqe.configure_backend(VQE_backend, num_shots=VQE_shots, simulator_options=simulator_options)
    if VQE_quantum_device != None:
        vqe.import_noise_model(VQE_quantum_device, error_mitigation=VQE_error_mitigation)
    iteration_file = folder + "/" + contracted_name + "_iteration.txt"
    real, immaginary = vqe.run(method=VQE_optimizer, max_iter=VQE_max_iter, tol=VQE_tol, filename=iteration_file, verbose=True, optimizer_options=opt_options)
    print("Expectation value: {} + {}j".format(real, immaginary))
    print("-------------------------------------------------------------")
    vqe_runtime = time.time() - start_time
    print("OPTIMIZATION TERMINATED - Runtime: {}s".format(vqe_runtime))

    report_file = folder + "/" + contracted_name + "_report.txt"
    report = open(report_file, 'w')
    report.write("Date: {}\n".format(start_date.strftime("%d/%m/%Y")))
    report.write("Time: {}\n\n".format(start_date.strftime("%H:%M:%S")))
    report.write("VQE SETTINGS:\n")
    report.write("Entangler type: {}, depth: {}\n".format(VQE_entanglement, VQE_depth))
    report.write("Optimizer: {}, Max Iter: {}\n".format(VQE_optimizer, VQE_max_iter))
    if VQE_optimizer != "SPSA":
        report.write("Tol: {}\n".format(VQE_tol))
    else:
        report.write("\n")
    report.write("Backend: {}, Shots: {}\n\n".format(VQE_backend, VQE_shots))
    if VQE_quantum_device != None:
        error_mitigation_flag = "YES" if VQE_error_mitigation == True else "NO"
        report.write("Noise model: {}, Error mitigation: {}".format(VQE_quantum_device, error_mitigation_flag))
    report.write("SYSTEM DATA:\n")
    report.write("Number of basis functions: {}, Qubits count: {}\n".format(vqe.M, vqe.N))
    report.write("Non-zero matrix elements: {} of {}, Threshold: {}\n".format(len(vqe.integrals[2]), vqe.M**2, VQE_threshold))
    report.write("Total number of post rotations: {}\n\n".format(len(vqe.post_rot)))
    report.write("CALCULATION DATA:\n")
    report.write("Expectation value: Real part: {}, Imag part: {}\n".format(real, immaginary))
    if target_file != None:
        rel_error = (real-target)/target
        report.write("Theoretical value: {}, Relative Error: {}\n".format(target, rel_error))
    report.write("Runtime: {}s\n".format(vqe_runtime))
    report.close()

    #Plot convergence trend
    picture_name = folder + "/" + contracted_name + "_convergence.png"
    myplt.plot_convergence(iteration_file, target, path=picture_name)

    aux_statistic_flag = "N"
    if statistic_flag == True:
        aux_statistic_flag = input("Would you like to skip the statistic accumulation for this run (y/n)? ")
    
    if statistic_flag == True and aux_statistic_flag.upper() != "Y":
        #Collect sampling noise using current parameters
        statistic_file = folder + "/" + contracted_name + "_noise.txt"
        stats = vqe.get_expectation_statistic(sample=num_samples, filename=statistic_file, verbose=True)
        print("Mean value:")
        print(stats['mean'].real)
        print(stats['mean'].imag)
        print("Standard Deviation:")
        print(stats['std_dev'].real)
        print(stats['std_dev'].imag)

        #Plot sampling noide graph with gaussian approximation
        picture_name = folder + "/" + contracted_name + "_noise.png"
        myplt.plot_vqe_statistic(statistic_file, bins=num_bins, gauss=True, target=target, path=picture_name)

    print("-------------------------------------------------------------")
    print("NORMAL TERMINATION")

    restart = input("Would you like to run another calculation with the same parameters (y/n)? ")
    if restart.upper() != "Y":
        break