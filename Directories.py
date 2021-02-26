from pathlib            import Path
import platform


class Directories:
    @staticmethod
    def getOnlyDir(location = '/'):
        DIR = Path(location).iterdir()
        DIRS = []

        for item in DIR:
            if item.is_dir():
                DIRS.append(item.__str__())

        return {
            "path" : location,
            'dirs' : DIRS
        }

    
    @staticmethod
    def getDirData(location = '/'):
        DIR = Path(location).iterdir()
        data = []

        for item in DIR:
            fullPath = item.__str__()
            extension = ''
            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = item.stat()
            fSize = float(size / 1048576)
            size_in_str = str(round(fSize, 1)) + 'MB'
            if int(fSize) <= 0:
                size_in_str = str(round(fSize * 1024, 1)) + 'KB'
            elif int(fSize) >= 1024:
                size_in_str = str(round(fSize / 1024, 2)) + 'GB'


            if not item.is_dir() and fullPath.find('.') > 0:
                extension = fullPath[fullPath.rfind('.') : ]

            data.append({
                "name": fullPath[fullPath.rfind('\\' if platform.system() == 'Windows' else '/') + 1:],
                "extension" : extension,
                "is_dir" : item.is_dir(),
                "stat" : mtime,
                "size" : size_in_str
            })

        return {
            "path" : location,
            'data' : data
        }

    

    @staticmethod
    def previousFolder(location:str):
        if location == '/':
            return None


        if location.rfind('/') == 0:
            return Directories.getData()

        return Directories.getData(location[0 : location.rfind('/')])


    
    @staticmethod
    def nextFolder(currentPath = '/', location = ''):
        if currentPath == '/':
            location = currentPath + location
        else:
            location = currentPath + '/' + location


        return Directories.getData(location)

