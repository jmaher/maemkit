import os, re, maemkit

class xpcdriver(maemkit.maemkit):
  options = {}
  mochitestCommand = []
  directories = []

  def __init__(self, mkit):
    self.addOptions(mkit.config_options["xpcshell"])

  def addOptions(self, input):
    for option in input: self.options[option] = input[option]

  def getTests(self):
    #TODO: verify that we will only use .js scripts
    p = re.compile(".*test_.*.js")
   #TODO: we might have to change the path we walk if Ted's scripts adjust it from xpcshell-simple
    for root, dirs, files in os.walk(os.path.normpath(os.path.join(self.options["testroot"], "xpcshell-simple"))):
      for file in files:
        if (p.match(file)):
          try:
            if (self.directories.index(root) >= 0): continue
          except:
            self.directories.append(root)

  def prepTests(self):
    self.directories = self.splitListParallel(self.directories, self.options)

  def runTests(self):
    logdir = os.path.normpath(self.options["logdir"])
    if (os.path.exists(logdir)):                                                                         
      self.move(logdir, logdir + ".bak")                                                 
    self.mkdir(logdir)     

    buffered = False
    utilname = os.path.normpath(os.path.join(self.options["utility-path"], "runxpcshelltests.py"))
    for test in self.directories:
      command = "python " + utilname
      command += os.path.normpath(os.path.join(self.options["xre-path"], "xpcshell")) + " " 
      command += os.path.normpath(os.path.join(self.options["testroot"], "_tests")) + " "
      command += test 
      testResults = self.addCommand(command, buffered)                                                                   
      self.cleanup()                                                  
      print testResults

