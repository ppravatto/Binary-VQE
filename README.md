# Binary-VQE
A simple python implementation of a binary mapping based Variational Quantum Eigensolver algorithm. The program requires the Qiskit library, we strongly advise the use of Anaconda as a virtual environment.

## Requirements
- [python3](https://www.python.org/)
- [qiskit](https://qiskit.org/)
- [numpy](https://numpy.org/)
- [scipy](https://www.scipy.org/)
- [matplotlib](https://matplotlib.org/)
- [mpi4py](https://mpi4py.readthedocs.io/en/stable/index.html) (only for VQE statistic)

Once installed python3 the requirements can be installed. For the Anaconda users we advise to install `mpi4py` using the conda package manager with the command:
```
conda install -c conda-forge mpi4py
```
All the other requirements can be installed with the command:
```
pip install -r requirements
```


## Running a calculation
The program features a terminal-based user interface from which the user can select the required files and set all the necessary options. The minimum requirement to run a calculation is a text file containing the Hamiltonian matrix. Optionally an eigenvalue list can be given to the program to automatically compute the relative error and to add graphical indications on the plotted data. The program can be interfaced directly with the [Smoluchowski-Rotor-Chain](https://github.com/ppravatto/Smoluchowski-Rotor-Chain.git) software.

### Running an interactive calculation
The simplest way to run a VQE simulation is to launch directly the application script without any argument. In this mode an interactive terminal based interface will allow the user to set up and run the calculation.

In order to run a simple single VQE calculation the program can be started directly calling the `main.py` script:
```
python3 main.py
```
In order to run multiple VQE calculations in order to collect statistical data the script `MPI_scan.py` must be used. In order to execute the script the library `mpi4py` must be installed. In order to run this type of calculation the following command can be used:
```
mpiexec -n <number-of-task> python3 MPI_scan.py
```
The `<number-of-task>` value must be equal to or less than the number of physical cores in the machine.

### Running a calculation on a remote machine
If the interactive mode cannot be used (e.g. submission of the computation to an HPC system) a file based calculation can be performed. An imput file can be generated using the `input_generator.py` using the syntax:
```
python3 input_generator.py
```
this will open an interactive terminal based application that will allow the generation of an input file.

The input file can then be used to submit a calculation in a remote machine using the syntax:
```
python3 main.py <input_file>
```
for a single VQE calculation or:
```
mpiexec -n <number-of-task> python3 MPI_scan.py <input_file>
```
for a multiple VQE calculation. Keep in mind that the indirect mode will still save all the graphs and data but no interactive windows will be open.

WARNING: The input file contains all the informations about date and time of the input creation and the location of the output folders. Do not run multiple calculations with the same input file or only the data from the last calculation will be saved.


## Currently supported optimizers
- Nelder-mead
- COBYLA
- SLSQP
- SPSA
