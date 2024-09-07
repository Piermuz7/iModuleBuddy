import requests

API_BASE_URL = 'https://ec.europa.eu/esco/api/resource/occupation'
SELECTED_VERSION = 'v1.2.0'


class Skill:
    def __init__(self, title, uri, skill_type):
        self.uri = uri
        self.title = title
        self.skill_type = skill_type

    def __repr__(self):
        return f'Skill(uri={self.uri!r}, title={self.title!r}, skill_type={self.skill_type!r})'


class Occupation:
    def __init__(self, title, description, skills, optional_skills, uri):
        self.uri = uri
        self.title = title
        self.description = description
        self.skills = skills
        self.optional_skills = optional_skills

    def __repr__(self):
        return (f'Occupation(uri={self.uri!r}, title={self.title!r}, description={self.description!r}, '
                f'skills={self.skills!r}, 'f'optional_skills={self.optional_skills!r}, )')


def fetch_occupation_json(uri):
    params = {
        'uri': uri,
        'selectedVersion': SELECTED_VERSION
    }
    try:
        response = requests.get(API_BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data for URI {uri}: {e}")
        return {}


def extract_skills(json_data, link_key):
    skills = []

    for skill in json_data.get('_links', {}).get(link_key, []):
        skill_name = skill.get('title')
        skill_uri = skill.get('uri')
        skill_category = skill.get('skillType')
        if skill_category == 'http://data.europa.eu/esco/skill-type/skill':
            skills.append(Skill(skill_name, skill_uri, 'skill'))
        elif skill_category == 'http://data.europa.eu/esco/skill-type/knowledge':
            skills.append(Skill(skill_name, skill_uri, 'knowledge'))

    return skills


def build_occupation(json_data):
    job_title = json_data.get('title')
    job_description = json_data.get('description', {}).get('en', {}).get('literal', '')

    # Extract the URI from the JSON data
    uri = json_data.get('uri', '')

    skills = extract_skills(json_data, 'hasEssentialSkill')
    optional_skills = extract_skills(json_data, 'hasOptionalSkill')

    return Occupation(job_title, job_description, skills, optional_skills, uri)


def gather_occupations(uri):
    json_data = fetch_occupation_json(uri)
    occupations = []

    # Check for both 'narrowerOccupation' and 'narrowerConcept'
    narrower_uris = json_data.get('_links', {}).get('narrowerOccupation', []) + json_data.get('_links', {}).get(
        'narrowerConcept', [])

    for narrower_occupation in narrower_uris:
        narrower_occupation_uri = narrower_occupation.get('uri')
        if narrower_occupation_uri:
            occupations.extend(gather_occupations(narrower_occupation_uri))

    if 'hasEssentialSkill' in json_data.get('_links', {}):
        occupation = build_occupation(json_data)
        occupations.append(occupation)

    return occupations
