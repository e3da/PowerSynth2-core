import seaborn as sns

def color_list_generator(N=None):
	if N==None:
		N=10000
	
	colors = sns.color_palette(None, N)
	
	return colors