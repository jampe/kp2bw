import json
from pykeepass import PyKeePass

from bitwardenclient import BitwardenClient

KP_REF_IDENTIFIER = "{REF:"

def create_bw_python_object(title, notes, url, username, password):
    return {
        "organizationId": None,
        "folderId": None,
        "type":1,
        "name": title,
        "notes":notes,
        "favorite":False,
        "fields":[],
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

def generate_folder_name(entry):
    return str(entry.group.path).split("/")[0]

def add_bw_entry_to_dict(entries_dict, entry, username, password):
    bw_item_object = create_bw_python_object(
        title = entry.title if entry.title else '',
        notes =  entry.notes if entry.notes else '',
        url = entry.url if entry.url else '',
        username = username,
        password = password
    )

    folder = generate_folder_name(entry)

    entries_dict[str(entry.uuid).replace("-", "").upper()] = (folder, bw_item_object)

def parse_kp_ref_string(ref_string):
    # {REF:U@I:CFC0141068E83547BCEEAF0C1ADABAE0}
    tokens = ref_string.split(":")

    if len(tokens) != 3:
        raise Exception("Invalid REF string found")
    
    ref_compare_string = tokens[2][:-1]
    field_referenced, lookup_mode = tokens[1].split("@")

    return (field_referenced, lookup_mode, ref_compare_string)

def get_referenced_entry(entries_dict, lookup_mode, ref_compare_string):
    if lookup_mode == "I":
        # KP_ID lookup
        try:
            return entries_dict[ref_compare_string]
        except Exception as e:
            print(f"!! - Could not resolve REF to {ref_compare_string} !!")
            raise e
    else:
        raise Exception("Unsupported REF lookup_mode")

def find_referenced_value(entries_dict, field_referenced, lookup_mode, ref_compare_string):
    folder, ref_entry = get_referenced_entry(entries_dict, lookup_mode, ref_compare_string)
    
    if field_referenced == "U":
        # Username
        return ref_entry["login"]["username"]
    elif field_referenced == "P":
        # Password
        return ref_entry["login"]["password"]
    else:
        raise Exception("Unsuppoorted REF field_referenced")

def convert(keepass_file_path, keepass_password, bitwarden_password):
    kp = PyKeePass(keepass_file_path, password=keepass_password)
    bw = BitwardenClient(bitwarden_password)

    # aggregate entries
    kp_ref_entries = []
    entries = {}
    print(f"Found {len(kp.entries)} entries in KeePass DB. Parsing now...")
    for entry in kp.entries:
        if not entry.password and not entry.username and not entry.notes:
            continue

        if not entry.title or not "ZHAW Students" in entry.title:
            continue

        username = entry.username if entry.username else ''
        password = entry.password if entry.password else ''

        # Skip REFs as ID might not be in dict yet
        if KP_REF_IDENTIFIER in username or KP_REF_IDENTIFIER in password:
            kp_ref_entries.append(entry)
            continue
        
        # Normal entry
        add_bw_entry_to_dict(entries, entry, username, password)

    # resolve {REF:...} stuff
    print(f"Parsed {len(entries)} entries")
    print(f"Have to resolve {len(kp_ref_entries)} REF entries now...")
    for kp_entry in kp_ref_entries:
        try:
            # username
            resolved_username_kp_id_tripple = None
            if KP_REF_IDENTIFIER in kp_entry.username:
                field_referenced, lookup_mode, ref_compare_string =  parse_kp_ref_string(kp_entry.username)
                resolved_username_kp_id_tripple = (field_referenced, lookup_mode, ref_compare_string)

                value = find_referenced_value(
                    entries,
                    field_referenced,
                    lookup_mode,
                    ref_compare_string)
                
                kp_entry.username = value
                    
            # password
            if KP_REF_IDENTIFIER in kp_entry.password:
                if resolved_username_kp_id_tripple:
                    # add url to bw_item => username / pw identical
                    field_referenced, lookup_mode, ref_compare_string = parse_kp_ref_string(kp_entry.password)
                    folder, ref_entry = get_referenced_entry(entries, lookup_mode, ref_compare_string)
                    
                    ref_entry["login"]["uris"].append({"match": None,"uri": kp_entry.url})
                else:
                    # get value and create new entry
                    field_referenced, lookup_mode, ref_compare_string = parse_kp_ref_string(kp_entry.password)
                    folder, ref_entry = get_referenced_entry(entries, lookup_mode, ref_compare_string)

                    kp_entry.password = ref_entry["login"]["password"]

                    add_bw_entry_to_dict(entries, kp_entry, entry.username, entry.password)
        except Exception as e:
            print(f"!! Could not resolve entry for {kp_entry.group.path}{kp_entry.title} [{str(kp_entry.uuid)}] !!")

    # store aggregated entries in bw
    i = 1
    max_i = len(entries)

    for kp_id, (folder, bw_item_object) in entries.items():
        print(f"[{i} of {max_i}] Creating Bitwarden entry in {folder} for {bw_item_object['name']}...")
        
        if not bw.create_entry(folder, bw_item_object):
            print("!! ERROR: Creattion of entry failed !!")
        
        i += 1