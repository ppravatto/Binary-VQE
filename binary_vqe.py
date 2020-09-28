import os
from qiskit import *
from qiskit.aqua.components.optimizers import spsa
import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt
import random as rnd
from qiskit.quantum_info.operators.pauli import Pauli
from qiskit.quantum_info.operators import Operator
from qiskit import Aer
from qiskit.aqua import QuantumInstance
from qiskit.aqua.operators import PauliExpectation, CircuitSampler, StateFn, CircuitStateFn

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

def convert_pauli_string_to_aqua_op(pauli_string):
    pauli_string_list = [element for element in pauli_string]
    pauli_operator = Pauli(label = pauli_string_list)
    return pauli_operator
    
    
def build_hamiltonian_with_aqua(op, coeff, pauli_string):
    op += coeff*convert_pauli_string_to_aqua_op(pauli_string).to_operator()


class BIN_VQE():

    def __init__(self, filename, expectation_value, verbose=False, entanglement="full", depth=1, threshold=0):
        self.expectation_value = None
        self.expectation_statistic = None
        self.n_iter = 0
        self.opt_history = []
        self.state = 0
        self.entanglement = entanglement
        if int(depth) <= 0:
            print("ERROR: the depth of the circuit cannot be {}".format(depth))
            exit()
        self.depth = int(depth)
        if float(threshold) < 0:
            print("ERROR: the matrix element threshold cannot be negative")
            exit()
        self.threshold = float(threshold)
        self.integrals = [[],[],[]]
        if os.path.isfile(filename)==True:
            myfile = open(filename, 'r')
            for row, line in enumerate(myfile):
                myline = line.split()
                if row==0:
                    self.M = len(myline)
                for col, element in enumerate(myline):
                    if np.abs(float(element)) > self.threshold:
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
        self.hamiltonian = Operator(np.zeros((2**(self.N), 2**(self.N))), (2**(self.N-1),2), (2,2**(self.N-1)))
        self.post_rot = []
        for i, row in enumerate(self.integrals[0]):
            col = self.integrals[1][i]
            row_bin = get_bin_list(row, self.N)
            col_bin = get_bin_list(col, self.N)
            for term in range(2**self.N):
                term_bin = get_bin_list(term, self.N)
                pauli_string, coeff = get_pauli_string(row_bin, col_bin, term_bin)
                build_hamiltonian_with_aqua(self.hamiltonian, coeff, pauli_string)
                search_string = get_post_rotation(pauli_string)
                if self.post_rot.count(search_string) == 0:
                    self.post_rot.append(search_string)
        self.hamiltonian.data = np.multiply(self.hamiltonian.data, self.integrals[2])  ### N.B. Qua al posto di self.integrals[2] c'è bisogno di tutti gli integrali (anche i non nulli)
        self.backend_name = 'qasm_simulator'
        self.backend = Aer.get_backend('qasm_simulator')
        self.shots = 1024
        self.simulator_options = {"method": "automatic"}
        if verbose==True:
            print("VQE CLASS INITIALIZATION:")
            print(" -> Total number of basis functions: {}".format(self.M))
            print(" ---> Required number of Qubits: {}".format(self.N))
            print(" -> Non-zero matrix elements: {} of {}".format(len(self.integrals[2]), self.M**2))
            print(" ---> Matrix element threshold: {}".format(self.threshold))
            print(" -> Total number of post rotations: {} of {}".format(len(self.post_rot), 3**self.N))
            print(" -> Total number of variational prameters: {}".format(self.num_params))
            print("")
    
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
    
    def measure(self, post_rotation, measure=True):
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
        if measure == True:
            for qubit in self.qubits:
                qc.measure(qubit, qubit)
        return qc
    
    def configure_backend(self, backend_name='qasm_simulator', num_shots=1024, simulator_options=None):
        self.backend = Aer.get_backend(backend_name)
        self.backend_name = backend_name
        if backend_name != 'statevector_simulator':
            self.shots = num_shots
        else:
            self.shots = 1
        if simulator_options != None:
            self.simulator_options = simulator_options

    #Old function to run a single post rotation circuit (not used in VQE run)
    def run_circuit(self, post_rotation, parameters):
        qc = self.initialize_circuit()
        qc += self.ryrz(parameters)
        if self.backend_name == 'qasm_simulator':
            qc += self.measure(post_rotation, measure=True)
            job = execute(qc, self.backend, shots=self.shots, backend_options=self.simulator_options)
            results = job.result()
            counts = results.get_counts()
        elif self.backend_name == 'statevector_simulator':
            qc += self.measure(post_rotation, measure=False)
            job = execute(qc, self.backend, backend_options=self.simulator_options)
            results = job.result().get_statevector(qc)
            sqmod_results = [np.abs(x)**2 for x in results]
            counts = {}
            for i, x in enumerate(sqmod_results):
                buffer = get_bin_list(i, self.N, invert=True)
                label = ""
                for char in buffer:
                    label += str(char)
                counts[label] = x
        else:
            print("ERROR: Invalid backend ({})\n".format(self.backend_name))
            exit()
        return counts
    
    def get_circuit_no_measurement(self, parameters):
        qc = self.initialize_circuit()
        qc += self.ryrz(parameters)
        return qc
    
    def get_circuit(self, post_rotation, parameters):
        qc = self.initialize_circuit()
        qc += self.ryrz(parameters)
        if self.backend_name == 'qasm_simulator':
            qc += self.measure(post_rotation, measure=True)
        elif self.backend_name == 'statevector_simulator':
            qc += self.measure(post_rotation, measure=False)
        else:
            print("ERROR: Invalid backend ({})\n".format(self.backend_name))
            exit()
        return qc
    
    def get_post_rotation_data(self, parameters):
        circuit_buffer = []
        for post_rotation in self.post_rot:
            qc = self.get_circuit(post_rotation, parameters)
            circuit_buffer.append(qc)
        post_rotation_data = {}
        if self.backend_name == 'qasm_simulator':
            job = execute(circuit_buffer, self.backend, shots=self.shots, backend_options=self.simulator_options)
            results = job.result()
            counts = results.get_counts()
            for index, post_rotation in enumerate(self.post_rot):
                post_rotation_data[post_rotation] = counts[index]
        elif self.backend_name == 'statevector_simulator':
            job = execute(circuit_buffer, self.backend, backend_options=self.simulator_options)
            job_results = job.result()
            for index, post_rotation in enumerate(self.post_rot):
                result = job_results.results[index].data.statevector
                sqmod_results = [np.abs(x)**2 for x in result]
                counts = {}
                for i, x in enumerate(sqmod_results):
                    buffer = get_bin_list(i, self.N, invert=True)
                    label = ""
                    for char in buffer:
                        label += str(char)
                    counts[label] = x
                post_rotation_data[post_rotation] = counts
        else:
            print("ERROR: Invalid backend ({})\n".format(self.backend_name))
            exit()
        return post_rotation_data

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
        value = 0
        post_rotation_data = self.get_post_rotation_data(parameters)
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
    
    def compute_expectation_value_qiskit(self, params):
        qc = self.get_circuit_no_measurement(params)
        psi = CircuitStateFn(qc)
        q_instance = QuantumInstance(self.backend, shots = self.shots, backend_options = self.simulator_options)
        measurable_expression = StateFn(self.hamiltonian, is_measurement=True).compose(psi)
        expectation = PauliExpectation().convert(measurable_expression)
        sampler = CircuitSampler(q_instance).convert(expectation)
        return sampler.eval().real
    
    def run(self, expectation_value, method='Nelder-Mead', inital_parameters=[], max_iter=1000, tol=1e-5, verbose=False, filename=None, optimizer_options={}):
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
            if expectation_value == "Graph_coloring":
                value = self.compute_expectation_value_qiskit(params)
                self.opt_history.append(value)
                self.n_iter += 1
                if verbose==True:
                    print("{0:4d}\t{1:3.6f}".format(self.n_iter, value))
                if filename != None:
                    datafile.write("{}\t{}\n".format(value, value))
                return value
            else:
                value = self.compute_expectation_value(params)
                self.opt_history.append(value.real)
                self.n_iter += 1
                if verbose==True:
                    print("{0:4d}\t{1:3.6f}".format(self.n_iter, value.real))
                if filename != None:
                    datafile.write("{}\t{}\n".format(value.real, value.imag))
                return value.real

        def get_opt_constraints():
            constraints = []
            for arg in range(self.num_params):
                lower = 0
                upper = 2*np.pi
                l = {'type': 'ineq', 'fun': lambda x, lb=lower, i=arg: x[i] - lb}
                u = {'type': 'ineq', 'fun': lambda x, ub=upper, i=arg: ub - x[i]}
                constraints.append(l)
                constraints.append(u)
            return constraints

        print("OPTIMIZATION STARTED")
        if method == 'Nelder-Mead':
            options = {'adaptive':True, 'maxiter':max_iter, 'fatol':tol}
            opt_results = opt.minimize(target_function, self.parameters, method='Nelder-Mead', options=options)
        elif method == 'COBYLA':
            constr = get_opt_constraints()
            options = {'rhobeg':np.pi, 'tol':tol, 'disp':True, 'maxiter':max_iter, 'catol':1e-4}
            opt_results = opt.minimize(target_function, self.parameters, method='COBYLA', constraints=constr, options=options)
        elif method == 'SLSQP':
            constr = get_opt_constraints()
            options = {'ftol':tol, 'disp':True, 'maxiter':max_iter}
            opt_results = opt.minimize(target_function, self.parameters, method='SLSQP', constraints=constr, options=options)
        elif method == 'SPSA':
            default_spsa_c = [0.6283185307179586, 0.1, 0.602, 0.101, 0]
            _c = []
            for i in range(5):
                label = "c" + str(i)
                _c.append(optimizer_options[label] if label in optimizer_options else default_spsa_c[i])
            print("-> SPSA optimizer coefficients:", _c)
            optimizer = spsa.SPSA(max_trials=max_iter, c0=_c[0], c1=_c[1], c2=_c[2], c3=_c[3], c4=_c[4])
            bounds = [(0, 2*np.pi) for i in range(self.num_params)]
            opt_results, final_expectation, _dummy = optimizer.optimize(self.num_params, target_function, variable_bounds=bounds, initial_point=self.parameters)
        else:
            print("ERROR: {} is not a supported optimization method".format(method))
        if method != 'SPSA':
            print("OPTIMIZATION: {}".format(opt_results.message))
        else:
            print("OPTIMIZATION ENDED")
        self.parameters = opt_results.x if method != 'SPSA' else opt_results
        if expectation_value == "Graph_coloring":
            self.expectation_value = self.compute_expectation_value_qiskit(self.parameters)
        else:
            self.expectation_value = self.compute_expectation_value(self.parameters)
        if(filename != None):
            datafile.close()
        return self.expectation_value.real, self.expectation_value.imag
    
    def get_expectation_statistic(self, expectation_value, sample=100, verbose=False, filename=None, ext_params=None):
        self.expectation_statistic = {}
        self.expectation_statistic['sample'] = sample
        data = []
        parameters = ext_params if ext_params != None else self.parameters
        for n in range(sample):
            if expectation_value == "Graph_coloring":
                value = self.compute_expectation_value_qiskit(self.parameters)
            else:
                value = self.compute_expectation_value(self.parameters)
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
