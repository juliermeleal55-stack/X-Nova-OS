import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from zipfile import ZipFile


def transform(data: bytes, model: str, iv: bytes, decrypt: bool) -> bytes:
    result = subprocess.run(
        [
            "openssl", "enc", "-aes-256-cbc", "-d" if decrypt else "-e",
            "-K", hashlib.sha256(model.encode("utf-8")).hexdigest(),
            "-iv", iv.hex(),
        ],
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    parser.add_argument("floating_features", type=Path)
    parser.add_argument("target_model")
    parser.add_argument("model_policy", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    source_model = ET.parse(arguments.floating_features).findtext(
        "SEC_FLOATING_FEATURE_SYSTEM_CONFIG_SIOP_POLICY_FILENAME"
    )
    if not source_model or not source_model.strip():
        raise ValueError("Donor SIOP model is missing")
    policies = {}
    with ZipFile(arguments.apk) as archive:
        for name in ("siop_default", "siop_model", "ssrm_default"):
            encoded = archive.read(f"assets/{name}")
            decoded = transform(encoded[16:], source_model.strip(), encoded[:16], True)
            root = ET.fromstring(decoded)
            if name == "siop_model":
                root = ET.parse(arguments.model_policy).getroot()
            if root.tag not in ("siop_document", "ssrm_document"):
                raise ValueError(f"Unexpected policy root for {name}: {root.tag}")
            for complex_node in root.iter("complex"):
                for node in list(complex_node):
                    if node.tag == "DEX":
                        complex_node.remove(node)
            decoded = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            iv = os.urandom(16)
            encoded = iv + transform(decoded, arguments.target_model, iv, False)
            if transform(encoded[16:], arguments.target_model, iv, True) != decoded:
                raise ValueError(f"Policy encoding round trip failed for {name}")
            policies[name] = encoded
    arguments.destination.mkdir(parents=True, exist_ok=True)
    for name, encoded in policies.items():
        (arguments.destination / name).write_bytes(encoded)
        print(f"Prepared S10 policy: {name}")


if __name__ == "__main__":
    main()