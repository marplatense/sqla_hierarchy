from setuptools import setup

readme = open('README.rst', 'r')
README_TEXT = readme.read()
readme.close()

setup(
    name='sqla_hierarchy',
    packages=['sqla_hierarchy'],
    version='0.1',
    description='Adjacency List Relationships helper (only using databases own implementations)',
    long_description=README_TEXT,
    author='Mariano Mara',
    author_email='mariano.mara@gmail.com',
    url='https://github.com/marplatense/sqla_hierarchy',
    download_url='https://github.com/marplatense/sqla_hierarchy/downloads',
    license='MIT License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords = ['sqlachemy', 'hierarchy', 'adjacency list', 'python']
    ,install_requires=['sqlalchemy<0.7']
)
