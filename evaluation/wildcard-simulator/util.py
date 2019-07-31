import os,shutil
import numpy as np

'''
Error handler function
It will try to change file permission and call the calling function again,
'''
def handleError(func, path, exc_info):
    print('Handling Error for file ' , path)
    print(exc_info)
    # Check if file access issue
    if not os.access(path, os.W_OK):
       print('Hello')
       # Try to change the permision of file
       os.chmod(path, stat.S_IWUSR)
       # call the calling function again
       func(path)

def index_marks(nrows, chunk_size):
    return range(1 * chunk_size, (nrows // chunk_size + 1) * chunk_size, chunk_size)

def split(dfm, chunk_size):
    indices = index_marks(dfm.shape[0], chunk_size)
    return np.split(dfm, indices)

def create_directory(path):
    try:
        os.makedirs(path)
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path)

def delete_directory(path):
    try:
        shutil.rmtree(path, onerror=handleError)
    except:
        print ("Deletion of the directory %s failed" % path)
    else:
        print ("Successfully deleted the directory %s " % path)

