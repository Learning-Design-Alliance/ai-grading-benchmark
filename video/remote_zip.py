"""Read single members out of a large remote zip by HTTP range requests (no full download).

LASANA's videos come as one 15-28 GB zip per task and camera; the benchmark needs about 100 videos.
The server (TU Dresden OPARA) answers byte ranges, so this reads the zip's central directory from its
tail and then fetches only the members asked for. Handles zip64. Stored and deflated members.
"""
import struct
import subprocess
import zlib


def _range(url, start, end):
    out = subprocess.run(["curl", "-sSfL", "-r", f"{start}-{end}", url], capture_output=True, check=True).stdout
    if len(out) != end - start + 1:
        raise IOError(f"short read {len(out)} of {end - start + 1} at {start}")
    return out


def _size(url):
    hdr = subprocess.run(["curl", "-sSfL", "-r", "0-0", "-D", "-", "-o", "/dev/null", url], capture_output=True, check=True).stdout.decode()
    for line in hdr.splitlines():
        if line.lower().startswith("content-range:"):
            return int(line.split("/")[-1])
    raise IOError("no Content-Range: server does not answer byte ranges")


def members(url):
    """{name: (local_header_offset, compressed_size, method)}"""
    size = _size(url)
    tail = _range(url, max(0, size - 65536 - 22), size - 1)
    base = size - len(tail)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise IOError("end of central directory not found")
    cd_size, cd_off = struct.unpack("<II", tail[i + 12:i + 20])
    if cd_off == 0xFFFFFFFF or cd_size == 0xFFFFFFFF:  # zip64
        j = tail.rfind(b"PK\x06\x07", 0, i)
        (z64_eocd_off,) = struct.unpack("<Q", tail[j + 8:j + 16])
        rec = _range(url, z64_eocd_off, z64_eocd_off + 55)
        cd_size, cd_off = struct.unpack("<QQ", rec[40:56])
    cd = _range(url, cd_off, cd_off + cd_size - 1)
    out, p = {}, 0
    while p < len(cd) and cd[p:p + 4] == b"PK\x01\x02":
        method = struct.unpack("<H", cd[p + 10:p + 12])[0]
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28])
        nlen, xlen, clen = struct.unpack("<HHH", cd[p + 28:p + 34])
        (off,) = struct.unpack("<I", cd[p + 42:p + 46])
        name = cd[p + 46:p + 46 + nlen].decode("utf-8", "replace")
        extra = cd[p + 46 + nlen:p + 46 + nlen + xlen]
        q = 0
        while q + 4 <= len(extra):
            hid, hlen = struct.unpack("<HH", extra[q:q + 4])
            if hid == 1:  # zip64 extended information, fields present only where the 32-bit one is saturated
                vals, r = [], q + 4
                for sat in (usize == 0xFFFFFFFF, csize == 0xFFFFFFFF, off == 0xFFFFFFFF):
                    if sat:
                        vals.append(struct.unpack("<Q", extra[r:r + 8])[0]); r += 8
                    else:
                        vals.append(None)
                usize = vals[0] if vals[0] is not None else usize
                csize = vals[1] if vals[1] is not None else csize
                off = vals[2] if vals[2] is not None else off
            q += 4 + hlen
        out[name] = (off, csize, method)
        p += 46 + nlen + xlen + clen
    return out


def fetch(url, entry, dest):
    off, csize, method = entry
    hdr = _range(url, off, off + 29)
    nlen, xlen = struct.unpack("<HH", hdr[26:30])
    start = off + 30 + nlen + xlen
    data = _range(url, start, start + csize - 1)
    if method == 8:
        data = zlib.decompress(data, -15)
    elif method != 0:
        raise IOError(f"compression method {method} not supported")
    with open(dest, "wb") as f:
        f.write(data)
    return len(data)
