import os, re, maemkit

class chromedriver(maemkit.maemkit):
  options = {}
  mochitestCommand = []
  directories = []

  def __init__(self, mkit):
    self.addOptions(mkit.config_options["chrome"])

  def addOptions(self, input):
    for option in input: self.options[option] = input[option]
    #TODO: figure out if we are doing a splitdirs here (might be required for wince or symbian)
    #TODO: figure out if we are going to support a test-path for chrome
    self.options["backupdir"] = os.path.normpath(os.path.join(self.options["testroot"], self.options["backupdir"]))

  def getTests(self):
    #TODO: what do we do if chrome is empty already?
    fromdir = os.path.normpath(os.path.join(self.options["backupdir"], "*"))
    todir = os.path.normpath(os.path.join(self.options["testroot"], "chrome"))
    self.copytree(fromdir, todir)

    myre = re.compile(".*([a-zA-Z0-9\-\_]+).*")
    for dir in os.listdir(todir):
      if (myre.match(dir)): self.directories.append(dir)

    self.directories.sort()

  def prepTests(self):
    #TODO: figure out a method for setting these user_pref in the profile (automation.py?)
    #set user_pref("browser.sessionhistory.max_total_viewers", -1)
    #set user_pref("dom.storage.default_quota", 640)

    todir = os.path.normpath(self.options["backupdir"])
    fromdir = os.path.normpath(os.path.join(self.options["testroot"], "chrome"))

    self.rmdir(todir)
    self.mkdir(todir)
    self.copytree(os.path.join(fromdir, "*"), todir)
    self.rmdir(fromdir)
    self.mkdir(fromdir)

    self.directories = self.splitListParallel(self.directories, self.options)

  def runTests(self):
    logdir = os.path.normpath(self.options["logdir"])
    if (os.path.exists(logdir)):
      self.move(logdir, logdir + ".bak")
    self.mkdir(logdir)

    #TODO: this block is the same as MochiDriver except for the --chrome flag
    #TODO: figure out a method for utilizing all the other config/cli options available
    cmd = os.path.normpath(os.path.join(self.options["testroot"], "runtests.py"))
    self.mochitestCommand = ["python " + cmd + " --autorun --close-when-done --chrome"]
    for option in ["utility-path","appname","xre-path","certificate-path"]:
      self.mochitestCommand.append("--" + option + "=" + os.path.normpath(self.options[option]))
    mCommand = " ".join(self.mochitestCommand)

    print "\n".join(self.directories)

    for directory in self.directories:
      targetdir = os.path.normpath(os.path.join(self.options["testroot"], "chrome"))
      self.rmdir(targetdir)
      self.mkdir(targetdir)
      self.copytree(os.path.normpath(os.path.join(self.options["backupdir"], str(directory))), targetdir)
      self.addCommand(mCommand + " --log-file=" + os.path.normpath(os.path.join(logdir, self.getLogFileName(directory))))
