from setuptools import setup,find_packages

setup(name='samurai',
      version='0.1.0',
      description='Synthetic aperture measurements with uncertainty and angle of incidence (SAMURAI) code.',
      author='Alec Weiss, Ben Jamroz, Rob Jones, Peter Vouras, Jeanne Quimby, Rodney Leonhardt, Kate Remley, Dylan Williams, NIST SAMURAI Team',
      author_email=['{}@nist.gov'.format(name) for name in ['alec.weiss','benjamin.jamroz','robert.jones','peter.vouras','jeanne.quimby','rodney.leonhardt','kate.remley','dylan.williams']],
      packages=find_packages(),
      package_data={'':['*command_sets/*.json']},
      python_requires='>3.3,<4',
     )

#use `pip install -e .` for editable install

