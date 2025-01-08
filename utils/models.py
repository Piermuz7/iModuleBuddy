from typing import List, Optional

class Student:
    def __init__(self,
                 desired_jobs: Optional[List[str]], 
                 full_time: bool, 
                 id: str, 
                 name: str, 
                 surname: str,
                 expected_semesters: int,
                 taken_courses: Optional[List[str]]):
        self.desired_jobs = desired_jobs or []
        self.full_time = full_time
        self.id = id
        self.name = name
        self.surname = surname
        self.expected_semesters = expected_semesters
        self.taken_courses = taken_courses or []

    def to_dict(self) -> dict:
        """Converts the Student object to a dictionary."""
        return {
            'desired_jobs': self.desired_jobs,
            'full_time': self.full_time,
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'taken_courses': self.taken_courses,
            'expected_semesters': self.expected_semesters
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Student':
        """Creates a Student object from a dictionary."""
        return cls(
            desired_jobs=data.get('desired_jobs', []),
            full_time=data['full_time'],
            id=data['id'],
            name=data['name'],
            surname=data['surname'],
            expected_semesters=data['expected_semesters'],
            taken_courses=data.get('taken_courses', [])
        )

    def __repr__(self) -> str:
        """String representation of the object."""
        return f"Student(id={self.id}, name={self.name}, surname={self.surname})"

    @classmethod
    def new_student(cls) -> 'Student':
        """Creates a new student with default values."""
        return cls([], True, "", "", "", 3, [])