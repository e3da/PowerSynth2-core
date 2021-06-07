from libc.math cimport sqrt,atan,log,pow,fabs,M_PI,asinh
import numpy as np
from cython.parallel cimport parallel
from libc.stdio cimport printf
from cython.parallel import prange
cimport openmp
# This contains test functions for mutual inductance:
# Test 1: Exact Inductance Equations for Rectangular Conductors With Applications to More Complicated Geometries
# Page 5-6
# http://nvlpubs.nist.gov/nistpubs/jres/69C/jresv69Cn2p127_A1b.pdf

cpdef double[:] mutual_mat_eval(double[:,:] m_mat,int nt,int mode):
    '''
    
    Args:
        m_mat: mutual parameters sent from python 
        nt: number of threads requested
        mode: 0 for bar, 1 for plane

    Returns:

    '''
    cdef double [:,:] m_mat1 = np.asarray(m_mat)
    cdef int rows = np.asarray(m_mat).shape[0]
    cdef double [:] result = np.zeros(rows)
    cdef int i,num_t,chunksize
    openmp.omp_set_dynamic(36)
    with nogil, parallel():
        openmp.omp_set_num_threads(nt)
        num_t = 8 #openmp.omp_get_num_threads()
        #printf("number of threads: %f\n",num_t)
        chunksize = rows/num_t
        for i in prange(rows, schedule='static',chunksize=chunksize):
            if mode == 0: # use bar equation
                result[i] = mutual_between_bars(m_mat1[i,:])
            elif mode ==1:# use plane equation
                result[i] = mutual_between_plane(m_mat1[i,:])
    return result

cpdef double self_ind(double trace_width, double trace_length, double trace_thickness):
    return self_term(trace_width,trace_length,trace_thickness)

cdef double self_term(double trace_width, double trace_length, double trace_thickness) nogil:
    '''This function is from FastHenry Joelself.c might consider to rewrite this in C++ for speed up
    https://github.com/ediloren/FastHenry2/blob/master/src/fasthenry/joelself.c
    '''
    cdef double w, t, aw, at, ar, r, z;

    w = trace_width / trace_length;
    t = trace_thickness / trace_length
    r = sqrt(w * w + t * t)
    aw = sqrt(w * w + 1.0)
    at = sqrt(t * t + 1.0)
    ar = sqrt(w * w + t * t + 1.0)

    z = 0.25 * ((1 / w) * asinh(w / at) + (1 / t) * asinh(t / aw) + asinh(1 / r))
    z += (1 / 24.0) * ((t * t / w) * asinh(w / (t * at * (r + ar))) + (w * w / t) * asinh(t / (w * aw * (r + ar))) +\
                       ((t * t) / (w * w)) * asinh(w * w / (t * r * (at + ar))) + ((w * w) / (t * t)) * \
                       asinh(t * t / (w * r * (aw + ar))) +(1.0 / (w * t * t)) * asinh(w * t * t / (at * (aw + ar)))\
                       + (1.0 / (t * w * w)) * asinh(t * w * w / (aw * (at + ar))))
    z -= (1.0 / 6.0) * ((1.0 / (w * t)) * atan(w * t / ar) + (t / w) * atan(w / (t * ar)) + (w / t) * atan(t / (w * ar)))
    z -= (1.0 / 60.0) * (((ar + r + t + at) * t * t) / ((ar + r) * (r + t) * (t + at) * (at + ar))
                         + ((ar + r + w + aw) * (w * w)) / ((ar + r) * (r + w) * (w + aw) * (aw + ar))
                         + (ar + aw + 1 + at) / ((ar + aw) * (aw + 1) * (1 + at) * (at + ar)))
    z -= (1.0 / 20.0) * ((1.0 / (r + ar)) + (1.0 / (aw + ar)) + (1.0 / (at + ar)))

    z *= (2.0 / M_PI)
    z *= trace_length

    return z


cdef double inter_func1(double x,double y,double z) nogil:
    '''
    Inner calculation of mutual inductance fucntion
    '''
    cdef double x2,x3,x4,y2,y3,y4,z2,z3,z4,sum1,sum2,sum3,sum4,sum5,sum6,sum7,sumxyz2

    #printf("x %f\n", x)
    #printf("y %f\n", y)
    #printf("z %f\n", z)

    x2 = pow(x,2)
    x3 = pow(x, 3)
    x4 = pow(x, 4)
    y2 = pow(y, 2)
    y3 = pow(y, 3)
    y4 = pow(y, 4)
    z2 = pow(z, 2)
    z3 = pow(z, 3)
    z4 = pow(z, 4)
    sum4 = 1 / 60.0 * (x4 + y4 + z4 - 3 * x2 * y2 - 3 * y2 * z2 - 3 * x2 * z2) * sqrt(x2 + y2 + z2)
    if (y != 0 and z != 0) or (x != 0 and y != 0) or (x != 0 and z != 0):


        sum1 = (y2 * z2 / 4.0 - y4 / 24.0 - z4 / 24.0) * x * log(
            (x + sqrt(x2 + y2 + z2)) / sqrt(y2 + z2))  # if ((z2+y2)!=0) else 0
        sum2 = (x2 * z2 / 4.0 - x4 / 24.0 - z4 / 24.0) * y * log(
            (y + sqrt(x2 + y2 + z2)) / sqrt(x2 + z2))  # if ((z2 + x2) != 0) else 0

        sum3 = (x2 * y2 / 4.0 - x4 / 24.0 - y4 / 24.0) * z * log(
            (z + sqrt(x2 + y2 + z2)) / sqrt(x2 + y2))  # if ((x2+y2) != 0) else 0
        sumxyz2 = x2 + y2 + z2
        if sumxyz2 !=0:
            sum5 = -x * y * z3 / 6.0 * atan(x * y / (z * sqrt(sumxyz2))) if z != 0 else 0
            sum6 = -x * y3 * z / 6.0 * atan(x * z / (y * sqrt(sumxyz2))) if y != 0 else 0
            sum7 = -x3 * y * z / 6.0 * atan(y * z / (x * sqrt(sumxyz2))) if x != 0 else 0
        else:
            sum5=0
            sum6=0
            sum7=0
        return sum1 + sum2 + sum3 + sum4 + sum5 + sum6 + sum7
    else:
        return sum4

