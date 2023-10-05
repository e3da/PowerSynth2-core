import os,sys

is_64bits = sys.maxsize > 2 ** 32
print(is_64bits)
compiler = "mingw32"
print(os.getcwd())
os.system("python setup.py build_ext --inplace")

