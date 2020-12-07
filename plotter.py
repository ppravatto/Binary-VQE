import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from distutils.spawn import find_executable

if find_executable('latex'):
    plt.rc('font', **{'family':'serif', 'serif':['Computer Modern Roman'], 'size':14})
    plt.rc('text', usetex=True)

def unitary_height_gaussian(x, c, w):
    return np.exp(-(x-c)**2/(2*w**2))

def plot_convergence(filename, target=None, save_plot=True, path=None, show=True):
    if show == False:
        matplotlib.use('Agg')
    myfile = open(filename, 'r')
    data = [[],[],[]]
    for index, line in enumerate(myfile):
        element = line.split()
        data[0].append(index)
        data[1].append(float(element[0]))
        data[2].append(float(element[1]))
    myfile.close()
    plt.plot(data[0], data[1], linewidth=1.5)
    if target != None:
        line = [target for i in data[0]]
        plt.plot(data[0], line, color='red', linewidth=0.8)
    plt.grid(which="major", color='#E0E0E0')
    plt.xlabel("Iterations")
    plt.ylabel("Expectation value")
    plt.tight_layout()
    if save_plot == True:
        fig_name = "convergence.png" if path == None else path
        plt.savefig(fig_name, dpi=600)
    if show == True:
        plt.show()

def plot_vqe_statistic(filename, bins=100, gauss=False, target=None, save_plot=True, path=None, show=True):
    if show == False:
        matplotlib.use('Agg')
    myfile = open(filename, 'r')
    data = [[],[]]
    for line in myfile:
        if "#" in line:
            continue
        data[0].append(float((line.split())[0]))
        data[1].append(float((line.split())[1]))
    myfile.close()
    hist_data = plt.hist(data[0], bins=bins, orientation='horizontal')
    if gauss == True:
        mean = 0
        std_dev = 0
        for element in data[0]:
            mean += element
        mean = mean/len(data[0])
        for element in data[0]:
            std_dev += (element-mean)**2
        std_dev = np.sqrt(std_dev/len(data[0]))
        x, y = [], []
        for i in range(1000):
            z = -4*std_dev + 8*i*std_dev/1000 + mean
            x.append(z)
            y.append(max(hist_data[0])*unitary_height_gaussian(z, mean, std_dev))
        plt.plot(y, x)
    if target != 0:
        plt.plot([0, max(hist_data[0])], [target, target], color='red', linestyle='--')
    plt.xlabel("Number of sample")
    plt.ylabel("Expectation value")
    if save_plot == True:
        fig_name = "sampling_noise.png" if path == None else path
        plt.savefig(fig_name, dpi=600)
    if show == True:
        plt.show()


def plot_vqe_statistic_comparison(data, xlabel=None, ylabel=None, path=None, save=True, marker=None):
    plt.plot(data[0], data[1], c='#AE0096')
    for i, mylist in enumerate(data[2]):
        x, y = [],[]
        for value in mylist:
            x.append(data[0][i])
            y.append(value)
        plt.scatter(x, y, alpha=0.02, c='#0072BD', edgecolor='none')
    if marker!=None:
        plt.scatter(data[0], marker, marker="_", c='#E8971E', edgecolor='#E8971E')
    if xlabel != None:
        plt.xlabel(xlabel)
    if ylabel != None:
        plt.ylabel(ylabel)
    filename = "VQE_scan_comp.png"
    if path!=None:
        filename = path + "/" + filename
    if save==True:
        plt.savefig(filename, dpi=600)
    plt.show()
