from typing import List, Optional


class Student:
    def __init__(self,
                 desired_jobs: Optional[List[str]],
                 id: str,
                 name: str,
                 surname: str,
                 expected_semesters: int,
                 taken_courses: Optional[List[str]],
                 desired_lecturers: Optional[List[str]],
                 available_days: Optional[List[str]],
                 assessment_type: str,
                 oral_assessment: bool,
                 project_work: bool):
        self.desired_jobs = desired_jobs or []
        self.id = id
        self.name = name
        self.surname = surname
        self.expected_semesters = expected_semesters
        self.taken_courses = taken_courses or []
        self.desired_lecturers = desired_lecturers or []
        self.available_days = available_days or []
        self.assessment_type = assessment_type
        self.oral_assessment = oral_assessment
        self.project_work = project_work

    def to_dict(self) -> dict:
        """Converts the Student object to a dictionary."""
        return {
            'desired_jobs': self.desired_jobs,
            'full_time': self.full_time,
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'taken_courses': self.taken_courses,
            'expected_semesters': self.expected_semesters,
            'desired_lecturers': self.desired_lecturers,
            'available_days': self.available_days,
            'assessment_type': self.assessment_type,
            'oral_assessment': self.oral_assessment,
            'project_work': self.project_work
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Student':
        """Creates a Student object from a dictionary."""
        return cls(
            desired_jobs=data.get('desired_jobs', []),
            id=data['id'],
            name=data['name'],
            surname=data['surname'],
            expected_semesters=data['expected_semesters'],
            taken_courses=data.get('taken_courses', []),
            desired_lecturers=data.get('desired_lecturers'),
            available_days=data.get('available_days', []),
            assessment_type=data['assessment_type'],
            oral_assessment=data['oral_assessment'],
            project_work=data['project_work']
        )

    def __repr__(self) -> str:
        """String representation of the object."""
        return f"Student(id={self.id}, name={self.name}, surname={self.surname})"

    @classmethod
    def new_student(cls) -> 'Student':
        """Creates a new student with default values."""
        return cls([], True, "", "", "", 3, [], [], [], "", False, False)
