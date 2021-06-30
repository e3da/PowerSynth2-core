
import csv
import copy
import sys
import os

def input_script_generator(solution_csv=None,initial_input_script=None,exported_input_script=None):
    '''
    :param solution_csv: a csv file with bottom-left coordinate of each component in the layout
    :param initial_input_script: initial input script
    :return: updated input script
    '''

    solution_rows=[]
    with open(solution_csv, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # skip first row
        for row in reader:
            if row[0]=='Component_Name':
                continue
            elif len(row)>4:
                solution_rows.append(row)


    #print solution_rows
    solution_script=[]

    with open(initial_input_script) as fp:
        line = fp.readlines()
    for l in line:
        texts = l.split(' ')
        solution_script.append(texts)
    print (len(solution_script),solution_script)
    solution_script_info=[]
    for row in solution_rows:
        if row[0] == 'Substrate':
            solution_script_info.append([row[3],row[4]])
        else:

            for l in line:
                texts=l.strip().split(' ')

                if len(texts)>=5:

                    if row[0]!='Substrate' and row[0] in texts:
                        texts_new = copy.deepcopy(texts)

                        if (row[0][0]=='T' or row[0][0]=='B'):

                            for i in range(len(texts)):
                                if texts[i].isdigit():
                                    #x_index=i
                                    #print i
                                    break
                                else:
                                    texts_new[i]=texts[i]
                            texts_new[i]=row[1]
                            texts_new[i+1]=row[2]
                            #if row[0][0]!='D' or row[0][0]!='L':
                            texts_new[i+2]=row[3]
                            texts_new[i+3]=row[4]
                        else:
                            for i in range(len(texts)):
                                if texts[i].isdigit():
                                    #x_index=i
                                    #print i
                                    break
                                else:
                                    texts_new[i]=texts[i]
                            texts_new[i]=row[1]
                            texts_new[i+1]=row[2]



                        if texts_new not in solution_script_info:
                            solution_script_info.append(texts_new)

    print (len(solution_script_info),solution_script_info)
    if exported_input_script==None:
        directory=os.path.dirname(initial_input_script)
        file = open(directory+"/Exported.txt", "w")
    else:
	    file=open(exported_input_script,"w")

    #file.write("Text to write to file")
    #file.close()
    lines=[]
    for line in solution_script:

        if len(line)==2 and line[0].isdigit():
            for row in solution_script_info:
                if len(row)==2:
                    line[0]=row[0]
                    line[1]=row[1]
        else:
            for row in solution_script_info:
                if row[1] in line:
                    start_index=line.index(row[1])
                    end_index=start_index+len(row)
                    #print start_index, end_index
                    line[start_index:end_index+1]=row[1:]

        #print line
        for element in line:
            #print element
            file.write(element)
            file.write(' ')

        file.write('\n')
        lines.append(line)

    #file.write("\n".join(str(item) for item in lines))
    #for line in lines:
        #file.write(line)


    file.close()






input_script_generator(solution_csv='/nethome/qmle/testcases/Unit_Test_Cases/Case_0_0/Solutions/Solution_7.csv',
                       initial_input_script="/nethome/qmle/testcases/Unit_Test_Cases/Case_0_0/layout_main.txt",
					   exported_input_script="/nethome/qmle/testcases/Unit_Test_Cases/Case_0_0/layout_7.txt")
