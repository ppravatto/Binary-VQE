import os

def load_composite_basis_set(filename, parity=False):
    basis_set_data = {}
    data_string = []
    if os.path.isfile(filename) == False:
        print("""ERROR: "{}" file not found""".format(filename))
        exit()
    search = "GERADE" if parity==True else "UNGERADE"
    section = False
    with open(filename, 'r') as myfile:
        for line in myfile:
            if search in line:
                section = True
                continue
            elif "#" in line and section == True:
                section = False
                continue
            if section == True:
                data = line.split()
                if "N_dihedral" not in basis_set_data.keys():
                    basis_set_data["N_dihedral"] = (len(data)-1)/2
                data_string.append([i for i in data[1::]])
    basis_set_data["data"] = data_string
    return basis_set_data
                

def get_ordering_lists(root, nmax, parity=False):
    basis_data, ordering = [], []
    for n in range(2, nmax+1):
        filename = root +"_{}Q.txt".format(n)
        data = load_composite_basis_set(filename, parity)
        if basis_data != []:
            if basis_data[-1]["N_dihedral"] != data["N_dihedral"]:
                print("ERROR: mismatch in number of dihedral")
                exit()
        basis_data.append(data)
    for qubit in range(2, nmax+1):
        if qubit==2:
            nth_order = [i for i in range(4)]
        else:
            nth_order = []
            for index in ordering[-1]:
                target = basis_data[qubit-3]["data"][index]
                for i, element in enumerate(basis_data[qubit-2]["data"]):
                    if element == target:
                        nth_order.append(i)
                        break
            for index in range(2**qubit):
                if index not in nth_order:
                    nth_order.append(index)
        #Debug
        if len(nth_order) != 2**qubit:
            print("ALLARME ROSSO")
        ordering.append(nth_order)
    return ordering


