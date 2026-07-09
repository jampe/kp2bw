import json
import logging
import os
import shutil
import subprocess
import tempfile
from itertools import groupby


class BitwardenClient():

    def __init__(self, password, orgId):
        # check for bw cli installation
        if not "bitwarden" in self._exec(["bw", "--version"]):
            raise Exception("Bitwarden Cli not installed! See https://help.bitwarden.com/article/cli/#download--install for help")

        # save org
        self._orgId = orgId

        # login
        self._key = self._exec(["bw", "unlock", password, "--raw"], redact_log=True)
        if "error" in self._key:
            raise Exception("Could not unlock the Bitwarden db. Is the Master Password correct and are bw cli tools set up correctly?")

        # make sure data is up to date
        if not "Syncing complete." in self._exec(["bw", "sync", "--session", self._key]):
            raise Exception("Could not sync the local state to your Bitwarden server")

        # get folder list
        self._folders = {folder["name"]: folder["id"] for folder in json.loads(self._exec(["bw", "list", "folders", "--session", self._key]))}

        # get existing entries
        self._folder_entries = self._get_existing_folder_entries()

        # get existing collections
        if orgId:
            self._colls = {coll["name"]: coll["id"] for coll in json.loads(self._exec(["bw", "list", "org-collections", "--organizationid", orgId, "--session", self._key]))}
        else:
            self._colls = None

    def __enter__(self):
        self._temp_dir = tempfile.mkdtemp(prefix="kp2bw-")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._remove_temporary_attachment_folder()

    def _create_temporary_attachment_folder(self):
        if not os.path.isdir(self._temp_dir):
            os.mkdir(self._temp_dir)

    def _remove_temporary_attachment_folder(self):
        if os.path.isdir(self._temp_dir):
            shutil.rmtree(self._temp_dir)

    def _exec(self, args, stdin_data=None, redact_log=False):
        """Run a command with list-form args (avoiding shell). Return stdout on
        success, stderr on failure, or the exception text as a fallback."""
        log_safe = ' '.join(args)
        if redact_log and len(args) >= 3 and args[1] == "unlock":
            log_safe = f"{args[0]} {args[1]} ***REDACTED*** {' '.join(args[3:])}"
        if hasattr(self, '_key') and self._key:
            log_safe = log_safe.replace(self._key, "***REDACTED***")

        logging.debug(f"-- Executing command: {log_safe}")
        try:
            proc = subprocess.run(
                args,
                input=stdin_data,
                capture_output=True,
                timeout=120,
            )
            output = proc.stdout if proc.returncode == 0 else proc.stderr
        except subprocess.TimeoutExpired as e:
            output = e.stderr or b"Timeout expired"
        except Exception as e:
            return str(e)

        result = output.decode("utf-8", "ignore") if isinstance(output, bytes) else str(output)
        logging.debug(f"  |- Output: {result[:500]}")
        return result

    def _get_existing_folder_entries(self):
        folder_id_lookup_helper = {folder_id: folder_name for folder_name,folder_id in self._folders.items()}
        items = json.loads(self._exec(["bw", "list", "items", "--session", self._key]))

        # fix None folderIds for entries without folders
        for item in items:
            if not item['folderId']:
                item['folderId'] = ''

        items.sort(key=lambda item: item["folderId"])
        return {folder_id_lookup_helper[folder_id] if folder_id in folder_id_lookup_helper else None: [entry["name"] for entry in entries]
            for folder_id, entries in groupby(items, key=lambda item: item["folderId"])}

    def has_folder(self, folder):
        return folder in self._folders

    def create_folder(self, folder):
        if not folder or self.has_folder(folder):
            return

        data = {"name": folder}
        json_bytes = json.dumps(data).encode("utf-8")

        output = self._exec(["bw", "create", "folder", "--session", self._key], stdin_data=json_bytes)

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

        json_bytes = json.dumps(entry).encode("utf-8")

        output = self._exec(["bw", "create", "item", "--session", self._key], stdin_data=json_bytes)

        return output

    def _validate_attachment_filename(self, filename: str) -> str:
        """Validate and sanitize attachment filename using os.path.basename."""
        safe_name = os.path.basename(filename)
        if not safe_name or safe_name in ('.', '..'):
            raise ValueError(f"Invalid attachment filename: {filename!r}")
        if '\x00' in safe_name:
            raise ValueError("Attachment filename contains null byte")
        return safe_name

    def create_attachment(self, item_id, attachment):
        # store attachment on disk
        filename = ""
        data = None
        if isinstance(attachment, tuple):
            # long custom property
            key, value = attachment
            filename = self._validate_attachment_filename(key + ".txt")
            data = value.encode("UTF-8")
        else:
            # real kp attachment
            filename = self._validate_attachment_filename(attachment.filename)
            data = attachment.data

        # make sure temporary attachment folder exists
        self._create_temporary_attachment_folder()

        path_to_file_on_disk = os.path.join(self._temp_dir, filename)
        with open(path_to_file_on_disk, "wb") as f:
            f.write(data)

        try:
            output = self._exec(["bw", "create", "attachment", "--file", path_to_file_on_disk, "--itemid", item_id, "--session", self._key])
        finally:
            os.remove(path_to_file_on_disk)

        return output

    def create_org_get_collection(self, collectionname):

        if not collectionname: return None

        # check for existing
        if self._colls.get(collectionname):
            return self._colls.get(collectionname)

        # get template
        entry = json.loads(self._exec(["bw", "get", "template", "org-collection", "--session", self._key]))

        # set org and Name
        entry['name'] = collectionname
        entry['organizationId'] = self._orgId

        json_bytes = json.dumps(entry).encode("utf-8")

        output = self._exec(["bw", "create", "org-collection", "--organizationid", self._orgId, "--session", self._key], stdin_data=json_bytes)
        if (not output): return None
        data = json.loads(output)
        if (not data["id"]): return None
        newCollId = data["id"]

        #store in cache
        self._colls[collectionname] = newCollId

        return newCollId
