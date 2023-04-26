from core.engine.LayoutSolution.cs_solution import CornerStitchSolution
import numpy as np
import matplotlib.pyplot as plt
import os
import csv
import glob
import matplotlib

def pareto_solutions(solutions):
    all_data={}
    pareto_data={}
    solutions.sort(key=lambda x: x.index, reverse=False)
    for solution in solutions:
        keys=list(solution.params.keys())

    for key in keys:
        pareto_data.setdefault(key,[])

    for solution in solutions:
        ret=[]
        key=solution.index
        for k,v in list(solution.params.items()):
            ret.append(v)
        all_data[key]=ret
    pareto_front=pareto_frontiter2D(data_in=all_data)
    return pareto_front

def pareto_frontiter2D(data_in=None, MinX=True, MinY=True):
        '''

        :param data: nx2 nd array for the data [f1,f2]
        :param MinX: If find minX
        :param MinY: If find minY
        :return: pareto frontier
        '''
        # Display only the pareto front solution
        # ID=data[:, 0].tolist()
        data_1 = list(data_in.values())

        
        data=np.array(data_1)
        try:
            X = data[:, 0].tolist()
        except:
            X = range(len(data_in))
            
        try:
            Y = data[:, 1].tolist()
        except:
            Y = range(len(data_in))
        raw_list = [[X[i], Y[i]] for i in range(len(X))]
        data_list = sorted(raw_list, reverse=not (MinX))
        p_front = [data_list[0]]
        for pair in data_list[1:]:
            if MinY:
                if pair[1] <= p_front[-1][1]:  # Look for higher values of Y
                    p_front.append(pair)  # and add them to the Pareto frontier

            else:
                if pair[1] >= p_front[-1][1]:  # Look for lower values of Y
                    p_front.append(pair)  # and add them to the Pareto frontie

        #print "No of Solutions on Pareto-front", len(p_front)
        #print "Total solutions", len(data_1)
        pareto_data = np.array(p_front)

        plot = False
        if plot:

            plt.scatter(pareto_data[:, 0], pareto_data[:, 1])
            plt.show()
        p_data = {}
        for k,v in list(data_in.items()):

            if v in p_front:
                p_data[k]=v

        return p_data

def export_to_eagle(solutions=None, sol_path = None):
    # export to eagle format
    for i in range(len(solutions)):
        item = solutions[i].name
        file_name = sol_path + '/' + item + '.txt'
        with open(file_name, 'w',newline='') as my_file:
            for k, v in list(solutions[i].abstract_info[item]['rect_info'].items()):
                if k[0] == 'T':
                    x1 = v.x / 1000.0
                    x2 = (v.x + v.width) / 1000.0
                    y1 = v.y / 1000.0
                    y2 = (v.y + v.height) / 1000.0
                    print('<rectangle x1="{}" y1="{}" x2="{}" y2="{}" layer="1"/>'.format(str(x1), str(y1),
                                                                                                      str(x2), str(y2)), file=my_file)
            for k, v in list(solutions[i].abstract_info[item]['rect_info'].items()):
                if k == 'Substrate':
                    x1 = v.x / 1000.0
                    x2 = (v.x + v.width) / 1000.0
                    y1 = v.y / 1000.0
                    y2 = (v.y + v.height) / 1000.0
                    print('<rectangle x1="{}" y1="{}" x2="{}" y2="{}" layer="16"/>'.format(str(x1), str(y1),
                                                                                                       str(x2), str(y2)), file=my_file)
                    break

        my_file.close()
