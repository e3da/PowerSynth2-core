# This includes all special exceptions messages for the electrical extraction.
class Error(Exception):
    pass

class NeighbourSearchErr(Error):
    def __init__(self, direction):
        self.message = "Cannot find the " + direction + "neighbour for this node, check the mesh again"
