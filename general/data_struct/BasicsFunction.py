# List of Functions that can be used anywhere

def add_num_to_list(list, num):
    # Add same number to every tuple of a list
    res=[]
    for data in list:
        data=data+num
        res.append(data)
    return res
def print_test(a):
    print(a)
    
def list_mult(list):
    # return multiplication of all list elements
    res=1
    for i in list:
        res*=i
    return res

def recurs_for_loops(y,number,f,params):
    # do a job y*number times
        # f: any function
    if (number>1):
        for x in range (y):
            f(*params)
        recurs_for_loops ( y, number-1,f,params)
    else:
        for x in range (y):
            f(*params)
        
if __name__ == '__main__':
    # Test add_num_to_list
    
    recurs_for_loops(2, 5,print_test,'1')
        
        