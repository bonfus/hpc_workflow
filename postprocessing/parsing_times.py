
import numpy as np
import matplotlib.pyplot as plt
import argparse
import colorsys
from collections import defaultdict
from aux_routines import *


parser = argparse.ArgumentParser()
parser.add_argument("workflow_pk",type=int,nargs='+',help="workflow number")
args = parser.parse_args()
scale = str([3,2,2])


#nomi = []
times = defaultdict(list)
wfpk = defaultdict(list)
structures = defaultdict(list)
labels = defaultdict(list)
count_wf=0
string_for_title=defaultdict(list)
computer_cores = []
calculation_PK = defaultdict(list)
number_of_iterations = defaultdict(list)


for wf_pk in args.workflow_pk:
    wf = load_workflow(wf_pk)
    subworkflows = wf.get_steps()[1].get_sub_workflows()
    count_sub_wf=0
    for i in subworkflows:
        calc=i.get_all_calcs()
        values=list(calc[0].get_inputs_dict()['structure'].get_composition().viewvalues())
        keys=list(calc[0].get_inputs_dict()['structure'].get_composition().viewkeys())
        name=''
        names = []
        if count_sub_wf is 0:
            count_sub_wf+=1
            computer_MPI = calc[0].get_computer().get_default_mpiprocs_per_machine()
            computer_cores.append(computer_MPI)
        for q in range(len(values)):
           name+=keys[q]+str(values[q])
        names.append(name)
        structure = name
        nomi = []
        tempi = []
        count_wf_calc=0
        for j in calc[1:]:
            kpoints=j.get_extras()['parallelization_dict']['nk']
            name='nk_'
            name+=str(kpoints)
            if (j.get_state() == 'FINISHED' or j.get_state() == 'FAILED') and \
              'Error while parsing the output file' not in j.res.parser_warnings:
              try:
                 tempi.append(j.res.wall_time_seconds)
                 number_of_iterations[structure].append(j.res.total_number_of_scf_iterations)
              except AttributeError:
                 tempi.append(0.0)
                 number_of_iterations[structure].append(0)
              nkpoints=j.res.number_of_k_points
              cutoff=j.get_inputs_dict()['parameters'].get_attrs()['SYSTEM']['ecutwfc']
              string_for_title[structure].append(structure+'_nk_'+str(nkpoints)+'_cutoff_'+str(cutoff))
            else:
              tempi.append(0.0)
              energie.append(0.0)
              string_for_title[structure].append(structure)
            nomi.append(name)
            calculation_PK[structure].append(j)
            count_wf_calc+=1
        for k in nomi:
            structures[structure].append(k)

        for k in tempi:
            times[structure].append(k)
            wfpk[structure].append(count_wf)
            computer=str(subworkflows[0].get_all_calcs()[1].get_code()).split()[4][:-1]
            labels[structure].append(computer)
    count_wf+=1

#for k,v in labels.iteritems():
#    v[4] = 'PizDaintGPU'

print 'Calculations PK'
print ''
for k,v in calculation_PK.iteritems():
   print k,v
print 'Number of iterations'
print ''
for k,v in number_of_iterations.iteritems():
   print k,v


new_array=defaultdict(list)
new_array_all=defaultdict(list)
iterations_completed=defaultdict(list)
keys_computers=labels.values()[0]


for i in structures:
    print 'Struct #',i, times[i], number_of_iterations[i], all_same(number_of_iterations[i]),  (all(times[i])>0.0), len(times[i]),len(args.workflow_pk)
    if all_same(number_of_iterations[i]) and (all(times[i])>0.0) and (len(times[i]) is len(args.workflow_pk)):
       new_array[i].append(times[i])
    if(all(times[i])>0.0) and (len(times[i]) is len(args.workflow_pk)):
       new_array_all[i].append(times[i])
       iterations_completed[i].append(number_of_iterations[i])
       
    
print 'Calculations with the same number of iterations:'
print ''
for k,v in new_array.iteritems():
   print k,v
print 'Calculations with the different number of iterations:'
print ''
for k,v in new_array_all.iteritems():
   print k,v



values_summary_plot=create_plot_array(new_array)
values_summary_plot_all=create_plot_array(new_array_all)
values_summary_plot_iterations=create_plot_array(iterations_completed)

computer_summary_plot=np.array(computer_cores)
keys_summary_plot=keys_computers

width=1.0/(len(keys_summary_plot)+1)
ind = np.arange(len(keys_summary_plot))
colors = []
labels_plot = []
N = len(keys_summary_plot)
HSV_tuples = [(x*1.0/N, 0.5, 0.5) for x in range(N)]
RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
for i in range(len(keys_summary_plot)):
    colors.append(RGB_tuples[i])
    labels_plot.append(keys_summary_plot[i])

def create_plots(figure,array,title,ind,width,colors,labels_plot,nome_file):
    plt.figure(figure)
    fig, ax = plt.subplots()
    tts=ax.bar(ind+width, array, width, color=colors,label=labels_plot )
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width , box.height* 0.9])
    ax.set_ylabel('Time(s)')
    ax.set_title(title)
    ax.set_xticks(ind)
    ax.legend(tts,labels_plot,loc='upper center',ncol=3, bbox_to_anchor=(0.5,1.25))
    plt.savefig(nome_file)


print 'AAAAA', values_summary_plot, labels_plot
create_plots(0,values_summary_plot,'Average times - per node '+scale,
            ind,width,colors,labels_plot,'riassunto_node.png')

create_plots(1,values_summary_plot_all*computer_summary_plot,'Average times - per core'+scale,
            ind,width,colors,labels_plot,'riassunto_core.png')
create_plots(2,values_summary_plot_all,'Average times - per node'+scale,
            ind,width,colors,labels_plot,'riassunto_node_all.png')
create_plots(3,values_summary_plot_iterations,'Average number of iterations'+scale,
            ind,width,colors,labels_plot,'riassunto_iterations.png')



for t in xrange(0,len(structures)):
    
    plt.figure(t)
    fig, ax = plt.subplots()
    width=1.0/(len(times.values()[t])+1)
    ind = np.arange(len(times.values()[t]))
    tts={}
    energy={}

    colors = []
    labels_plot = []
    N = len(args.workflow_pk)
    HSV_tuples = [(x*1.0/N, 0.5, 0.5) for x in range(N)]
    RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)

    for i in range(len(times.values()[t])):
      colors.append(RGB_tuples[wfpk.values()[t][i]])
      labels_plot.append(labels.values()[t][i])
 
    tts[t]=ax.bar(ind+width, times.values()[t], width, color=colors,label=labels_plot )


    ax.set_ylabel('Time(s)')

    ax.set_title(string_for_title.values()[t][0])
    ax.set_xticks(ind)
    ax.set_xticklabels(structures.values()[t][0:len(ind)],rotation=45)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    ax.legend(tts[t],labels.values()[t],loc='upper center',ncol=1, bbox_to_anchor=(1.20,1.02))
    plt.savefig(structures.keys()[t])


    fig, bx = plt.subplots()



