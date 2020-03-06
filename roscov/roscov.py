"""
Main module for roscov. Provides a way to obtain code coverage statistics for any
ROS-based workspace, repository, or package using Mike Ferguson's code_coverage
package that can be found on GitHub.
"""

import sys
import os
import argparse
import re
import shlex
import subprocess
from statistics import mean

class BrokenRegexException(Exception):
	"""Raised when the regex strings in test_package() may be broken."""
	pass

class PackageNotFoundException(Exception):
	"""Raised when a package is not found by get_package_path"""
	pass

class TestFailedException(Exception):
	"""Raised in the event a package fails 1 or more tests"""
	def __init__(self):
		self.numFailedPackages = 0

class Package():
	"""Used to store information for each package that is being tested"""
	def __init__(self, name, path):
		self.name = name
		self.path = path
		self.lineCount = count_lines_of_code(path)
		self.hasTestDir = hasTestDir(path)

	def setWeight(self, weight):
		self.weight = weight

def test_package(pkg, path=None, 
					test_args=None, 
					cmake_build_type="Debug",
					suppress_catkin_output=False):
	"""
	Runs tests for pkg at path using test_cmd and returns the total coverage
	for the given package at the given path if one is given. If any tests fail, 
	the coverage number returned will be negative.
	
	Default test command is `catkin  <pkg> <default args>
	Default args are `--no-status --no-deps --force-cmake --force-color`

	Required arguments:
		pkg				(string) The package to test and obtain coverage for

	Optional arguments:
		path 			(string) Used for providing a path to test the package
							at. If one is not given, the path will be obtained
							using `catkin locate` from the current directory.
		test_args		(string) Use this as an override for the command args.
		cmake_build_type
						(string) Provide a build type to use with catkin build.
							Default: `Debug`
		suppress_catkin_output
						(bool) Enable or disable whether to display catkin output
	"""

	if not pkg:
		raise Exception("<pkg> argument is required for test_package()")

	test_cmd = "catkin build "+pkg+" -v --no-status --no-deps --force-color --catkin-make-args "+pkg+"_coverage_report"

	re_failed_test = re.compile(r"(?<=Failed: )[1-9]*[0-9]*(?= packages failed.)") # Based on catkin output
	re_coverage_pct = re.compile(r"Overall coverage rate:") # Based on code_coverage: 0.2.4
	re_line_pct = re.compile(r"\d*\.\d*(?=%)")

	# Test the package with coverage enabled
	print("Testing package %s..." % pkg)
	proc = subprocess.Popen(shlex.split(test_cmd), universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	pcts = []
	get_pkg_percentages = False # TODO: Remove this variable, no clue what it does

	# run tests on the package only if it contains a test/ directory
	if not hasTestDir(pkg.path):
		print("Package %s has no tests, so its coverage is 0%%" % pkg)
		return 0

	for line in proc.stdout:

		if not suppress_catkin_output:
			sys.stdout.write(line)

		if re.match(re_failed_test, line):
			sys.stderr.write("Unit tests failed for package: "+pkg+"\n")
			raise TestFailedException(69) # TODO: Change this to be the actual number of tests failed

		# track total avg of that package (equally weighted between lines covered and functions covered)
		if get_pkg_percentages:

			if not pcts: # grab lines_pct

				matches = re.findall(re_line_pct, line)
				if not matches:
					raise BrokenRegexException("Error: possible broken regex in coverage.py (re_line_pct)")
				pcts.append(float(matches[0]))

			else: # grab functions_pct

				matches = re.findall(re_line_pct, line)
				if not matches:
					raise BrokenRegexException("Error: possible broken regex in coverage.py (re_line_pct)")
				pcts.append(float(matches[0]))
				get_pkg_percentages = False

		if re.match(re_coverage_pct, line):
			get_pkg_percentages = True

	proc.wait()

	if not pcts:
		raise BrokenRegexException("Error: possible broken regex in coverage.py (re_coverage_pct)")

	return mean([pcts[0], pcts[1]])

def hasTestDir(path):
	for fname in os.listdir(path):
		if os.path.isdir(os.path.join(path, fname)) and fname.lower() == "test":
			return True
	return False

def count_lines_of_code(path):
	"""Calculate and return linecount from 'path' using cloc and extracting 
	output with grep. Only counts C++ code.

	required arguments:
		path 			the path at which the lines of code are counted
	"""
	try:
		proc1 = subprocess.Popen(shlex.split("cloc %s --quiet --csv" % path), stdout=subprocess.PIPE)
		proc2 = subprocess.Popen(shlex.split("grep -i ',C++'"), stdin=proc1.stdout, stdout=subprocess.PIPE)
		proc1.stdout.close()
		linecount = proc2.stdout.read().decode(sys.stdout.encoding)
		return int(linecount[linecount.rfind(',')+1:])
	except FileNotFoundError:
		print("Error: cloc not installed")
		sys.exit(1)

def get_package_path(pkg, debug=True):
	"""Queries 'catkin locate' and returns the absolute path of 'pkg' in the 
	current workspace.

	required arguments:
		pkg 			the package to search for

	optional arguments:
		debug 			if True, prints debug statements
	"""
	path = ""
	try:
		proc = subprocess.Popen(["catkin", "locate", pkg], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		path = proc.stdout.read()
		if path.startswith('ERROR'):
			raise PackageNotFoundException("Package %s not found with catkin locate:\n\t%s" % (pkg, path))
		if debug:
			print("Found package %s at path %s" % (pkg, path))
		return path.rstrip()
	except FileNotFoundError:
		sys.exit("Error: Roscov: searching for package '%s' failed. Catkin is likely not installed." % pkg)

def get_package(pkg, debug=True):
	"""Used for turning a string input into a Package class

	required arguments:
		pkg 			the package to search for

	optional arguments:
		debug 			if True, prints debug statements
	"""
	path = get_package_path(pkg)
	return Package(pkg, path)

def print_results(packages, unfound=None, failed=None, threshold=None):
	"""Used for printing the final output of the tool

	required arguments:
		packages 			list of Package objects tested

	optional arguments:
		unfound_packages 	list of unfound packages in the test
		failed_packages		list of failed packages in the test
	"""
	for pkg in unfound:
		sys.stderr.write("Package not found: "+pkg+"\n")
		packages.remove(pkg)

	if not packages:
		sys.exit("Error: no coverage data generated for given list of packages")

	# calculate and print all summaries, then weight and total coverage stat for each package (weight = #lines_in_pkg / #lines_total)
	i = 0
	for pkg in packages:
		print("Coverage summary for '%s':\n\t%s%% line coverage\n\t%s%% function coverage\n\t%s%% average coverage" % (pkg, pkg_summaries[i][1], pkg_summaries[i][2], pkg_summaries[i][0]))
		i += 1
	i = 0
	for pkg in packages:
		print("Package '%s' has average coverage of %s%%, and contains %s lines out of %s total lines being tested." % (pkg, pkg_avgs[i], linecounts[i], totallines))
		weighted_pcts.append(float(linecounts[i]) / float(totallines) * float(pkg_avgs[i]))
		i += 1
	
	total_weighted_coverage = sum(weighted_pcts)
	print("Total coverage: %s%%" % str(round(total_weighted_coverage, 2)))
	os.system("catkin_test_results")

	if threshold and total_weighted_coverage < threshold:
		sys.exit("Resulting total coverage is below threshold. Script exited with exit code 1.")

def run(packages, quiet_output=False, 
				threshold=None, 
				debug=False):
	"""General main method for this script

	required arguments:
		TODO 			

	optional arguments:
		TODO 			
	"""

	totallines = 0
	pkg_totals = []
	unfound_packages = []
	failed_packages = []

	test_packages = []
	for pkg in packages:
		try:
			test_packages.append(get_package(pkg))
		except PackageNotFoundException:
			unfound_packages.append(pkg)

	for pkg in test_packages:
		try:	
			coverage = test_package(pkg, suppress_catkin_output=quiet_output)

			if not coverage:
				sys.exit("Error: no coverage data obtainable for package '%s'" % pkg.name) 

			pkg_avgs.append(coverage)
			totallines += pkg.lineCount

		except TestFailedException:
			failed_packages.append(pkg.name)

	print_results(test_packages, unfound=unfound_packages, failed=failed_packages)

if __name__ == "__main__":
	run(sys.argv[1:])