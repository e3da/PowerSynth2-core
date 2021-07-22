
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.path import Path

from powercad.corner_stitch.CornerStitch import Rectangle
from powercad.cons_aware_en.database import create_connection,create_table,retrieve_data
class CornerStitchSolution:

    def __init__(self, name='', index=None, params=None,fig_data=None):
        """Describes a solution saved from the Solution Browser

        Keyword arguments:
        name -- solution name
        index -- cs solution index
        params -- list of objectives in tuples (name, unit, value)
        """
        self.name = name
        self.index = index
        self.params = params
        self.layout_info={}   # dictionary holding layout_info for a solution with key=size of layout
        self.abstract_info={} # dictionary with solution name as a key and layout_symb_dict as a value


    def form_abs_obj_rect_dict(self, div=1000):
        '''
        From group of CornerStitch Rectangles, form a single rectangle for each trace
        Output type : {"Layout id": {'Sym_info': layout_rect_dict,'Dims': [W,H]} --- Dims is the dimension of the baseplate
        where layout_rect_dict= {'Symbolic ID': [R1,R2 ... Ri]} where Ri is a Rectangle object
        '''
        if isinstance(self.layout_info, dict):
            p_data = self.layout_info
        else:
            #print self.layout_info
            p_data=self.layout_info[0]
        layout_symb_dict={}
        layout_rect_dict = {}


        W, H = list(p_data.keys())[0]
        W = float(W) / div
        H = float(H) / div

        rect_dict=list(p_data.values())[0]

        #for rect_dict in dict_list:
        for k,v in list(rect_dict.items()):
            if not isinstance(v,Rectangle):
                x=v[1]
                y=v[2]
                width=v[3]
                height=v[4]
                type=v[0]

                layout_rect_dict[k] = Rectangle(x=x, y=y, width=width, height=height, type=type)
            else:
                layout_rect_dict[k]=v



        layout_symb_dict[self.name] = {'rect_info': layout_rect_dict, 'Dims': [W, H]}
        #print layout_symb_dict[layout]
        #print layout_symb_dict

        return layout_symb_dict



    def layout_plot(self, layout_ind=0, db=None, fig_dir=None, all_layers=False, a= None):
        fig1, ax1 = plt.subplots()

        choice = 'Layout ' + str(layout_ind)

        conn = create_connection(db)
        v1=[]

        with conn:
            # create a new project
            #table = 'Layout_' + str(layout_ind)
            all_data = retrieve_data(conn,layout_ind)
            #print("H,all",all_data)
            #all_data=json.loads(all_data)

            #print "A",all_data
            #data=str(all_data[0])
            data=all_data[0].decode("utf-8")
            #all_lines=data
            #print(data)
            #'''
            data=data.rstrip()
            lines=data.split('\n')
            #lines=lines.rstrip()
            lines_bytes=[]
            for line in lines:
                #print("D",line)
                line=line.rstrip()
                line=line.split(',')
                line=[i.encode("utf-8") for i in line]
                if len(line)>2:
                    line[0]=((line[0].decode("utf-8")).replace('[','')).encode("utf-8")
                    line[-1]=((line[-1].decode("utf-8")).replace(']','')).encode("utf-8")
                    
                else:
                   line=[ (line[0].decode("utf-8")).replace('[',''),(line[1].decode("utf-8")).replace(']','')]
                  
                lines_bytes.append(line)
                #print (line)
            #lines_bytes=[list for list in lines_bytes if list!=[]]
            #for line in lines_bytes:
                #print (line[0],line[-1])
                #print (line)
            
            all_lines=[]
            for line in lines_bytes:
                l=[]
                for i in line:
                    if not isinstance(i,str):
                        i=(i.decode("utf-8")).replace('"','')
                    else:
                        
                        i=i
                    l.append(i)
                #line=[i.decode("utf-8") for i in line]
                #print (l)
                all_lines.append(l)
            '''
            for i in lines_bytes:
                #print (i,len(i))
                #print (i[-1])
                l=[]
                if i[-1]!=']':
                    if i[0]=='[':
                        l.append(i[1:-2])

                    else:
                        l.append(i[0:-2])
                else:
                    j=i[0:-1]
                    l.append(j)
                print (l)
                all_lines.append(l)
            '''


            colors = ['white', 'green', 'red', 'blue', 'yellow', 'purple','pink','magenta','orange','violet','black']

            colours=[" 'white'"," 'green'"," 'red'"," 'blue'"," 'yellow'"," 'purple'"," 'pink'"," 'magenta'"," 'orange'"," 'violet'"," 'black'"]

            
            for row in all_lines:
                #print("R", row)
                if len(row) < 4:
                    k1 = (float(row[0]), float(row[1]))
                    #print "plot",k1

                else:
                    if row[5] == " 'Type_3'":

                        point1 = (float(row[0]), float(row[1]))
                        point2 = (float(row[2]), float(row[3]))
                        verts = [point1, point2]
                        #print"here", verts
                        codes = [Path.MOVETO, Path.LINETO]
                        path = Path(verts, codes)
                        colour = (row[4])
                        ind = colours.index(colour)
                        colour = colors[ind]
                        patch = matplotlib.patches.PathPatch(path, edgecolor=colour, lw=0.5,zorder=3)
                        v1.append(patch)


                    else:
                        x = float(row[0])
                        y = float(row[1])
                        w = float(row[2])
                        h = float(row[3])
                        colour = (row[4])
                        ind=colours.index(colour)
                        colour=colors[ind]
                        order = int(row[6])
                        if row[7] != " 'None'" :
                            linestyle = row[7]
                            edgecolor = row[8]
                            ind = colours.index(edgecolor)
                            edgecolor = colors[ind]

                        if row[7] == " 'None'":
                            #print "IN"
                            R1 = matplotlib.patches.Rectangle(
                                (x, y),  # (x,y)
                                w,  # width
                                h,  # height
                                facecolor=colour,
                                zorder=order

                            )
                        else:
                            #print x, y, w, h, colour, order, row[6], row[7]
                            #print "here"
                            R1 = matplotlib.patches.Rectangle(
                                (x, y),  # (x,y)
                                w,  # width
                                h,  # height
                                facecolor=colour,
                                linestyle='--',
                                edgecolor=edgecolor,
                                zorder=order

                            )
                        v1.append(R1)

            
            for p in v1:
                ax1.add_patch(p)

            ax1.set_xlim(0, k1[0])
            ax1.set_ylim(0, k1[1])
            ax1.set_aspect('equal')
            plt.savefig(fig_dir+'/layout_'+str(layout_ind)+'.png')
            plt.savefig((fig_dir + '/layout_' + str(layout_ind) + '.svg'),dpi=1200, bbox_inches = 'tight',pad_inches = 0)
            # Try to release memory
            fig1.clf()
            plt.close()

        conn.close()

