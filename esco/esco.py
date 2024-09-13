import requests

API_OCCUPATION_URL = 'https://ec.europa.eu/esco/api/resource/occupation'
API_SKILL_URL = 'https://ec.europa.eu/esco/api/resource/skill'
SELECTED_VERSION = 'v1.2.0'


class Skill:
    def __init__(self, title, uri, skill_type, description=""):
        self.uri = uri
        self.title = title
        self.skill_type = skill_type
        self.description = description

    def __repr__(self):
        return (f'Skill(uri={self.uri!r}, title={self.title!r}, skill_type={self.skill_type!r}, '
                f'description={self.description!r})')


class Occupation:
    def __init__(self, title, description, skills, optional_skills, uri):
        self.uri = uri
        self.title = title
        self.description = description
        self.skills = skills
        self.optional_skills = optional_skills

    def __repr__(self):
        return (f'Occupation(uri={self.uri!r}, title={self.title!r}, description={self.description!r}, '
                f'skills={self.skills!r}, optional_skills={self.optional_skills!r})')


def fetch_occupation_json(uri):
    params = {
        'uri': uri,
        'selectedVersion': SELECTED_VERSION
    }
    try:
        response = requests.get(API_OCCUPATION_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data for URI {uri}: {e}")
        return {}


def fetch_skill_json(uri):
    """Fetch skill details from the API_SKILL_URL."""
    params = {
        'uri': uri,
        'selectedVersion': SELECTED_VERSION
    }
    try:
        response = requests.get(API_SKILL_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching skill data for URI {uri}: {e}")
        return {}


def extract_skills(json_data, link_key):
    skills = []

    for skill in json_data.get('_links', {}).get(link_key, []):
        skill_name = skill.get('title')
        skill_uri = skill.get('uri')
        skill_category = skill.get('skillType')

        # Fetch the description of the skill from the API
        skill_description_json = fetch_skill_json(skill_uri)
        skill_description = skill_description_json.get('description', {}).get('en', {}).get('literal', '')

        if skill_category == 'http://data.europa.eu/esco/skill-type/skill':
            skills.append(Skill(skill_name, skill_uri, 'skill', description=skill_description))
        elif skill_category == 'http://data.europa.eu/esco/skill-type/knowledge':
            skills.append(Skill(skill_name, skill_uri, 'knowledge', description=skill_description))

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

