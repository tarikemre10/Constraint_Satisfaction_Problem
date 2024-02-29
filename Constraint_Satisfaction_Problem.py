import csv
import os

def read_csv(file_path):
    """
    Reads a CSV file from the given relative path and prints its contents.
    """
    # Convert the relative path to an absolute path based on the script's location
    script_dir = os.path.dirname(__file__)  # Gets the directory where the script is located
    absolute_file_path = os.path.join(script_dir, file_path)

    data_list = []
    try:
        with open(absolute_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                data_list.append(row)
        return data_list
    except FileNotFoundError:
        print(f"File not found: {absolute_file_path}")

def create_useful_lists(classrooms_csv, coordinations_csv, courses_csv, preferences_csv):
    classrooms = arrange_classrooms(classrooms_csv)
    coordinations = arrange_coordinations(coordinations_csv)
    courses = arrange_courses(courses_csv)
    preferences = arrange_preferences(preferences_csv)
    return classrooms, coordinations, courses, preferences

def arrange_classrooms(classrooms_csv):
    del classrooms_csv[0]
    return classrooms_csv

def arrange_courses(classrooms_csv):
    del classrooms_csv[0]
    return classrooms_csv

#Convert the preferences csv file into a dictionary instructor:times key:value pairs
def arrange_preferences(instructor_csv):
    instructor_dict = {}
    del instructor_csv[0]
    for instructor in instructor_csv:
        instructor_dict[instructor[0]]=turn_to_list(instructor[1])
    return instructor_dict  

#Splits the time values of instructions and converts to a list.
def turn_to_list(input_list):    
    return input_list.split() 

def arrange_coordinations(coordinations_csv):
    del coordinations_csv[0]
    liste=[]
    for class_name in coordinations_csv:
        liste.append(turn_to_list(class_name[0]))
    return liste
      
    
def is_consecutive(hours_list):
    # Example of hours_list: ['Mon1', 'Mon2', 'Mon3']
    days = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4}

    # Convert hours_list into a list of tuples (day_index, hour)
    converted_hours = [(days[hour[:3]], int(hour[3:])) for hour in hours_list]

    # Sort by day and hour
    converted_hours.sort()

    # Check for consecutivity
    for i in range(len(converted_hours) - 1):
        current_day, current_hour = converted_hours[i]
        next_day, next_hour = converted_hours[i + 1]

        # Check if next hour is consecutive
        if not (next_day == current_day and next_hour == current_hour + 1):
            return False

    return True

def is_classroom_suitable(classroom, student_count):
    
    return int(classroom[1]) >= student_count

def generate_domains(courses, classrooms, preferences, coordinations):
    # Dictionary to store assignments classified by course names
    domain_dict = {}  

    for course in courses:
        course_info = [course[0], course[1], course[2], course[3]]  
        
        if course_info[0] not in domain_dict:
            domain_dict[course_info[0]] = []

        inst_pref = preferences.get(course_info[1], [])
        last_start_hour = len(inst_pref) - int(course_info[3]) + 1

        for pref_iter in range(last_start_hour):
            assigned_hours = [inst_pref[pref_iter + hour_count] for hour_count in range(int(course_info[3]))]
            course_info_with_time = course_info + [assigned_hours]
            
            if is_consecutive(assigned_hours):
                for classroom in classrooms:
                    if is_classroom_suitable(classroom, int(course_info[2])):
                        course_info_with_class = course_info_with_time + [classroom]
                        domain_dict[course_info[0]].append(course_info_with_class)

    return domain_dict

    
    
