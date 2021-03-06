import os
import shutil

class DirArchive(object):
    """
    Read, write, access directory archives.  Treats a directory like an 
    archive.
    """
    def __init__(self, path, mode=None):
        """
        Initialize a DirArchive.
        
        Arguments:
        
        path -- Path to the archive directory
        mode -- Archive mode.  Default: None (unused, here for compatiblity)
        """
        self.path = path
        self.mode = mode
        if not os.path.exists(path):
            os.makedirs(path)

    def add_file(self, path, name):
        """
        Add a file to the archive.
        
        Arguments:
        
        path -- Path to file for which to add to archive.
        name -- Name of dest file
        """
        target_path = os.path.join(self.path, name)
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        shutil.copy2(path, target_path)

    def add_string(self, string, name):
        """
        Add a string to the archive, saved as a file.
        
        Arguments:
        
        string  -- String to add to archive.
        name    -- Name of file to create string as.
        """
        target_path = os.path.join(self.path, name)
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        fileobj = open(target_path, 'w')
        print >> fileobj, string
        fileobj.close()

    def list(self):
        """
        List members of the archive.
        """
        result = []
        top = self.path
        size = len(top.split(os.sep))
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                path = os.path.join(root, name)
                result.append(os.sep.join(path.split(os.sep)[size:]))
            for name in dirs:
                path = os.path.join(root, name)
                result.append(os.sep.join(path.split(os.sep)[size:]))
        return result

    def extract(self, name, dest):
        """
        Extract a member from the archive.
        
        Arguments:
        
        name -- Name of the member to extract.
        dest -- Destination path to extract the member to.
        """
        target_src = os.path.join(self.path, name)
        shutil.copy2(target_src, dest)

    def close(self):
        """
        Close archive.
        """
        import subprocess
        status = subprocess.call(['gzip', '-1', '--recursive', self.path])
        if status != 0:
            LOGGER.error("Failed to compress %r" % self.path)
            
if __name__ == '__main__':
    import time
    now = time.time()
    xv = DirArchive('backup/')
    xv.add_string("[mysqldump]\nignore-table=mysql.user\n", "my.cnf")
    xv.add_string("blah", "test/test.MYD")
    xv.add_file("user.frm", "mysql/user.frm")
    xv.add_file("user.MYD", "mysql/user.MYD")
    xv.add_file("user.MYI", "mysql/user.MYI")
    xv.close()
    print (time.time() - now), "seconds"
