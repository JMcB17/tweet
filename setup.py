import setuptools
import tweet


with open('README.md', 'r', encoding='utf-8') as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name='tweet',
    version=tweet.__version__,
    author='Joel McBride',
    author_email='joel.mcbride1@live.com',
    license='GPLv3',
    description='Random thought saver',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/JMcB17/tweet',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'tweet=tweet:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Environment :: Console',
    ],
    python_requires='>=3'
)
