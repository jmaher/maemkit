import os, re, maemkit

class refdriver(maemkit.maemkit):
  options = {}
  directories = []

  def addDir(self,targetDir):
    try:
      if (self.directories.index(targetDir) >= 0):
        return
    except ValueError: self.directories.append(targetDir)

  def parseManifest(self, manifest):
    p = re.compile("^include ([a-zA-Z0-9\\\/\-\.]+)")

    parts = manifest.split(self.dirtype)
    num = len(parts) - 1
    name = parts[num]
    rootdir = self.dirtype.join(parts[0:num])

    #backup manifest, use backup incase we are running again
    self.move(manifest + ".bak", manifest + "")
    self.move(manifest, manifest + ".bak")

    fHandle = open(manifest + ".bak", "r")
    lines = fHandle.readlines()
    fHandle.close()

    self.addDir(rootdir)

    #rewrite manifest with include lines # out
    fHandle = open(manifest, "w")
    for line in lines:
      test = p.match(line)
      if (test):
        self.addDir(os.path.normpath(os.path.join(rootdir, test.group(1))))
        line = "#" + line
      fHandle.write(line)
    fHandle.close()

  #parse out manifest for main reftest.list, and any splitdirs
  def findDirs(self, rootdir, rootfile):
    self.parseManifest(os.path.normpath(os.path.join(os.path.join(refdriver.options["testroot"], rootdir), rootfile)))
    for splitdir in self.options["split-directories"]:
      try:
        if (self.directories.index(os.path.normpath(splitdir.strip())) >= 0):
          self.parseManifest(os.path.normpath(os.path.join(refdriver.options["testroot"], splitdir)))
      except: continue

  def addOptions(self, input):
    for option in input:
      if (option == "split-directories"):
        self.options[option] = []
        for part in input[option].split(','): self.options[option].append(os.path.normpath(part.strip('\"')))
      else:
        self.options[option] = input[option]

  #split directories, do parallel
  def prepTests(self):
    logdir = os.path.normpath(str(refdriver.options["logdir"]))
    self.rmdir(logdir)
    self.mkdir(logdir)

    for dir in self.directories:
      test = dir.split(os.path.normpath(refdriver.options["testroot"]))
      test = test[1].lstrip(self.dirtype)
      try:
        if (self.options["split-directories"].index(test) >= 0): self.splitManifest(dir)
      except ValueError: continue

    refdriver.directories = refdriver.splitListParallel(self, self.directories, self.options)

  #split a manifest info many parts defined by split-percentage as the maximum # of items
  def splitManifest(self, dir):
    fHandle = open(dir, "r")
    lines = fHandle.readlines()
    fHandle.close()

    iter = 0
    counter = 0
    max = int(self.options["split-percentage"])
    if (max*2 >= len(lines)): return

    self.directories.remove(dir)
    while (counter < len(lines)):
      fHandle = open(dir + str(iter), "w")
      for line in lines[counter:counter+max]: fHandle.write(line)
      fHandle.close()
      self.addDir(dir + str(iter))
      iter += 1
      counter += max

class reftest(refdriver):

  reftestdir = "layout/reftests"
  reftest = "reftest.list"

  def __init__(self, mkit):
    self.addOptions(mkit.config_options["reftest"])

  def addOptions(self, options):
    refdriver.addOptions(self, options)

  def getTests(self):
    refdriver.findDirs(self, self.reftestdir, self.reftest)

  def prepTests(self):
    refdriver.prepTests(self)

  def runTests(self):
    logdir = os.path.normpath(str(refdriver.options["logdir"]))
    if (os.path.exists(logdir)):
      self.move(logdir, logdir + ".bak")
    self.mkdir(logdir)


    for dir in refdriver.directories:
      utilname = os.path.normpath(os.path.join(self.options["utility-path"], "runreftest.py"))
      print refdriver.addCommand(self, "python " + utilname + " --appname=" + os.path.normpath(refdriver.options["appname"]) + " " + dir, True)
      refdriver.cleanup(self)

class crashtest(refdriver):

  crashtestdir = "testing/crashtest"
  crashtest = "crashtests.list"

  def __init__(self, mkit):
    self.addOptions(mkit.config_options["crashtest"])

  def addOptions(self, options):
    refdriver.addOptions(self, options)

  def getTests(self):
    refdriver.findDirs(self, os.path.normpath(self.crashtestdir), self.crashtest)

  def prepTests(self):
    refdriver.prepTests(self)

  def runTests(self):
    logdir = os.path.normpath(refdriver.options["logdir"])
    if (os.path.exists(logdir)):
      self.move(logdir, logdir + ".bak")
    self.mkdir(logdir)

    for dir in refdriver.directories:
      utilname = os.path.normpath(os.path.join(self.options["utility-path"], "runreftest.py"))
      print refdriver.addCommand(self, "python " + utilname + " --appname=" + refdriver.options["appname"] + " " + dir, True)
      refdriver.cleanup(self)
