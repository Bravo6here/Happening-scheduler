

from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
import random
import time

# Branch and bound pro max unikátních, greedy pro max všech


@dataclass
class Performance():
    class_name: str
    start: int
    end: int
    bit_id: int
    bit_mask: int # From the right, e.g. 0100 is ID 2
    bit_collision: int | None = None

    def collides_with(self, other: "Performance", travel_time: int) -> bool:
        """Kolidují 2 představení?"""
        return not (self.start >= other.end + travel_time or self.end + travel_time <= other.start)

    def collides_with_fast(self, other: "Performance") -> bool:
        """Využívá bit masku"""
        return (self.bit_collision & other.bit_mask)

    def __repr__(self) -> str:
        """Hezké print"""
        s_h, s_m = self.start // 60, self.start % 60
        e_h, e_m = self.end // 60, self.end % 60
        return f"{self.class_name}_{self.bit_id} {s_h:02d}:{s_m:02d} - {e_h:02d}:{e_m:02d}"

    @classmethod
    def from_raw_time(cls, class_name: str, start_time: str, length: int, bit_id: int):
        """Konstruktor přímo z textu"""
        start = int(start_time[:2]) * 60 + int(start_time[2:])
        return cls(class_name, start, start + length, bit_id, 1 << bit_id)


class ScheduleOptimizerCore():
    @staticmethod
    def load_times_from_file(filepath: Path, cls_length: int = 15) -> dict[str, list[Performance]]:
        all_performances = {}
        with open(filepath, "r") as f:
            bit_id = 0
            for line in f:
                parts = line.strip().split()
                if not parts: continue
                cls_name = parts[0]
                cls_perfs = []
                for t in parts[1:]:
                    cls_perfs.append(Performance.from_raw_time(cls_name, t, cls_length, bit_id))
                    bit_id += 1
                all_performances[cls_name] = cls_perfs
                #all_performances[cls_name] = [Performance.from_raw_time(cls_name, t, cls_length, bit_id) for t in parts[1:]]

        return all_performances

    @staticmethod
    def solve_priorities(user_class: str | None, referee: str | None, priority_classes: list[str], travel_time: int, data: dict[str, list[Performance]]) -> list[Performance] | None:
        """První fáze řešení. Výroba rozvrhu pouze z prioritních představení."""
        start_skeleton = []
        steps = [0]

        random.shuffle(priority_classes)

        if user_class is not None:
            for perf in data[user_class]:
                start_skeleton.append(perf)
            if user_class in priority_classes:
                priority_classes.remove(user_class)

        if referee is not None:
            match(referee):
                case "Vyšší gymnázium":
                    for referee_class in ["5AG", "5BG", "6AG", "6BG", "7AG", "7BG"]:
                        if referee_class not in priority_classes:
                            priority_classes.append(referee_class)
                case "Nižší gymnázium":
                    for referee_class in ["1AG", "1BG", "2AG", "2BG", "3AG", "3BG", "4AG", "4BG"]:
                        if referee_class not in priority_classes:
                            priority_classes.append(referee_class)
                case "Zakladní škola":
                    for referee_class in ["6AZ", "6BZ", "7AZ", "7BZ", "8AZ", "8BZ", "9AZ", "9BZ"]:
                        if referee_class not in priority_classes:
                            priority_classes.append(referee_class)
                

        total_priorities = len(priority_classes)

        def backtrack(index: int, current_skeleton: list[Performance]) -> list[Performance] | None:
            steps[0] += 1

            if index == total_priorities:
                return list(current_skeleton)

            target_class = priority_classes[index]
            available_slots = data.get(target_class, [])

            for slot in available_slots:
                collision = any(slot.collides_with(scheduled, travel_time) for scheduled in current_skeleton)
                if not collision:
                    current_skeleton.append(slot)

                    result = backtrack(index + 1, current_skeleton)

                    if result is not None: # Byl nalezen rozvrh
                        return result

                    current_skeleton.pop() # Slepá cesta

            return None

        
        r = backtrack(0, list(start_skeleton))
        print(f"Uděláno: {steps[0]} kroků")
        return r

    @staticmethod
    def create_sorted_performances_list(data: dict[str, list[Performance]]) -> list[Performance]:
        all_performances = []
        for perfs in data.values():
            for perf in perfs:
                all_performances.append(perf)

        random.shuffle(all_performances)
        sorted_performances = ScheduleOptimizerCore.sort_performances_list(all_performances)
        return sorted_performances

    @staticmethod
    def sort_performances_list(all_performances: list[Performance]) -> list[Performance]:
        return sorted(all_performances, key=lambda x: x.end)

    @staticmethod
    def create_bit_map(tt: int, data: dict[str, list[Performance]]):
        list_performances = ScheduleOptimizerCore.create_sorted_performances_list(data)
        for performance in list_performances:
            performance.bit_collision = 0
            for other_performance in list_performances:
                if not (performance.start >= other_performance.end + tt or performance.end + tt <= other_performance.start): # collides with
                    performance.bit_collision = performance.bit_collision | other_performance.bit_mask
        
        


    @staticmethod
    def solve_rest_fill(skeleton: list[Performance], travel_time: int, sorted_performances: list[Performance]) -> list[Performance]:
        for candidate in sorted_performances:
            not_collides = True
            for bone in skeleton:
                if candidate.collides_with(bone, travel_time):
                    not_collides = False
                    break
            if not_collides:
                skeleton.append(candidate)
        return ScheduleOptimizerCore.sort_performances_list(skeleton)

    @staticmethod
    def find_most_priorities(user_class: str | None, priority_classes: list[str], travel_time: int, data: dict[str, list[Performance]]) -> list[Performance]:
        start_skeleton = []

        random.shuffle(priority_classes)

        if user_class is not None:
            for perf in data[user_class]:
                start_skeleton.append(perf)

        greedy_skeleton = list(start_skeleton)
        greedy_score = 0

        for target_class in priority_classes:
            for slot in data.get(target_class, []):
                if not any(slot.collides_with(s, travel_time) for s in greedy_skeleton):
                    greedy_skeleton.append(slot)
                    greedy_score += 1
                    break  # vezmi první možný a jdi na další třídu
               
        total_priorities = len(priority_classes)
        best_score = greedy_score # B&B teď začíná s vysokým laťkem, ořezává hned od 1. úrovně!
        best_skeleton = list(greedy_skeleton)

        start_mask = 0
        for perf in start_skeleton:
            start_mask |= perf.bit_collision

        def branch_and_bound(index: int, current_skeleton: list[Performance], current_score: int, current_mask: int): #TODO: Přidat referee
            nonlocal best_score, best_skeleton

            if current_score > best_score:
                best_score = current_score
                best_skeleton = list(current_skeleton)

            if index == total_priorities:
                return

            if total_priorities + current_score - index <= best_score:
                return

            target_class = priority_classes[index]
            available_slots = data.get(target_class, [])

            for slot in available_slots:
                #collision = any(slot.collides_with(scheduled, travel_time) for scheduled in current_skeleton)
                collision = (slot.bit_mask & current_mask) != 0
                if not collision:
                    current_skeleton.append(slot)
                    branch_and_bound(index + 1, current_skeleton, current_score + 1, current_mask | slot.bit_collision)
                    current_skeleton.pop()                    
            branch_and_bound(index + 1, current_skeleton, current_score, current_mask)

        branch_and_bound(0, start_skeleton, 0, start_mask)
        print(f"Nejvíce je možno mít {best_score} z {total_priorities}. Zde je nejlepší rozvrh:")
        print(ScheduleOptimizerCore.sort_performances_list(best_skeleton))




