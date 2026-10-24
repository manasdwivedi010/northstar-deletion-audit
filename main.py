"""
Root entrypoint for running Northstar Shop Deletion Audit Agent.
Usage: python main.py
"""
import os
import sys

# Add code directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'code'))

from main import main

if __name__ == '__main__':
    main()
