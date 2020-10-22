# -*- coding: utf-8 -*-

import numpy as np
from qiskit import IBMQ
from qiskit.providers.aer.noise import NoiseModel
import os

### create directory to store noise models ####

## N.B. if a directory named noise_models already exist in the current path, delete it before running this script ##

os.mkdir('noise_models')

current_path = "/Users/castd/Desktop/Smoluchowski_rate_constant_QC/Binary-VQE-adding_noise_offline/Binary-VQE-adding_noise_offline/"

noise_model_directory_path = current_path + "/noise_models/"

### create noise_models ###

devices_to_be_loaded = ['ibmq_santiago',
'ibmq_vigo',
'ibmq_valencia',
'ibmq_16_melbourne',
'ibmq_ourense',
'ibmqx2']

provider = IBMQ.load_account()

for device in devices_to_be_loaded:
    computer_noise = []
    computer = provider.get_backend(device)
    computer_properties = computer.properties()
    coupling_map = computer.configuration().coupling_map
    noise_model = NoiseModel.from_backend(computer_properties)
    computer_noise.append(noise_model)
    computer_noise.append(coupling_map)
    computer_noise.append(computer_properties)
### save noise models ####
    np.save(device, computer_noise, allow_pickle = True)
    os.replace(current_path + device + ".npy", noise_model_directory_path + device + ".npy")




