DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'CoachDiary_Backend',
    'users.apps.UsersConfig',
    'students.apps.StudentsConfig',
    'standards.apps.StandardsConfig',
    'common.apps.CommonConfig'
]

EXTERNAL_APPS = [
    'rest_framework',
    'oauth2_provider',
    'corsheaders',
    'django_extensions',
    'drf_spectacular',
]

INSTALLED_APPS = [
    *DJANGO_APPS,
    *LOCAL_APPS,
    *EXTERNAL_APPS,
]
