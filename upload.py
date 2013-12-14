import os
import shutil

os.system("python setup.py sdist upload")
shutil.rmtree('pypeline_db.egg-info')