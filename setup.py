from setuptools import setup, find_packages

setup(
    name='disstat',
    version='1.0.1',
    description='A Python wrapper for the DisStat API.',
    author='Your Name',
    author_email='TheUntraceable@The-Untraceable.xz',
    url='https://github.com/TheUntraceable/disstat',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)
