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
pip install -r requirements.txt
```

## Currently supported optimizers
- Nelder-mead
- COBYLA
- SLSQP
- SPSA
