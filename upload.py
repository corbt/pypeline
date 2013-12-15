import os
import shutil
import pypandoc

def register():
    # print doc.rst
    with open('README.txt','w') as f:
        f.write(pypandoc.convert('README.md', 'rst'))

    os.system("python setup.py register")
    os.remove('README.txt')

def upload():
    os.system("python setup.py sdist upload")
    shutil.rmtree('pypeline_db.egg-info')

register()
upload()