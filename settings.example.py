DEBUG = True
TEMPLATE_DEBUG = DEBUG
ADMINS = ()
MANAGERS = ADMINS
DATABASES = {}
TIME_ZONE = 'Europe/Amsterdam'
LANGUAGE_CODE = 'nl-nl'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
MEDIA_URL = '/static'
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

ROOT_URLCONF = 'tkb.urls'
TEMPLATE_DIRS = ()
INSTALLED_APPS = (
        'tkb'
)

MEDIA_ROOT = '/change/me'
SECRET_KEY = 'CHANGE ME'