def export_solutions(solutions=None,directory=None,pareto_data=None,export = False):
    sol_path = directory + '/Layout_Solutions'
    if pareto_data!=None:
        pareto_path = directory + '/Pareto_Solutions'
    if not os.path.exists(sol_path):
        os.makedirs(sol_path)

    if len(solutions) > 1000:
        print("Thousands of csv files are going to be generated")

    # export to eagle format
    for i in range(len(solutions)):
        for layer_name, abstract_info in solutions[i].abstact_infos.items():
            item = solutions[i].name+'_'+layer_name
            file_name = sol_path + '/' + item + '.txt'
            with open(file_name, 'w',newline='') as my_file:
                for k, v in list(abstract_info['rect_info'].items()):
                    if k[0]=='T' :
                        x1=v.x/1000.0
                        x2=(v.x+v.width)/1000.0
                        y1=v.y/1000.0
                        y2=(v.y+v.height)/1000.0
                        print('<rectangle x1="{}" y1="{}" x2="{}" y2="{}" layer="1"/>'.format(str(x1),str(y1),str(x2),str(y2)), file=my_file)
                for k, v in list(abstract_info['rect_info'].items()):
                    if k=='Substrate':
                        x1 = v.x / 1000.0
                        x2 = (v.x + v.width) / 1000.0
                        y1 = v.y / 1000.0
                        y2 = (v.y + v.height) / 1000.0
                        print('<rectangle x1="{}" y1="{}" x2="{}" y2="{}" layer="16"/>'.format(str(x1), str(y1),str(x2), str(y2)), file=my_file)
                        break



            my_file.close()

    if export:
        export_to_eagle(solutions=solutions,sol_path=sol_path)
    params=solutions[0].params
    performance_names=list(params.keys())
    for i in range(len(solutions)):
        
        item = solutions[i].name
        file_name = sol_path + '/' + item + '.csv'
        with open(file_name, 'w', newline='') as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=',')
            if len (performance_names) >=2: # Multi (2) objectives optimization
                csv_writer.writerow(["Size", performance_names[0], performance_names[1]])
                # for k, v in _fetch_currencies.iteritems():
                Size = solutions[i].abstract_info[item]['Dims']
                Perf_1 = solutions[i].params[performance_names[0]]
                Perf_2 =  solutions[i].params[performance_names[1]]
                data = [Size, Perf_1, Perf_2]
            else: # Single objective eval
                csv_writer.writerow(["Size", performance_names[0]])
                Size = solutions[i].abstract_info[item]['Dims']
                Perf_1 = solutions[i].params[performance_names[0]]
                data = [Size, Perf_1]

            csv_writer.writerow(data)
            csv_writer.writerow(["Component_Name", "x_coordinate", "y_coordinate", "width", "length"])
            for k, v in list(solutions[i].abstract_info[item]['rect_info'].items()):
                layout_data = [k, v.x, v.y, v.width, v.height]
                csv_writer.writerow(layout_data)
        my_csv.close()

    if pareto_data!=None:
        if not os.path.exists(pareto_path):
            # print "path doesn't exist. trying to make"
            os.makedirs(pareto_path)
        for i in range(len(solutions)):
            if solutions[i].index in list(pareto_data.keys()):
                item = solutions[i].name
                file_name = pareto_path + '/' + item + '.csv'
                with open(file_name, 'w') as my_csv:
                    csv_writer = csv.writer(my_csv, delimiter=',')
                    csv_writer.writerow(["Size", performance_names[0], performance_names[1]])
                    # for k, v in _fetch_currencies.iteritems():
                    Size = solutions[i].abstract_info[item]['Dims']
                    Perf_1 = solutions[i].params[performance_names[0]]
                    Perf_2 = solutions[i].params[performance_names[1]]
                    data = [Size, Perf_1, Perf_2]
                    csv_writer.writerow(data)
                    csv_writer.writerow(["Component_Name", "x_coordinate", "y_coordinate", "width", "length"])
                    for k, v in list(solutions[i].abstract_info[item]['rect_info'].items()):
                        layout_data = [k, v.x, v.y, v.width, v.height]
                        csv_writer.writerow(layout_data)
                my_csv.close()


def plot_solutions(file_location=None):
    '''

    :param file: a csv file that has solution information. Will read the line where size, inductance, and temp is available
    :return:
    '''
    files = glob.glob(file_location+'/'+'*.csv')
    all_data={}
    for file in files:

        head, tail = os.path.split(file)
        name=tail.strip('.csv')
        data={}
        with open(file) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                if row[0]=='Size':
                    print(row)
                    key1=row[1]
                    key2=row[2]
                    key3=row[0]
                    continue
                if row[0]=='Component_Name':
                    break
                else:
                    #print row[0],row[1],row[2]

                    data[key1]=(float(row[1])) # inductance (nH)
                    data[key2]=(float(row[2])) # Temperature (K)
                    data[key3]=(row[0]) # size [w,h]
            all_data[name]=data
    print(all_data)
    file_name = head + '/' + 'plot_data' + '.csv'
    with open(file_name, 'w', newline='') as my_csv:
        csv_writer = csv.writer(my_csv, delimiter=',')
        for k, v in list(all_data.items()):
            keys = list(v.keys())
            csv_writer.writerow(["Layout_ID", keys[0],keys[1],keys[2]])
            break
    my_csv.close()

    with open(file_name, 'a') as my_csv:
        csv_writer = csv.writer(my_csv, lineterminator='\n')
        #csv_writer = csv.writer(my_csv, delimiter=',')
        for k, v in list(all_data.items()):
            keys = list(v.keys())
            val=list(v.values())
            data=[k,val[0],val[1],val[2]]

            csv_writer.writerow(data)
    my_csv.close()



    '''
    x=[]
    y=[]
    z=[]
    for k,v in all_data.items():
        keys=v.keys()
        x.append(v[keys[0]])
        y.append(v[keys[1]])
        z.append(v[keys[3]])
    
    '''
