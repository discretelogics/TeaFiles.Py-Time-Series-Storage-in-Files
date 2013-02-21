from distutils.core import setup

setup(
    name='teafiles',
    version='0.7.4',
    author='discretelogics',
    author_email='pythonapi@discretelogics.com',
    url='http://discretelogics.com',
    download_url='http://pypi.python.org/packages/source/t/teafiles',
    description='Time Series storage in flat files.',
    long_description=open('README.txt').read(),

    packages=["teafiles"],
    #package_dir={'': 'teafiles'},
    py_modules=['examples'],
    
    keywords='timeseries time series analysis event processing teatime simulation finance',
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    classifiers= [
                  #  'Development Status :: 3 - Alpha' // pypi chokes on that
                    'Intended Audience :: Developers',
                    'Intended Audience :: Science/Research',
                    'License :: OSI Approved',
                    'License :: OSI Approved :: GNU General Public License (GPL)',
                    'Operating System :: MacOS',
                    'Operating System :: Microsoft :: Windows',
                    'Operating System :: POSIX',
                    'Operating System :: Unix',
                    'Programming Language :: Python',
                    'Topic :: Scientific/Engineering',
                    'Topic :: Software Development'
                    
                  ]
    )