class SchedulePlaner():
    """Nejvyšší abstrakce"""
    DEFAULT_CLASS_LENGTH: int = 15
    DEFAULT_TRAVEL_TIME: int = 5
    DEFAULT_FILE_PATH: Path = (Path(__file__).parent / "happening_times.txt")

    def __init__(self, file_path: Path = DEFAULT_FILE_PATH, class_length: int = DEFAULT_CLASS_LENGTH):
        self.file_path: Path = file_path
        self.class_length = class_length
        self.data = self._set_up()
        
    def _set_up(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"Konfigurační soubor nenalezen: {self.file_path}")
        
        return ScheduleOptimizerCore.load_times_from_file(self.file_path, self.class_length)

    def check_priority_schedule(self, user_class: str | None, referee: str | None, priority_classes: list[str], travel_time: int = DEFAULT_TRAVEL_TIME) -> bool | None:

        if ScheduleOptimizerCore.solve_priorities(user_class, referee, priority_classes, travel_time, self.data) is None:
            return None
        else:
            return True

    def make_priority_schedule(self, user_class: str | None, referee: str | None, priority_classes: list[str], travel_time: int = DEFAULT_TRAVEL_TIME) -> tuple[list[dict], list[Performance]]:
        rozvrh: list[dict] = []
        performance_list = ScheduleOptimizerCore.solve_priorities(user_class, referee, priority_classes, travel_time, self.data)
        for perf in performance_list:
            rozvrh.append({
                            "Představení": perf.class_name, 
                            "Místnost": "Zatím nevím",
                            "Čas začátku": f"{perf.start // 60:02d}:{perf.start % 60:02d}",
                            "Čas konce": f"{perf.end // 60:02d}:{perf.end % 60:02d}"
                        })
        return (rozvrh, performance_list)

    def fill_priority_schedule(self, priority_performances: list[Performance], travel_time: int, all_performances: list[str]) -> list[dict]:
        all_performances_perf = []
        for a_perf in all_performances:
            for perf in self.data.get(a_perf, []):
                all_performances_perf.append(perf)

        rozvrh: list[dict] = []
        performance_list = ScheduleOptimizerCore.solve_rest_fill(priority_performances, travel_time, ScheduleOptimizerCore.sort_performances_list(all_performances_perf))
        for perf in performance_list:
            rozvrh.append({
                            "Představení": perf.class_name, 
                            "Místnost": "Zatím nevím",
                            "Čas začátku": f"{perf.start // 60:02d}:{perf.start % 60:02d}",
                            "Čas konce": f"{perf.end // 60:02d}:{perf.end % 60:02d}"
                        })
        return rozvrh



