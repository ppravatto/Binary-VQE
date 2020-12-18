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

class Plot_VQE_stats():
    def __init__(self, bins=100, alpha=1, gauss=False, target=None, save_plot=True, path=None, show=True):
        self.bins=bins
        self.alpha=alpha
        self.gauss=gauss
        self.target=target
        self.save_plot=save_plot
        self.path=path
        self.show=show
        self.filenames=[]
        self.labels=[]
        self.legend=False
    
    def add_datafile(self, filename, label=None):
        self.filenames.append(filename)
        self.labels.append(label)
        if label != None:
            self.legend = True
    
    def plot(self):
        if self.show == False:
            matplotlib.use('Agg')
        max_hist = 0
        loaded_data = []
        for filename in self.filenames:
            myfile = open(filename, 'r')
            data = [[],[]]
            for line in myfile:
                if "#" in line:
                    continue
                data[0].append(float((line.split())[0]))
                data[1].append(float((line.split())[1]))
            myfile.close()
            loaded_data.append(data)
        
        loaded_data_real = [x[0] for x in loaded_data]
        min_range = min([min(x) for x in loaded_data_real])
        max_range = max([max(x) for x in loaded_data_real])
        hist_range=[min_range, max_range]
        
        for index, dataset in enumerate(loaded_data_real):
            hist_data = plt.hist(dataset, bins=self.bins, alpha=self.alpha ,range=hist_range, orientation='horizontal', label=self.labels[index])
            if max(hist_data[0]) > max_hist:
                max_hist = max(hist_data[0])
            if self.gauss == True:
                mean = 0
                std_dev = 0
                for element in dataset:
                    mean += element
                mean = mean/len(dataset)
                for element in dataset:
                    std_dev += (element-mean)**2
                std_dev = np.sqrt(std_dev/len(dataset))
                x, y = [], []
                for i in range(1000):
                    z = -4*std_dev + 8*i*std_dev/1000 + mean
                    x.append(z)
                    y.append(max(hist_data[0])*unitary_height_gaussian(z, mean, std_dev))
                plt.plot(y, x)
        
        if self.target != 0:
            plt.plot([0, max_hist], [self.target, self.target], color='red', linestyle='--')
        plt.xlabel("Number of samples")
        plt.ylabel("Expectation value")
        if self.legend == True:
            plt.legend(loc=1)
        if self.save_plot == True:
            fig_name = "sampling_noise.png" if self.path == None else self.path
            plt.savefig(fig_name, dpi=600)
        if self.show == True:
            plt.show()
    

def plot_vqe_statistic(filename, bins=100, gauss=False, target=None, save_plot=True, path=None, show=True):
    myplot = Plot_VQE_stats(bins=bins, gauss=gauss, target=target, save_plot=save_plot, path=path, show=show)
    myplot.add_datafile(filename)
    myplot.plot()

def plot_vqe_statistic_comparison(input_data, statevector=None, statevector_type="average", xlabel=None, ylabel=None, path=None, save=True, marker=None):
    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12,6))
    ax_list = {ax1: "normal", ax2: "shifted"}
    for ax, plot_type in ax_list.items():
        data, _marker, sv_average, sv_min = [[],[],[]], [], [], []
        sorted_order = [i for i in input_data[0]]
        sorted_order.sort()
        for order in sorted_order:                              
            index = input_data[0].index(order)
            shift = input_data[1][index] if plot_type=="shifted" else 0
            data[0].append(input_data[0][index])
            data[1].append(input_data[1][index])
            shifted_data = []
            for element in input_data[2][index]:
                shifted_data.append(element-shift)
            data[2].append(shifted_data)
            _marker.append(marker[index]-shift)
            if statevector != None:
                sv_avg = 0
                sv_index = statevector[0].index(order)
                for element in statevector[2][sv_index]:
                    sv_avg += element/len(statevector[2][sv_index])
                sv_average.append(sv_avg-shift)
                sv_min.append(min(statevector[2][sv_index])-shift)
        if plot_type=="normal":
            ax.plot(data[0], data[1], c='#000000', label="Target value", zorder=2)
        if statevector != None and plot_type=="shifted":
            if statevector_type == "average" or statevector_type == "both":
                ax.plot(data[0], sv_average, c='#00BD35', label="Statevector avg", linestyle=":", zorder=3)
            if statevector_type == "min" or statevector_type == "both":
                ax.plot(data[0], sv_min, c='#BD1413', label="Statevector min", linestyle="--", zorder=3)
        alpha_plot = 0.025 if plot_type == "normal" else 0.08
        for i, mylist in enumerate(data[2]):
            x, y = [],[]
            for value in mylist:
                x.append(data[0][i])
                y.append(value)
            ax.scatter(x, y, alpha=alpha_plot, c='#0072BD', edgecolor='none', zorder=1)
        if _marker!=None:
            ax.plot(data[0], _marker, linestyle="--", marker="v", c='#E8971E', label="Average")
        if xlabel != None:
            ax.set_xlabel(xlabel)
        if ylabel != None:
            ax.set_ylabel(ylabel[plot_type])
        ax.legend(loc=1)
    plt.tight_layout()
    if path!=None:
        filename = path + "/" + "VQE_scan_comp.png"
    if save==True:
        plt.savefig("VQE_scan_comp.png", dpi=600)
    plt.show()
