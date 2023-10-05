"""@ author qmle
This module allow an alternative evaluation for mutual_inductance.
The equations are first compiled in C to optimize speed
However the just in time compiler is good enough for most cases.
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from Cython.Build import cythonize
from distutils.extension import Extension
import numpy


ext_modules = [
    Extension(
        "mutual_inductance",
        ["mutual_inductance.pyx"],
        extra_compile_args=['-fopenmp'],
        extra_link_args=['-fopenmp'],
    )
]

''' python setup.py build_ext --inplace --compiler=mingw32 -DMS_WIN64 install '''
setup(
    name="multithreads_mutual",
    include_dirs=[numpy.get_include()],
    #cmdclass={'build_ext': build_ext},
    ext_modules=cythonize(ext_modules)

)