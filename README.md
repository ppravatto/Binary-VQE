# Binary-VQE
A simple python implementation of a binary mapping based Variational Quantum Eigensolver algorithm. The program requires the Qiskit library, we strongly advise the use of Anaconda as a virtual environment.

## Requirements
- [python3](https://www.python.org/)
- [qiskit](https://qiskit.org/)
- [numpy](https://numpy.org/)
- [scipy](https://www.scipy.org/)
- [matplotlib](https://matplotlib.org/)
- [mpi4py](https://mpi4py.readthedocs.io/en/stable/index.html) (only for VQE_scan)

Once installed python3 the requirements can be installed. For the Anaconda users we advise to install `mpi4py` using the conda package manager with the command:
```
conda install -c conda-forge mpi4py
```
All the other requirements can be installed with the command:
```
pip install -r requirements
```


## Running a calculation
The program features a terminal-based user interface from which the user can select the required files and set all the necessary options. The minimum requirement to run a calculation is a text file containing the Hamiltonian matrix. Optionally an eigenvalue list can be given to the program to automatically compute the relative error and to add graphical indications on the plotted data. The program can be interfaced directly with the [Smoluchowski-Rotor-Chain](https://github.com/ppravatto/Smoluchowski-Rotor-Chain.git) software. In order to run a simple single VQE calculation the program can be started directly calling the `main.py` script:
```
python3 main.py
```
In order to run multiple VQE calculations in order to collect statistical data the script `MPI_scan.py` must be used. In order to execute the script the library `mpi4py` must be installed. In order to run a calculation the following command can be used:
```
mpiexec -n <number-of-task> python3 main.py
```
The `<number-of-task>` value must be equal to or less than the number of physical cores in the machine.

## Currently supported optimizers
- Nelder-mead
- COBYLA
- SLSQP
- SPSA
