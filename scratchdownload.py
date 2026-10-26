import io
import json
import sys
import zipfile
import requests

project_id = sys.argv[1]

session = requests.Session()


def download(url, **kwargs):
    response = session.get(url, timeout=60, **kwargs)
    response.raise_for_status()
    return response.content


# Fetch metadata and project token
metadata = json.loads(download(
    f"https://api.scratch.mit.edu/projects/{project_id}"
))

token = metadata["project_token"]

# Fetch project data
data = download(
    f"https://projects.scratch.mit.edu/{project_id}",
    params={"token": token},
)

# Scratch 1.x: legacy binary format
if data.startswith(b"ScratchV"):
    filename = f"{project_id}.sb"

    with open(filename, "wb") as f:
        f.write(data)

    print(f"Downloaded legacy Scratch project: {filename}")
    sys.exit(0)


# SB2/SB3 uploaded as ZIP archives
if data.startswith(b"PK\x03\x04"):
    filename = f"{project_id}.sb2"

    with open(filename, "wb") as f:
        f.write(data)

    print(f"Downloaded ZIP-based project: {filename}")
    print("Inspect the archive to determine its format.")
    sys.exit(0)


# Remaining responses should be JSON
try:
    project = json.loads(data)
except (ValueError, UnicodeDecodeError):
    print("Unknown project format.")
    print("First 32 bytes:", repr(data[:32]))
    sys.exit(1)


# Scratch 3 project JSON
if "meta" in project and "targets" in project:
    filename = f"{project_id}.sb3"

    with zipfile.ZipFile(filename, "w") as archive:
        archive.writestr(
            "project.json",
            json.dumps(project, ensure_ascii=False),
        )

        assets = set()

        for target in project["targets"]:
            for costume in target.get("costumes", []):
                assets.add(costume.get("md5ext"))

            for sound in target.get("sounds", []):
                assets.add(sound.get("md5ext"))

        assets.discard(None)

        for asset in sorted(assets):
            url = (
                "https://assets.scratch.mit.edu/"
                + asset
            )

            try:
                content = download(url)
                archive.writestr(asset, content)
                print(f"Downloaded asset: {asset}")
            except requests.RequestException as error:
                print(f"Failed to download {asset}: {error}")

    print(f"Created {filename}")
    sys.exit(0)


# Scratch 2 JSON
if "objName" in project or "children" in project:
    print("Detected Scratch 2 JSON.")
    print("Conversion to SB3 requires converting the project schema.")
    print("Save the JSON and use the Scratch editor to convert it.")

    with open(f"{project_id}.json", "wb") as f:
        f.write(data)

    sys.exit(0)


print("Unrecognized project JSON structure.")
print("Top-level keys:", list(project.keys()))
