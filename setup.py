from setuptools import find_packages, setup

setup(
    name='dlernen',
    version='1.1.1',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
        'mysql-connector-python',
        'jsonschema',
        'requests'
    ],
)
