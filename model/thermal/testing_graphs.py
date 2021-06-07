'''
Created on Mar 19, 2013

@author: bxs003
'''

import numpy as np

import matplotlib.pyplot as plt

def edge_coupling_test():
    d1_model=[433.9264254,
            431.8504442,
            429.8389388,
            428.9327779,
            427.9216667,
            427.5408609,
            428.0753647]
    
    d1_model = np.array(d1_model)
    d1_model += 5.3

    d2_model=[433.9264254,
            431.8504442,
            429.8389388,
            428.9327779,
            427.9216667,
            427.7793517,
            429.9732041]
    
    d2_model = np.array(d2_model)
    d2_model += 5.3
    
    d1_fem = [439.58,437.14,
            435.62,434.54,
            433.72,433.06,
            432.56]
    
    d2_fem = [439.58,437.19,
            435.66,434.7,
            434.02,433.65,
            434.66]
    
    x = [6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0]
    plt.plot(x, d1_model)
    plt.plot(x, d2_model)
    plt.plot(x, d1_fem)
    plt.plot(x, d2_fem)
    plt.show()


edge_coupling_test()