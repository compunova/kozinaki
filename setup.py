from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='Kozinaki',
    description='OpenStack multi-cloud driver for AWS, Azure',
    url='https://github.com/compunova/kozinaki.git',
    author='Compunova',
    author_email='kozinaki@compu-nova.com',
    version='0.1.5',
    long_description=readme(),
    packages=find_packages(),
    install_requires=[
        'haikunator==2.1.0',
        'requests==2.11',
        'azure==2.0.0rc6',
        'boto3==1.4.0',
        'google-cloud==0.21.0',
        'cryptography==1.4',
        'Fabric3==1.12.post1',
        'Jinja2==2.8',
        'PyYAML==3.12',
        'terminaltables==3.1.0',
    ],
    entry_points={
        'console_scripts': [
            'kozinaki-manage=kozinaki.manage.__main__:main',
        ],
    }
)
