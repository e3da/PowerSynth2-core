import matplotlib.pyplot as plt
from matplotlib import pylab
import networkx as nx

def save_graph(graph,file_name):
  #initialze Figure
  plt.figure(num=None, figsize=(20, 20), dpi=80)
  plt.axis('off')
  fig = plt.figure(1)
  pos = nx.spring_layout(graph)
  nx.draw_networkx_nodes(graph,pos)
  nx.draw_networkx_edges(graph,pos)
  nx.draw_networkx_labels(graph,pos)

  cut = 1.00
  xmax = cut * max(xx for xx, yy in pos.values())
  ymax = cut * max(yy for xx, yy in pos.values())
  plt.xlim(0, xmax)
  plt.ylim(0, ymax)

  plt.savefig(file_name,bbox_inches="tight")
  pylab.close()
  del fig

#Assuming that the graph g has nodes and edges entered
save_graph(g,"my_graph.pdf")