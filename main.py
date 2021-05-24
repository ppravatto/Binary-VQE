import binary_vqe, user_interface, incremental
import plotter as myplt
import numpy as np
import time, os, sys, shutil
from datetime import datetime

def VQE_run_function(config_data, ordering=None, incremental_index=None):

    start_time = time.time()
    offset = None if config_data["auto_flag"] == False else False

    VQE_matrix_filename = config_data["VQE_file"] if config_data["incremental"] == False else config_data["VQE_file"] + "_{}Q.txt".format(incremental_index)

    vqe = binary_vqe.BIN_VQE(
        VQE_matrix_filename,
        ordering=ordering,
        method=config_data["VQE_exp_val_method"],
        entanglement=config_data["VQE_entanglement"],
        verbose=True,
        depth=config_data["VQE_depth"],
        threshold=config_data["VQE_threshold"],
        offset=offset
        )
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
    iteration_file = config_data["iteration_folder"] + "/" + config_data["contracted_name"] + "_iteration.txt"
    
    RyRz_params = []
    if config_data["incremental"] == True:
        if incremental_index != 2:
            RyRz_incr_filename = "RyRz_incremental_{}Q.txt".format(incremental_index-1)
            RyRz_params = user_interface.load_array_for_file(RyRz_incr_filename)
    elif config_data["RyRz_param_file"] != None:
        RyRz_params = user_interface.load_array_for_file(config_data["RyRz_param_file"])
    
    show_flag = True if config_data["auto_flag"]==False else False
    
    if config_data["VQE_opt_skip"] == False:
        real, immaginary = vqe.run(
            method=config_data["VQE_optimizer"],
            max_iter=config_data["VQE_max_iter"],
            tol=config_data["VQE_tol"],
            filename=iteration_file,
            verbose=True,
            optimizer_options=config_data["opt_options"],
            inital_parameters=RyRz_params
            )
        print("Expectation value: {} + {}j".format(real, immaginary))
        print("-------------------------------------------------------------")
        vqe_runtime = time.time() - start_time
        print("OPTIMIZATION TERMINATED - Runtime: {}s".format(vqe_runtime))
        config_data["runtime"] = vqe_runtime

        user_interface.save_report(config_data, real, immaginary)
        
        optimized_parameters = vqe.parameters
        if config_data["incremental"] == True:
            RyRz_incr_filename = "RyRz_incremental_{}Q.txt".format(incremental_index)
            with open(RyRz_incr_filename, 'w') as ryrz_file:
                for element in optimized_parameters:
                    ryrz_file.write("{}\n".format(element))
                for i in range(4):
                    ryrz_file.write("{}\n".format(0.))

        opt_param_file = open(config_data["iteration_folder"] + "/" + "VQE_opt_params.txt", 'w')
        for element in optimized_parameters:
            opt_param_file.write("{}\n".format(element))
        opt_param_file.close()

        #Plot convergence trend
        conv_picture_name = config_data["base_folder"] + "/" + config_data["contracted_name"] + "_convergence.png"
        myplt.plot_convergence(iteration_file, config_data["target"], path=conv_picture_name, show=show_flag)

    if config_data["VQE_backend"] != "qasm_simulator" and config_data["VQE_backend"] != "statevector_simulator":
        expect_val = vqe.compute_expectation_value(RyRz_params)
        print("Expectation value: {} + {}j".format(expect_val.real, expect_val.imag))
        print("-------------------------------------------------------------")
        vqe_runtime = time.time() - start_time
        print("TERMINATED - Runtime: {}s".format(vqe_runtime))
        config_data["runtime"] = vqe_runtime
        user_interface.save_report(config_data, expect_val.real, expect_val.imag)
    
    aux_statistic_flag = "N"
    if config_data["statistic_flag"] == True and config_data["auto_flag"] == False and config_data["VQE_opt_skip"] == False:
        aux_statistic_flag = input("Would you like to skip the statistic accumulation for this run (y/n)? ")
    
    if config_data["statistic_flag"] == True and aux_statistic_flag.upper() != "Y":
        #Collect sampling noise using current parameters
        statistic_file = config_data["base_folder"] + "/" + config_data["contracted_name"] + "_noise.txt"
        ext_params = None if config_data["VQE_opt_skip"] == False else RyRz_params
        if config_data["VQE_opt_skip"] == True:
            print("Initial parameters considered:")
            print(ext_params)
            print("")
        stats = vqe.get_expectation_statistic(sample=config_data["num_samples"], filename=statistic_file, verbose=True, ext_params=ext_params)
        print("Mean value:")
        print(stats['mean'].real)
        print(stats['mean'].imag)
        print("Standard Deviation:")
        print(stats['std_dev'].real)
        print(stats['std_dev'].imag)

        #Plot sampling noide graph with gaussian approximation
        noise_picture_name = config_data["base_folder"] + "/" + config_data["contracted_name"] + "_noise.png"
        myplt.plot_vqe_statistic(statistic_file, bins=config_data["num_bins"], gauss=True, target=config_data["target"], path=noise_picture_name, show=show_flag)

    print("-------------------------------------------------------------")
    print("NORMAL TERMINATION")

    user_interface.finalize_execution(config_data, incremental_index=incremental_index)

    if config_data["auto_flag"] == True:
        if config_data["temp_file"] == True:
            temp_folder = ".VQE_temp"
            if os.path.isdir(temp_folder):
                shutil.rmtree(temp_folder)
            os.mkdir(temp_folder)
            user_interface.save_report(config_data, real, immaginary, path=".VQE_temp")
            temp_picture_name = temp_folder + "/" + config_data["contracted_name"] + "_convergence.png"
            shutil.copyfile(conv_picture_name, temp_picture_name)
            if config_data["statistic_flag"] == True and aux_statistic_flag.upper() != "Y":
                temp_picture_name = temp_folder + "/" + config_data["contracted_name"] + "_noise.png"
                shutil.copyfile(noise_picture_name, temp_picture_name)



config_data = None
if len(sys.argv)==1:
    input_buffer = input("Do you want to perform an incremental VQE calculation (Y/N)?")
    if input_buffer.upper() == "Y":
        incr_flag = True
    else:
        incr_flag = False
    config_data = user_interface.get_user_input(incremental_flag=incr_flag)
else:
    if os.path.isfile(sys.argv[1])==True:
        config_data = user_interface.load_dictionary_from_file(sys.argv[1])
    else:
        print("""ERROR: input file ("{}") not found""".format(sys.argv[1]))
        exit()

while True:

    config_data = user_interface.initialize_execution(config_data)

    if config_data["incremental"] == True:
        ordering_list = incremental.get_ordering_lists(config_data["Inc_basis_root"], config_data["Inc_max_Q"])
        for incr_idx in range(2, config_data["Inc_max_Q"]+1):
            oredring = ordering_list[incr_idx-2]
            VQE_run_function(config_data, ordering=oredring, incremental_index=incr_idx)
    else:
        VQE_run_function(config_data)
    
    if config_data["auto_flag"] == True:
        break
    else:
        restart = input("Would you like to run another calculation with the same parameters (y/n)? ")
        if restart.upper() != "Y":
            break