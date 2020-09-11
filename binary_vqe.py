import os
from qiskit import *
import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt
import random as rnd

I = complex(0, 1)

def get_bin_list(number, register_length, invert=False):
    string = "{0:b}".format(number)
    buffer = [int(i) for i in string]
    buffer = buffer[::-1]
    while len(buffer)<register_length:
        buffer.append(0)
    if invert == True:
        buffer = buffer[::-1]
    return buffer

def get_post_rotation(pauli_string):
    mystring = ""
    for gate in pauli_string:
        if gate == "I" or gate == "Z":
            mystring += "Z"
        else:
            mystring += gate
    return mystring

def get_pauli_string(row_bin, col_bin, term_bin):
    coeff = complex(1, 0)
    pauli_string = ""
    for i, select in enumerate(term_bin):
        coeff *= 0.5
        if row_bin[i] == col_bin[i]:
            if select == 0:
                pauli_string += "I"
            else:
                pauli_string += "Z"
                coeff *= (-1)**row_bin[i]
        else:
            if select == 0:
                pauli_string += "X"
            else:
                pauli_string += "Y"
                coeff *= I * (-1)**row_bin[i]
    return pauli_string, coeff


class BIN_VQE():

    def __init__(self, filename, verbose=False, entanglement="full", depth=1):
        self.expectation_value = None
        self.expectation_statistic = None
        self.n_iter = 0
        self.opt_history = []
        self.state = 0
        self.entanglement = entanglement
        if depth <= 0:
            print("ERROR: the depth of the circuit cannot be {}".format(depth))
            exit()
        self.depth = depth
        self.integrals = [[],[],[]]
        if os.path.isfile(filename)==True:
            myfile = open(filename, 'r')
            for row, line in enumerate(myfile):
                myline = line.split()
                if row==0:
                    self.M = len(myline)
                for col, element in enumerate(myline):
                    if float(element) != 0.:
                        self.integrals[0].append(int(row))
                        self.integrals[1].append(int(col))
                        self.integrals[2].append(float(element))
            myfile.close()
        else:
            print("ERROR: datafile not found\n")
            exit()
        self.N = int(np.ceil(np.log2(self.M)))
        self.qubits = range(self.N)
        self.num_params = 2*(1+self.depth)*self.N
        self.post_rot = []
        for i, row in enumerate(self.integrals[0]):
            col = self.integrals[1][i]
            row_bin = get_bin_list(row, self.N)
            col_bin = get_bin_list(col, self.N)
            for term in range(2**self.N):
                term_bin = get_bin_list(term, self.N)
                pauli_string, coeff = get_pauli_string(row_bin, col_bin, term_bin)
                search_string = get_post_rotation(pauli_string)
                if self.post_rot.count(search_string) == 0:
                    self.post_rot.append(search_string)
        self.backend = Aer.get_backend('qasm_simulator')
        self.shots = 1024
        if verbose==True:
            print("VQE CLASS INITIALIZATION:")
            print(" -> Total number of basis functions: {}".format(self.M))
            print(" -> Required number of Qubits: {}".format(self.N))
            print(" -> Non-zero matrix elements: {} of {}".format(len(self.integrals[2]), self.M**2))
            print(" -> Total number of post rotations: {} of {}".format(len(self.post_rot), 3**self.N))
            print(" -> Total number of variational prameters: {}".format(self.num_params))
    
    def set_initial_state(self, state):
        if state >= self.M:
            print("ERROR: The value {} is out of bounds ({})".format(state, self.M))
            exit()
        self.state = state
    
    def initialize_circuit(self):
        qc = QuantumCircuit(self.N, self.N)
        if self.state != 0:
            state_bin = get_bin_list(self.state, self.N)
            for qubit, state in enumerate(state_bin):
                if state == 1:
                    qc.x(qubit)
            qc.barrier()
        return qc

    def ryrz(self, param):
        if len(param) != self.num_params:
            print("ERROR: {} parameters cannot be passed to a {} qubits RyRz network of depth {}".format(len(param), self.N, self.depth))
            exit()
        qc = QuantumCircuit(self.N, name="RyRz\n({}, d{})".format(self.entanglement, self.depth))
        for qubit in self.qubits:
            qc.ry(param[qubit], qubit)
            qc.rz(param[qubit+self.N], qubit)
        for layer in range(1, self.depth+1):
            qc.barrier()
            for control in range(self.N-1):
                for target in range(control+1, self.N):
                    if (self.entanglement == "linear" and target > control+1):
                        continue
                    qc.h(target)
                    qc.cx(control, target)
                    qc.h(target)
            qc.barrier()
            for qubit in self.qubits:
                qc.ry(param[qubit+2*layer*self.N], qubit)
                qc.rz(param[qubit+(2*layer+1)*self.N], qubit)    
            qc.barrier()  
        return qc
    
    def measure(self, post_rotation):
        if len(post_rotation) != self.N:
            print("ERROR: Invalid group string passed to group_operator function\n")
            exit()
        qc = QuantumCircuit(self.N, self.N, name="{}\nPost.Rot.".format(post_rotation))
        for qubit, pauli in enumerate(post_rotation):
            if pauli == "X":
                qc.h(qubit)
            elif pauli == "Y":
                qc.sdg(qubit)
                qc.h(qubit)
            else:
                pass
        if post_rotation != "Z"*self.N:
            qc.barrier()
        for qubit in self.qubits:
            qc.measure(qubit, qubit)
        return qc
    
    def configure_backend(self, backend_name='qasm_simulator', num_shots=1024):
        self.backend = Aer.get_backend(backend_name)
        self.shots = num_shots

    def run_circuit(self, post_rotation, parameters):
        qc = self.initialize_circuit()
        qc += self.ryrz(parameters)
        qc += self.measure(post_rotation)
        job = execute(qc, self.backend, shots=self.shots)
        results = job.result()
        counts = results.get_counts()
        return counts
    
    def compute_pauli_expect_val(self, pauli_string, counts_data):
        value = 0
        for state in range(2**self.N):
            state_bin = get_bin_list(state, self.N)
            outcome = ""
            for i in state_bin[::-1]:
                outcome += str(i)
            if outcome not in counts_data:
                continue
            sign = 1
            for qubit in self.qubits:
                if pauli_string[qubit] != "I":
                    sign *= -1 if state_bin[qubit] == 1 else 1
            value += sign*counts_data[outcome]
        return value/self.shots
            
    def compute_expectation_value(self, parameters):
        post_rotation_data = {}
        for post_rotation in self.post_rot:
            post_rotation_data[post_rotation] = self.run_circuit(post_rotation, parameters)
        value = 0
        for i, row in enumerate(self.integrals[0]):
            col = self.integrals[1][i]
            row_bin = get_bin_list(row, self.N)
            col_bin = get_bin_list(col, self.N)
            partial_sum = 0
            for term in range(2**self.N):
                term_bin = get_bin_list(term, self.N)
                pauli_string, coeff = get_pauli_string(row_bin, col_bin, term_bin)
                post_rotation = get_post_rotation(pauli_string)
                counts = post_rotation_data[post_rotation]
                partial_sum += coeff*self.compute_pauli_expect_val(pauli_string, counts)
            value += partial_sum*self.integrals[2][i]
        return value
    
    def run(self, method='Nelder-Mead', inital_parameters=[], max_iter=1000, tol=1e-5, verbose=False, filename=None):
        if inital_parameters==[]:
            self.parameters = [rnd.uniform(0, 2*np.pi) for i in range(self.num_params)]
        else:
            if len(inital_parameters) != self.num_params:
                print("ERROR: {} parameters are insufficient for a {} qubits RyRz network of depth {}".format(len(inital_parameters), self.N, self.depth))
                exit()
            self.parameters = inital_parameters
        if(filename != None):
            datafile = open(filename, 'w')
        
        def target_function(params):
            value = self.compute_expectation_value(params)
            self.opt_history.append(value.real)
            self.n_iter += 1
            if verbose==True:
                print("{0:4d}\t{1:3.6f}".format(self.n_iter, value.real))
            if filename != None:
                datafile.write("{}\t{}\n".format(value.real, value.imag))
            return value.real

        if method == 'Nelder-Mead':
            options = {'adaptive':True, 'maxiter':max_iter, 'fatol':tol}
            opt_results = opt.minimize(target_function, self.parameters, method='Nelder-Mead', options=options)
        elif method == 'COBYLA':
            constr = []
            for arg in range(self.num_params):
                lower = 0
                upper = 2*np.pi
                l = {'type': 'ineq', 'fun': lambda x, lb=lower, i=arg: x[i] - lb}
                u = {'type': 'ineq', 'fun': lambda x, ub=upper, i=arg: ub - x[i]}
                constr.append(l)
                constr.append(u)
            options = {'rhobeg':np.pi, 'tol':tol, 'disp':True, 'maxiter':max_iter, 'catol':1e-4}
            opt_results = opt.minimize(target_function, self.parameters, method='COBYLA', constraints=constr, options=options)
        else:
            print("ERROR: {} is not a supported optimization method".format(method))
        print("OPTIMIZATION: {}".format(opt_results.message))
        self.parameters = opt_results.x
        self.expectation_value = self.compute_expectation_value(self.parameters)
        if(filename != None):
            datafile.close()
        return self.expectation_value.real, self.expectation_value.imag
    
    def get_expectation_statistic(self, sample=100, verbose=False, filename=None, ext_params=None):
        self.expectation_statistic = {}
        self.expectation_statistic['sample'] = sample
        data = []
        parameters = ext_params if ext_params != None else self.parameters
        for n in range(sample):
            value = self.compute_expectation_value(parameters)
            if verbose==True:
                print("{0:4d}\t{1:3.6f}\t{2:3.6f}".format(n, value.real, value.imag))
            data.append(value)
        self.expectation_statistic['data'] = data
        if filename != None:
            myfile = open(filename, 'w')
            for element in data:
                myfile.write("{}\t{}\n".format(element.real, element.imag))
            myfile.close()
        my_sum = 0
        for element in data:
            my_sum += element
        self.expectation_value = my_sum/sample
        self.expectation_statistic['mean'] = self.expectation_value
        my_sum = 0
        for element in data:
            my_sum += (element-self.expectation_value)**2
        self.expectation_statistic['std_dev'] = np.sqrt(my_sum/sample)
        return self.expectation_statistic
