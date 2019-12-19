import sys
import os
import argparse
import glob
import warnings
import re

from __future__ import print_function

regex = {
	RE_FAILED_TEST: re.compile("(?<=Failed: )[1-9]*[0-9]*(?= packages failed.)"),
	RE_COVERAGE_PCT: re.compile("Overall coverage rate:")
}

def run(packages):
	for pkg in packages:
		# find package path
		dir_matches = glob.glob("src/*/"+pkg)

		if dir_matches:

			os.chdir(dir_matches[0])
			print("found package at path "+os.getcwd())

			# run tests on the package
			pkg_percents=[]

			os.system("export PKG="+pkg)
			stream = os.popen('catkin run_tests $PKG --no-status --no-deps --force-cmake --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DENABLE_COVERAGE_TESTING=ON --catkin-make-args ${PKG}_coverage')
			
			# track total avg of that package
			for line in stream.readLines():

				if re.match(RE_FAILED_TEST, line): # more than 0 packages failed in the test
					print("Unit tests failed for package: "+pkg)
					sys.exit(1) # TODO: change to custom error code?

				if re.match(RE_COVERAGE_PCT, line)
					pkg_percents.append("some_value_from_regex")


			# calculate total coverage stat and print output
		
		else:
			warnings.warn("Package not found"+pkg, Warning)

		os.system("catkin_test_results")

if __name__ == '__main__':
	parser = argparse.ArgumentParser(usage='coverage [<args>] [<packages>]')
	parser.add_argument('-h', dest='help', default=None, action='store_true',
	                    help="Print the help message for this tool")
	parser.add_argument('packages', dest='pkgs', metavar='packages', nargs='+')
	args = parser.parse_args(sys.argv[1:])

	if (args.help):
		parser.print_help()
		sys.exit(0)

    run(args.pkgs.split(' '))
