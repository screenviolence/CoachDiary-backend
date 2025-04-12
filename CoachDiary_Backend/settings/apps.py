DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'users.apps.UsersConfig',
    'students.apps.StudentsConfig',
    'standards.apps.StandardsConfig',
    'common.apps.CommonConfig'
]

EXTERNAL_APPS = [
    'rest_framework',
    'corsheaders',
    'django_extensions',
    'drf_spectacular',
]

INSTALLED_APPS = [
    *DJANGO_APPS,
    *LOCAL_APPS,
    *EXTERNAL_APPS,
]
