import os, sys, re, copy, shutil
import ConfigParser, optparse
import datetime, time, subprocess, commands

class maemkit(object):
  config_options = {}
  default_options = {}
  testtype = "mochitest"
  testdriver = ""
  config_file = "maemkit.cfg"

  testtypes = ["mochitest","chrome","reftest","crashtest","xpcshell"]

  def __init__(self):
    self.defaultOptions()

  def defaultOptions(self):
    self.default_options["close-when-done"] = False
    self.default_options["utility-path"] = "."
    self.default_options["xre-path"] = "."
    self.default_options["certificate-path"] = "certs"
    self.default_options["log-file"] = ""
    self.default_options["autorun"] = False
    self.default_options["console-level"] = ""
    self.default_options["file-level"] = "INFO"
    self.default_options["chrome"] = False
    self.default_options["browser-chrome"] = False
    self.default_options["a11y"] = False
    self.default_options["setenv"] = []
    self.default_options["browser-arg"] = []
    self.default_options["leak-threshold"] = []
    self.default_options["fatal-assertions"] = False
    self.default_options["test-path"] = ""

    self.default_options["split-directories"] = ""
    self.default_options["split-percentage"] = 20   

    self.default_options["appname"] = "fennec"
    self.default_options["total-clients"] = 1
    self.default_options["client-number"] = 1
    self.default_options["testroot"] = "."
    self.default_options["logdir"] = "logs"

    for type in self.testtypes:
      self.config_options[type] = {}
      self.config_options[type].update(self.default_options)

  def getConfigFile(self, input_section):
    config = ConfigParser.ConfigParser()
    config.read(self.config_file)
    temp_options = {}
    if (config.has_section(input_section)):
      for item in config.items(input_section):
        temp_options[item[0]] = item[1]
    return temp_options

  def getConfig(self):
    general = self.getConfigFile("general")
    for section in self.testtypes:
      self.config_options[section].update(general)
      self.config_options[section].update(self.getConfigFile(section))

  def getCli(self):
    parser = optparse.OptionParser()

    parser.add_option("--testtype", "-t", 
                       default="mochitest", action="store", type="string", dest="testtype",
                       help="Which test to run: mochitest, chrome, reftest, crashtest")

    parser.add_option("--client-number", 
                       default="-1", action="store", type="int", dest="clientnumber",
                       help="Which client you are in a parallel run. Range is 0:total-clients")

    parser.add_option("--total-clients", 
                       default="-1", action="store", type="int", dest="totalclients",
                       help="Number of clients in your testpass in parallel mode.  Used with client-number")

    #TODO: add other cli options;  need to figure out which ones we really care about
    (cli_options, args) = parser.parse_args()
    self.testtype = cli_options.testtype
    if (cli_options.clientnumber != -1): self.config_options[self.testtype]["client-number"] = cli_options.clientnumber
    if (cli_options.totalclients != -1): self.config_options[self.testtype]["total-clients"] = cli_options.totalclients

  def shellCommand(self, cmd):
    return commands.getoutput(cmd)

  def addCommand(self, newcmd, retry=False, timeout=60):
    timeout = 60
    topsrc = self.options["testroot"]
    myenv = copy.copy(os.environ)
    myenv["NATIVE_TOPSRCDIR"] = self.options["testroot"]
    myenv["TOPSRCDIR"] = self.options["testroot"]
    myenv["MOZILLA_FIVE_HOME"] = self.options["xre-path"]
    myenv["LD_LIBRARY_PATH"] = self.options["xre-path"]

    parts = []
    for cmd in newcmd.split(" "):
      if (cmd.strip() != ""):
        parts.append(cmd.strip())
    print " ".join(parts)
    sub_proc = subprocess.Popen(parts, bufsize=-1, env=myenv, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    starttime = datetime.datetime.now()

    retVal = ""
    std_out = ""
    std_err = ""

    while (datetime.datetime.now() - starttime < datetime.timedelta(minutes=timeout)):
      if (retry == True):
        print "doing retry logic on command"
        #TODO: consider putting this in a thread so it isn't blocking
        std_out += sub_proc.stdout.read();
        std_err += sub_proc.stderr.read();
      if (sub_proc.poll() is not None):
        std_out += sub_proc.stdout.read();
        std_err += sub_proc.stderr.read();
        break
      time.sleep(1)                                       
    retVal = std_out + "\n" + std_err

    if (datetime.datetime.now() - starttime >= datetime.timedelta(minutes=timeout)):
      retVal = "*** TIMEOUT ***"
    return retVal


  def cleanup(self):
    self.addCommand("killall fennec")
    self.addCommand("killall ssltunnel")
    self.addCommand("killall xpcshell")

  def getLogFileName(self, aDir):
    # returns the name of a log file from a directory
    logPrefix = "log_"
    logExtension = ".txt"
    p = re.compile('/')
    logMiddle = p.sub('_', aDir)
    logFileName = logPrefix + logMiddle + logExtension
    return logFileName

  #split a list of tests up to be run as parallel.
  #requires: total-clients and client-number in order to
  #calculate number of list items to return
  def splitListParallel(self, list, options):
    dirlist = []
    for dir in list: dirlist.append(dir)

    if (int(options["total-clients"]) > 1):
      client_workload = []
      dirs_per_client = abs(len(list) / int(options["total-clients"])) + 1

      iter = -1
      for dir in dirlist:
        iter += 1
        if (iter < (dirs_per_client * (int(options["client-number"]) - 1))): continue
        if (iter > (dirs_per_client * int(options["client-number"]))): break
        client_workload.append(dir)
      return client_workload

    # return self if we have just 1 client
    return dirlist

  def copytree(self, src, dst):
    self.shellCommand("cp -R "  +src + " " + dst)

  def copy(self, src, dst):
    self.shellCommand("cp " + src + " " + dst)
#    shutils.copytree(src, dst)

  def move(self, src, dst):
    self.shellCommand("mv " + src + " " + dst)
#    shutils.move(src, dst)

  def mkdir(self, src):
    self.shellCommand("mkdir " + src)
#    os.makedirs(src)

  def rmdir(self, src):
    self.shellCommand("rm -Rf " + src)
#    shutils.rmtree(src)
