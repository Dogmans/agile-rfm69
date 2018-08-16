import sys
# Put the mock stuff in the path so we get a mock RFM69
sys.path.insert(0, "./mocks")
from run_server import *

if __name__ == '__main__':
	main()