if __name__ == "__main__":
    
    script_dir = Path(__file__).parent
    infile = script_dir / "happening_times.txt"
    
    class_length = 15
    
    data = ScheduleOptimizerCore.load_times_from_file(infile, class_length)
    
    user_class = None #"7BG"
    priority_classes = ["1AG", "1BG", "2AG", "2BG", "3AG", "3BG", "4AG", "4BG", "5AG", "5BG", "6AG", "6BG", "7AG", "7BG"]#, "6AZ", "6BZ", "7AZ", "7BZ", "8AZ", "8BZ", "9AZ", "9BZ"]
    travel_time = 5

    
        
    result_priorities = ScheduleOptimizerCore.solve_priorities(user_class, None, priority_classes, travel_time, data)
    #print(result_priorities)
    

    # sorted_performances = ScheduleOptimizerCore.create_sorted_performances_list(data)
    # if result_priorities is not None:
    #     plan = ScheduleOptimizerCore.solve_rest_fill(result_priorities, travel_time, sorted_performances)
    #     # print(plan)
    #     print(f"Délka: {len(plan)}")


    #start_time_c = time.perf_counter()
    #ScheduleOptimizerCore.create_bit_map(travel_time, data)
    
    #ScheduleOptimizerCore.find_most_priorities(user_class, priority_classes, travel_time, data)
    #end_time_c = time.perf_counter()
    
    #elapsed_ms = (end_time_c - start_time_c) * 1000
    #print(f"Výpočet trval: {elapsed_ms:.3f} ms")