def plot_solution(rectlist,name):
    patches=[]
    for r in rectlist:
        if r[0][0]=='T':
            colour='green'
            zorder=0
        elif r[0]=='Substrate':
            size=[float(r[3]),float(r[4])]
            continue
        else:
            zorder=1
            if r[0][0]=='D':
                colour='red'
            if r[0][0]=='L':
                colour='purple'
            if r[0][0]=='B':
                colour='blue'

        P = matplotlib.patches.Rectangle(
            (r[1], r[2]),  # (x,y)
            r[3],  # width
            r[4],  # height
            facecolor=colour,
            alpha=0.5,
            zorder=zorder,
            edgecolor='black',
            linewidth=1,
        )
        patches.append(P)

    fig2, ax2 = plt.subplots()
    for p in patches:
        ax2.add_patch(p)
    ax2.set_xlim(0, size[0])
    ax2.set_ylim(0, size[1])
    ax2.set_aspect('equal')
    #plt.show()
    plt.savefig('D:\Demo\\New_Flow_w_Hierarchy\Journal_Case\Final_Version\Figs\\40X50'+'/'+name+'.png')





if __name__ == '__main__':

    #plot_solutions('D:\Demo\New_Flow_w_Hierarchy\Journal_Case\Final_Version\Solution\\60X60_new\Layout_Solutions')
    '''
    folder_name='D:\Demo\POETS_ANNUAL_MEETING_2019\\testcases_setup\Test\Test_Cases\Half_Bridge_Journal_Tristan\Solution_New\Layout_Solutions'
    all_data=[]
    i=0
    for filename in glob.glob(os.path.join(folder_name, '*.csv')):
        with open(filename) as csvfile:
            base_name= os.path.basename(filename)
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                if row[0] == 'Size':
                    continue
                else:
                    if row[0][0]=='[':
                        data=[base_name,float(row[1]), float(row[2])]
                        all_data.append(data)

                    else:
                        continue
            i += 1
    #for data in all_data:
        #print data
    file_name = 'D:\Demo\POETS_ANNUAL_MEETING_2019\\testcases_setup\Test\Test_Cases\Half_Bridge_Journal_Tristan\Solution_New\\all_data.csv'
    with open(file_name, 'wb') as my_csv:
        csv_writer = csv.writer(my_csv, delimiter=',')
        csv_writer.writerow(['Layout_ID','Temperature','Inductance'])
        for data in all_data:
            if data[2]>20:
                print(data)
                data=[data[0].rsplit('.csv')[0],data[1],data[2]]
                csv_writer.writerow(data)
        my_csv.close()
    '''
    sol_data={}
    file='D:\Demo\\New_Flow_w_Hierarchy\Journal_Case\Journal_Result_collection\Cmd_flow_case\Half_Bridge_Layout\Test_solutions_kelvin\Result_Processing\\all_raw_data.csv'
    with open(file) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            if row[0]=='Layout_ID':
                continue
            else:
                sol_data[(row[0],float(row[3]))]=([float(row[1]), float(row[2])])
    #sol_data = np.array(sol_data)
    #print sol_data
    pareto_data = pareto_frontiter2D(sol_data)
    print(len(pareto_data))
    file_name='D:\Demo\\New_Flow_w_Hierarchy\Journal_Case\Journal_Result_collection\Cmd_flow_case\Half_Bridge_Layout\Test_solutions_kelvin\Result_Processing\\final_pareto.csv'
    with open(file_name, 'w',newline='') as my_csv:
        csv_writer = csv.writer(my_csv, delimiter=',')
        for k,v in list(pareto_data.items()):
            data=[k,v[0],v[1]]
            csv_writer.writerow(data)
    my_csv.close()

    #plot a layout
    '''
    names=[
        'Layout_1708',
        'Layout_1709',
        'Layout_1710',
        'Layout_1711',
        'Layout_1712',
        'Layout_1713',
        'Layout_1714',
        'Layout_1715',
        'Layout_1716',
        'Layout_1717',
        'Layout_1718',
       'Layout_1719',
        'Layout_1720',
        'Layout_1721',
        'Layout_1722',
        'Layout_1723',
        'Layout_1724',
        'Layout_1725',
        'Layout_1726',
        'Layout_1727',
        'Layout_1728',
        'Layout_1729',
        'Layout_1730',
        'Layout_1731',
        'Layout_1732',
        'Layout_1733',
        'Layout_1734',
        'Layout_1735',
        'Layout_1736',
        'Layout_1737',
        'Layout_1738',
        'Layout_1739',
        'Layout_1740',
        'Layout_1741',
        'Layout_1742',
        'Layout_1743'

    ]
    #for name in names:
    rectlist=[]
    name='Layout_1568'
    file = 'D:\Demo\\New_Flow_w_Hierarchy\Journal_Case\Final_Version\Solution\\40X50\Layout_Solutions\\'+name+'.csv'
    start=0
    with open(file) as csvfile:
        c=0
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            c+=1
            if row[0]=='Component_Name':
                start=c
                break
    print start
    with open(file) as csvfile:
        c=0
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            c+=1
            if c>start:
                rect=[row[0],float(row[1]),float(row[2]),float(row[3]),float(row[4])]
                rectlist.append(rect)
    plot_solution(rectlist,name)

    '''




