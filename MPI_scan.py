import binary_vqe, user_interface
import plotter as myplt
import numpy as np
import time, os, sys, shutil
from datetime import datetime
from mpi4py import MPI

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

if rank == 0:
    data_buffer = []
    config_data = None
    if len(sys.argv)==1:
        config_data = user_interface.get_user_input(VQE_statistic_flag=True)
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
    start_time = time.time()
else:
    config_data = None

local_data = [[],[]]
config_data = comm.bcast(config_data, root=0)    

myload = (config_data["workload"])[rank]
for VQE_stat_iter in range(myload):
    offset = None if config_data["auto_flag"] == False else False
    vqe = binary_vqe.BIN_VQE(
        config_data["VQE_file"],
        method=config_data["VQE_exp_val_method"],
        verbose=False,
        depth=config_data["VQE_depth"],
        offset=offset
        )
    if VQE_stat_iter == 0 and rank == 0:
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
            error_mitigation=config_data["VQE_error_mitigation"]
            )
    iteration_file = config_data["iteration_folder"] + "/" + config_data["contracted_name"] + "_rank" + str(rank) + "_" + str(VQE_stat_iter) +  "_iteration.txt"
    real, imag = vqe.run(
        method=config_data["VQE_optimizer"],
        max_iter=config_data["VQE_max_iter"],
        tol=config_data["VQE_tol"],
        filename=iteration_file,
        verbose=False,
        optimizer_options=config_data["opt_options"]
        )
    local_data[0].append(real)
    local_data[1].append(imag)

data_buffer = comm.gather(local_data, root=0)

if rank==0:
    runtime = time.time() - start_time
    config_data["runtime"] = runtime

    real_avg, imag_avg = 0, 0
    local_data = [[],[]]
    for data_list in data_buffer:
        for i, r in enumerate(data_list[0]):
            local_data[0].append(r)
            local_data[1].append(data_list[1][i])
    for r in local_data[0]:
        real_avg += r
    for i in local_data[1]:
        imag_avg += i
    real_avg /= len(local_data[0])
    imag_avg /= len(local_data[0])
    
    data_filename = config_data["base_folder"] + "/VQE_samples.txt"
    data_file = open(data_filename, 'w')
    for i, real in enumerate(local_data[0]):
        imag = local_data[1][i]
        data_file.write("{}\t{}\n".format(real, imag))
    data_file.close()

    user_interface.save_report(config_data, real_avg, imag_avg)

    show_flag = True if config_data["auto_flag"]==False else False
    picture_name = config_data["base_folder"] + "/" + config_data["contracted_name"] + "_VQE_scan.png"
    myplt.plot_vqe_statistic(
        data_filename,
        bins=config_data["VQE_num_bins"],
        gauss=False,
        target=config_data["target"],
        path=picture_name,
        show=show_flag
        )
    
    if config_data["temp_file"] == True:
        temp_folder = ".VQE_temp"
        if os.path.isdir(temp_folder):
            shutil.rmtree(temp_folder)
        os.mkdir(temp_folder)
        user_interface.save_report(config_data, real_avg, imag_avg, path=temp_folder)
        temp_picture_name = temp_folder + "/" + config_data["contracted_name"] + "_VQE_scan.png"
        shutil.copyfile(picture_name, temp_picture_name)

    user_interface.finalize_execution(config_data)
    
    print("Average expectation value:")
    print("Real part: {}".format(real_avg))
    print("Immaginary part: {}".format(imag_avg))
    print("-------------------------------------------------------------")
    print("NORMAL TERMINATION: runtime: {}s".format(runtime))
