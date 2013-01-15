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

# v0.1 - John Schlerf, March 2011

import time, os, stat, ctypes, random
from shutil import copy2 as cp
from shutil import rmtree

# Import GUI stuff
from Tkinter import *
import tkMessageBox, tkFileDialog

# This will do hard links on Windows XP:
def CreateHardlink(src,dest):
  if not(ctypes.windll.kernel32.CreateHardLinkA(dest,src,None)):
    raise OSError

# Windows XP doesn't have os.link, so add it for cross-platform niceness:
if os.name=="nt": os.link=CreateHardlink

"""
Moved this below
# Set some default os-specific stuff:
if os.name == "nt":
  config_file = "C:\BackupTool.cfg"
  # XP does not have os.link, so add it:
  os.link = CreateHardlink
elif os.name == "posix":
  mkdir_better(os.path.expanduser("~/.config"))
  config_file = os.path.expanduser("~/.config/BackupTool.conf")
else:
  config_file = None
"""

###########################################
# These are my go-to GUI functions:


# Make a simple "Yes or No" dialog box:
def yesNoDialog(question):
  return(tkMessageBox.askyesno("Yes or No",question))

def OKDialog(textIn):
  tkMessageBox.showinfo('Click OK to continue',textIn)

def OKDialog_obsolete(textIn):
  """ 
  This function makes a new window which basically displays
  some text and an OK button, and dies when the user clicks 
  OK.  There are probably built-ins to do this, but I want
  to keep this code as close to Tkinter as possible.
  """
  # Make a new window:
  OK = Toplevel()
  # Give it a title:
  OK.title('Click OK to continue')
  # Set up the grid:
  OK.grid()
  # Add a spacer line:
  b = GridLabel(OK,"",0,0)
  # Now add my custom text:
  L = GridLabel(OK,textIn,1,0)
  # Another blank line:
  b2=GridLabel(OK,"",2,0)
  # And finally my OK button which destroys the window:
  B = Button(OK,text="OK",command=OK.destroy)
  B.grid(row=3,column=0)

def GridLabel(Parent,Text,Row,Column):
  """
  This is a helper function which adds a label to a grid.
  This is normally a couple of lines, so multiple labels
  gets a little cumbersome...
  """
  L = Label(Parent,text=Text)
  L.grid(row=Row,column=Column)
  return L

def GridEntry(Parent,DefaultText,Row,Column):
  """
  This is a helper function which adds an Entry widget
  to a grid.  Also sets default text.
  """
  E = Entry(Parent)
  E.insert(0,DefaultText)
  E.grid(row=Row,column=Column)
  return E

def GridCheck(Parent,DefaultSelected,Row,Column):
  """
  This is a helper function which adds a Checkbutton widget
  to a grid.  Also sets the default value, and assigns the
  value variable to the widget itself for easy coding later.
  """
  dummyvar = IntVar()
  C = Checkbutton(Parent,var=dummyvar)
  if DefaultSelected == 1:
    C.select()
  C.grid(row=Row,column=Column)
  C.isChecked = dummyvar
  return C


##################################################
# This exists for testing purposes ONLY; should be
# overridden with a GUI and/or config file.
source_dir_for_testing = "C:/TestDirectory"
target_dir_for_testing = "C:/destdir"
archival_dir_for_testing = os.path.join("C:/Archive",time.strftime("%Y%U--%a-%b-%d-%Y-%H_%M_%S"))


# Walk through the files in a directory, return a 
# list of tuples containing all filenames (as 
# relative paths) and modification times (rounded
# to nearest second):
def ModificationDates(directory):
  my_list = []
  for dirpath,dirnames,filenames in os.walk(directory):
    for file in filenames:
      modtime = round(os.path.getmtime(os.path.join(dirpath,file)))
      filepath = os.path.join(dirpath[1+len(directory):],file)
      my_list.append((filepath,modtime))
  return set(my_list)

# Make a list out of my set; re-add path if 
# necessary.
def setToList(mySet,prefix=None):
  myList = []
  for item in mySet:
    if prefix:  myList.append(os.path.join(prefix,item[0]))
    else:       myList.append(item[0])
  return myList

