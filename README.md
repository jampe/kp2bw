# kp2bw -- KeePass 2.x to Bitwarden Converter

> This repository is no longer under active development by the original maintainer.
>
> The project has been forked and is actively maintained at
> **[kjanat/kp2bw](https://github.com/kjanat/kp2bw)** (v3.7.0+, Python >=3.14).
> The fork uses `bw serve` HTTP transport instead of the subprocess-based approach
> in this version, supports nested collections, proper org/collection item creation,
> and ongoing bug fixes. Should you miss any features here, try to use the maintained fork.

---

kp2bw converts KeePass 2.x databases to Bitwarden using the Bitwarden CLI.

Compared to Bitwarden's built-in importer:

- Data never touches disk unencrypted (except temporary attachment files,
  which are removed after upload)
- Resolves KeePass `{REF:...}` entries (username, password) -- matching
  entries get merged URLs; non-matching entries are created separately
- TOTP/OTP migrated from KeePass (standard `otp` field and common custom
  properties like `otpauth`, `TOTP Settings`, etc.)
- Custom properties imported as Bitwarden custom fields; values over 10,000
  characters become attachments
- Attachments imported from KeePass
- Notes over 10,000 characters imported as `notes.txt` attachment
- Idempotent import -- re-running does not duplicate entries
- Nested folder structure recreated in Bitwarden
- Entries imported one by one to avoid Bitwarden query timeout on large databases
- UTF-8 support
- Windows, macOS, Linux

## Installation

### Pre-built (recommended)

Download the latest build artifact for your platform from
[GitHub Actions](https://github.com/jampe/kp2bw/actions/workflows/build.yml)
(select the most recent successful run, scroll to Artifacts).

Each artifact is a zip containing a `.whl` file. Install it with pip:

```sh
pip install kp2bw-<platform>-py<version>.zip/kp2bw-*.whl
```

### From source

Requires Python >=3.9 and pip.

```sh
python -m venv .env/kp2bw
source .env/kp2bw/bin/activate   # Windows: .env\kp2bw\Scripts\activate
pip install .
```

## Usage

### Prerequisites

Install the [Bitwarden CLI](https://help.bitwarden.com/article/cli/) and log in:

```sh
bw login <username>
```

For self-hosted instances, set the server URL first:

```sh
bw config server https://your-domain.com/
```

### Import

```sh
kp2bw passwords.kdbx
```

### Options

| Flag | Description |
|------|-------------|
| `keepass_file` | Path to KeePass 2.x database |
| `-kppw` | KeePass database password |
| `-kpkf` | KeePass database key file |
| `-bwpw` | Bitwarden master password |
| `-bworg` | Bitwarden Organization ID |
| `-bwcoll` | Organization Collection ID, or `auto` to match by top-level folder name |
| `-import_tags` | Only import items with given tags (space-separated) |
| `-path2name` | Prepend folder path to entry names |
| `-path2nameskip` | Skip first N folders when using `-path2name` (default: 1) |
| `-y` | Skip Bitwarden setup confirmation |
| `-v` | Verbose output |

## Troubleshooting

### Invalid master password on unlock

```
DEBUG: -- Executing command: bw unlock My?Master>>Password123 --raw
DEBUG:   |- Output: b'Invalid master password.'
```

Wrap the password in double quotes at the password prompt. The `bw unlock`
command does not handle shell special characters in unquoted input.

## License

MIT. Copyright Daniel Jampen.

