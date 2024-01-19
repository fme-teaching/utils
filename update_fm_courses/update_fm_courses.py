from github import Github
import json
import re  # for validating URLs

# For this to work, you need to provide an API key
# (in a file fme_github_keys.py and var fme_github_key)
from fme_github_keys import fme_github_key

# Github repository with course data
courses_repo = 'fme-teaching/fm-courses'


def map_to_keys(field):
    # Normalize field
    field = field.lower()
    # The following dictionary maps the keys used in Github issues
    # to the keys that we want to use internally (e.g. in the json data)
    d = {'course code, if applicable': 'course_code',
         'university hosting the course': 'course_institution',
         'contact person': 'course_contact',
         'concepts taught': 'course_concepts',
         'tools used': 'course_tools',
         'webpage': 'course_webpage',
         'year/level': 'course_year_level',
         'reviewed': 'reviewed'
         }
    if field not in d:
        d[field] = ''
    return d[field]


def process_issue_body(issue_body):
    """ Each issue corresponds to a course.
    This function extracts the information from the issue body
    and creates a dictionary with that information.

    We assume the following order of fields (keys):
        - Course code, if applicable:
        - University hosting the course
        - Contact person
        - Concepts taught
        - Tools used
        - Webpage
    """

    # We first create a list with elements of type (name, [[key, value]])
    flist = filter(lambda f: len(f) == 2,
                   map(lambda f: f.split(': '), issue_body.split('\r\n')))

    # We now normalise the keys
    flist_norm = map(lambda pair: [map_to_keys(pair[0]), pair[1].strip()],
                     flist)

    return dict(flist_norm)


def standardise_keyword(word):
    """ The idea is to define here all the transformations that we want
    to do so that keywords are uniform. For example, 'hoare logic' and
    'Hoare logic' are both mapped to 'Hoare Logic'.
    """
    new_word = word.strip().title()
    return new_word


def is_valid_url(url):
    regex = re.compile(
      r'^(?:http|ftp)s?://'  # http:// or https://
      r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
      r'localhost|'  # localhost...
      r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
      r'(?::\d+)?'  # optional port
      r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


def create_list_courses(courses_repo, fme_github_key):
    # Create access based on the key provided
    g = Github(fme_github_key)

    # Get all courses (open issues)
    repo = g.get_repo(courses_repo)
    open_issues = repo.get_issues(state='open')

    courses = []
    for issue in open_issues:
            course = process_issue_body(issue.body)
            course['course_title'] = issue.title

            if issue.labels:
                course['course_country'] = issue.labels[0].name

            # Change string of tools and concepts to list
            if 'course_concepts' in course and course['course_concepts']:
                concepts = course['course_concepts']
                concepts = list(map(lambda s: standardise_keyword(s),
                                    concepts.split(',')))
                course['course_concepts'] = concepts
            else:
                course['course_concepts'] = ["Unknown"]
            if 'course_tools' in course and course['course_tools']:
                tools = course['course_tools']
                tools = list(map(lambda s: standardise_keyword(s),
                                 tools.split(',')))
                course['course_tools'] = tools
            else:
                course['course_tools'] = ["Unknown"]

            # Check whether the institution is defined
            if 'course_institution' not in course:
                course['course_institution'] = ["Unknown"]

            # Check whether the year/level is defined
            if 'course_year_level' not in course:
                course['course_year_level'] = ["Unknown"]

            # Check whether the webpage is defined and remove trailing /
            if 'course_webpage' not in course:
                course['course_webpage'] = "#"
            else:
                course['course_webpage'] = \
                    course['course_webpage'].split(' ')[0]
                webpage = course['course_webpage']
                if is_valid_url(webpage):
                    if len(webpage) > 0 and webpage[-1] == '/':
                        course['course_webpage'] = webpage[:-1]
                else:
                    course['course_webpage'] = "#"

            # Remove email address from contact.
            if 'course_contact' in course:
                contact = course['course_contact'].split(',')
                if len(contact) > 1:
                    contact_name, contact_email = contact
                    if (PRINT_EMAILS):
                        print(contact_email.strip())
                else:
                    contact_name = contact[0]
                course['course_contact'] = contact_name

            courses.append(course.copy())

    return courses


def list_by_key(list_courses, key):
    """ Given a list of courses (as dictionaries) and a key, this
    function returns a sorted list of all the 'keys' used.
    """
    concepts = []
    for course in list_courses:
        concepts.extend(course[key])
    concepts = list(set(concepts))
    concepts.sort()
    return concepts


def list_of_countries(list_courses):
    """ Given a list of courses (as dictionaries), this function
    returns a sorted list of all the countries used.
    """
    countries = []
    for course in list_courses:
        # IMPORTANT: note the use of lists for course_country
        if 'course_country' in course:
            countries.extend([course['course_country']])
    countries = list(set(countries))
    countries.sort()
    return countries


# Driver code below

PRINT_EMAILS = False

courses = create_list_courses(courses_repo, fme_github_key)
courses_json = json.dumps(courses, indent=4)

concepts = list_by_key(courses, 'course_concepts')
concepts_json = json.dumps(concepts, indent=4)

tools = list_by_key(courses, 'course_tools')
tools_json = json.dumps(tools, indent=4)

countries = list_of_countries(courses)
countries_json = json.dumps(countries, indent=4)


# Write to file
f_out = open('fme-courses-github.js', 'w')
f_out.write('var courses = \n')
f_out.write(courses_json)
f_out.write('\nvar concepts = \n')
f_out.write(concepts_json)
f_out.write('\nvar tools = \n')
f_out.write(tools_json)
f_out.write('\nvar countries = \n')
f_out.write(countries_json)
f_out.close()
