import argparse
import sys
import getpass
import logging

from convert import Converter

class MyArgParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('Error: %s\n\n' % message)
        self.print_help()
        sys.exit(2)

if __name__ == "__main__":
    print("⁻" * 58)
    print("--[kp2bw - KeePass 2.x to Bitwarden converter by @jampe]--")
    print("-" * 58)
    print(" ")

    parser = MyArgParser()
    parser.add_argument('-kpfile', dest='kpfile', help='Path to your KeePass 2.x db.', required=True)
    parser.add_argument('-kppw', dest='kppw', help='KeePass db password', default=None)
    parser.add_argument('-bwpw', dest='bwpw', help='Bitwarden Password', default=None)
    parser.add_argument('-y', dest='skip_confirm', help='Skips the confirm bw installation question', action="store_const", const=True, default=False)
    parser.add_argument('-v', dest='verbose', help='Verbose output', action="store_const", const=True, default=False)

    args = parser.parse_args()

    # logging
    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s',level=logging.INFO)

    # bw confirmation
    if not args.skip_confirm:
        confirm = None
        print("Do you have bw cli installed and is it set up?")
        print("1) If you use an on premise installation, use bw config to set the url: bw config server <url>")
        print("2) execute bw login once, as this script uses bw unlock only: bw login <user>")
        print(" ")

        while(confirm != "y" and confirm != "n"):
            confirm = input("Confirm that you have set up bw cli [y/n]: ").lower()

        if confirm == "n":
            print("exiting...")
            sys.exit(2)

    # stdin password
    kppw = args.kppw
    if not kppw:
        kppw = getpass.getpass(prompt="Please enter your KeePass 2.x db password: ")

    bwpw = args.bwpw
    if not bwpw:
        bwpw = getpass.getpass(prompt="Please enter your Bitwarden password: ")

    # call converter
    c = Converter(args.kpfile, kppw, bwpw)
    c.convert()

    print(" ")
    print("All done.")