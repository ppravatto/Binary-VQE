import binary_vqe, user_interface
import plotter as myplt
import numpy as np
import time, os, sys
from datetime import datetime

config_data = None
if len(sys.argv)==1:
    config_data = user_interface.get_user_input()
else:
    if os.path.isfile(sys.argv[1])==True:
        config_data = user_interface.load_dictionary_from_file(sys.argv[1])
    else:
        print("""ERROR: input file ("{}") not found""".format(sys.argv[1]))
        exit()

config_data = user_interface.initialize_execution(config_data)

while True:
    start_time = time.time()
    
    offset = None if config_data["auto_flag"] == False else False
    vqe = binary_vqe.BIN_VQE(
        config_data["VQE_file"],
        method=config_data["VQE_exp_val_method"],
        verbose=True,
        depth=config_data["VQE_depth"],
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
            error_mitigation=config_data["VQE_error_mitigation"]
            )
    iteration_file = config_data["iteration_folder"] + "/" + config_data["contracted_name"] + "_iteration.txt"
    real, immaginary = vqe.run(
        method=config_data["VQE_optimizer"],
        max_iter=config_data["VQE_max_iter"],
        tol=config_data["VQE_tol"],
        filename=iteration_file,
        verbose=True,
        optimizer_options=config_data["opt_options"]
        )
    print("Expectation value: {} + {}j".format(real, immaginary))
    print("-------------------------------------------------------------")
    vqe_runtime = time.time() - start_time
    print("OPTIMIZATION TERMINATED - Runtime: {}s".format(vqe_runtime))
    config_data["runtime"] = vqe_runtime

    user_interface.save_report(config_data, real, immaginary)

    #Plot convergence trend
    show_flag = True if config_data["auto_flag"]==False else False
    picture_name = config_data["base_folder"] + "/" + config_data["contracted_name"] + "_convergence.png"
    myplt.plot_convergence(iteration_file, config_data["target"], path=picture_name, show=show_flag)

    aux_statistic_flag = "N"
    if config_data["statistic_flag"] == True and config_data["auto_flag"] == False:
        aux_statistic_flag = input("Would you like to skip the statistic accumulation for this run (y/n)? ")
    
    if config_data["statistic_flag"] == True and aux_statistic_flag.upper() != "Y":
        #Collect sampling noise using current parameters
        statistic_file = config_data["base_folder"] + "/" + config_data["contracted_name"] + "_noise.txt"
        stats = vqe.get_expectation_statistic(sample=config_data["num_samples"], filename=statistic_file, verbose=True)
        print("Mean value:")
        print(stats['mean'].real)
        print(stats['mean'].imag)
        print("Standard Deviation:")
        print(stats['std_dev'].real)
        print(stats['std_dev'].imag)

        #Plot sampling noide graph with gaussian approximation
        picture_name = config_data["base_folder"] + "/" + config_data["contracted_name"] + "_noise.png"
        myplt.plot_vqe_statistic(statistic_file, bins=config_data["num_bins"], gauss=True, target=config_data["target"], path=picture_name, show=show_flag)

    print("-------------------------------------------------------------")
    print("NORMAL TERMINATION")

    if config_data["auto_flag"]==False:
        restart = input("Would you like to run another calculation with the same parameters (y/n)? ")
        if restart.upper() != "Y":
            break
    else:
        break