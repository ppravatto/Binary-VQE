import user_interface
import time, os
from datetime import datetime

os.system('cls' if os.name == 'nt' else 'clear')

print('''-------------------------------------------------------------
                 BINARY VQE - INPUT GENERATOR
-------------------------------------------------------------
    ''')

input_type = input('''Select the type of input file to generate:

  A) Statistical sampling of different VQE cofigurations
  B) Regular VQE with/without converged statistic sampling

Selection (default: A): ''')
input_type = True if input_type.upper() != "B" else False
print("")

filename = input("Select input filename (default: input.txt): ")
filename = "input.txt" if filename=="" else str(filename)

config_data = user_interface.get_user_input(VQE_statistic_flag=input_type)
config_data["auto_flag"]=True
user_interface.save_dictionary_to_file(config_data, filename)

print("-------------------------------------------------------------\n")
