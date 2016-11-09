from setuptools import setup, find_packages

setup(
    name='Kozinaki',
    description='OpenStack multi-cloud driver for AWS, Azure',
    url='https://github.com/compunova/kozinaki.git',
    author='Compunova',
    author_email='kozinaki@compu-nova.com',
    version='0.1.1',
    packages=find_packages(),
    install_requires=[
        'haikunator==2.1.0',
        'azure==2.0.0rc6',
        'boto3==1.4.0'
    ]
    )
