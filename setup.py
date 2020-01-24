from setuptools import setup,find_packages

setup(name='Distutils',
      version='0.1',
      description='Synthetic aperture measurements with uncertainty and angle of incidence (SAMURAI) code.',
      author='Alec Weiss, Ben Jamroz, Rob Jones, NIST',
      author_email='alec.weiss@nist.gov',
      packages=find_packages(where='samurai'),
      python_requires='>3.3,<4',
      package_dir={'': 'samurai'},
     )


#use `pip install -e .` for editable install

