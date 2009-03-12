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
    self.options["backupdir"] = self.options["testroot"] + "/" + self.options["backupdir"]

  def getTests(self):
    #TODO: what do we do if chrome is empty already?  
    self.copytree(self.options["backupdir"] + "/*", self.options["testroot"] + "/chrome")

    myre = re.compile(".*([a-zA-Z0-9\-\_]+).*")
    for dir in os.listdir(self.options["testroot"] + "/chrome"):
      if (myre.match(dir)): self.directories.append(dir)

    self.directories.sort()

  def prepTests(self):
    #TODO: figure out a method for setting these user_pref in the profile (automation.py?)
    #set user_pref("browser.sessionhistory.max_total_viewers", -1)
    #set user_pref("dom.storage.default_quota", 640)

    self.rmdir(self.options["backupdir"])
    self.mkdir(self.options["backupdir"])
    self.copytree(self.options["testroot"] + "/chrome/*", self.options["backupdir"])
    self.rmdir(self.options["testroot"] + "/chrome")
    self.mkdir(self.options["testroot"] + "/chrome")

    self.directories = self.splitListParallel(self.directories, self.options)

  def runTests(self):
    if (os.path.exists(self.options["logdir"])):
      self.move(self.options["logdir"], self.options["logdir"] + ".bak")
    self.mkdir(self.options["logdir"])

    #TODO: this block is the same as MochiDriver except for the --chrome flag
    #TODO: figure out a method for utilizing all the other config/cli options available
    self.mochitestCommand = ["python " + self.options["testroot"] + "/runtests.py --autorun --close-when-done --chrome"]
    for option in ["utility-path","appname","xre-path","certificate-path"]:
      self.mochitestCommand.append("--" + option + "=" + self.options[option])
    mCommand = " ".join(self.mochitestCommand)

    print "\n".join(self.directories)

    for directory in self.directories:
      self.rmdir(self.options["testroot"] + "/chrome/*")
      self.copytree(str(self.options["backupdir"]) + "/" + str(directory), str(self.options["testroot"]) + "/chrome/")
      self.addCommand(mCommand + " --log-file=" + self.options["logdir"] + "/" + self.getLogFileName(directory))
