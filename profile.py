import os
try:
    import bpy
except ModuleNotFoundError:
    pass
from . import gazu

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

    @classmethod
    def refresh_tasks(cls):
        tasks = cls.get_zou_tasks()
        #TODO prebuild file path from genesis
        for task in tasks:
            task['working_file_path'] = gazu.files.build_working_file_path(task['id'])

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


