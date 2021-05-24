import user_interface
import time, os
import random as rnd
import numpy as np
from datetime import datetime

os.system('cls' if os.name == 'nt' else 'clear')

print('''-------------------------------------------------------------
                 BINARY VQE - INPUT GENERATOR
-------------------------------------------------------------
    ''')

input_buffer = input('''Select the type of input file to generate:

  A) Statistical sampling of different VQE cofigurations
  B) Regular VQE with/without converged statistic sampling
  C) Generate a RyRz parameter file
  D) Single incremental VQE run

Selection (default: A): ''')
print("")

if input_buffer.upper() == "C":
  qubits = int(input("-> Select the number of qubits: "))
  depth = int(input("-> Select the RyRz depth: "))
  filename = input("-> Select a name for the parameter file (default: RyRz_params.txt): ")
  filename = "RyRz_params.txt" if filename == "" else filename
  
  RyRz_file = open(filename, 'w')
  for i in range(2*(1+depth)*qubits):
    RyRz_file.write("{}\n".format(rnd.uniform(0, 2*np.pi)))
  RyRz_file.close()

else:
  if input_buffer.upper() == "A":
    VQE_stat = True
    Incr_flag = False
  elif input_buffer.upper() == "B":
    VQE_stat = False
    Incr_flag = False
  elif input_buffer.upper() == "D":
    VQE_stat = False
    Incr_flag = True

  filename = input("Select input filename (default: input.txt): ")
  filename = "input.txt" if filename=="" else str(filename)

  config_data = user_interface.get_user_input(VQE_statistic_flag=VQE_stat, auto_flag=True, incremental_flag=Incr_flag)

  print("Do you want to copy the temporary data to temporary folder (y/n)?")
  buffer = input("Selection (default: y): ")
  config_data["temp_file"] = True if buffer.upper() != "N" else False

  user_interface.save_dictionary_to_file(config_data, filename)

print("-------------------------------------------------------------\n")
