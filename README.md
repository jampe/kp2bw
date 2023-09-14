# KP2BW - KeePass 2.x to Bitwarden Converter

This tool helps to convert existing KeePass databases to Bitwarden accounts. It provides the following advantages compared to the importer by the bitwarden project:

* **Import the all the data without having it ever touching the disk in unencrypted form** . Note: as attachments must be stored on disk prior to upload, those files will be on the disk during the upload phase. The files are removed from disk after uploading.
* **Resolve KeePass reference entries**(username and password only) in a "Bitwarden" way. For each entry with a reference field, the following happens:
  * If username and password are identical to the referenced entry, the url field will be added to the already existing entry
  * Otherwise, a new entry is created
* **Importing custom properties** from KeePass. The properties will be stored as text custom field in the corresponding Bitwarden item. If the property value is longer than 10,000 chars, it will be uploaded as attachment (Bitwarden limitation)
* **Importing attachments** from KeePass
* **Importing notes longer than 10,000 chars**. Notes can't be longer than this. The notes will be imported as an attachment named notes.txt.
* **Idempotent import**: Entries won't be duplicated when running the import multiple times.
* **Nested folders supported**: If you have nested folder in KeePass, kp2bw will recreate the same folder structure in Bitwarden for you.
* Importing of the entries one by one, it is slower but it will prevent bitwarden db query max time exceeded errors for bigger KeePass databases
* **Full UTF-8 support**
* **Multi OS support**: Works on Windows, macOS, & Linux.

## Installation
1) choose either one of the installation methods below

### Install using the pre built whl file
1) Make sure you've installed python 3 and pip on your system.
1) Download the newest whl release from the releases
1) Install kp2bw via pip:
  ```
  pip install kp2bw-1.1-py3-none-any.whl
  ```

### Install from source
1) Make sure you've installed python 3 and pip on your system.
1) Clone / download this repository and enter the directory.
1) Create a new python venv and activate it
  ```
  python -m venv .env/kp2bw

  Windows:
  .env\kp2bw\Scripts\activate
  
  Linux:
  .env/kp2bw/bin/activate
  ```
1) pip install .

## Usage
First, make sure you install the Bitwarden CLI tool on your system (https://help.bitwarden.com/article/cli/). After installing, set up the client:

If you use a on premise installation, set your url like this:
```
bw config server https://your-domain.com/
```

Now, you have to log into your account once:
```
bw login username
```

After that, you can use the kp2bw.py tool to import the data. This file is located in the kp2bw folder. Execute it using:
```
kp2bw passwords.kdbx
```

The help text of the tool is listed below:
```
usage: kp2bw [-h] [-kppw KP_PW] [-kpkf KP_KEYFILE] [-bwpw BW_PW] [-y] [-v] keepass_file [-import_tags tags1 tags2] 

KeePass 2.x to Bitwarden converter by @jampe

positional arguments:
  keepass_file      Path to your KeePass 2.x db.

optional arguments:
  -h, --help        show this help message and exit
  -kppw KP_PW       KeePass db password
  -kpkf KP_KEYFILE  KeePass db key file
  -bwpw BW_PW       Bitwarden Password
  -bworg BW_OrgId   Id of Organization to Upload Into
  -bwcoll BW_CollId Id of Org-Collection, or 'auto' to use name from toplevel-folders
  -import_tags      Only import items with tags
  -path2name        Prepend folderpath of entries to each name
  -path2nameskip PATH2NAMESKIP
                    Skip first X folders for path2name (default: 1)
  -y                Skips the confirm bw installation question
  -v                Verbose output
```

## Troubleshooting
### Invalid master password error on bw unlock

```
DEBUG: -- Executing command: bw unlock My?Master>>Password123 --raw
DEBUG:   |- Output: b'Invalid master password.'
DEBUG: -- Executing command: bw sync --session 'Invalid master password.'
```

The solution is to encapsulate the master password in double quotes (when you're typing it in at the password prompt), then the bw unlock command will run successfully and sync will continue. Thanks @readysteadywhoa for reporting this and providing a solution!

