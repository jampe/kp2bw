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
Clone this repository and enter the directory. Install the tool dependencies using:
```
pip install -r requirements.txt

or

pipenv install -r requirements.txt
```

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
python kp2bw/kp2bw.py -kpfile passwords.kdbx
```

The help text of the tool is listed below:
```
usage: kp2bw.py [-h] -kpfile KPFILE [-kppw KPPW] [-bwpw BWPW] [-y] [-v] [-folder-generation-mode FOLDER_GENERATION_MODE]

required arguments:
  -kpfile KPFILE        Path to your KeePass 2.x db.

optional arguments:
  -h, --help        show this help message and exit
  -kpfile KP_FILE   Path to your KeePass 2.x db.
  -kppw KP_PW       KeePass db password
  -kpkf KP_KEYFILE  KeePass db key file
  -bwpw BW_PW       Bitwarden Password
  -y                Skips the confirm bw installation question
  -v                Verbose output
```