# This is code to delete a list of files;
def deleteList(listOfFiles,fromdir):
  if not(listOfFiles): return
  if set(listOfFiles) == listOfFiles: listOfFiles = setToList(listOfFiles)
  for file in listOfFiles:
    os.unlink(os.path.join(fromdir,file))


# This makes a directory read-only:
def makeReadOnly(some_directory):
  None
  """
  # Unfortunately this code does not work properly.  Windows
  # XP allows read-only folders to be deleted, changed, etc;
  # so, in the spirit of "false security is worse than no 
  # security" I've stubbed this function out.  Leaving it in
  # for historical purposes only.
  #
  # People on the Interwebs say that this SHOULD be possible
  # with NTFS permissions settings, but in my own messing
  # around with NTFS permissions they are abused just as
  # badly as the "read-only" setting.  I can still delete to
  # my heart's content, without so much as a warning about
  # the files being read-only!
  #   -- JS
  for dirpath,dirnames,filenames in os.walk(some_directory):
    os.chmod(dirpath,stat.S_IREAD)
    for file in filenames:
      os.chmod(os.path.join(dirpath,file),stat.S_IREAD)
  """

# This makes a directory writeable:
def makeWritable(some_directory):
  None
  """
  # Since I stubbed out my ReadOnly function, I've gone
  # ahead and stubbed this out too.
  #   -- JS
  for dirpath,dirnames,filenames in os.walk(some_directory):
    os.chmod(dirpath,stat.S_IWRITE)
    for file in filenames:
      os.chmod(os.path.join(dirpath,file),stat.S_IWRITE)
  """

# I need a better version of mkdir, so here it
# is.  Main differences are that it doesn't 
# raise an error if a directory exists, and
# also that it handles nested directories.
# IE, by default os.mkdir('foo/bar') will fail
# if foo is not already a directory; this will
# not.
def mkdir_better(new_directory):
  if not(os.path.isdir(new_directory)):
    # Recursion is necessary here:
    parent_dir = os.path.dirname(new_directory)
    if not(os.path.isdir(parent_dir)):
      mkdir_better(parent_dir)
    # This is checking twice, which is stupid.
    # However, for whatever reason it seems to
    # break if I don't check twice:
    if not(os.path.isdir(new_directory)):
      os.mkdir(new_directory)


# This is code to copy a list of files from one 
# location to another, making sure the proper
# subdirectories get created:
def copyList(listOfFiles,fromdir,todir):
  if not(listOfFiles): return
  if set(listOfFiles) == listOfFiles: 
    listOfFiles = setToList(listOfFiles)
    #listOfFiles = newListOfFiles
  for file in listOfFiles:
    sourcefile = os.path.join(fromdir,file)
    destfile = os.path.join(todir,file)
    destfolder = os.path.dirname(destfile)
    if not(os.path.isdir(destfolder)): mkdir_better(destfolder)
    cp(sourcefile,destfile)

#################################################################
# Here's a quick and dirty function to do an incremental backup:
def freshCopy(source_dir,target_dir):
  # Figure out fresh and obsolete files:
  files_in_backup = ModificationDates(target_dir)
  files_to_backup = ModificationDates(source_dir)
  
  fresh_files = files_to_backup - files_in_backup
  obsolete_files = files_in_backup - files_to_backup

  # OK, now delete obsolete files:
  deleteList(obsolete_files,target_dir)
  
  # and back up fresh files:
  copyList(fresh_files,source_dir,target_dir)


###################################################################
# Create a full copy of a directory tree using hard links
def directoryLink(source_dir,target_dir,assumingLinksWork=True):
  # Some filesystems (FAT 32) do not support hardlinks.  If we're 
  # trying to make a snapshot on one of those drives, it's better
  # to use a real copy than fail utterly.

  for dirpath, dirnames, filenames in os.walk(source_dir):
    new_directory = os.path.join(target_dir,dirpath[1+len(source_dir):])
    if not(os.path.isdir(new_directory)): mkdir_better(new_directory)
    for file in filenames:
      if assumingLinksWork:
        try: os.link(os.path.join(dirpath,file),os.path.join(new_directory,file))
        except:
          # If we get here, then we tried to make a hardlink and could
          # not.  Ask the participant if they 
          assumingLinksWork = False
          if not(tkMessageBox.askyesno("Yes or No","Small snapshots are not possible on this disk. This can happen if the disk is formatted as FAT rather than NTFS. Would you like to make a snapshot anyway? (NOTE: this can take up a LOT of extra disk space.)")):
            return (False,False)
          cp(os.path.join(dirpath,file),os.path.join(new_directory,file))
      else:
        cp(os.path.join(dirpath,file),os.path.join(new_directory,file))
  return (assumingLinksWork,True)


