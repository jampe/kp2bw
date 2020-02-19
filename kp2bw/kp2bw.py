import argparse
import sys
import getpass

from convert import convert

class MyArgParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('Error: %s\n\n' % message)
        self.print_help()
        sys.exit(2)

if __name__ == "__main__":
    print("kp2bw")
    print("=============================")
    print("by github.com/jampe")
    print(" ")
    print("!! Make sure that you have bw installed and it's set up (use bw config to set on presmise server and execute bw login once! This script uses bw unlock only)")
    print("=============================")
    print(" ")

    parser = MyArgParser()
    parser.add_argument('-kpfile', dest='kpfile', help='Path to your KeePass 2.x db.', required=True)
    parser.add_argument('-kppw', dest='kppw', help='KeePass db password', default=None)
    parser.add_argument('-bwpw', dest='bwpw', help='Bitwarden Password', default=None)

    args = parser.parse_args()

    # bw confirmation
    confirm = None
    while(confirm != "y" and confirm != "n"):
        confirm = input("Confirm that you have set up bw [y/n]:")
    
    if confirm == "n":
        print("exiting...")
        exit()

    # stdin password
    kppw = args.kppw
    if not kppw:
        kppw = getpass.getpass(prompt="Please enter your KeePass 2.x db password: ")

    bwpw = args.bwpw
    if not bwpw:
        bwpw = getpass.getpass(prompt="Please enter your Bitwarden password: ")

    convert(args.kpfile, kppw, bwpw)