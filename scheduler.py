dotaznik = False

import heapq
from pathlib import Path
from collections import defaultdict
import random


script_dir = Path(__file__).parent


infile = script_dir / "happening_times.txt"
class_length = 15
travel_time = 1
user_type = "jiny" # jiny = vybírá ze všech aktivit, zak = musí být na všech představení své třídy
class_num = "7BG"
priority_classes = ["6BG", "8AZ", "2AG", "5AG", "7BG", "9BZ"]

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

best_time_plan = []
best_time_plan_set = 0
could_fit_p_classes = True # check at end

for _ in range(1000):

    items = list(classes_u.items())
    random.shuffle(items)
    classes = dict(items)

    time_to_class = defaultdict(list)
    went_to = {}
    for class_i in classes:
        for time in classes[class_i]:
            time_to_class[time].append(class_i)
        went_to[class_i] = False

    skeleton = []
    if user_type == "zak":
        mandatory_times = classes[class_num]
        mandatory_times.sort()
        for time in mandatory_times:
            skeleton.append((class_num, time, time + class_length))
    
    restart = False
    for p_class in priority_classes:
        move_p_class = False
        random.shuffle(classes[p_class])
        for time in classes[p_class]: 
            collision = False           
            for s in skeleton:
                if max(s[1] - travel_time, time - travel_time) < min(s[2], time + class_length):
                    collision = True
                    break
            if not collision:
                skeleton.append((p_class, time, time + class_length))
                break
        else:
            restart = True
        if restart:
            break

    if restart:
        continue





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

        # function main loop
        while p:
            activity = heapq.heappop(p)
            
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

        return results


    
    if user_type == "jiny" and priority_classes == []:
        time_plan = activitySelection(classes, -1, 9999) 
        
    else:
        skeleton.sort(key=lambda x: x[2])
        skeleton.append(("EXIT", 9998, 9999))
        time_plan = []
        time_plan.extend(activitySelection(classes, -1, skeleton[0][1]))
        for bone_i in range(len(skeleton) - 1):
            time_plan.append((skeleton[bone_i][0], skeleton[bone_i][1], skeleton[bone_i][2]))
            time_plan.extend(activitySelection(classes, skeleton[bone_i][2], skeleton[bone_i + 1][1]))
        

    time_plan_set = set()
    for i in range(len(time_plan)):
        time_plan[i] = (time_plan[i][0], str(time_plan[i][1] // 60) + ":" + str(time_plan[i][1] % 60), str(time_plan[i][2] // 60) + ":" + str(time_plan[i][2] % 60))
        time_plan_set.add(time_plan[i][0])
    
    if len(time_plan_set) > best_time_plan_set:
        best_time_plan = time_plan
        best_time_plan_set = len(time_plan_set)
   
if best_time_plan == []:
    print("Nepodařilo se najít plán")
else:
    print("Váš nejlepší plán:")
    for i in range(len(best_time_plan)):
        print(best_time_plan[i])

    print(f"Počet navštívených představení: {len(best_time_plan)}")
    print(f"Počet navštívených tříd (unikátní představení): {best_time_plan_set}")