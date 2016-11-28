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
    version='0.1.3',
    long_description=readme(),
    packages=find_packages(),
    install_requires=[
        'haikunator==2.1.0',
        'azure==2.0.0rc6',
        'boto3==1.4.0',
        'google-cloud==0.21.0',
        'cryptography==1.4'
    ]
)