##################################################################
# This is my workhorse.  Maybe it shouldn't be a class, but it
# seems to work OK... should figure that out for niceness, though.
class BackupTool:

  directories_to_backup = []
  system_key = None
  target_directory = None
  target_key = None
  targetkeyname = 'target.key'
  current_directory = 'Current'
  archive_directory = 'OldSnapshots'
  backupRun = False

  def __init__(self,configfile):
    self.filename = configfile
    if os.path.isfile(configfile):
      self.parse()
    self.backupdialog()

  def saveconfig(self):
    # OK, this is much less ambitious than the "parse" file below.
    # I'm throwing away most custom comments.  Could be done better.
    cfg = open(self.filename,'w')
    cfg.write('# Autosaving config file.'+'\n')
    cfg.write('last_backup ' + time.strftime('%h %D %Y %H:%M',self.backuptime) + '\n')
    for d in self.directories_to_backup:
      cfg.write('directory_to_backup ' + d + '\n')
    cfg.write('system_key ' + self.system_key + '\n')
    cfg.write('target_directory ' + self.target_directory + '\n')
    cfg.write('latest_snapshot_name ' + self.current_directory + '\n')
    cfg.write('archival_name ' + self.archive_directory + '\n')

  def parse(self):
    config = open(self.filename)
    for line in config.readlines():
      if line[0] in "!@#$%&*\n": None
      else:
        words = line.split()
        if words[0] == "directory_to_backup":
          self.directories_to_backup.append(words[1])
        elif words[0]=="system_key":
          self.system_key = words[1]
        elif words[0]=="target_directory":
          self.target_directory = words[1]
        elif words[0]=="latest_snapshot_name":
          self.current_directory = words[1]
        elif words[0]=="archival_name":
          self.archive_directory = words[1]

  def populated2bup(self):
    self.d2bup.delete(0,END)
    for directory in self.directories_to_backup:
      self.d2bup.insert(END,directory)

  def get_directory(self,text):
    return tkFileDialog.askdirectory(title=text)

  def add_d2bup(self):
    self.directories_to_backup.append(self.get_directory('Select directory to backup.'))
    self.directories_to_backup.sort()
    self.populated2bup()

  def rm_d2bup(self):
    indicestoremove = self.d2bup.curselection()
    itemstoremove = []
    for index in indicestoremove:
      itemstoremove.append(self.directories_to_backup[int(index)])
    for item in itemstoremove:
      self.directories_to_backup.remove(item)
    self.populated2bup()

  def adjusttdir(self):
    self.tdir.delete(0,END)
    self.tdir.insert(END,self.target_directory)

  def settdir(self):
    self.target_directory = self.get_directory('Select destination folder')
    self.adjusttdir()

  def backupdialog(self):
    # First, make the "root" window:
    self.tkroot = Tk()
    self.tkroot.title('BackupTool')

    # Now, make a frame within the window, and pack it:
    self.gui = Frame(self.tkroot,height=300,width=400)
    self.gui.pack()

    # Next, lay out the GUI.
    # Directories to backup:
    tag = Label(self.gui,text="Directories to back up")
    tag.place(relx=0.05,rely=0.03)
    self.d2bup = Listbox(self.gui,selectmode=EXTENDED)
    self.d2bup.place(relx=0.05,rely=0.1,relwidth=0.4,relheight=0.7)
    self.populated2bup()
    addButton = Button(self.gui,text="Add",command=self.add_d2bup)
    addButton.place(relx=0.05,rely=0.85,relwidth=0.18,relheight=0.1)
    delButton = Button(self.gui,text="Remove",command=self.rm_d2bup)
    delButton.place(relx=0.27,rely=0.85,relwidth=0.18,relheight=0.1)

    # Target directory:
    tag2 = Label(self.gui,text="Destination Directory")
    tag2.place(relx=0.55,rely=0.03)
    self.tdir = Listbox(self.gui)
    self.tdir.place(relx=0.55,rely=0.1,relwidth=0.4,relheight=0.2)
    self.adjusttdir()
    changebutton = Button(self.gui,text="Set",command=self.settdir)
    changebutton.place(relx=0.55,rely=0.35,relwidth=0.2,relheight=0.1)
    
    # Run button:
    self.runbutton = Button(self.gui,text="Backup!",command=self.runbackup)
    self.runbutton.place(relx=0.55,rely=0.55,relwidth=0.2,relheight=0.2)
    
    # Quit button:
    self.quitbutton = Button(self.gui,text="Quit",command=self.quit)
    self.quitbutton.place(relx=0.55,rely=0.75,relwidth=0.2,relheight=0.2)

    # Status label
    self.status = StringVar()
    self.status.set("Waiting")
    self.statuslabel = Label(self.gui,textvariable=self.status)
    self.statuslabel.place(relx=0.80,rely=0.55,relwidth=0.2,relheight=0.2)

    # And finally, run it:
    self.gui.mainloop()
    None

  def quit(self):
    self.gui.quit()
    if self.backupRun:
      self.saveconfig()
    exit

  def setTargetKey(self):
    targetkeyfile = os.path.join(self.target_directory,self.targetkeyname)
    tkf = open(targetkeyfile,'w')
    tkf.write(self.system_key + '\n')
    tkf.close()

  def getTargetKey(self):
    targetkeyfile = os.path.join(self.target_directory,self.targetkeyname)
    if not(os.path.isfile(targetkeyfile)):
      print "found no target key, generating"
      self.setTargetKey()
    tkf = open(targetkeyfile,'r')
    self.target_key = tkf.readline()
    # strip off the newline:
    self.target_key = self.target_key[:-1]
    tkf.close()
    return self.target_key == self.system_key

  def runbackup(self):
    # Change the status label:
    self.status.set("Running...")
    self.backupRun = False
    backingup = True
    if not(self.system_key):
      key = random.Random()
      self.system_key = ''
      for i in range(10):
        self.system_key += str(int(key.uniform(-100,100)))
    if not(os.path.isdir(self.target_directory)):
      mkdir_better(self.target_directory)
    if not(self.getTargetKey()):
      if not(yesNoDialog('WARNING -- This appears to be a backup of a different system.  This backup may overwrite/delete previous files.  Continue anyway?')):
        backingup = False
    if backingup:
      self.backuptime = time.localtime()
      current_backup = os.path.join(self.target_directory,self.current_directory)
      archival_snapshot = os.path.join(self.target_directory,self.archive_directory,time.strftime("%Y%U--%a-%b-%d-%Y-%H_%M_%S",self.backuptime))
      # new trick: list filtering!  Woo-hoo!
      if os.path.isdir(current_backup):
        targetdirs_stale = [d for d in os.listdir(current_backup) if os.path.isdir(os.path.join(current_backup,d))]
      else:
        targetdirs_stale = []
      for source_dir in self.directories_to_backup:
        target_dir = os.path.join(current_backup,os.path.basename(source_dir))
        freshCopy(source_dir,target_dir)
        try: 
          targetdirs_stale.remove(os.path.basename(source_dir))
        except:
          pass
      for d in targetdirs_stale:
        rmtree(os.path.join(current_backup,d))
      directoryLink(current_backup,archival_snapshot)
      self.setTargetKey()
      self.backupRun = True
    if self.backupRun:
      self.status.set("Finished!")
    else:
      self.status.set("Aborted.")

if __name__ == '__main__':
  # Set some default os-specific stuff:
  if os.name == "nt":
    config_file = "C:\BackupTool.cfg"
  elif os.name == "posix":
    mkdir_better(os.path.expanduser("~/.config"))
    config_file = os.path.expanduser("~/.config/BackupTool.conf")
  else:
    config_file = None
  BackupTool(config_file)
  
