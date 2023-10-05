
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.path import Path

from core.engine.CornerStitch.CSinterface import Rectangle
from core.engine.LayoutSolution.database import create_connection,create_table,retrieve_data
import copy
import csv

class LayerSolution():
    def __init__(self, name):
        '''
        similar as 2D solution object
        '''
        self.name=name
        self.layout_rects=[]# list of rects to plot solution
        self.layout_plot_info={} # dict of layout_info of each layer in the structure
        self.abstract_infos={} # dict of abstract_info of each layer in the structure
        self.min_dimensions=None # To store fixed dimension component minimum dimensions
        self.objects_3D=[] # list of cell_3D objects
        
    def update_objects_3D_info(self,initial_input_info=None,mode=0):
        '''
        updating initial input objects with solution coordinates, diemnsions
        '''
        self.objects_3D=copy.deepcopy(initial_input_info)
        if len(self.abstract_infos)>0 and mode>=0:
            for object_ in self.objects_3D:
                
                for name,rect_object in self.abstract_infos[self.name]['rect_info'].items():
                    
                    if object_.name!='Substrate':
                        if object_.name==name :
                           
                            object_.x=rect_object.x 
                            object_.y=rect_object.y
                            object_.w=rect_object.width
                            object_.l=rect_object.height

                    else:
                        
                        object_.x=rect_object.x 
                        object_.y=rect_object.y
                        object_.w=rect_object.width
                        object_.l=rect_object.height
        
    def export_layer_info(self,sol_path=None,id=None):
        
        item = 'solution_'+str(id)+'_'+self.name
        
        file_name = sol_path + '/' + item + '.csv'
        with open(file_name, 'w') as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=',')
            
            csv_writer.writerow(["Component_Name", "x_coordinate", "y_coordinate", "width", "length"])
            for k, v in self.abstract_infos[self.name]['rect_info'].items():
                
                k=k.split('.')[0]
                layout_data = [k, v.x, v.y, v.width, v.height]
                csv_writer.writerow(layout_data)
        my_csv.close()


