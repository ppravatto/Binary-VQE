import binary_vqe as bm
import plotter as myplt
import numpy as np
import time

print('''
-------------------------------------------------------------
                        BINARY VQE
-------------------------------------------------------------
''')

VQE_file = input("""Select the Hamiltonian matrix file (default: "VQE.txt"): """)
VQE_file = "VQE.txt" if VQE_file == "" else VQE_file
VQE_threshold = input("    -> Select matrix element threshold: (default: 0): " )
VQE_threshold = 0 if VQE_threshold == "" else float(VQE_threshold)

while True:
    VQE_entanglement = input('''
Variational form: RyRz
    -> Entangle type: 
           F) Full entanglement between qubits
           L) Linear entanglement between qubits
       Selection (default: F): ''')
    if VQE_entanglement.upper() == "F":
        VQE_entanglement = "full"
        break
    elif VQE_entanglement.upper() == "L":
        VQE_entanglement = "linear"
        break
    elif VQE_entanglement.upper() == "":
        VQE_entanglement = "full"
        break
    else:
        print("ERROR: {} is not a valid entry".format(VQE_entanglement))

VQE_depth = input("    -> Select the variational form depth (default: 1): ")
VQE_depth = 1 if VQE_depth == "" else int(VQE_depth)

while True:
    Expectation_value = input('''
Expectation value:
    -> Criteria type:
        D) Direct
        G) Graph coloring sorted
    Selection: ''')
    if Expectation_value.upper() == "D":
        Expectation_value = "Direct"
        break
    elif Expectation_value.upper() == "G":
        Expectation_value = "Graph_coloring"
        break
    else:
        print("ERROR: {} is not a valid entry".format(Expectation_value))
        
        
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
        break
    elif VQE_optimizer.upper() == "C":
        VQE_optimizer = "COBYLA"
        break
    elif VQE_optimizer.upper() == "L":
        VQE_optimizer = "SLSQP"
        break
    elif VQE_optimizer.upper() == "S":
        VQE_optimizer = "SPSA"
        break
    else:
        print("ERROR: {} is not a valid entry".format(VQE_optimizer))

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
        VQE_backend = "qasm_simulator"
        VQE_shots = input("    qasm_simulator number of shots (default: 8192): ")
        VQE_shots = 8192 if VQE_shots == "" else int(VQE_shots)
        break
    elif VQE_backend.upper() == "S":
        VQE_backend = "statevector_simulator"
        break
    else:
        print("ERROR: {} is not a valid backend".format(VQE_backend))

print("\nOther options:")
target_file = None
if input("    -> Do you want to load a eigenvalue list file (y/n)? ").upper() == "Y":
    target_file = input("""         Select the file (default: "eigval_list.txt"): """)
    target_file = "eigval_list.txt" if target_file == "" else target_file

statistic_flag = False
if input("    -> Do you want to accumulate converged value statistic (y/n)? ").upper() == "Y":
    statistic_flag = True
    num_samples = int(input("         Select number of samples: "))
    num_bins = int(input("         Select number of bins: "))

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

#Run a VQE calculation
simulator_options = {
    "method": "automatic",
    "max_parallel_threads": threads,
    "max_parallel_experiments": threads,
    "max_parallel_shots": 1
    }
start_time = time.time()
vqe = bm.BIN_VQE(VQE_file, Expectation_value, verbose=True, depth=VQE_depth)
vqe.configure_backend(VQE_backend, num_shots=VQE_shots, simulator_options=simulator_options)
real, immaginary = vqe.run(expectation_value = Expectation_value, method=VQE_optimizer, max_iter=VQE_max_iter, tol=VQE_tol, filename="Iteration.txt", verbose=True, optimizer_options=opt_options)
print("Expectation value: {} + {}j".format(real, immaginary))
print("-------------------------------------------------------------")
print("OPTIMIZATION TERMINATED - Runtime: {}s".format(time.time() - start_time))

#Plot convergence trend
myplt.plot_convergence("Iteration.txt", target)

if statistic_flag == True:
    #Collect sampling noise using current parameters
    stats = vqe.get_expectation_statistic(Expectation_value, sample=num_samples, filename="Noise.txt", verbose=True)
    print("Mean value:")
    print(stats['mean'].real)
    print(stats['mean'].imag)
    print("Standard Deviation:")
    print(stats['std_dev'].real)
    print(stats['std_dev'].imag)

    #Plot sampling noide graph with gaussian approximation
    myplt.plot_vqe_statistic("Noise.txt", bins=num_bins, gauss=True, target=target)

print("-------------------------------------------------------------")
print("NORMAL TERMINATION")