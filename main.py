import binary_vqe as bm
import plotter as myplt
import numpy as np

#Load file from SRM to plot the reference value
myfile = open("eigval_list.txt", 'r')
lines = myfile.readlines()
target = float((lines[1].split())[-1])
print("Target: {}".format(target))
myfile.close()

#Run a VQE calculation
vqe = bm.BIN_VQE("VQE.txt", verbose=True, depth=3)
vqe.configure_backend('statevector_simulator')
real, immaginary = vqe.run(method='COBYLA', max_iter=600, tol=1e-5, filename="Iteration.txt", verbose=True)
print("Expectation value: {} + {}j".format(real, immaginary))

#Plot convergence trend
myplt.plot_convergence("Iteration.txt", target)

#Collect sampling noise using current parameters
stats = vqe.get_expectation_statistic(sample=1000, filename="Noise.txt", verbose=True)
print("Mean value:")
print(stats['mean'].real)
print(stats['mean'].imag)
print("Standard Deviation:")
print(stats['std_dev'].real)
print(stats['std_dev'].imag)

#Plot sampling noide graph with gaussian approximation
myplt.plot_vqe_statistic("Noise.txt", bins=100, gauss=True, target=target)
