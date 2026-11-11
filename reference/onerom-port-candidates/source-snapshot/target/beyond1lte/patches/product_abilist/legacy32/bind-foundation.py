from pathlib import Path
import struct
import sys


def bind_internal_symbols(path: Path) -> None:
    data = bytearray(path.read_bytes())
    if data[:6] != b"\x7fELF\x01\x01":
        raise ValueError(f"Expected little-endian ELF32: {path}")
    program_offset = struct.unpack_from("<I", data, 28)[0]
    entry_size, entry_count = struct.unpack_from("<HH", data, 42)
    if entry_size != 32:
        raise ValueError(f"Unexpected ELF32 program header size: {path}")
    for index in range(entry_count):
        program_type, offset, virtual_address, physical_address, size = struct.unpack_from(
            "<IIIII", data, program_offset + index * entry_size
        )
        if program_type != 2:
            continue
        if offset + size > len(data) or size % 8:
            raise ValueError(f"Invalid ELF32 dynamic table: {path}")
        for entry_offset in range(offset, offset + size, 8):
            tag, value = struct.unpack_from("<iI", data, entry_offset)
            if tag == 0:
                break
            if tag == 30:
                struct.pack_into("<I", data, entry_offset + 4, value | 2)
                path.write_bytes(data)
                print(f"Bound internal Stagefright symbols: {path.name}")
                return
    raise ValueError(f"ELF32 DT_FLAGS not found: {path}")


if __name__ == "__main__":
    for argument in sys.argv[1:]:
        bind_internal_symbols(Path(argument))