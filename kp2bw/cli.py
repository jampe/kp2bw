
import getpass
import logging
import sys
from argparse import ArgumentParser
from .convert import Converter

class MyArgParser(ArgumentParser):
    def error(self, message):
        sys.stderr.write(f'{self.prog}: {message}\n\n')
        self.print_help()
        sys.exit(2)


def _argparser():
    parser = MyArgParser(description="KeePass 2.x to Bitwarden converter by @jampe")

    parser.add_argument('keepass_file', help='Path to your KeePass 2.x db.')
    parser.add_argument('-kppw', dest='kp_pw', help='KeePass db password', default=None)
    parser.add_argument('-kpkf', dest='kp_keyfile', help='KeePass db key file', default=None)
    parser.add_argument('-bwpw', dest='bw_pw', help='Bitwarden password', default=None)
    parser.add_argument('-bworg', dest='bw_org', help='Bitwarden Organization Id', default=None)
    parser.add_argument('-import_tags', dest='import_tags', help='Only import tagged items', nargs='+',default=None)
    parser.add_argument('-bwcoll', dest='bw_coll', help='Id of Org-Collection, or \'auto\' to use name from toplevel-folders', default=None)
    parser.add_argument('-path2name', dest='path2name', help='Prepend folderpath of entries to each name',
                        action="store_const", const=True, default=True),
    parser.add_argument('-path2nameskip', dest='path2nameskip', help='Skip first X folders for path2name (default: 1)',
                        default=1, type=int ),
    parser.add_argument('-y', dest='skip_confirm', help='Skips the confirm bw installation question',
                        action="store_const", const=True, default=False)
    parser.add_argument('-v', dest='verbose', help='Verbose output', action="store_const", const=True, default=False)

    return parser


def _read_password(arg, prompt):
    if not arg:
        arg = getpass.getpass(prompt=prompt)

    return arg

def main():
    args = _argparser().parse_args()

    if (args.bw_coll and not args.bw_org):
        sys.stderr.write(f'ERROR: -bwcoll requires --bworg\n\n')
        _argparser().print_help()
        sys.exit(2)

    # logging
    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    # bw confirmation
    if not args.skip_confirm:
        confirm = None
        print("Do you have bw cli installed and is it set up?")
        print("1) If you use an on premise installation, use bw config to set the url: bw config server <url>")
        print("2) execute bw login once, as this script uses bw unlock only: bw login <user>")
        print(" ")

        while confirm != "y" and confirm != "n":
            confirm = input("Confirm that you have set up bw cli [y/n]: ").lower()

        if confirm == "n":
            print("exiting...")
            sys.exit(2)

    # stdin password
    kp_pw = _read_password(args.kp_pw, "Please enter your KeePass 2.x db password: ")
    bw_pw = _read_password(args.bw_pw, "Please enter your Bitwarden password: ")

    # call converter
    c = Converter(
        keepass_file_path=args.keepass_file,
        keepass_password=kp_pw,
        keepass_keyfile_path=args.kp_keyfile,
        bitwarden_password=bw_pw,
        bitwarden_organization_id=args.bw_org,
        bitwarden_coll_id=args.bw_coll,
        path2name=args.path2name,
        path2nameskip=args.path2nameskip,
        import_tags=args.import_tags
        )
    c.convert()

    print(" ")
    print("All done.")

if __name__ == "__main__":
    main()
