# Binary-VQE
Binary-VQE is a simple python implementation of a binary-mapping-based Variational Quantum Eigensolver (VQE) algorithm. The program is based on the IBM Qiskit library.

### How to cite this code
This code can be used and modified freely under the GPL-3.0 License. If you use this code please cite the URL of this repository (or the URL of the correspondent release) and the paper: [Pierpaolo Pravatto et al 2021 New J. Phys. 23 123045](https://iopscience.iop.org/article/10.1088/1367-2630/ac3ff9/meta)


## Requirements
In order to use this software we strongly advise the use of [Anaconda](https://www.anaconda.com/products/individual) as a virtual environment.

- [python3](https://www.python.org/)
- [qiskit](https://qiskit.org/)
- [numpy](https://numpy.org/)
- [scipy](https://www.scipy.org/)
- [matplotlib](https://matplotlib.org/)
- [mpi4py](https://mpi4py.readthedocs.io/en/stable/index.html) (only for VQE statistic)

For the Anaconda users we advise installing `mpi4py` using the conda package manager with the command:
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
The simplest way to run a VQE simulation is to launch directly the application script without any argument. In this mode, an interactive terminal-based interface will allow the user to set up and run the calculation.

In order to run a simple single VQE calculation the program can be started directly calling the `main.py` script:
```
python3 main.py
```
In order to run multiple VQE calculations to collect statistical data, the script `MPI_scan.py` must be used. In order to execute this script, the library `mpi4py` must be installed. To run this type of calculation the following command can be used:
```
mpiexec -n <number-of-task> python3 MPI_scan.py
```
The `<number-of-task>` value must (usually) be equal to or less than the number of physical cores in the machine.

### Running a calculation on a remote machine
If the interactive mode cannot be used (e.g. submission of the computation to an HPC system) a file-based calculation can be performed. An input file can be generated using the `input_generator.py` using the syntax:
```
python3 input_generator.py
```
this will open an interactive terminal-based application that will allow the generation of an input file.

The input file can then be used to submit a calculation in a remote machine using the syntax:
```
python3 main.py <input_file>
```
for a single VQE calculation or:
```
mpiexec -n <number-of-task> python3 MPI_scan.py <input_file>
```
for multiple VQE calculations. Keep in mind that the indirect mode will still save all the graphs and data but no interactive windows will be open.

## Currently supported optimizers
- Nelder-mead (from SciPy)
- COBYLA (from SciPy)
- SLSQP (from SciPy)
- SPSA (modified version based on Qiskit)
