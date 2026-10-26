import sys
import os
import struct
import hashlib
from datetime import datetime

MAGIC = b"SVC3"
HEADER_SIZE = len(MAGIC)
LENGTH_SIZE = 8


def repo_path(name):
    return f"{name}.svc"


def read_versions(path):
    """Read and validate all versions stored in a repository."""
    with open(path, "rb") as f:
        if f.read(HEADER_SIZE) != MAGIC:
            raise ValueError("Invalid SVC repository.")

        versions = []

        while True:
            length_bytes = f.read(LENGTH_SIZE)

            if not length_bytes:
                break

            if len(length_bytes) != LENGTH_SIZE:
                raise ValueError("Corrupted version length.")

            length = struct.unpack(">Q", length_bytes)[0]
            data = f.read(length)

            if len(data) != length:
                raise ValueError("Corrupted version data.")

            versions.append(data)

    return versions


def write_versions(path, versions):
    """Write versions using length-prefixed binary records."""
    temp_path = path + ".tmp"

    with open(temp_path, "wb") as f:
        f.write(MAGIC)

        for version in versions:
            f.write(struct.pack(">Q", len(version)))
            f.write(version)

    os.replace(temp_path, path)


def init(name):
    path = repo_path(name)

    if os.path.exists(path):
        print(f"Repository already exists: {path}")
        return

    write_versions(path, [])
    print(f"Initialized repository: {path}")


def add(name, filename):
    path = repo_path(name)

    if not os.path.isfile(path):
        print("Repository not found. Run init first.")
        return

    if not os.path.isfile(filename):
        print(f"File not found: {filename}")
        return

    with open(filename, "rb") as f:
        data = f.read()

    versions = read_versions(path)
    versions.append(data)
    write_versions(path, versions)

    digest = hashlib.sha256(data).hexdigest()[:12]

    print(f"Added version {len(versions)}")
    print(f"File: {filename}")
    print(f"Size: {len(data)} bytes")
    print(f"SHA-256: {digest}")


def undo(name):
    path = repo_path(name)

    if not os.path.isfile(path):
        print("Repository not found.")
        return

    versions = read_versions(path)

    if not versions:
        print("Nothing to undo!")
        return

    versions.pop()
    write_versions(path, versions)

    print(f"Undo successful. {len(versions)} version(s) remaining.")


def log(name):
    path = repo_path(name)

    if not os.path.isfile(path):
        print("Repository not found.")
        return

    versions = read_versions(path)

    if not versions:
        print("No versions saved.")
        return

    print(f"Repository: {path}")
    print(f"Total versions: {len(versions)}\n")

    for index, data in enumerate(versions, start=1):
        digest = hashlib.sha256(data).hexdigest()[:12]

        print(f"Version {index}")
        print(f"  Size: {len(data)} bytes")
        print(f"  SHA-256: {digest}")


def checkout(name, version, output):
    path = repo_path(name)

    if not os.path.isfile(path):
        print("Repository not found.")
        return

    versions = read_versions(path)

    if not 1 <= version <= len(versions):
        print(f"Invalid version. Available versions: 1-{len(versions)}")
        return

    with open(output, "wb") as f:
        f.write(versions[version - 1])

    print(f"Restored version {version} to {output}")


def usage():
    print("""
Scratch Version Control

Usage:
  python svc.py init <repo>
  python svc.py add <repo> <file>
  python svc.py undo <repo>
  python svc.py log <repo>
  python svc.py checkout <repo> <version> <output>

Examples:
  python svc.py init myproject
  python svc.py add myproject project.sb3
  python svc.py add myproject project.json
  python svc.py log myproject
  python svc.py checkout myproject 1 restored.sb3
  python svc.py undo myproject
""")


def main():
    print("Scratch Version Control")

    if len(sys.argv) < 2:
        usage()
        return

    command = sys.argv[1]

    try:
        if command == "init" and len(sys.argv) == 3:
            init(sys.argv[2])

        elif command == "add" and len(sys.argv) == 4:
            add(sys.argv[2], sys.argv[3])

        elif command == "undo" and len(sys.argv) == 3:
            undo(sys.argv[2])

        elif command == "log" and len(sys.argv) == 3:
            log(sys.argv[2])

        elif command == "checkout" and len(sys.argv) == 5:
            checkout(sys.argv[2], int(sys.argv[3]), sys.argv[4])

        else:
            usage()

    except (OSError, ValueError, struct.error) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
