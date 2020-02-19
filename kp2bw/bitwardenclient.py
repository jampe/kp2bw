import json

from subprocess import check_output, STDOUT, CalledProcessError

class BitwardenClient():
    def __init__(self, password):
        # login
        self.key = self._exec(f"bw unlock {password} --raw")
        if "error" in self.key:
            raise Exception("Could not unlock the bitwarden db. Is the Master Password corrent and are bw cli tools set up correctly?")

        # make sure data is up to date
        if not "Syncing complete." in self._exec_with_session("bw sync"):
            raise Exception("Could not sync the local state to your bitwarden server")

        # get folder list
        self.folders = {folder["name"]: folder["id"] for folder in json.loads(self._exec_with_session("bw list folders"))}
 
    def _exec(self, command):
        try:
            output = check_output(command, stderr=STDOUT, shell=True)
        except CalledProcessError as e:
            output = e.output
        
        return str(output.decode("utf-8"))
    

    def _exec_with_session(self, command):
        return self._exec(f"{command} --session {self.key}")

    def has_folder(self, folder):
        return folder in self.folders

    def create_folder(self, folder):
        if self.has_folder(folder):
            return

        data = {"name": folder }
        output = self._exec_with_session(f'echo \'{json.dumps(data)}\' | bw encode | bw create folder')

        output_obj = json.loads(output)

        self.folders[output_obj["name"]] = output_obj["id"]

    def create_entry(self, folder, entry):
        self.create_folder(folder)

        # set id
        entry["folderId"] = self.folders[folder]

        json_str = json.dumps(entry)

        # string escaping due to echo "string"
        json_str = json_str.replace('"', r'\"')

        output = self._exec_with_session(f'echo "{json_str}" | bw encode')

        return not "error" in output