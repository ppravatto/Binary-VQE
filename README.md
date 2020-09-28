# Binary-VQE
A simple python implementation of a binary mapping based Variational Quantum Eigensolver algorithm. The program requires the Qiskit library, we strongly advise the use of Anaconda as a virtual environment.

## Requirements
- [python3](https://www.python.org/)
- [qiskit](https://qiskit.org/) (0.19.2)
- [numpy](https://numpy.org/) (1.18.4)
- [scipy](https://www.scipy.org/) (1.4.1)
- [matplotlib](https://matplotlib.org/) (3.2.1)

Once installed python3 the requirements can be installed via the command
```
pip install -r requirements
```

## Running a calculation
The program features a terminal-based user interface from which the user can select the required files and set all the necessary options. The minimum requirement to run a calculation is a text file containing the Hamiltonian matrix. Optionally an eigenvalue list can be given to the program to automatically compute the relative error and to add graphical indications on the plotted data. The software can be interfaced directly with the [Smoluchowski-Rotor-Chain](https://github.com/ppravatto/Smoluchowski-Rotor-Chain.git) software.

## Currently supported optimizers
- Nelder-mead
- COBYLA
- SLSQP
- SPSA
