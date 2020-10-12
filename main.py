import binary_vqe, user_interface
import plotter as myplt
import numpy as np
import time, os
from datetime import datetime

config_data = user_interface.get_user_input()

while True:

    start_time = time.time()
    vqe = binary_vqe.BIN_VQE(
        config_data["VQE_file"],
        method=config_data["VQE_exp_val_method"],
        verbose=True,
        depth=config_data["VQE_depth"]
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
    picture_name = config_data["base_folder"] + "/" + config_data["contracted_name"] + "_convergence.png"
    myplt.plot_convergence(iteration_file, config_data["target"], path=picture_name)

    aux_statistic_flag = "N"
    if config_data["statistic_flag"] == True:
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
        myplt.plot_vqe_statistic(statistic_file, bins=config_data["num_bins"], gauss=True, target=config_data["target"], path=picture_name)

    print("-------------------------------------------------------------")
    print("NORMAL TERMINATION")

    restart = input("Would you like to run another calculation with the same parameters (y/n)? ")
    if restart.upper() != "Y":
        break