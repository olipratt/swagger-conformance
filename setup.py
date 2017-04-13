from setuptools import find_packages, setup
import pypandoc


def readme():
    return pypandoc.convert('readme.md', 'rst')


setup(
    name='swagger-conformance',
    packages=find_packages(exclude=['examples', 'docs', 'tests']),
    install_requires=['hypothesis', 'pyswagger', 'requests'],
    version='0.1',
    description="Tool for testing whether your API conforms to it's swagger specification",
    long_description=readme(),
    author='Oli Pratt',
    author_email='olipratt@users.noreply.github.com',
    url='https://github.com/olipratt/swagger-conformance',
    download_url='https://github.com/olipratt/swagger-conformance/archive/0.1.tar.gz',
    keywords=['swagger', 'testing', 'OpenAPI', 'hypothesis'],
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
