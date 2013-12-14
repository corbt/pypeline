import pypandoc
import os

# print doc.rst
with open('README.txt','w') as f:
    f.write(pypandoc.convert('README.md', 'rst'))

os.system("python setup.py register")
os.remove('README.txt')