import json
import logging

from enum import Enum
from pykeepass import PyKeePass

from bitwardenclient import BitwardenClient

KP_REF_IDENTIFIER = "{REF:"
MAX_BW_ITEM_LENGTH = 10 * 1000

class Converter():
    def __init__(self, keepass_file_path, keepass_password, keepass_keyfile_path, bitwarden_password):
        self._keepass_file_path = keepass_file_path
        self._keepass_password = keepass_password
        self._keepass_keyfile_path = keepass_keyfile_path
        self._bitwarden_password = bitwarden_password

        self._kp_ref_entries = []
        self._entries = {}

        self._member_reference_resolving_dict = {
            "username": "U",
            "password": "P"
        }

    def _create_bw_python_object(self, title, notes, url, username, password, custom_properties):
        return {
            "organizationId": None,
            "folderId": None,
            "type":1,
            "name": title,
            "notes":notes,
            "favorite":False,
            "fields":[{"name": key,"value": value,"type":0} for key, value in custom_properties.items() if value is not None and len(value) <= MAX_BW_ITEM_LENGTH],
            "login": {
                "uris":[
                    {"match": None,"uri": url}
                ] if url else [],
                "username": username,
                "password":password,
                "totp": None,
                "passwordRevisionDate": None
            },
            "secureNote": None,
            "card": None,
            "identity": None
        }

    def _generate_folder_name(self, entry):
        if not entry.group.path or entry.group.path == "/":
            return None
        else:
            return "/".join(entry.group.path)

    def _add_bw_entry_to_entires_dict(self, entry):
        bw_item_object = self._create_bw_python_object(
            title = entry.title if entry.title else '_untitled',
            notes =  entry.notes if entry.notes and len(entry.notes) <= MAX_BW_ITEM_LENGTH else '',
            url = entry.url if entry.url else '',
            username = entry.username if entry.username else '',
            password = entry.password if entry.password else '',
            custom_properties = entry.custom_properties
        )

        folder = self._generate_folder_name(entry)

        # get attachments to store later on
        attachments = [(key, value) for key,value in entry.custom_properties.items() if value is not None and len(value) > MAX_BW_ITEM_LENGTH]

        if entry.notes and len(entry.notes) > MAX_BW_ITEM_LENGTH:
            attachments.append(("notes", entry.notes))

        if entry.attachments or attachments:
            attachments += entry.attachments
            self._entries[str(entry.uuid).replace("-", "").upper()] = (folder, bw_item_object, attachments)

        else:
            self._entries[str(entry.uuid).replace("-", "").upper()] = (folder, bw_item_object)

    def _parse_kp_ref_string(self, ref_string):
        # {REF:U@I:CFC0141068E83547BCEEAF0C1ADABAE0}
        tokens = ref_string.split(":")

        if len(tokens) != 3:
            raise Exception("Invalid REF string found")

        ref_compare_string = tokens[2][:-1]
        field_referenced, lookup_mode = tokens[1].split("@")

        return (field_referenced, lookup_mode, ref_compare_string)

    def _get_referenced_entry(self, lookup_mode, ref_compare_string):
        if lookup_mode == "I":
            # KP_ID lookup
            try:
                return self._entries[ref_compare_string]
            except Exception as e:
                logging.warning(f"!! - Could not resolve REF to {ref_compare_string} !!")
                raise e
        else:
            raise Exception("Unsupported REF lookup_mode")

    def _find_referenced_value(self, ref_entry, field_referenced):
        for member, reference_key in self._member_reference_resolving_dict.items():
            if field_referenced == reference_key:
                return ref_entry["login"][member]

        raise Exception("Unsuppoorted REF field_referenced")

    def _load_keepass_data(self):
        # aggregate entries
        kp = PyKeePass(
            filename=self._keepass_file_path,
            password=self._keepass_password,
            keyfile=self._keepass_keyfile_path)

        # reset data structures
        self._kp_ref_entries = []
        self._entries = {}

        logging.info(f"Found {len(kp.entries)} entries in KeePass DB. Parsing now...")
        for entry in kp.entries:
            # if not entry.password and not entry.username and not entry.notes:
            #     logging.warn(f"Ignoring entry {entry.title} since it has neither (1) a password, (2) a username, or (3) notes")
            #     continue

            # prevent not iteratable errors at "in" checks
            username = entry.username if entry.username else ''
            password = entry.password if entry.password else ''

            # Skip REFs as ID might not be in dict yet
            if KP_REF_IDENTIFIER in username or KP_REF_IDENTIFIER in password:
                self._kp_ref_entries.append(entry)
                continue

            # Normal entry
            self._add_bw_entry_to_entires_dict(entry)

        logging.info(f"Parsed {len(self._entries)} entries")

    def _resolve_entries_with_references(self):
        ref_entries_length = len(self._kp_ref_entries)

        if ref_entries_length == 0:
            return

        logging.info(f"Resolving {ref_entries_length} REF entries now...")
        for kp_entry in self._kp_ref_entries:
            try:
                # replace values
                replaced_entries = []
                for member in self._member_reference_resolving_dict.keys():
                    if KP_REF_IDENTIFIER in getattr(kp_entry, member):
                        field_referenced, lookup_mode, ref_compare_string = self._parse_kp_ref_string(getattr(kp_entry, member))
                        folder, ref_entry = self._get_referenced_entry(lookup_mode, ref_compare_string)

                        value = self._find_referenced_value(ref_entry, field_referenced)
                        setattr(kp_entry, member, value)

                        replaced_entries.append(ref_entry)

                # handle storing bitwarden style
                username_and_password_match = True
                for ref_entry in replaced_entries:
                    if ref_entry["login"]["username"] != kp_entry.username or ref_entry["login"]["password"] != kp_entry.password:
                        username_and_password_match = False
                        break

                if username_and_password_match:
                    # => add url to bw_item => username / pw identical
                    ref_entry["login"]["uris"].append({"match": None,"uri": kp_entry.url})
                else:
                    # => create new bitwarden item
                    self._add_bw_entry_to_entires_dict(kp_entry)

            except Exception as e:
                logging.warning(f"!! Could not resolve entry for {kp_entry.group.path}{kp_entry.title} [{str(kp_entry.uuid)}] !!")

        logging.debug(f"Resolved {ref_entries_length} REF entries")

    def _create_bitwarden_items_for_entries(self):
        i = 1
        max_i = len(self._entries)

        bw = BitwardenClient(self._bitwarden_password)
        for kp_id, value in self._entries.items():
            if len(value) == 2:
                (folder, bw_item_object) = value
                attachments = None
            else:
                (folder, bw_item_object, attachments) = value

            logging.info(f"[{i} of {max_i}] Creating Bitwarden entry in {folder} for {bw_item_object['name']}...")

            # create entry
            output = bw.create_entry(folder, bw_item_object)
            if "error" in output.lower():
                logging.error(f"!! ERROR: Creation of entry failed: {output} !!")
                continue
            if "skip" in output:
                continue

            # upload attachments
            if attachments:
                item_id = json.loads(output)["id"]

                for attachment in attachments:
                    logging.info(f"        - Uploading attachment for item {bw_item_object['name']}...")
                    res = bw.create_attachement(item_id, attachment)
                    if "failed" in res:
                        logging.error(f"!! ERROR: Uploading attachment failed: {res}")

            i += 1


    def convert(self):
        # load keepass data from database
        self._load_keepass_data()

        # resolve {REF:...} stuff
        self._resolve_entries_with_references()

        # store aggregated entries in bw
        self._create_bitwarden_items_for_entries()

