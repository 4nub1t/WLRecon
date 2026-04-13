import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from cli import CLI
from config import Config

def main():
    config = Config()
    cli = CLI(config)
    cli.run()

if __name__ == "__main__":
    main()
