from itertools import permutations
import os, random, math, time, binary_vqe, user_interface
from mpi4py import MPI

def generate_permutation_lists(M, length):
    permutations = []
    if length > math.factorial(M):
        print("ERROR: cannot generate more permutations of the list length factorial")
        exit()
    while len(permutations) < length:
        permutation = []
        label_list = [i for i in range(M)]
        for curr_lenght in range(M-1, -1, -1):
            i = random.randint(0, curr_lenght)
            permutation.append(label_list[i])
            label_list.pop(i)
        if permutation not in permutations:
            permutations.append(permutation)
    return permutations


def MPI_VQE_run_function(config_data, rank, ord_iter, iter, ordering):
    
    offset = None if config_data["auto_flag"] == False else False
    
    vqe = binary_vqe.BIN_VQE(
        config_data["VQE_file"],
        ordering=ordering,
        method=config_data["VQE_exp_val_method"],
        entanglement=config_data["VQE_entanglement"],
        verbose=False,
        depth=config_data["VQE_depth"],
        threshold=config_data["VQE_threshold"],
        offset=offset
        )
    
    if rank==0 and "N" not in config_data.keys():
        config_data["N"] = vqe.N
        config_data["M"] = vqe.M
        config_data["num_integrals"] = len(vqe.integrals[2])
        config_data["num_post_rot"] = len(vqe.post_rot)

    vqe.configure_backend(
        config_data["VQE_backend"],
        num_shots=config_data["VQE_shots"],
        simulator_options=config_data["simulator_options"]
        )
    if config_data["VQE_quantum_device"] != None:
        vqe.import_noise_model(
            config_data["VQE_quantum_device"],
            error_mitigation=config_data["VQE_error_mitigation"],
            online=config_data["online"]
            )
    vqe.set_q_instance()
    
    RyRz_params = []
    if config_data["RyRz_param_file"] != None:
        RyRz_params = user_interface.load_array_for_file(config_data["RyRz_param_file"])
    
    iteration_file = config_data["iteration_folder"] + "/" + config_data["contracted_name"] + "_rank{}_{}_{}.txt".format(rank, ord_iter, iter)
    real, imag = vqe.run(
        method=config_data["VQE_optimizer"],
        max_iter=config_data["VQE_max_iter"],
        tol=config_data["VQE_tol"],
        filename=iteration_file,
        verbose=False,
        optimizer_options=config_data["opt_options"],
        inital_parameters=RyRz_params
        )
    
    return real, imag


comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

if rank == 0:

    os.system('cls' if os.name == 'nt' else 'clear')
    print('''-------------------------------------------------------------
                BINARY VQE - PERMUTATION
-------------------------------------------------------------
''')

    n_qubits = int(input("Select the number of qubits: "))
    n_perm = int(input("Select the number of ordering permutations: "))

    config_data = user_interface.get_user_input(VQE_statistic_flag=True)
    config_data = user_interface.initialize_execution(config_data)
    config_data["permutations"] = generate_permutation_lists(2**n_qubits, n_perm)

    workload = []
    extra_work = int(n_perm%size)
    norm_work = int((n_perm - extra_work)/size)
    for i in range(size):
        workload.append(norm_work)
    for i in range(extra_work):
        workload[i] += 1
    config_data["workload"] = workload
    
    start_time = time.time()

else:
    config_data = None

config_data = comm.bcast(config_data, root=0) 

local_data = []

start_load_idx = 0
myload = config_data["workload"][rank]
for i in range(rank):
    start_load_idx += config_data["workload"][i]

for ord_idx in range(myload):
    ordering = config_data["permutations"][start_load_idx + ord_idx]
    current = {"ordering": ordering}
    av_real, av_imag = 0, 0
    real, imag = [], []
    for samp_idx in range(config_data["VQE_num_samples"]):
        Re, Im = MPI_VQE_run_function(config_data, rank, ord_idx, samp_idx, ordering)
        real.append(Re)
        imag.append(Im)
        av_real += Re/config_data["VQE_num_samples"]
        av_imag += Im/config_data["VQE_num_samples"]
    current["real"] = real
    current["imag"] = imag
    current["average_real"] = av_real
    current["average_imag"] = av_imag
    local_data.append(current)

data_buffer = comm.gather(local_data, root=0)

if rank==0:

    runtime = time.time() - start_time

    data = []
    for list in data_buffer:
        for element in list:
            data.append(element)
    
    stat_folder = config_data["base_folder"] + "/statistic"
    os.mkdir(stat_folder)
    for i, dict in enumerate(data):
        filename = stat_folder + "/stat_{}.txt".format(i)
        with open(filename, 'w') as file:
            file.write("Ordering: {}\n".format(dict["ordering"]))
            file.write("Average Real: {}\n".format(dict["average_real"]))
            file.write("Average Imag: {}\n\n".format(dict["average_imag"]))
            for j in range(len(dict["real"])):
                file.write("{}\t{}\n".format(dict["real"][j], dict["imag"][j]))

    for dict in data:
        print("{}\t{}\t{}\t{}".format(dict["ordering"], dict["average_real"], dict["average_imag"], min(dict["real"])))
