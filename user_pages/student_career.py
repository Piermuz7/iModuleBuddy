import streamlit as st
from utils.neo4j_methods import Neo4jMethods
from utils.supabase_methods import get_student, update_student, create_student
from utils.models import Student

MANDATORY_MODULES = [
    "Alignment of Business and IT",
    "Business Intelligence",
    "Business Process Management",
    "Strategic Business Innovation"
]
MAX_MODULES = 10  # Maximum allowed modules
MAX_FREE_MODULES = 6  # Maximum free modules (36 credits)

INDIVIDUAL = "INDIVIDUAL"
GROUP = "GROUP"
INDIVIDUAL_AND_GROUP = "INDIVIDUAL_AND_GROUP"

st.title("Student Career and Preferences Details")
student = get_student()
new_account = False
if student is None:
    new_account = True
    student = Student.new_student()
neo4j_methods = Neo4jMethods()
courses = neo4j_methods.get_filtered_modules()
occupations = neo4j_methods.get_occupations()
professors = neo4j_methods.get_professors()

project_type_labels = {
    "Individual Project": INDIVIDUAL,
    "Group Project": GROUP,
    "Both": INDIVIDUAL_AND_GROUP
}

# student -> desired_lecturers, available_days, individual_or_group_exam, oral_exam_or_not, project_work

with st.form("my_form"):
    name = st.text_input("Name", value=student.name)
    surname = st.text_input("Surname", value=student.surname)
    part_time = st.checkbox("I am a Part-Time Student", value=not student.full_time)
    semesters = st.slider("Expected Semesters", 3, 10, value=student.expected_semesters)
    desired_jobs = st.multiselect(
        "Select your career path",
        occupations,
        placeholder="Choose zero or more options",
        default=filter(lambda i: i in student.desired_jobs, occupations),
    )
    taken_courses = st.multiselect(
        "Courses already taken",
        courses,
        default=filter(lambda i: i in student.taken_courses, courses),
        placeholder="Choose zero or more options",
    )
    # to_take_courses = st.multiselect("Courses you'd like to take",
    #                                  filter(lambda i: i not in taken_courses, courses),
    #                                  placeholder='Choose one or more options', )
    desired_lecturers = st.multiselect(
        "Select your desired lecturers",
        professors,
        placeholder="Choose zero or more options",
        default=filter(lambda i: i in student.desired_lecturers, professors),
    )

    # Day of week selection
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    available_days = st.multiselect(
        "Select your available days",
        options=days_of_week,
        placeholder="Choose one or more days"
    )

    # Individual or group exam
    project_type_label = st.radio(
        "Select the type of project you are interested in:",
        options=list(project_type_labels.keys())
    )
    assessment_type = project_type_labels[project_type_label]

    # Oral exam
    oral_exam_label = st.radio(
        "Select if you want an oral assessment or not:",
        options=["Oral Exam", "No Oral Exam"]
    )
    # Map to boolean
    oral_assessment = oral_exam_label == "Oral Exam"

    # Project Work
    project_work_label = st.radio(
        "Select if you want a project work or not:",
        options=["Project Work", "No Project Work"]
    )
    # Map to boolean
    project_work = project_work_label == "Project Work"

    submitted = st.form_submit_button("Submit")
    if submitted:
        # Perform validation
        free_modules_selected = [module for module in taken_courses if module not in MANDATORY_MODULES]
        mandatory_modules_selected = [module for module in taken_courses if module in MANDATORY_MODULES]
        missing_mandatory = [module for module in MANDATORY_MODULES if module not in taken_courses]

        # Case 1: Exceeding total module limit
        if len(taken_courses) > MAX_MODULES:
            st.error("Submission failed: You cannot select more than 10 modules (60 credits).")
        # Case 2: Not enough space for mandatory modules
        elif len(free_modules_selected) > MAX_FREE_MODULES:
            st.error(
                f"Submission failed: You have selected {len(free_modules_selected)} free modules. "
                f"This leaves insufficient space for all mandatory modules: {', '.join(missing_mandatory)}"
            )
        # Case 3: Valid submission
        else:
            # Create or update the student record
            new_s = Student(
                desired_jobs,
                not part_time,
                student.id,
                name,
                surname,
                semesters,
                taken_courses,
                desired_lecturers,
                available_days,
                assessment_type,
                oral_assessment,
                project_work
            )
            data = create_student(new_s) if new_account else update_student(new_s)
            if data is not None:
                st.success("Your details have been saved successfully.")
                new_account = False