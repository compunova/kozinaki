from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='kozinaki',
    description='OpenStack multi-cloud driver for AWS, Azure',
    url='https://github.com/compunova/kozinaki.git',
    author='Compunova',
    author_email='kozinaki@compu-nova.com',
    version='0.1.6',
    long_description=readme(),
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'haikunator',
        'requests==2.11',
        'azure',
        'boto3',
        'google-cloud',
        'cryptography',
        'Fabric3',
        'Jinja2',
        'PyYAML',
        'terminaltables',
        'apache-libcloud',
    ],
    entry_points={
        'console_scripts': [
            'kozinaki-manage=kozinaki.manage.__main__:main',
        ],
    }
)
