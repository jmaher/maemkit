import mochidriver, chromedriver, refdriver, xpcdriver, maemkit


def runTest(kit):
  if (kit.testtype == "mochitest"): testdriver = mochidriver.mochikit(kit)
  if (kit.testtype == "chrome"): testdriver = chromedriver.chromedriver(kit)
  if (kit.testtype == "reftest"): testdriver = refdriver.reftest(kit)
  if (kit.testtype == "crashtest"): testdriver = refdriver.crashtest(kit)
  if (kit.testtype == "xpcshell"): testdriver = xpcdriver.xpcdriver(kit)

  if (testdriver != ""):
    testdriver.getTests()
    testdriver.prepTests()
    testdriver.runTests()


def main():
  mk = maemkit.maemkit()
  mk.getConfig()
  mk.getCli()
  runTest(mk)

if __name__ == "__main__":
  main()

