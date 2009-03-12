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
    for root, dirs, files in os.walk(self.options["testroot"] + "/xpcshell-simple"):
      for file in files:
        if (p.match(file)): self.directories.append(root + "/" + file)


  def prepTests(self):
    self.directories = self.splitListParallel(self.directories, self.options)


  def getSupportFiles(self, test):
    head = ""
    tail = ""
      
    headre = re.compile("^head_.*.js$")
    tailre = re.compile("^tail_.*.js$")
    parts = test.split("/")
    #TODO: can I use a -1 instead of the len(parts)-1 clause?
    targetdir = "/".join(parts[0:len(parts)-1])
    for root, dirs, files in os.walk(targetdir):
      for file in files:
        if (headre.match(file)): head = " -f " + targetdir + "/" + file + " " + head
        if (tailre.match(file)): tail = " -f " + targetdir + "/" + file + " " + tail
    
    return head, tail
  

  def parseOutput(self, output):
    p = re.compile("\*\*\* PASS \*\*\*")
    f = re.compile("\*\*\* FAIL \*\*\*")
    t = re.compile("\*\*\* TIMEOUT \*\*\*")
    l = re.compile(".*mFreeCount.*LEAKED.([0-9]+).*")

    result = ""
    leaked = ""
  
    lines = output.split('\n')

    for line in lines:
      if (p.match(line)):
        result = "PASS"
      elif (f.match(line)):
        result = "FAIL"
      elif (t.match(line)):
        result = "TIMEOUT"
  
      leak_match = l.match(line)
      if (leak_match):
        leaked = leak_match.group(1)
  
    return result, leaked

  def runTests(self):
    if (os.path.exists(self.options["logdir"])):
      self.move(self.options["logdir"], self.options["logdir"] + ".bak")
    self.mkdir(self.options["logdir"])

    #TODO: fix this to get buffered tests from .cfg file
    for test in self.directories:
      buffered = False
      if (test == self.options["testroot"] + "/xpcshell-simple/test_necko/test/test_request_line_split_in_two_packets.js"):
        buffered = True
      if (test == self.options["testroot"] + "/xpcshell-simple/test_necko/test/test_sjs_throwing_exceptions.js"):
        buffered = True
      if (test == self.options["testroot"] + "/xpcshell-simple/test_places/queries/test_querySerialization.js"):
        buffered = True
      if (test == self.options["testroot"] + "/xpcshell-simple/test_intl_locale/unit/test_pluralForm.js"):
        buffered = True

      head, tail = self.getSupportFiles(test)

      self.mochitestCommand = []
      self.mochitestCommand.append(self.options["xre-path"] + "/xpcshell")
      self.mochitestCommand.append(" -f " + self.options["utility-path"] + "/head.js")
      self.mochitestCommand.append(head)
      self.mochitestCommand.append(" -f " + test)
      self.mochitestCommand.append(" -f " + self.options["utility-path"] + "/tail.js")
      self.mochitestCommand.append(tail)
      self.mochitestCommand.append(" -f " + self.options["utility-path"] + "/execute_test.js")
      command = " ".join(self.mochitestCommand)
      testResults = self.addCommand(command, buffered)
      self.cleanup()
      result, leaked = self.parseOutput(testResults)

      testname = test.split(self.options["testroot"], 1)
      output = "TEST-" + result + " | " + testname[1]
      if (leaked != ""): output = output + " | leaked: " + leaked

      #TODO: do we print to a log file?
      print testResults
      print output
		
