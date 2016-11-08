from setuptools import setup, find_packages

setup(
    name='kozinaki',
    description='OpenStack nova driver for cloud providers',
    url='https://github.com/compunova/kozinaki.git',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'haikunator==2.1.0',
        'azure==2.0.0rc6',
        'boto3==1.4.0'
    ]
    )
