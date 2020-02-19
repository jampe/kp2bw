import json
import os
import logging

from itertools import groupby

from subprocess import check_output, STDOUT, CalledProcessError

class BitwardenClient():
    def __init__(self, password):
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
        
        logging.debug(f"  -- Output: {output}")
        return str(output.decode("utf-8"))

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
        return self._exec(f"{command} --session {self._key}")

    def has_folder(self, folder):
        return folder in self._folders

    def create_folder(self, folder):
        if not folder or self.has_folder(folder):
            return

        data = {"name": folder }
        output = self._exec_with_session(f'echo \'{json.dumps(data)}\' | bw encode | bw create folder')

        output_obj = json.loads(output)

        self._folders[output_obj["name"]] = output_obj["id"]

    def create_entry(self, folder, entry):
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

        # string escaping due to echo "string"
        json_str = json_str.replace('"', r'\"')

        output = self._exec_with_session(f'echo "{json_str}" | bw encode | bw create item')

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
            output = self._exec_with_session(f'bw create attachment --file ./{filename} --itemid {item_id}')
        finally:
            os.remove(filename)
        
        return output