class CornerStitchSolution():

    def __init__(self, index=0, params=None):
        """Describes a solution saved from the Solution Browser

        Keyword arguments:
        name -- solution name
        index -- cs solution index
        params -- list of objectives in tuples (name, unit, value)
        """
        #self.name = name
        self.index = index # solution index for database
        self.params = params # performance values dictionary
        self.layer_solutions=[] # list of Layer solution objects
        self.floorplan_size=None # floorplan size of the solution
        self.module_data=None # ModuleDataCornerStitch object
        
        
     
    def populate_objects_3D(self):
        '''
        makes Cell3D objects and appends in the objects_3D.
        '''
        objects_3D=[]
        signal_layer_info=[]
        for id, layer_object in self.module_data.layer_stack.all_layers_info.items():
            if (layer_object.e_type=='S') : # from layer stack all layers with electrical components are excluded here
                name=layer_object.name
                x=layer_object.x
                y=layer_object.y
                z=layer_object.z_level
                width=layer_object.width
                length=layer_object.length
                height=layer_object.thick
                
                material_name=layer_object.material.name
                
                signal_layer=Cell3D(name=name, x=x, y=y, z=z, w=width, l=length, h=height, material_name=material_name) # creating Cell3D object for each routing layer
                signal_layer_info.append(signal_layer)
        
        for layer in all_layers:
            
            comps_names=[]
            for comp in layer.New_engine.all_components:
                name=(comp.layout_component_id)
                if name[0]!='B':
                    comps_names.append(name)
                    
                    if isinstance(comp,Part):
                        if name[0]=='D': # only device thickness is considered
                            height=comp.thickness
                        else:
                            height=0.18 # fixed for now ; need to implement properly
                        material=comp.material_id # assumed that components have material id from component file
                        width=comp.footprint[0] # width from component file
                        length=comp.footprint[1] # length from component file
                        z=-1 # initialize with negative z value, later will be replaced by actual z value
                    elif isinstance(comp,RoutingPath): # routing path involves traces, bonding wire pads. Here we have excluded bonding wire pads.
                        for f in dummy_features:
                            if f.name==layer.name:
                                height=f.height
                                material=f.material_name
                                z=f.z
                        width=0
                        length=0
                    
                    
                    feature=PSFeature(name=name,z=z,width=width,length=length,height=height,material_name=material)
                    dummy_features.append(feature) 

    def hex_to_rgb(self,value):
        value=str(value)
        value=value.lstrip(" '#")
        value=value.rstrip("'")
        
        
        lv = len(value)
        
        conv_value= list(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        return tuple([i/255 for i in conv_value])
    
    def plot_all_layers(self, all_patches= [],sol_ind=0, sol_path=None, ax_lim=[]):
        
        ax2 = plt.subplots()[1]
        for p in all_patches:
            ax2.add_patch(p)
        ax2.set_xlim(ax_lim[0])
        ax2.set_ylim(ax_lim[1])
    
        ax2.set_aspect('equal')
        
        plt.legend(loc='lower left', bbox_to_anchor = (1.005, 0.005))
        plt.savefig(sol_path+'/layout_all_layers_'+str(sol_ind)+'.png', pad_inches = 0, bbox_inches = 'tight')
        
        plt.close()

    def layout_plot(self, layout_ind=0,layer_name=None, db=None, fig_dir=None, bw_type=None, all_layers=False, a= None, c= None,lab=None):
        fig1, ax1 = plt.subplots()
        if bw_type!=None:
            bondwire_type=" '{}'".format(bw_type)
        else:
            bondwire_type=None


       

        conn = create_connection(db)
        v1=[]
        all_patches=[]

        with conn:
            
            all_data = retrieve_data(conn,layout_ind, layer_name)
            
            data=all_data[0].decode("utf-8")
            
            data=data.rstrip()
            lines=data.split('\n')
            
            
            lines_bytes=[]
            for line in lines:
                
                line=line.rstrip()
                line=line.split(',')
                line=[i.encode("utf-8") for i in line]
                if len(line)>2:
                    line[0]=((line[0].decode("utf-8")).replace('[','')).encode("utf-8")
                    line[-1]=((line[-1].decode("utf-8")).replace(']','')).encode("utf-8")
                    
                else:
                   line=[ (line[0].decode("utf-8")).replace('[',''),(line[1].decode("utf-8")).replace(']','')]
                  
                lines_bytes.append(line)
                
            
            all_lines=[]
            for line in lines_bytes:
                l=[]
                for i in line:
                    if not isinstance(i,str):
                        i=(i.decode("utf-8")).replace('"','')
                    else:
                        
                        i=i
                    l.append(i)
                
                all_lines.append(l)
            


            
            all_layers_plot_rows=[]
            for row in all_lines:
                if row[-1]==" 'True'" and all_layers== True and len(row)>4 and row[5] != bondwire_type:
                    all_layers_plot_rows.append(row)

            for row in all_lines:
                

                if len(row) < 4:
                    k1 = (float(row[0]), float(row[1]))
                    
                elif row[5] == " 'EMPTY'":
                    
                    x0,y0=(float(row[0]), float(row[1]))
                else:
                    
                    if row[5] == bondwire_type:
                        

                        point1 = (float(row[0]), float(row[1]))
                        point2 = (float(row[2]), float(row[3]))
                        verts = [point1, point2]
                        
                        codes = [Path.MOVETO, Path.LINETO]
                        path = Path(verts, codes)
                        colour = (row[4])
                        
                        colour=self.hex_to_rgb(colour)
                        
                       
                        patch = matplotlib.patches.PathPatch(path, edgecolor=colour, lw=0.8,zorder=int(row[6]))
                        v1.append(patch)


                    else:
                        x = float(row[0])
                        y = float(row[1])
                        w = float(row[2])
                        h = float(row[3])
                        colour = (row[4])
                        colour=self.hex_to_rgb(colour)
                        
                        order = int(row[6])
                        if row[7] != " 'None'" :
                            linestyle = row[7]
                            edgecolour = row[8]
                            
                            edgecolor=self.hex_to_rgb(edgecolour)

                        if row[7] == " 'None'":
                            
                            R1 = matplotlib.patches.Rectangle(
                                (x, y),  # (x,y)
                                w,  # width
                                h,  # height
                                facecolor=colour,
                                zorder=order

                            )
                        else:
                            
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

                        if row[-1]==" 'True'" and all_layers== True:
                            if row==all_layers_plot_rows[-1]:
                                label=lab
                                
                            else:
                                label=None
                            if a<0.9:
                                linestyle='--'
                                linewidth=order
                            else:
                                linestyle='-'
                                linewidth=order
                            
                            
                            P = matplotlib.patches.Rectangle(
                            (x, y),  # (x,y)
                            w,  # width
                            h,  # height
                            edgecolor=c,
                            facecolor="white",
                            zorder=order,
                            linewidth=linewidth,
                            alpha=a,
                            fill=False,
                            linestyle=linestyle,
                            label=label
                            )
                            all_patches.append(P)


            for p in v1:
                ax1.add_patch(p)

            ax1.set_xlim(x0, k1[0])
            ax1.set_ylim(y0, k1[1])
            ax1.set_aspect('equal')
            plt.savefig(fig_dir+'/layout_'+str(layout_ind)+'_'+layer_name+'.png', bbox_inches = 'tight', pad_inches = 0)
            
            # Try to release memory
            fig1.clf()
            plt.close()

        conn.close()
        if len(all_patches)>0:
            x_lim=(x0, k1[0])
            y_lim=(y0, k1[1])
            return all_patches, [x_lim,y_lim]
        else:
            return None

if __name__ == '__main__':

    db_file='D:\Demo\\New_Flow_w_Hierarchy\Journal_Case\Journal_Result_collection\Cmd_flow_case\Half_Bridge_Layout\\Test_solutions_kelvin\Sols_35X40\layouts_db\layout.db'
    fig_dir='D:\Demo\\New_Flow_w_Hierarchy\Journal_Case\Journal_Result_collection\Cmd_flow_case\Half_Bridge_Layout\\Test_Figs_kelvin\Figs_35X40\Pareto_solutions'
    sol=CornerStitchSolution()
    ids=[165,258,306,352,52,523,765,781,782,925,950]#35X40

    for id in ids:
        try:
            sol.layout_plot(layout_ind=id, db=db_file, fig_dir=fig_dir)
        except:
            print (id)
