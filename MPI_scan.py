import binary_vqe, user_interface, incremental
import plotter as myplt
import numpy as np
import time, os, sys, shutil
from datetime import datetime
from mpi4py import MPI

def MPI_VQE_run_function(config_data, rank, ordering=None, incremental_index=None, incr_scratch=None):
    
    if config_data["incremental"] == True and (incremental_index==None or incr_scratch==None):
        print("ERROR: incremental configuration encountered in 'MPI_VQE_run_function'")
        exit()

    offset = None if config_data["auto_flag"] == False else False
    VQE_matrix_filename = config_data["VQE_file"] if config_data["incremental"] == False else config_data["VQE_file"] + "_{}Q.txt".format(incremental_index)

    vqe = binary_vqe.BIN_VQE(
        VQE_matrix_filename,
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
    if config_data["incremental"] == True:
        if incremental_index != 2:
            RyRz_incr_filename = incr_scratch + "RyRz_incremental_{}Q.txt".format(incremental_index-1)
            RyRz_params = user_interface.load_array_for_file(RyRz_incr_filename)
    elif config_data["RyRz_param_file"] != None:
        RyRz_params = user_interface.load_array_for_file(config_data["RyRz_param_file"])
    
    iteration_file = config_data["iteration_folder"] + "/" + config_data["contracted_name"] + "_rank{}_{}".format(rank, VQE_stat_iter)
    iteration_file += "_iteration.txt" if config_data["incremental"] == False else "_{}Q_iteration.txt".format(incremental_index)
    real, imag = vqe.run(
        method=config_data["VQE_optimizer"],
        max_iter=config_data["VQE_max_iter"],
        tol=config_data["VQE_tol"],
        filename=iteration_file,
        verbose=False,
        optimizer_options=config_data["opt_options"],
        inital_parameters=RyRz_params
        )
    
    optimized_parameters = vqe.parameters
    if config_data["incremental"] == True:
        RyRz_incr_filename = incr_scratch + "RyRz_incremental_{}Q.txt".format(incremental_index)
        with open(RyRz_incr_filename, 'w') as ryrz_file:
            for element in optimized_parameters:
                ryrz_file.write("{}\n".format(element))
            for i in range(4):
                ryrz_file.write("{}\n".format(0.))

    return real, imag

    

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

if rank == 0:
    data_buffer = []
    config_data = None
    if len(sys.argv)==1:
        print("\nSTARTING MPI CALCULATION:")
        input_buffer = input("\nDo you want to perform an incremental VQE calculation (Y/N)? ")
        if input_buffer.upper() == "Y":
            incr_flag = True
        else:
            incr_flag = False
        config_data = user_interface.get_user_input(VQE_statistic_flag=True, incremental_flag=incr_flag)
    else:
        if os.path.isfile(sys.argv[1])==True:
            config_data = user_interface.load_dictionary_from_file(sys.argv[1])
        else:
            print("""ERROR: input file ("{}") not found""".format(sys.argv[1]))
            exit()

    config_data = user_interface.initialize_execution(config_data)

    workload = []
    extra_work = int(config_data["VQE_num_samples"]%size)
    norm_work = int((config_data["VQE_num_samples"] - extra_work)/size)
    for i in range(size):
        workload.append(norm_work)
    for i in range(extra_work):
        workload[i] += 1
    config_data["workload"] = workload
    if config_data["incremental"] == True:
        os.mkdir(config_data["iteration_folder"] + "/incremental_data")
    start_time = time.time()

else:
    config_data = None

config_data = comm.bcast(config_data, root=0)    

if config_data["incremental"] == True:
    local_data = [[[],[]] for i in range(2, config_data["Inc_max_Q"]+1)]
else:
    local_data = [[],[]]

config_data = comm.bcast(config_data, root=0)    

myload = (config_data["workload"])[rank]
for VQE_stat_iter in range(myload):

    if config_data["incremental"] == True:
        ordering_list = incremental.get_ordering_lists(config_data["Inc_basis_root"], config_data["Inc_max_Q"])
        scratch_folder = config_data["iteration_folder"] + "/incremental_data/RyRz_{}_{}/".format(rank, VQE_stat_iter)
        os.mkdir(scratch_folder)
        for incr_idx in range(2, config_data["Inc_max_Q"]+1):
            ordering = ordering_list[incr_idx-2]
            out_real, out_imag = MPI_VQE_run_function(config_data, rank, ordering=ordering, incremental_index=incr_idx, incr_scratch=scratch_folder)
            local_data[incr_idx-2][0].append(out_real)
            local_data[incr_idx-2][1].append(out_imag)
    else:
        out_real, out_imag = MPI_VQE_run_function(config_data, rank)
        local_data[0].append(out_real)
        local_data[1].append(out_imag)

data_buffer = comm.gather(local_data, root=0)

if rank==0:

    runtime = time.time() - start_time
    config_data["runtime"] = runtime

    for inc_idx in range(2, config_data["Inc_max_Q"]+1):
        user_interface.finalize_execution(config_data, incremental_index=inc_idx)
    
    if config_data["incremental"] == True:
        average = [[0., 0.] for i in range(2, config_data["Inc_max_Q"]+1)]
        local_data = [[[],[]] for i in range(2, config_data["Inc_max_Q"]+1)]
    else:
        average = [0., 0.]
        local_data = [[],[]]

    for data_list in data_buffer:
        if config_data["incremental"] == True:
            for i in range(2, config_data["Inc_max_Q"]+1):
                for j in range(len(data_list[i-2][0])):
                    local_data[i-2][0].append(data_list[i-2][0][j])
                    local_data[i-2][1].append(data_list[i-2][1][j])
                    average[i-2][0] += data_list[i-2][0][j]
                    average[i-2][1] += data_list[i-2][1][j]
        else:
            for i in range(len(data_list[0])):
                local_data[0].append(data_list[0][i])
                local_data[1].append(data_list[1][i])
                average[0] += data_list[0][i]
                average[1] += data_list[1][i]
    
    if config_data["incremental"] == True:
        for i in range(2, config_data["Inc_max_Q"]+1):
            average[i-2][0] /= len(local_data[i-2][0])
            average[i-2][1] /= len(local_data[i-2][1])
    else:
        average[0] /= len(local_data[0])
        average[1] /= len(local_data[1])
    
    show_flag = True if config_data["auto_flag"]==False else False
    if config_data["incremental"] == True:
        for i in range(2, config_data["Inc_max_Q"]+1):
            data_filename = config_data["base_folder"] + "/VQE_samples_{}Q.txt".format(i)
            with open(data_filename, 'w') as data_file:
                for row in range(len(local_data[0][0])):
                    data_file.write("{}\t{}\t".format(local_data[i-2][0][row], local_data[i-2][1][row]))
                    data_file.write("\n")
            picture_name = config_data["base_folder"] + "/" + config_data["contracted_name"] + "_VQE_scan_{}Q.png".format(i)
            myplt.plot_vqe_statistic(
                data_filename,
                bins=config_data["VQE_num_bins"],
                gauss=False,
                target=config_data["target"],
                path=picture_name,
                show=show_flag,
                clear=True
                )
    else:
        data_filename = config_data["base_folder"] + "/VQE_samples.txt"
        with open(data_filename, 'w') as data_file:
            for row in range(len(local_data[0])):
                data_file.write("{}\t{}\n".format(local_data[0][row], local_data[1][row]))
        picture_name = config_data["base_folder"] + "/" + config_data["contracted_name"] + "_VQE_scan.png"
        myplt.plot_vqe_statistic(
            data_filename,
            bins=config_data["VQE_num_bins"],
            gauss=False,
            target=config_data["target"],
            path=picture_name,
            show=show_flag
            )

    config_data["average_VQE_stat"] = average
    real = average[0] if config_data["incremental"] == False else average[-1][0]
    imag = average[1] if config_data["incremental"] == False else average[-1][1]
    
    user_interface.save_report(config_data, real, imag)
    
    if config_data["auto_flag"] == True:
        if config_data["temp_file"] == True:
            temp_folder = ".VQE_temp"
            if os.path.isdir(temp_folder):
                shutil.rmtree(temp_folder)
            os.mkdir(temp_folder)
            user_interface.save_report(config_data, real, imag, path=temp_folder)
            temp_picture_name = temp_folder + "/" + config_data["contracted_name"] + "_VQE_scan.png"
            shutil.copyfile(picture_name, temp_picture_name)
    
    print("Average expectation value:")
    print("Real part: {}".format(real))
    print("Immaginary part: {}".format(imag))
    print("-------------------------------------------------------------")
    print("NORMAL TERMINATION: runtime: {}s".format(runtime))
