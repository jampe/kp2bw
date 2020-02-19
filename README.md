# KP2BW Converter

This tool helps to convert existing KeePass databases to Bitwarden accounts. This tool brings the following advantages over the bitwarden importer:

* Import the all the data without having it ever touching the disk in unencrypted form
* Generate folders in Bitwarden based on your KeePass folder structure
  * If you have several folder levels in KeePass, it will only create a folder for the highest level folder. Bitwarden does not support nested folders.
* Resolve KeePass reference entries (username and password only) in a "Bitwarden" way. For each entry with a reference field, the following happens:
  * If username and password are identical to the referenced entry, the url field will be added to the already existing entry
  * Otherwise, a new entry is created
* Importing of the entries one by one, it is slower but it will prevent bitwarden db query max time exceeded errors for bigger KeePass databases

## Usage
First, make sure you install the Bitwarden CLI tool on your system. After installing, set up the client:

If you use a on premise installation, set your url like this:
```
bw config server https://your-domain.com/
```

Now, you have to log into your account once:
```
bw login username
```

After that, you can use the kp2bw.py tool to import the data. The help text of the tool is listed below:
```
usage: kp2bw.py [-h] -kpfile KPFILE -kppw KPPW -bwpw BWPW

optional arguments:
  -h, --help      show this help message and exit
  -kpfile KPFILE  Path to your KeePass 2.x db.
  -kppw KPPW      KeePass db password
  -bwpw BWPW      Bitwarden Password
```