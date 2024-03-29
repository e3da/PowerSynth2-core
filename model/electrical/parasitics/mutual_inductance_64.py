import time
from numba import njit,prange
import numpy as np
import csv
import matplotlib.pyplot as plt

#from core.model.electrical.parasitics.mutual_inductance.mutual_inductance import mutual_mat_eval

from multiprocessing import Pool




# This contains test functions for mutual inductance:
# Test 1: Exact Inductance Equations for Rectangular Conductors With Applications to More Complicated Geometries
# Page 5-6
# http://nvlpubs.nist.gov/nistpubs/jres/69C/jresv69Cn2p127_A1b.pdf

@njit()
def inter_func1(x, y, z):
    '''
    Inner calculation of mutual inductance fucntion
    '''
    x2 = x * x
    x3 = x2 * x
    x4 = x3 * x
    y2 = y * y
    y3 = y2 * y
    y4 = y3 * y
    z2 = z * z
    z3 = z2 * z
    z4 = z3 * z
    sum4 = 1 / 60.0 * (x4 + y4 + z4 - 3 * x2 * y2 - 3 * y2 * z2 - 3 * x2 * z2) * np.sqrt(x2 + y2 + z2)
    if (y != 0 and z != 0) or (x != 0 and y != 0) or (x != 0 and z != 0):
        sum1 = (y2 * z2 / 4.0 - y4 / 24.0 - z4 / 24.0) * x * np.log(
            (x + np.sqrt(x2 + y2 + z2)) / np.sqrt(y2 + z2))  # if ((z2+y2)!=0) else 0
        sum2 = (x2 * z2 / 4.0 - x4 / 24.0 - z4 / 24.0) * y * np.log(
            (y + np.sqrt(x2 + y2 + z2)) / np.sqrt(x2 + z2))  # if ((z2 + x2) != 0) else 0
        sum3 = (x2 * y2 / 4.0 - x4 / 24.0 - y4 / 24.0) * z * np.log(
            (z + np.sqrt(x2 + y2 + z2)) / np.sqrt(x2 + y2))  # if ((x2+y2) != 0) else 0
        sum5 = -x * y * z3 / 6.0 * np.arctan(x * y / (z * np.sqrt(x2 + y2 + z2))) if z != 0 else 0
        sum6 = -x * y3 * z / 6.0 * np.arctan(x * z / (y * np.sqrt(x2 + y2 + z2))) if y != 0 else 0
        sum7 = -x3 * y * z / 6.0 * np.arctan(y * z / (x * np.sqrt(x2 + y2 + z2))) if x != 0 else 0
        return sum1 + sum2 + sum3 + sum4 + sum5 + sum6 + sum7
    else:
        return sum4


@njit()
def inter_func(x, y, z, sign):
    '''
    Inner calculation of mutual inductance fucntion
    '''
    x2 = x * x
    x3 = x2 * x
    x4 = x3 * x
    y2 = y * y
    y3 = y2 * y
    y4 = y3 * y
    z2 = z * z
    z3 = z2 * z
    z4 = z3 * z
    sum1,sum2,sum3,sum4,sum5 = [0,0,0,0,0]
    sum1 = (y2 * z2 / 4.0 - y4 / 24.0 - z4 / 24.0) * x * np.log(
        (x + np.sqrt(x2 + y2 + z2)) / np.sqrt(y2 + z2)) + (x2 * z2 / 4.0 - x4 / 24.0 - z4 / 24.0) * y * np.log(
        (y + np.sqrt(x2 + y2 + z2)) / np.sqrt(x2 + z2)) + (x2 * y2 / 4.0 - x4 / 24.0 - y4 / 24.0) * z * np.log(
        (z + np.sqrt(x2 + y2 + z2)) / np.sqrt(x2 + y2))
    sum2 =  -x * y * z3 / 6.0 * np.arctan(x * y / (z * np.sqrt(x2 + y2 + z2)))
    sum3 =  -x * y3 * z / 6.0 * np.arctan(x * z / (y * np.sqrt(x2 + y2 + z2)))
    sum4 =  -x3 * y * z / 6.0 * np.arctan(y * z / (x * np.sqrt(x2 + y2 + z2)))
    sum5 = 1 / 60.0 * (x4 + y4 + z4 - 3 * x2 * y2 - 3 * y2 * z2 - 3 * x2 * z2) * np.sqrt(x2 + y2 + z2)
    return sign * (sum1 + sum2 + sum3 + sum4 + sum5)


