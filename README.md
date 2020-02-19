# KP2BW - KeePass 2.x to Bitwarden Converter

This tool helps to convert existing KeePass databases to Bitwarden accounts. This tool brings the following advantages over the bitwarden importer:

* **Import the all the data without having it ever touching the disk in unencrypted form** . Note: as attachments must be stored on disk prior to upload, those files will be on the disk during the upload phase. The files are removed from disk after uploading.
* **Resolve KeePass reference entries**(username and password only) in a "Bitwarden" way. For each entry with a reference field, the following happens:
  * If username and password are identical to the referenced entry, the url field will be added to the already existing entry
  * Otherwise, a new entry is created
* **Importing custom properties** from KeePass. The properties will be stored as text custom field in the corresponding Bitwarden item. If the property value is longer than 10,000 chars, it will be uploaded as attachment (Bitwarden limitation)
* **Importing attachments** from KeePass
* **Importing notes longer than 10,000 chars**. Notes can't be longer than this. The notes will be imported as an attachment named notes.txt.
* **Auto generate folders** in Bitwarden based on your KeePass folder structure
  * If you have nested folder in KeePass, you can choose between two handling mechanisms for the folder creation as Bitwarden does not support nested folders:
    * root-only: The highest folder in the nesting hierarchy will be used to store all entries of the tree: All entries in foo and foo/bar will be stored in a folder foo in Bitwarden.
    * combine: The nested folders will be preserved as own folders and named like this: foo/bar in KeePass results in a foo-bar folder in Bitwarden
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
usage: kp2bw.py [-h] -kpfile KPFILE [-kppw KPPW] [-bwpw BWPW] [-y] [-folder-generation-mode FOLDER_GENERATION_MODE]

required arguments:
  -kpfile KPFILE        Path to your KeePass 2.x db.

optional arguments:
  -h, --help            show this help message and exit
  -kppw KPPW            KeePass db password
  -bwpw BWPW            Bitwarden Password
  -y                    Skips the confirm bw installation question
  -folder-generation-mode FOLDER_GENERATION_MODE
                        Set the folder generation mode. Options: root-only => nested or not, only the root folder of the folder tree is created, combine => nested folders will be created with a combined name.
                        E.g. foo/bar in KeePass results in a foo-bar folder in Bitwarden.
```