cdef double inter_func2(double x, double z,double p) nogil:
    '''
    Inner calculation of mutual inductance fucntion
    '''
    # page 4 in paper
    cdef double x2,z2, sum1, sum2, sum3, sum4, sq
    x2 = x*x
    z2 = z*z
    p2 = p*p+(z-x)*(z-x)
    sq = sqrt(x2 + p2 + z2)
    sum1 = 0.5*(x2-p2)*z*log(z+sq)
    sum2 = 0.5*(z2-p2)*x*log(x+sq)
    sum3 = -1/6*(x2-2*p2+z2)*sq
    if p*sq!=0:
        sum4 = -x*p*z*atan(x*z/(p*sq))
    else:
        sum4 =0
    return sum1+sum2+sum3+sum4

cdef double mutual_between_plane (double[:] param) nogil:
    '''
    This function is used to compute the mutual inductance value between 2 rectangular plane in space.
    all dimension are in mm

    :param w1: first bar 's width
    :param l1: first bar 's length
    :param w2: second bar 's width
    :param t2: second bar 's thick
    :param l3: distance between two bars' (longtitude)
    :param p: height of second bar (+z)
    :param E: distance between 2 bars'
    :return: Mutual inductance of 2 bars in nH
    '''
    cdef double w1, l1, w2, l2, l3, p, E
    w1 = fabs(param[0] * 0.1)
    l1 = fabs(param[1] * 0.1)
    w2 = fabs(param[2] * 0.1)
    l2 = fabs(param[3] * 0.1)
    l3 = fabs(param[4] * 0.1)
    p = fabs(param[5] * 0.1)
    E = fabs(param[6] * 0.1)
    Const = 0.001/(w1*w2)
    Mb=Const*outer_addition_plane(q1=E-w1,q2=E+w2-w1,q3=E+w2,q4=E,s1=l3-l1,s2=l3+l2-l1,s3=l3+l2,s4=l3,p=p)
    return Mb*1000 #in nH

cdef double mutual_between_bars (double[:] param) nogil:
    '''
    This function is used to compute the mutual inductance value between 2 rectangular bars in space.
    all dimension are in mm

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
    cdef double w1,l1,t1,w2,l2,t2,l3,p,E,Mult,Const
    w1 = fabs(param[0]*0.1)
    l1 = fabs(param[1]*0.1)
    t1 = fabs(param[2]*0.1)
    w2 = fabs(param[3]*0.1)
    l2 = fabs(param[4]*0.1)
    t2 = fabs(param[5]*0.1)
    l3 = fabs(param[6]*0.1)
    p = fabs(param[7]*0.1)
    E = fabs(param[8]*0.1)
    Mult = w1 * t1 * w2 * t2
    if Mult == 0: # This is special case where to trace overlapped
        return  0
    Const=0.001/Mult
    Mb = Const * outer_addition(q1=E - w1, q2=E + w2 - w1, q3=E + w2, q4=E, r1=p - t1, r2=p + t2 - t1, r3=p + t2, r4=p,
                                s1=l3 - l1, s2=l3 + l2 - l1, s3=l2 + l3, s4=l3)

    #printf("Mb %f\n",Mb)

    return Mb*1000 # in nH


cdef double outer_addition(double q1, double q2, double q3, double q4, double r1, double r2, double r3, double r4, double s1,
                           double s2, double s3, double s4) nogil:


    cdef double[4] q,r,s
    q[0] = q1
    q[1] = q2
    q[2] = q3
    q[3] = q4
    r[0] = r1
    r[1] = r2
    r[2] = r3
    r[3] = r4
    s[0] = s1
    s[1] = s2
    s[2] = s3
    s[3] = s4
    cdef double interval,sign
    cdef int i,j,k
    cdef double res
    res = 0.0
    for i in xrange(1,5,1):
        for j in xrange(1, 5, 1):
            for k in xrange(1, 5, 1):
                inter_val = inter_func1(q[i - 1], r[j - 1], s[k - 1])
                sign = pow(-1, (i + j + k + 1))
                #printf("inside %i%i%i%f\n", i,j,k,sign*inter_val)
                res = res + sign*inter_val
                #printf("update sum %f\n", res)
    #printf("outer add %f\n", res)

    return res

cdef double outer_addition_plane(double q1, double q2, double q3, double q4,double s1,double s2, double s3, double s4, double p) nogil:
    cdef double[4] q, s
    q[0] = q1
    q[1] = q2
    q[2] = q3
    q[3] = q4
    s[0] = s1
    s[1] = s2
    s[2] = s3
    s[3] = s4
    cdef double interval, sign
    cdef int i, k
    cdef double res
    res = 0.0
    for i in xrange(1, 5, 1):
        for k in xrange(1, 5, 1):
            inter_val = inter_func2(q[i - 1], s[k - 1],p)
            sign = pow(-1, (i + k ))
            #printf("inside %i%i%i%f\n", i,j,k,sign*inter_val)
            res = res + sign * inter_val
    #printf("outer add %f\n", res)

