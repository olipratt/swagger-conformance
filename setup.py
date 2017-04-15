from setuptools import find_packages, setup
import pypandoc

URL = 'https://github.com/olipratt/swagger-conformance'
VERSION = '0.1.1'
LONG_DESC = pypandoc.convert('readme.md', 'rst').replace('\r\n', '\n')


setup(
    name='swagger-conformance',
    packages=find_packages(exclude=['examples', 'docs', 'tests']),
    install_requires=['hypothesis', 'pyswagger>=0.8.28', 'requests'],
    version=VERSION,
    description="Tool for testing whether your API conforms to its swagger "
                "specification",
    long_description=LONG_DESC,
    author='Oli Pratt',
    author_email='olipratt@users.noreply.github.com',
    url=URL,
    download_url='{}/archive/{}.tar.gz'.format(URL, VERSION),
    keywords=['swagger', 'testing', 'OpenAPI', 'hypothesis'],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