def generate_schedule(courses, classrooms, preferences, coordinations):
    all_assignments = []

    # Checks classroom capacity
    def is_classroom_suitable(classroom, student_count):
        return int(classroom[1]) >= student_count  # Convert capacity to int and compare.

    # Checks instructor availibility
    def instructor_already_assigned(instructor_id, time_slot, current_assignment):
        
        for assignment in current_assignment:
            
            if assignment[1] == instructor_id and set(assignment[4]).intersection(time_slot):
                return True  
            
        return False

    # Checks classroom availibility
    def classroom_already_assigned(classroom_name, time_slot, current_assignment):
        
        for assignment in current_assignment:
            
            if assignment[5] == classroom_name and set(assignment[4]).intersection(time_slot):
                return True 
            
        return False

    # checks if consecutive
    def is_not_consecutive(time_slots):
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
            # Check for each day if both the 4th and 5th hours are included.
            if f"{day}4" in time_slots and f"{day}5" in time_slots:
                return True  
        return False
    
    # Checks for scheduling conflicts among coordinated courses in the current assignment.
    def is_coordinated_conflict(course_name, time_slot, current_assignment):
    
    # Iterate through each course in the current assignment.        
        coordinated_ones = []
        for coordinated_courses in coordinations:
            
            if course_name in coordinated_courses:
                       
                for coordinated_course in coordinated_courses:
                    
                    if not coordinated_course== course_name:
                        coordinated_ones.append(coordinated_course)
                    
                for assignment2 in current_assignment:
                    
                    if assignment2[0] in coordinated_ones and  is_intersected(assignment2[4],time_slot):
                        
                        return True
                                
        return False    
                
    def is_intersected(list1,list2):
        for item1 in list1:
            for item2 in list2:
                if item1 == item2:
                    return True        
        return False
            

    # Recursive function to build the schedule assigning each course.
    def add_assignment(course_index, current_assignment):
        if course_index == len(courses):
            # All courses assigned completely, add the current assignment to the assignment list.
            all_assignments.append(current_assignment.copy())
            return

        course = courses[course_index]
        
        course_name, instructor_id, student_count_str, course_hours_str = course
        student_count = int(student_count_str) 
        course_hours = int(course_hours_str)    

        available_times = preferences.get(instructor_id, [])

        # Iterate each starting time for the course.
        for start_time_index in range(len(available_times) - course_hours + 1):
            # Formulate a time list for the course.
            time_list = available_times[start_time_index:start_time_index + course_hours]

            # Skip this time list if it violates the lunch break or coordinated conflict.
            if is_not_consecutive(time_list) or is_coordinated_conflict(course_name, time_list, current_assignment):
                continue

            # Check each classroom for suitability and availability.
            for classroom in classrooms:
                if is_classroom_suitable(classroom, student_count):
                    # Create a potential assignment for this course.
                    assignment = [course_name, instructor_id, student_count, course_hours, time_list, classroom[0], classroom[1]]

                    # Check for any conflicts with instructors or classrooms.
                    if instructor_already_assigned(instructor_id, time_list, current_assignment) or classroom_already_assigned(classroom[0], time_list, current_assignment):
                        continue  # Skip if there is a conflict.

                    # Temporarily add the assignment to the current set for further exploration.
                    current_assignment.append(assignment)
                    # Recursively try to add the next course.
                    add_assignment(course_index + 1, current_assignment)
                    # Remove the last assignment to backtrack and try other possibilities.
                    current_assignment.pop()

    # Initiate the recursive process of schedule generation.
    add_assignment(0, [])
    return all_assignments


def simplify_assignment(assignment):
    # Simplify an individual assignment
    course_name = assignment[0]
    time_slots = assignment[4][0]
    classroom_name = assignment[5]
    return [course_name, time_slots, classroom_name]


def write_assignments_to_csv(all_assignments):
    
    for i, assignment_set in enumerate(all_assignments):
        filename = f"assignment_set_{i+1}.csv"
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Course Name', 'Time Slots', 'Classroom Name'])

            for assignment in assignment_set:
                simplified_assignment = simplify_assignment(assignment)
                writer.writerow(simplified_assignment)
        print(f"Written Assignment Set {i+1} to {filename}")


#Paths
classrooms_path = "./problem1/classrooms.csv"
coordinations_path = "./problem1/coordinations.csv"
courses_path = "./problem1/courses.csv"
preferences_path = "./problem1/preferences.csv"

#Reading csvs
classrooms_csv = read_csv(classrooms_path)
coordinations_csv= read_csv(coordinations_path)
courses_csv = read_csv(courses_path)
preferences_csv = read_csv(preferences_path)
classrooms, coordinations, courses, preferences = create_useful_lists(classrooms_csv,coordinations_csv,courses_csv,preferences_csv)

#Execute functions
assignments = generate_schedule(courses,classrooms,preferences,coordinations)
write_assignments_to_csv(assignments)