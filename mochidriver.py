import os,re,maemkit

class mochikit(maemkit.maemkit):
  options = {}
  mochitestCommand = []

  def __init__(self, mkit):
    self.addOptions(mkit.config_options["mochitest"])

  def addOptions(self, input):
    for option in input:
      if (option == "split-directories"):
        self.options[option] = []
        for part in input[option].split(','): self.options[option].append(os.path.normpath(part.strip('\"')))
      else:
        self.options[option] = input[option]

  #parse log files, tally results
  def stitchLogs(self):
    p = 0
    f = 0
    t = 0
    myre = re.compile('.*TEST\-([A-Z]+).*')

    masterLog = open(os.path.normpath(self.options["log-file"]), "a")

    for root, dirs, files in os.walk(os.path.normpath(self.options["logdir"])):
      for logFile in files:

        #parse each line, looking for TEST-PASS (pass), TEST-UNEXPECTED-FAIL (fail), TEST-KNOWN-FAIL (todo)
        fLog = open(os.path.normpath(os.path.join(self.options["logdir"], logFile)), "r")
        for line in fLog:
          masterLog.write(line)
          res = None
          res = myre.match(line)
          if (res):
            if (res.group(1) == "PASS"): p = p + 1
            if (res.group(1) == "UNEXPECTED"): f = f + 1
            if (res.group(1) == "KNOWN"): t = t + 1

    masterLog.write("\n\n-------------------------\n")
    masterLog.write("INFO PASSED: " + str(p) + "\n")
    masterLog.write("INFO FAILED: " + str(f) + "\n")
    masterLog.write("INFO TODO: " + str(t) + "\n")
    masterLog.close()


  #originally written by harthur
  def getDirectories(self, aDir):
    testFilePattern = 'test_.*'
    testsDirPattern = ".*?" + self.dirtype + "tests" + self.dirtype + "(.*)"

    #returns the smallest possible directories containing tests (leaves of tests tree)
    dir = []
    relDirectories = []

    for split in self.options["split-directories"]: self.stitchDirectory(split)

    # get the smallest directories with test files in them
    for root, dirs, files in os.walk(aDir):
      p = re.compile(testFilePattern)
      for mFile in files:
        if(p.match(mFile)):
          dir.append(root)
          # don't search any further in this tree
          for directory in dirs:
            dirs.remove(directory)
          break

    # truncate path to path relative to tests directory
    testPatt = re.compile(testsDirPattern)
    for directory in dir:
      relDir = testPatt.match(directory)
      if relDir:
        relDirectories.append(relDir.group(1))

    relDirectories.sort()
    self.directories = relDirectories


  #Put directory back to normal; not necessary, but good to have
  def stitchDirectory(self, aDir):
    dirlist = []

    basedir = os.path.normpath(os.path.join(self.options["testroot"], "tests"))
    for root, dirs, files in os.walk(os.path.join(basedir, aDir)): 
      dirlist = dirs
      break

    numtosplit = abs(100 / int(self.options["split-percentage"]))
    try:
      if (dirlist.index(str(numtosplit)) >= 0):
        try:
	  if (dirlist.index(str(numtosplit + 1)) >= 0): stitch = True
        except: stitch = False
    except: stitch = True

    base_dir = os.path.normpath(os.path.join(basedir, aDir))

    if (stitch == True):
      myre = re.compile("^([0-9]+)$")
      for dir in dirlist:
        res = myre.match(dir)
        if (res):
          try:
            self.move(os.path.normpath(os.path.join(os.path.join(base_dir, res.group(1)), "*.*")), base_dir)
            self.rmdir(os.path.normpath(os.path.join(base_dir, res.group(1))))
          except: print "couldn't find directory: " + res.group(1) + " in " + aDir

      try:
        self.move(os.path.normpath(os.path.join(os.path.join(base_dir, "tests"), "*.*")), base_dir)
        self.rmdir(os.path.normpath(os.path.join(base_dir, "tests")))
      except: print "no directory tests in: " + aDir
    return

  def splitDirectory(self, aDir):

    num_files = 0
    for root,dirs,files in os.walk(os.path.normpath(os.path.join(os.path.join(self.options["testroot"], "tests"), aDir))):
      num_files = len(files)
      break

    bDir = os.path.normpath(os.path.join(os.path.join(self.options["testroot"], "tests"), aDir))

    dirlist = []
    for root, dirs, files in os.walk(bDir): 
      dirlist = dirs
      break

    self.mkdir(os.path.join(bDir, "tests"))
    self.move(os.path.join(bDir, "test_*"), os.path.join(bDir, "tests"))

    num_files = 0
    testfiles = []
    for root,dirs,files in os.walk(os.path.join(bDir, "tests")):
      for file in files: testfiles.append(file)
      num_files = len(testfiles)
      break

    numtosplit = abs(100 / int(self.options["split-percentage"]))
    self.directories.remove(aDir)
    for num in range(numtosplit):
      newdir = os.path.normpath(os.path.join(aDir, str(num)))
      bnewdir = os.path.normpath(os.path.join(bDir, str(num)))
      self.directories.append(newdir)
      self.mkdir(bnewdir)
      self.copy(os.path.join(bDir, "*"), bnewdir)

      for dir in dirlist:
        if (dir != "tests"):
          self.mkdir(os.path.normpath(os.path.join(bnewdir, dir)))
          self.copy(os.path.normpath(os.path.join(os.path.join(bDir, dir)), "*"), os.path.join(bnewdir, dir))

    num_copy = num_files / numtosplit
    count = 0
    round = 0
    for file in testfiles:
      self.copy(os.path.join(os.path.join(bDir, "tests"), file), os.path.join(bDir, str(round)))

      count = count + 1
      if (count >= num_copy): 
        count = 0
        if (round < numtosplit - 1): round = round + 1

    self.rmdir(os.path.join(bDir, "tests"))


  def getTests(self):
    rootdir = os.path.normpath(os.path.join(self.options["testroot"], "tests"))
    if (self.options["test-path"] != ""): 
      rootdir += os.path.normpath(os.path.join(rootdir, self.options["test-path"]))
    self.getDirectories(rootdir)

  def prepTests(self):

    # We need to copy to testdirs as self.splitDirectory modifies the self.directories variable
    testdirs = []
    for dir in self.directories: testdirs.append(dir)

    for dir in testdirs: 
      try: 
        if (self.options["split-directories"].index(dir) >= 0): self.splitDirectory(dir)
      except: continue

    self.directories = self.splitListParallel(self.directories, self.options)

  def runTests(self):
    logdir = os.path.normpath(self.options["logdir"])
    if (os.path.exists(logdir)):
      self.move(logdir, logdir + ".bak")
    self.mkdir(logdir)

    #TODO: figure out a method for utilizing all the other config/cli options available
    self.mochitestCommand = ["python " + os.path.normpath(os.path.join(self.options["testroot"], "runtests.py")) + " --autorun --close-when-done"]
    for option in ["utility-path","appname","xre-path","certificate-path"]:
      self.mochitestCommand.append("--" + option + "=" + os.path.normpath(self.options[option]))
    mCommand = " ".join(self.mochitestCommand)

    for directory in self.directories:
      self.addCommand(mCommand + " --test-path=" + directory + " --log-file=" + os.path.join(logdir,  self.getLogFileName(directory)))
      self.cleanup() #just for safety measures
