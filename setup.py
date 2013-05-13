from setuptools import setup

setup(
    name = 'GithubPlugin',
    version = '0.5.2',
    author = 'Colin Snover',
    author_email = 'tracplugins@zetafleet.com',
    description = 'GitHub support for Trac',
    long_description = 'Adds GitHub post-commit hook support to Trac.',
    url = 'https://github.com/csnover/github-trac',
    license = 'New BSD',
    packages = ['github'],
    package_data = { 'github' : [] },

    install_requires = [
        'Trac',
        'simplejson>=2.0.5'
    ],

    entry_points = {
        'trac.plugins': [
            'github = github.github'
        ]
    }
)
