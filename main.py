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
       Selection: ''')
    if VQE_entanglement.upper() == "F":
        VQE_entanglement = "full"
        break
    elif VQE_entanglement.upper() == "L":
        VQE_entanglement = "linear"
        break
    else:
        print("ERROR: {} is not a valid entry".format(VQE_entanglement))

VQE_depth = int(input("    -> Select the variational form depth: "))

while True:
    VQE_optimizer = input('''
Optimizer:
    -> Optimizer type:
        N) Nelder-Mead
        C) COBYLA
    Selection: ''')
    if VQE_optimizer.upper() == "N":
        VQE_optimizer = "Nelder-Mead"
        break
    elif VQE_optimizer.upper() == "C":
        VQE_optimizer = "COBYLA"
        break
    else:
        print("ERROR: {} is not a valid entry".format(VQE_optimizer))

VQE_max_iter = input("    -> Maximum number of iterations (default: 400): ")
VQE_max_iter = 400 if VQE_max_iter == "" else int(VQE_max_iter)
VQE_tol = input("    -> Optimizer tolerance (default: 1e-4): ")
VQE_tol = 1e-4 if VQE_tol == "" else float(VQE_tol)

VQE_shots = input("\nqasm_simulator number of shots (default: 8192): ")
VQE_shots = 8192 if VQE_shots == "" else int(VQE_shots)


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

print("-------------------------------------------------------------\n")

target = None
if target_file != None:
    myfile = open(target_file, 'r')
    lines = myfile.readlines()
    target = float((lines[1].split())[-1])
    print("Target: {}".format(target))
    myfile.close()

#Run a VQE calculation
start_time = time.time()
vqe = bm.BIN_VQE(VQE_file, verbose=True, depth=VQE_depth)
vqe.configure_backend('qasm_simulator', num_shots=VQE_shots)
real, immaginary = vqe.run(method=VQE_optimizer, max_iter=VQE_max_iter, tol=VQE_max_iter, filename="Iteration.txt", verbose=True)
print("Expectation value: {} + {}j".format(real, immaginary))
print("-------------------------------------------------------------")
print("OPTIMIZATION ENDED - Runtime: {}s".format(time.time() - start_time))

#Plot convergence trend
myplt.plot_convergence("Iteration.txt", target)

if statistic_flag == True:
    #Collect sampling noise using current parameters
    stats = vqe.get_expectation_statistic(sample=num_samples, filename="Noise.txt", verbose=True)
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