r"""
File required to relese on PyPI. More info here:
https://packaging.python.org/distributing/#packaging-your-project

To push a new release, assuming running on Windows:
1. Increment the `VERSION` below appropriately.
2. Delete old distributions:
    del dist
3. Build the `source` and `wheel` distributions with:
    python setup.py sdist bdist_wheel
4. Update the registered package on PyPI with `twine`:
    twine register dist\swagger_conformance-<VERSION>-py3-none-any.whl
5. Upload the new packages:
    twine upload dist\*
"""
from setuptools import find_packages, setup
import pypandoc

VERSION = '0.1.2'
URL = 'https://github.com/olipratt/swagger-conformance'
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
