import sys
import os
import argparse

from . import __version__
from . import roscov

class RoscovRunnable:

	def __init__(self):
		parser = argparse.ArgumentParser(usage='roscov [<args>] [<packages>]')
		parser.add_argument('-v', '--version', dest='get_version', default=None, action='store_true',
								help="Print the current version of python and roscov")
		parser.add_argument('--quiet', dest='quiet', action='store_true', default=False, 
								help='Suppress catkin output and only print statements from this tool')
		parser.add_argument('--threshold', dest='threshold', type=int, default=None, 
								help='Any resulting total coverage below this number results in an exit code of 1')
		parser.add_argument('--debug', dest='debug', action='store_true', default=None, 
								help='Show debug statements from function calls')
		parser.add_argument('packages', metavar='packages', nargs='*')
		
		args = parser.parse_args(sys.argv[1:])

		if args.get_version:
			self._version()
			sys.exit(0)

		if not args.packages:
			print("roscov: error: the following arguments are required: packages")
			parser.print_help()
			sys.exit(1)

		pkgs = args.packages
		if len(pkgs) == 1:
			pkgs = pkgs[0].split(" ")

		dirs =  next(os.walk('.'))[1]
		if not 'devel' in dirs: 
			sys.exit("Roscov: Error: devel/ directory not found. Directory is not a catkin workspace.")
		if not 'src' in dirs:
			sys.exit("Roscov: Error: src/ directory not found. Directory is not a catkin workspace.")

		if pkgs[0] == '.':
			print("workspace detected, running all packages using catkin list --unformatted")
			roscov.run_ws(None)
		else:
			if len(pkgs) == 1:
				print("one package detected")
			else:
				print("multiple packages detected")
			roscov.run(pkgs)

	def _version(self):
		print("Roscov version:", __version__)
		print("Python version:", str(sys.version_info[0])+"."+str(sys.version_info[1])+"."+str(sys.version_info[2]))
		sys.exit(0)

def main():
	RoscovRunnable()
