# This file contains all abstract data-types that is needed for PowerSynth
# This includes:
#   Stack,Linked_List, Buckets and so on...


class Stack():
    # A stack can be present as a list in Python, however only allow single data to go in and out each time
    # then we just add the push and pop function, peek will
    # tell which data is on top and size will tell the len of stack's list.
    # This example can be found at:
    # https://interactivepython.org/runestone/static/pythonds/BasicDS/ImplementingaStackinPython.html
    def __init__(self):
        self.data = []  # initialize stack's list

    def eraseAll(self):
        # Erase everything in the stack
        self.data = []

    def isEmpty(self):
        # check if the stack is Empty or not
        if self.data == []:
            return True
        else:
            return False

    def push(self, item):
        # push an item into the stack
        self.data.append(item)  #

    def pop(self):
        # pop out an item
        if not (self.isEmpty()):
            return self.data.pop()

    def peek(self):
        # check which item is on top
        return self.data[len(self.data) - 1]


if __name__ == '__main__':
    s1 = Stack()
    print(s1.isEmpty())
    s1.push(1)
    s1.push(2)
    print(s1.peek())
