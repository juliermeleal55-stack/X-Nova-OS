#!/usr/bin/env python3
"""Add a multilib APEX's 32-bit payload to a newer 64-bit-only APEX of the same name.

Every path of the base APEX wins; paths only the multilib APEX has are added. The
payload is re-signed with a throwaway key, which apexd accepts for a built-in APEX
because it reads the public key from the APEX itself.

usage: merge_multilib_apex.py BASE.apex MULTILIB.apex OUT.apex AVBTOOL SIGNAPK CERT.x509.pem KEY.pk8
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

BLOCK = 4096
PAYLOAD = "apex_payload.img"
# Same feature set apexer gives the donor images, minus the read-only shared_blocks.
FEATURES = "none,ext_attr,dir_index,filetype,extent,flex_bg,sparse_super,large_file,huge_file,uninit_bg,dir_nlink,extra_isize"


def run(*args):
    done = subprocess.run(args, capture_output=True, text=True)
    if done.returncode:
        raise SystemExit(f"{args[0]} {' '.join(args[1:3])} failed: {done.stderr or done.stdout}")
    return done.stdout


def debugfs(img, command):
    return run("debugfs", "-R", command, img)


def walk(img, path=""):
    """Yield (path, mode, uid, gid) for every entry below path, parents first."""
    for line in debugfs(img, f"ls -p {path or '/'}").splitlines():
        fields = line.split("/")
        if len(fields) < 7 or fields[5] in (".", "..", "lost+found"):
            continue
        child = f"{path}/{fields[5]}"
        mode = int(fields[2], 8)
        yield child, mode, int(fields[3]), int(fields[4])
        if mode & 0o170000 == 0o040000:
            yield from walk(img, child)


def selinux_label(img, path):
    out = debugfs(img, f"ea_get {path or '/'} security.selinux")
    match = re.search(r'"(u:[^"\\]+)', out)
    if not match:
        raise SystemExit(f"{img}:{path}: no SELinux label in {out!r}")
    return match.group(1)


def payload_image(apex, dest):
    with zipfile.ZipFile(apex) as archive, archive.open(PAYLOAD) as src, open(dest, "wb") as out:
        shutil.copyfileobj(src, out)
    return dest


def build_image(base, multilib, tree, out, label):
    entries = [(base, *entry) for entry in walk(base)]
    known = {entry[1] for entry in entries}
    added = [(multilib, *entry) for entry in walk(multilib) if entry[0] not in known]
    if not added:
        raise SystemExit(f"{multilib}: nothing to add to {base}")

    os.makedirs(f"{tree}/base")
    os.makedirs(f"{tree}/multilib")
    debugfs(base, f"rdump / {tree}/base")
    debugfs(multilib, f"rdump / {tree}/multilib")

    size = sum(os.lstat(f"{tree}/{'base' if img == base else 'multilib'}{entry}").st_size // BLOCK + 2
               for img, entry, *_ in entries + added)
    blocks = size + 1024
    run("mke2fs", "-F", "-q", "-t", "ext4", "-b", str(BLOCK), "-I", "256", "-m", "0",
        "-N", str(len(entries) + len(added) + 32), "-L", label, "-O", FEATURES,
        "-E", "lazy_itable_init=0,lazy_journal_init=0", out, str(blocks))

    commands = ["rmdir /lost+found"]
    label_files = {}

    def meta(path, mode, uid, gid, context):
        label_file = label_files.setdefault(context, f"{tree}/label{len(label_files)}")
        with open(label_file, "wb") as handle:
            handle.write(context.encode() + b"\0")
        commands.extend((f"sif {path} mode 0{mode:o}", f"sif {path} uid {uid}", f"sif {path} gid {gid}",
                         f"ea_set -f {label_file} {path} security.selinux"))

    root = walk(base).__next__ and debugfs(base, "stat /")
    root_mode = int(re.search(r"Mode:\s+(\d+)", root).group(1), 8) | 0o040000
    root_uid = int(re.search(r"User:\s+(\d+)", root).group(1))
    root_gid = int(re.search(r"Group:\s+(\d+)", root).group(1))
    meta("/", root_mode, root_uid, root_gid, selinux_label(base, ""))

    for img, path, mode, uid, gid in entries + added:
        source = f"{tree}/{'base' if img == base else 'multilib'}{path}"
        kind = mode & 0o170000
        if kind == 0o040000:
            commands.append(f"mkdir {path}")
        elif kind == 0o120000:
            commands.append(f"symlink {path} {os.readlink(source)}")
        else:
            commands.append(f"write {source} {path}")
        meta(path, mode, uid, gid, selinux_label(img, path))

    script = f"{tree}/commands"
    with open(script, "w") as handle:
        handle.write("\n".join(commands) + "\n")
    run("debugfs", "-w", "-f", script, out)
    run("e2fsck", "-fn", out)
    return len(added)


def write_apex(base_apex, image, pubkey, out):
    replaced = {PAYLOAD: image, "apex_pubkey": pubkey}
    with zipfile.ZipFile(base_apex) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as dst:
        for item in src.infolist():
            if item.filename.startswith("META-INF/"):
                continue
            info = zipfile.ZipInfo(item.filename, (2008, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            # apexd loop-mounts the payload in place, so it must start on a block boundary.
            start = dst.fp.tell() + 30 + len(item.filename.encode())
            info.extra = b"\0" * (-start % BLOCK)
            if item.filename in replaced:
                with open(replaced[item.filename], "rb") as handle:
                    dst.writestr(info, handle.read())
            else:
                dst.writestr(info, src.read(item.filename))


def main():
    base_apex, multilib_apex, out_apex, avbtool, signapk, cert, pk8 = sys.argv[1:8]
    with tempfile.TemporaryDirectory(prefix="apex-merge-") as tmp:
        base = payload_image(base_apex, f"{tmp}/base.img")
        multilib = payload_image(multilib_apex, f"{tmp}/multilib.img")
        for image in (base, multilib):
            # rdump and ls read past the footer harmlessly, but the footer must not be copied.
            run(avbtool, "erase_footer", "--image", image)
        info = run(avbtool, "info_image", "--image", payload_image(base_apex, f"{tmp}/info.img"))
        salt = re.search(r"Salt:\s+(\w+)", info).group(1)

        image = f"{tmp}/merged.img"
        label = os.path.basename(out_apex).removesuffix(".apex")[:16]
        added = build_image(base, multilib, f"{tmp}/tree", image, label)

        key = f"{tmp}/key.pem"
        pubkey = f"{tmp}/apex_pubkey"
        run("openssl", "genrsa", "-out", key, "4096")
        run(avbtool, "extract_public_key", "--key", key, "--output", pubkey)
        # Mirror apexer's descriptor: no partition name, no FEC, rollback index 0.
        partition_size = (os.path.getsize(image) * 51 // 50 + (1 << 20)) // BLOCK * BLOCK
        run(avbtool, "add_hashtree_footer", "--image", image, "--partition_name", "",
            "--partition_size", str(partition_size), "--do_not_generate_fec", "--algorithm", "SHA256_RSA4096",
            "--key", key, "--hash_algorithm", "sha256", "--salt", salt)
        run(avbtool, "verify_image", "--image", image, "--key", key)
        unsigned = f"{tmp}/unsigned.apex"
        write_apex(base_apex, image, pubkey, unsigned)
        # PackageManager parses every APEX as an APK and reboots the phone if its signature is invalid.
        run(signapk, "-a", str(BLOCK), "--align-file-size", cert, pk8, unsigned, out_apex)
    print(f"{out_apex}: added {added} entries, {os.path.getsize(out_apex)} bytes")


if __name__ == "__main__":
    main()
