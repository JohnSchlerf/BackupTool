##################################################
# Create a backup with archival copies using Hard 
# Links; AKA Poor Man's Time Machine
#
# Copies made with hard links take up very little
# space, since they point to the same file data.
##################################################

##################################################
# Copying and distribution of this file, with or 
# without modification, are permitted in any 
# medium without royalty provided the copyright
# notice and this notice are preserved.  This 
# file is offered as-is, without any warranty.
##################################################

# v0.1 - John Schlerf, Dec 2014

# Import everything from BackupTool:
from BackupTool import *
import datetime
import time

def syncDirs(sourceDir,destDir,preserveTime=None,ignoreDirs=None,ignoreFiles=None,deleteStale=True,pushStale=False,pullStale=False):

    # Create some placeholder lists:
    pushList = []
    pullList = []
    staleDest = []
    staleSource = []
    
    # Figure out dates of the two directories:
    sourceSet = ModificationDates(sourceDir,ignoreDirs,ignoreFiles)
    destSet = ModificationDates(destDir,ignoreDirs,ignoreFiles)
    
    # Throw out the things that are clearly the same, to save time:
    ignoreMe = sourceSet.intersection(destSet)
    
    sourceSet = sourceSet - ignoreMe
    destSet = destSet - ignoreMe
    
    # Time offset, in seconds, required to call two versions of the same file different:
    offset = 60
    
    # Minimum time for file preservation (this may result in headaches):
    # If a file is newer than this, and missing from the synch folder, we will copy it over!
    # Otherwise, we'll treat it as "stale" and follow the deleteStale flag.
    if preserveTime is None:
        preserveTime = time.mktime((datetime.datetime.now()-datetime.timedelta(days=7)).timetuple())
    else:
        preserveTime = time.mktime(preserveTime.timetuple())
     
    for sourceFile in sourceSet:
        fileFoundFlag = False
        for destFile in destSet:
            if sourceFile[0] == destFile[0]:
                fileFoundFlag = True
                if sourceFile[1] > destFile[1]+offset:
                    # Source version is newer, so put sourcefile in pushList:
                    pushList.append(sourceFile[0])
                elif sourceFile[1] < destFile[1]-offset:
                    # Dest version is newer, so put destfile in pullList:
                    pullList.append(destFile[0])
                else:
                    # Seems they're about even; do nothing.
                    None
                # Since destFile has been found and dealt with, remove it from destSet for later:
                destSet.remove(destFile)
                break
        if not(fileFoundFlag):
            if sourceFile[1] >= preserveTime:
                # If it's new enough, pull it over!
                pushList.append(sourceFile[0])
            else:
                staleSource.append(sourceFile[0])
    for destFile in destSet:
        # Whatever's left in here exists on dest but not on source, so... gotta decide what to do about that:
        if destFile[1] >= preserveTime:
            # If it's new enough, pull it over!
            pullList.append(destFile[0])
        else:
            staleDest.append(destFile[0])
    
    copyList(pushList,sourceDir,destDir)
    copyList(pullList,destDir,sourceDir)
    
    if pushStale:
        copyList(staleSource,sourceDir,destDir)
    elif deleteStale:
        deleteList(staleSource,sourceDir)

    if pullStale:
        copyList(staleDest,destDir,sourceDir)
    elif deleteStale:
        deleteList(staleDest,destDir)
        
# Load config files:
def syncTool(config):
    
    # Things we wanna keep:
    directoriesToBackup = []
    targetDirectoryBase = ''
    ignoreDir = []
    ignoreFile = []
    pushStale = True
    pullStale = False
    deleteStale = False
    
    if config is None:
        return -1
    
    # If there's no configuration file, then... uhh... crap out, I guess?
    configfile = open(config,'r')
    newconfiglines = []
    for line in configfile.readlines():
        # by default, pass the lines through to the output list as-is:
        outline = line
        if line[0] in "!@#$%&*\n": None
        else:
            words = line.split()
            if words[0] == "last_backup":
                preserveTime = datetime.datetime(*(int(x) for x in words[1:]))
                # OK, so if we're successful, we'll want to update this:
                outline = "last_backup " + datetime.datetime.now().strftime("%Y %m %d %H %M\n")
            elif words[0] == "directory_to_backup":
                directoriesToBackup.append(" ".join(words[1:]))
            elif words[0]=="target_directory":
                targetDirectoryBase = " ".join(words[1:])
            elif words[0]=="ignoredir":
                ignoreDir.append(" ".join(words[1:]))
            elif words[0]=="ignorefile":
                ignoreFile.append(" ".join(words[1:]))
            elif words[0]=="pushStale":
                pushStale = words[1]=="True"
            elif words[0]=="pullStale":
                pullStale = words[1]=="True"
            elif words[0]=="deleteStale":
                deleteStale = words[1]=="True"
            
        newconfiglines.append(outline)
    for sourceDir in directoriesToBackup:
        (tailDir,headDir) = os.path.split(sourceDir)
        if len(headDir) == 0:
            (tailDir,headDir) = os.path.split(tailDir)
        targetDir = os.path.join(targetDirectoryBase,headDir)
        syncDirs(sourceDir,targetDir,preserveTime,ignoreDir,ignoreFile,deleteStale,pushStale,pullStale)
    
    # OK, now go back and rewrite the config file so that the last sync time is updated:
    configFile = open(config,'w')
    configFile.writelines(newconfiglines)
    configFile.close()    
    return 1
    
if __name__ == '__main__':
    # Set some default os-specific stuff:
    if os.name == "nt":
        config_file = "C:\BackupTool.cfg"
    elif os.name == "posix":
        mkdir_better(os.path.expanduser("~/.config"))
        config_file = os.path.expanduser("~/.config/BackupTool.conf")
    else:
        config_file = None
    syncTool(config_file)
  