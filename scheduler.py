dotaznik = True

import heapq
from pathlib import Path
from collections import defaultdict
import random


script_dir = Path(__file__).parent




infile = script_dir / "happening_times.txt"
class_length = 15
travel_time = 1
user_type = "jiny" # jiny = vybírá ze všech aktivit, žák = musí být na všech představení své třídy
class_num = "7BG"

if dotaznik:
    travel_time = int(input("Jak dlouhou chcete mít rezervu mezi představeními? [minuty]: "))
    user_type = input('Jste žák? [a] nebo [n]: ')
    if user_type == "n":
        user_type = "jiny"
    elif user_type == "a":
        user_type = "zak"
        class_num = input("Z jaké jste třídy? Např. [2BG], [8AZ]: ")
    

classes_u = {}
# parsing file
with open(infile, "r") as f:
    for line in f:
        c = line.split()
        classes_u[c[0]] = []
        for i in range(1, len(c)):
            classes_u[c[0]].append(int(c[i][2:]) + 60*int(c[i][:2]))

items = list(classes_u.items())
random.shuffle(items)
classes = dict(items)

time_to_class = defaultdict(list)
went_to = {}
for class_i in classes:
    for time in classes[class_i]:
        time_to_class[time].append(class_i)
    went_to[class_i] = False



def activitySelection(time_table: dict, start_table_time: int, end_table_time: int):
    # initialise timetable
    start = []
    finish = []
    class_name = []
    for key, value in time_table.items():
        start.append(value[0])
        start.append(value[1])
        start.append(value[2])
        finish.append(value[0] + class_length)
        finish.append(value[1] + class_length)
        finish.append(value[2] + class_length)
        class_name.append(key)
        class_name.append(key)
        class_name.append(key)

       
    results = []

    # Minimum Priority Queue to sort activities in
    # ascending order of finishing time (end[i]).
    p = []
    for i in range(len(start)):
        heapq.heappush(p, (finish[i], start[i]))

    # to store the end time of last activity
    finishtime = start_table_time
    
    #removed_times = []

    # function main loop
    while p:
        activity = heapq.heappop(p)

        # if activity[1] in removed_times:
        #     removed_times.remove(activity[1])
        #     continue
        
        if activity[0] > end_table_time - travel_time:
            break

        if activity[1] >= finishtime + travel_time:
            finishtime = activity[0]

            while True:
                if time_to_class[activity[1]] == []:
                    name = class_name[start.index(activity[1])]
                    break
                else:
                    name = time_to_class[activity[1]].pop()
                    if not went_to[name]:
                        went_to[name] = True
                        break

            results.append((name, activity[1], activity[0]))
            # times_done = time_table[class_name[index]]
            # for time_done in times_done:
            #     if time_done > activity[1]:
            #         removed_times.append(time_done)
        
        


    return results


# main loop
if user_type == "jiny":
    time_plan = activitySelection(classes, -1, 9999)
    time_plan_set = set()
    print("Váš nejlepší plán:")
    for i in range(len(time_plan)):
        time_plan[i] = (time_plan[i][0], str(time_plan[i][1] // 60) + ":" + str(time_plan[i][1] % 60), str(time_plan[i][2] // 60) + ":" + str(time_plan[i][2] % 60))
        print(time_plan[i])
        time_plan_set.add(time_plan[i][0])
    print(f"Počet navštívených představení: {len(time_plan)}")
    print(f"Počet navštívených tříd (unikátní představení): {len(time_plan_set)}")
    

elif user_type == "zak":
    mandatory_times = classes[class_num]
    mandatory_times.sort()
    time_plan = []
    time_plan.extend(activitySelection(classes, -1, mandatory_times[0]))
    time_plan.append((class_num, mandatory_times[0], mandatory_times[0] + class_length))
    time_plan.extend(activitySelection(classes, mandatory_times[0] + class_length, mandatory_times[1]))
    time_plan.append((class_num, mandatory_times[1], mandatory_times[1] + class_length))
    time_plan.extend(activitySelection(classes, mandatory_times[1] + class_length, mandatory_times[2]))
    time_plan.append((class_num, mandatory_times[2], mandatory_times[2] + class_length))
    time_plan.extend(activitySelection(classes, mandatory_times[2] + class_length, 9999))

    print("Váš nejlepší plán:")
    time_plan_set = set()
    for i in range(len(time_plan)):
        time_plan[i] = (time_plan[i][0], str(time_plan[i][1] // 60) + ":" + str(time_plan[i][1] % 60), str(time_plan[i][2] // 60) + ":" + str(time_plan[i][2] % 60))
        print(time_plan[i])
        time_plan_set.add(time_plan[i][0])
    print(f"Počet navštívených představení: {len(time_plan)}")
    print(f"Počet navštívených tříd (unikátní představení): {len(time_plan_set)}")