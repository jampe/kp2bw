import json
import os
import logging
import shlex
import platform
import base64

from itertools import groupby

from subprocess import check_output, STDOUT, CalledProcessError

class BitwardenClient():
    def __init__(self, password):
        # check for bw cli installation
        if not "bitwarden" in self._exec("bw"):
            raise Exception("Bitwarden Cli not installed! See https://help.bitwarden.com/article/cli/#download--install for help")
        
        # login
        self._key = self._exec(f"bw unlock {password} --raw")
        if "error" in self._key:
            raise Exception("Could not unlock the bitwarden db. Is the Master Password corrent and are bw cli tools set up correctly?")

        # make sure data is up to date
        if not "Syncing complete." in self._exec_with_session("bw sync"):
            raise Exception("Could not sync the local state to your bitwarden server")

        # get folder list
        self._folders = {folder["name"]: folder["id"] for folder in json.loads(self._exec_with_session("bw list folders"))}

        # get existing entries
        self._folder_entries = self._get_existing_folder_entries()
 
    def _exec(self, command):
        try:
            logging.debug(f"-- Executing command: {command}")
            output = check_output(command, stderr=STDOUT, shell=True)
        except CalledProcessError as e:
            output = e.output
        
        logging.debug(f"  |- Output: {output}")
        return str(output.decode("utf-8","ignore"))

    def _get_existing_folder_entries(self):
        folder_id_lookup_helper = {folder_id: folder_name for folder_name,folder_id in self._folders.items()}
        items = json.loads(self._exec_with_session("bw list items"))
        
        # fix None folderIds for entries without folders
        for item in items:
            if not item['folderId']:
                item['folderId'] = ''

        items.sort(key=lambda item: item["folderId"])
        return {folder_id_lookup_helper[folder_id] if folder_id in folder_id_lookup_helper else None: [entry["name"] for entry in entries] 
            for folder_id, entries in groupby(items, key=lambda item: item["folderId"])}

    def _exec_with_session(self, command):
        return self._exec(f"{command} --session '{self._key}'")

    def has_folder(self, folder):
        return folder in self._folders

    def _get_platform_dependend_echo_str(self, string):
        if platform.system() == "Windows":
            return f'echo {string}'
        else:
            return f'echo \'{string}\''

    def create_folder(self, folder):
        if not folder or self.has_folder(folder):
            return

        data = {"name": folder }
        data_b64 = base64.b64encode(json.dumps(data).encode("UTF-8")).decode("UTF-8")

        output = self._exec_with_session(f'{self._get_platform_dependend_echo_str(data_b64)} | bw create folder')

        output_obj = json.loads(output)

        self._folders[output_obj["name"]] = output_obj["id"]

    def create_entry(self, folder, entry):

        if not entry["name"]:
            entry["name"] = "_untitled"

        # check if already exists
        if folder in self._folder_entries and entry["name"] in self._folder_entries[folder]:
            logging.info(f"-- Entry {entry['name']} already exists in folder {folder}. skipping...")
            return "skip"

        # create folder if exists
        if folder:
            self.create_folder(folder)

            # set id
            entry["folderId"] = self._folders[folder]

        json_str = json.dumps(entry)

        # convert string to base64
        json_b64 = base64.b64encode(json_str.encode("UTF-8")).decode("UTF-8")

        output = self._exec_with_session(f'{self._get_platform_dependend_echo_str(json_b64)} | bw create item')

        return output

    
    
    def create_attachement(self, item_id, attachment):
        # store attachement on disk
        filename = ""
        data = None
        if isinstance(attachment, tuple):
            # long custom property
            key, value = attachment
            filename = key + ".txt"
            data = value.encode("UTF-8")
        else:
            # real kp attachment
            filename = attachment.filename
            data = attachment.data

        with open(filename, "wb") as f:
            f.write(data)
        
        try:
            output = self._exec_with_session('bw create attachment --file "{}" --itemid {}'.format(filename, item_id))
        finally:
            os.remove(filename)
        
        return output
