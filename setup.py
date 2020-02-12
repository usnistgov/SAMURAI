from setuptools import setup,find_packages

setup(name='samurai',
      version='0.1',
      description='Synthetic aperture measurements with uncertainty and angle of incidence (SAMURAI) code.',
      author='Alec Weiss, Ben Jamroz, Rob Jones, Peter Vouras, the NIST SAMURAI Team',
      author_email='alec.weiss@nist.gov, benjamin.jamroz@nist.gov, robert.jones@nist.gov, peter.vouras@nist.gov',
      packages=find_packages(),
      python_requires='>3.3,<4',
     )

#use `pip install -e .` for editable install