@njit()
def mutual_between_bars(params):
    w1,l1,t1,w2,l2,t2,l3,p,E = params
    '''
    This function is used to compute the mutual inductance value between 2 rectangular bars in space.
    all dimension are in um with type int
    and return nH

    :param w1: first bar 's width
    :param l1: first bar 's length
    :param t1: first bar 's thick
    :param w2: second bar 's width
    :param l2: second bar 's length
    :param t2: second bar 's thick
    :param l3: distance between two bars' (longtitude)
    :param p: height of second bar (+z)
    :param E: distance between 2 bars'
    :return: Mutual inductance of 2 bars in nH
    '''
    w1 = w1*0.1 
    l1 = l1*0.1 
    t1 = t1*0.1 

    w2 = w2*0.1 
    l2 = l2*0.1 
    t2 = t2*0.1 

    l3 = l3*0.1 
    p = p*0.1 
    E = E*0.1
    Const = 0.001 / (w1 * t1 * w2 * t2)
    add_val = outer_addition(E - w1, E + w2 - w1, E + w2, E, p - t1, p + t2 - t1, p + t2, p, l3 - l1, l3 + l2 - l1, l2 + l3, l3)

    Mb = Const *  add_val
    return Mb   # in nH

@njit()
def outer_addition(q1, q2, q3, q4, r1, r2, r3, r4, s1, s2, s3, s4):
    '''
    Compute the out - most
    :param fxyz: function to be integrated
    :return:
    '''
    q = np.abs(np.array([q1, q2, q3, q4]))
    r = np.abs(np.array([r1, r2, r3, r4]))
    s = np.abs(np.array([s1, s2, s3, s4]))
    
    res = 0
    for i in range(1,5,1):
        for j in range(1, 5, 1):
            for k in range(1, 5, 1):
                inter_val=inter_func1(q[i - 1], r[j - 1], s[k - 1])
                res += np.power(-1,(i+j+k+1))* inter_val
    
    return res


def check_val(q,r,s):
    inter_val = inter_func1(q, r, s)
    return inter_val

def bar_ind(w, l, t, fxyz=inter_func):
    # convert to cm
    w1 = w * 0.1
    l1 = l * 0.1
    t1 = t * 0.1

    Const = 0.008 / (w1 ** 2 * t1 ** 2)

    res = 0
    q = [w1, 0]
    r = [t1, 0]
    s = [l1, 0]
    for i in range(1, 3, 1):
        for j in range(1, 3, 1):
            for k in range(1, 3, 1):
                res += np.power(-1, (i + j + k + 1)) * fxyz(q[i - 1], r[j - 1], s[k - 1])
    print((res * Const * 1000))
    return abs(res * Const * 1000)  # in nH


def Test_Mutual():
    start = time.time()
    print((mutual_between_bars(w1=10, l1=30, t1=0.64, w2=10, l2=30, t2=0.64, l3=0, p=0, d=2)))
    print((time.time() - start))  # *factorial(5)
    W1 = np.linspace(1, 20, 20)
    W2 = W1
    M = []
    csvfile = open('C:/Users/qmle/Desktop/Testing/Mutual Inductance Fast Henry/Test code/MutualQ3D.csv', 'rb')
    fieldnames = ['W1', 'W2', 'M']
    # writer=csv.DictWriter(csvfile,fieldnames=fieldnames)
    reader = csv.DictReader(csvfile)
    M3D = np.zeros((20, 20))
    for row in reader:
        M3D[int(row['w1']) - 1, int(row['w2']) - 1] = float(row['ACL'])
    # writer.writeheader()
    M = np.zeros((20, 20))
    for i in range(20):
        for j in range(20):
            M[i, j] = (mutual_between_bars(w1=W1[i], l1=30, t1=0.64, w2=W2[j], l2=30, t2=0.64, l3=0, p=0, d=2))

    REL_ERR = abs(M - M3D) / M3D * 100
    X, Y = np.meshgrid(W1, W2)
    fig1 = plt.figure(1)
    ax = fig1.gca(projection='3d')
    # surf1 = ax.plot_surface(X, Y, M)
    ax.scatter(X, Y, REL_ERR, c='b')
    # ax.scatter(X,Y,M3D,c='r')
    plt.xlabel('W1')
    plt.ylabel('W2')
    plt.show()

    csvfile = open('C:/Users/qmle/Desktop/Testing/Mutual Inductance Fast Henry/Test code/MutualQ3D_distance.csv', 'rb')
    fieldnames = ['d1', 'M']
    M = []
    M_Q3D = []
    reader = csv.DictReader(csvfile)
    for row in reader:
        M_Q3D.append(float(row['M']))
    for i in np.arange(2, 21, 1):
        print(i)
        M.append(mutual_between_bars(w1=10, l1=30, t1=0.64, w2=10, l2=30, t2=0.64, l3=0, p=0, d=i))

    plt.plot(np.arange(2, 21, 1), M, 'k:', label='Model', c='b', lw=3)
    plt.plot(np.arange(2, 21, 1), M_Q3D, 'k--', label='Q3D', c='r', lw=3)
    plt.xlabel('distance')
    plt.ylabel('M (nH)')
    plt.show()


