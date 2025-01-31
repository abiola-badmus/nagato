import os
try:
    import bpy
except ModuleNotFoundError:
    pass
from . import gazu
import re

# Set/created upon register.
profile_path = ''
profile_file = ''

# profile_path = ''
# profile_file = ''

class NagatoProfile():
    """Current Nagato profile.

    This is always stored at class level, as there is only one current
    profile anyway.
    """
    host = ''
    login = False
    user = None
    access_token = ''
    refresh_token = ''
    ldap = False

    lastest_openfile = {'file_path': None, 'task_id': None}
    tasks = dict()
    active_project = None
    active_task_type = None

    @classmethod
    def reset(cls):
        cls.host = ''
        cls.login = False
        cls.user = None
        cls.access_token = ''
        cls.refresh_token = ''
        cls.ldap = False
        cls._create_default_file()
        return {'logout': True}

    @classmethod
    def read_json(cls):
        """Updates the active profile information from the JSON file."""
        # cls.reset()
        active_profile = cls.get_profile_data()
        return active_profile

    @classmethod
    def save_json(cls):
        """Updates the JSON file with the active profile information."""
        jsonfile = {
            "host": cls.host,
            "login": cls.login,
            "user": cls.user,
            "ldap": cls.ldap,
            "access_token": cls.access_token,
            "refresh_token": cls.refresh_token
        }

        cls.save_profile_data(jsonfile)
    
    def slugify(text,separator='-', lowercase=True):
        """
        Make a slug from the given text.
        :param text (str): initial text
        :param separator (str): separator between words
        :param lowercase (bool): activate case sensitivity by setting it to False
        :return (str):
        """
        DEFAULT_SEPARATOR = '-'
        QUOTE_PATTERN = re.compile(r'[\']+')
        ALLOWED_CHARS_PATTERN = re.compile(r'[^-a-z0-9]+')
        DUPLICATE_DASH_PATTERN = re.compile(r'-{2,}')
        NUMBERS_PATTERN = re.compile(r'(?<=\d),(?=\d)')
        # replace quotes with dashes - pre-process
        text = QUOTE_PATTERN.sub(separator, text)

        # make the text lowercase (optional)
        if lowercase:
            text = text.lower()

        # remove generated quotes -- post-process
        text = QUOTE_PATTERN.sub('', text)

        # cleanup numbers
        text = NUMBERS_PATTERN.sub('', text)

        text = re.sub(ALLOWED_CHARS_PATTERN, DEFAULT_SEPARATOR, text)

        # remove redundant
        text = DUPLICATE_DASH_PATTERN.sub(DEFAULT_SEPARATOR, text).strip(DEFAULT_SEPARATOR)
        if separator != DEFAULT_SEPARATOR:
            text = text.replace(DEFAULT_SEPARATOR, separator)

        return text

    def task_file_directory(task_type: str, blend_file_path: str, project: dict):
        '''
            returns the full file path of a task
        '''
        try:
            file_map = project['data']['file_map']
        except KeyError:
            file_map = {'shading':'base','concept':'none','modeling':'base','rigging':'base','storyboard':'none','layout':'layout',
                        'previz':'layout','animation':'anim','lighting':'lighting','fx':'fx','rendering':'lighting','compositing':'comp',}
        if task_type.lower() in {'editing', 'edit'}:
            task_type_map = 'base'
        else:
            try:
                task_type_map = file_map[task_type.lower()]
            except KeyError:
                task_type_map = 'none'
        if task_type_map == 'base':
            directory = f'{blend_file_path}.blend'
            return directory
        elif task_type_map == 'none':
            pass
        else:
            directory = f'{blend_file_path}_{task_type_map}.blend'
            return directory

    @classmethod
    def refresh_tasks(cls):
        tasks = cls.get_zou_tasks()
        #TODO prebuild file path from genesis
        for task in tasks:
            project_id = task['project_id']
            project = gazu.project.get_project(project_id)
            task_type = task['task_type_name'].lower()
            task['working_file_path'] = gazu.files.build_working_file_path(task['id'])
            blend_file_path = os.path.expanduser(task['working_file_path'])

            if task_type.lower() in {'editing', 'edit'}:
                project_file_name = cls.slugify(project['name'], separator="_")
                if task['episode_name'] == None:
                    base_file_directory = os.path.join(project['file_tree']['working']['mountpoint'], \
                    project['file_tree']['working']['root'],project_file_name,'edit','edit.blend')
                else:
                    episode_name = cls.slugify(task['episode_name'], separator="_")
                    base_file_directory = os.path.join(project['file_tree']['working']['mountpoint'], \
                        project['file_tree']['working']['root'],project_file_name,'edit',f"{episode_name}_edit.blend")
                directory = os.path.expanduser(base_file_directory)
                task['full_working_file_path'] = directory
            else:
                task['full_working_file_path'] = cls.task_file_directory(task_type, blend_file_path, project)

        cls.tasks = cls.structure_task(tasks)
        cls.active_project = None
        cls.active_task_type = None

    @staticmethod
    def get_zou_tasks():
        tasks = gazu.user.all_tasks_to_do()
        return tasks

    @classmethod
    def group_task(cls, tasks:dict, fliter:str):
        new_grouped_tasks = dict()
        for task in tasks:
            group_name = task[fliter]
            if group_name not in new_grouped_tasks:
                new_grouped_tasks[group_name] = [task]
            else:
                new_grouped_tasks[group_name].append(task)
        for key in new_grouped_tasks.keys():
            new_grouped_tasks[key] = sorted(new_grouped_tasks[key], key = lambda i: i['entity_name'])
        return(new_grouped_tasks)
    
    @classmethod
    def structure_task(cls, tasks):
        tasks_by_projects = cls.group_task(tasks, 'project_name')
        for project in tasks_by_projects:
            project_tasks = tasks_by_projects[project]
            project_tasks_by_type = cls.group_task(project_tasks, 'task_type_name')
            tasks_by_projects[project] = project_tasks_by_type
            
        return tasks_by_projects

    @staticmethod
    def _create_default_file():
        """Creates the default profile file, returning its contents."""
        import json

        profile_default_data = {'login': False, 'user': None, 'ldap': False, 'access_token': None, 'refresh_token': None}
        os.makedirs(profile_path, exist_ok=True)

        # Populate the file, ensuring that its permissions are restrictive enough.
        old_umask = os.umask(0o077)
        try:
            with open(profile_file, 'w', encoding='utf8') as outfile:
                json.dump(profile_default_data, outfile)
        finally:
            os.umask(old_umask)

        return profile_default_data

    @staticmethod
    def get_active_user():
        """Get the id of the currently active profile. If there is no
        active profile on the file, this function will return None.
        """

        return __class__.get_profile_data()['user']

    @staticmethod
    def get_profile_data():
        """Pick the active profile from profiles.json. If there is no
        active profile on the file, this function will return None.

        @returns: dict like {'user_id': 1234, 'username': 'email@blender.org'}
        """

        import json

        # if the file does not exist
        if not os.path.exists(profile_file):
            return __class__._create_default_file()

        # try parsing the file
        with open(profile_file, 'r', encoding='utf8') as f:
            try:
                file_data = json.load(f)
                file_data['user']
                file_data['access_token']
                file_data['login']
                return file_data
            except (ValueError,  # malformed json data
                    KeyError):  # it doesn't have the expected content
                print('(%s) '
                    'Warning: profiles.json is either empty or malformed. '
                    'The file will be reset.' % __name__)

                # overwrite the file
                return __class__._create_default_file()

    @staticmethod
    def save_profile_data(profile: dict):
        """Saves the profile data to JSON."""
        import json

        with open(profile_file, 'w', encoding='utf8') as outfile:
            json.dump(profile, outfile, sort_keys=True)


class NagatoTasks():
    tasks = None


def register():
    global profile_path, profile_file
    profile_path = bpy.utils.user_resource('CONFIG', 'nagato', create=True)
    # profile_path = 'C:/Users/Tanjiro/AppData/Roaming/Blender Foundation/Blender/2.83/config/nagato'
    profile_file = os.path.join(profile_path, 'profiles.json')