@njit(parallel=True)
def two_d_array_reduction_prod(n):
    shp = (13, 17)
    result1 = 2 * np.ones(shp, np.int_)
    tmp = 2 * np.ones_like(result1)

    for i in prange(n):
        result1 *= tmp

    return result1

@njit(parallel = True)
def outer_addition_parallel(q1, q2, q3, q4, r1, r2, r3, r4, s1, s2, s3, s4):
    q = np.abs(np.array([q1, q2, q3, q4]))
    r = np.abs(np.array([r1, r2, r3, r4]))
    s = np.abs(np.array([s1, s2, s3, s4]))
    result= 0
    for i in prange(1,5,1):
        for j in prange(1, 5, 1):
            for k in prange(1, 5, 1):
                x = q[i - 1]
                y = r[j - 1]
                z = s[k - 1]
                sign = np.power(-1,(i+j+k+1))
                x2 = x * x
                x3 = x2 * x
                x4 = x3 * x
                y2 = y * y
                y3 = y2 * y
                y4 = y3 * y
                z2 = z * z
                z3 = z2 * z
                z4 = z3 * z
                sum1 = (y2 * z2 / 4.0 - y4 / 24.0 - z4 / 24.0) * x * np.log(
                    (x + np.sqrt(x2 + y2 + z2)) / np.sqrt(y2 + z2)) + (x2 * z2 / 4.0 - x4 / 24.0 - z4 / 24.0) * y * np.log(
                    (y + np.sqrt(x2 + y2 + z2)) / np.sqrt(x2 + z2)) + (x2 * y2 / 4.0 - x4 / 24.0 - y4 / 24.0) * z * np.log(
                    (z + np.sqrt(x2 + y2 + z2)) / np.sqrt(x2 + y2))
                sum2 =  -x * y * z3 / 6.0 * np.arctan(x * y / (z * np.sqrt(x2 + y2 + z2)))
                sum3 =  -x * y3 * z / 6.0 * np.arctan(x * z / (y * np.sqrt(x2 + y2 + z2)))
                sum4 =  -x3 * y * z / 6.0 * np.arctan(y * z / (x * np.sqrt(x2 + y2 + z2)))
                sum5 = 1 / 60.0 * (x4 + y4 + z4 - 3 * x2 * y2 - 3 * y2 * z2 - 3 * x2 * z2) * np.sqrt(x2 + y2 + z2)
                result+=sign * (sum1 + sum2 + sum3 + sum4 + sum5)
    return result

@njit(parallel = True)
def outer_addition_prange(params,signs):
    res = 0 
    for i in prange(len(signs)):
        p = params[i]
        res += signs[i] * inter_func(p[0], p[1], p[2])
    return res


def multi_process_outer_add(params):
    res = 0 
    num_cpu = 10
    with Pool(num_cpu) as p:
        results = p.starmap(inter_func,params)
    #p = params[i]
    #res += signs[i] * inter_func1(p[0], p[1], p[2])
    return results
if __name__ == '__main__':
    res1 = mutual_between_bars(np.array([100,1000,200,100,1000,200,1000,1000,500])) # init
    perf = time.perf_counter()
    for i in range(30000):
        res2 = mutual_between_bars(np.array([100,2000,200,100,1000,200,1000,1000,-500]))
    print(time.perf_counter()- perf, 's')
    #res = mutual_between_bars(np.array([1000,21200,200,1750,21200,200,1,1,1001]))
    #Verified


    # http://wcalc.sourceforge.net/cgi-bin/bars.cgi?freq=0.1&wc_unit_menu_2_0=MHz&a=0.1&wc_unit_menu_0_0=mm&b=0.2&l1=2&d=0.1&c=0.2&l2=1&E=0.5&P=1&l3=1&analyze=Analyze&L1=0.194776&wc_unit_menu_1_0=nH&L2=0.494682&M=0.0843632&k=0.271783
 