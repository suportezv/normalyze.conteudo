#!/usr/bin/env python3
"""Lista e extrai arquivos de um ZIP remoto sem baixar o ZIP inteiro.

Usa Range requests. Serve para os exports grandes do Drive (OneDrive_*.zip),
onde os MP4 costumam estar `stored` (sem compressao) e podem ser recortados
um a um direto do arquivo remoto.

Uso:
    python3 scripts/zip_index_remoto.py list  <file_id>
    python3 scripts/zip_index_remoto.py get   <file_id> <nome_no_zip> <destino>

O arquivo no Drive precisa estar como "qualquer pessoa com o link: leitor".
"""
import argparse
import signal
import struct
import subprocess
import sys
import zlib

DRIVE = "https://drive.usercontent.google.com/download?id={}&export=download&confirm=t"


def _curl(url, start, end, out=None):
    cmd = ["curl", "-sL", "--fail", "--max-time", "1800",
           "-H", f"Range: bytes={start}-{end}", url]
    if out:
        cmd += ["-o", out]
        subprocess.run(cmd, check=True)
        return None
    return subprocess.run(cmd, check=True, capture_output=True).stdout


def remote_size(url):
    head = subprocess.run(
        ["curl", "-sIL", "--max-time", "120", "-H", "Range: bytes=0-0", url],
        check=True, capture_output=True, text=True).stdout
    for line in head.splitlines():
        if line.lower().startswith("content-range:"):
            return int(line.split("/")[-1].strip())
    raise SystemExit("servidor nao informou content-range: sem suporte a Range")


def central_directory(url, size):
    """Devolve (bytes_do_central_directory, numero_de_entradas)."""
    tail_len = min(65_600, size)
    tail = _curl(url, size - tail_len, size - 1)

    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise SystemExit("EOCD nao encontrado (comentario de ZIP grande demais?)")
    entries = struct.unpack("<H", tail[i + 10:i + 12])[0]
    cd_size, cd_off = struct.unpack("<II", tail[i + 12:i + 20])

    # ZIP64: obrigatorio quando o arquivo passa de 4 GB
    j = tail.rfind(b"PK\x06\x07")
    if j >= 0:
        z64_off = struct.unpack("<Q", tail[j + 8:j + 16])[0]
        z = _curl(url, z64_off, z64_off + 55)
        if z[:4] == b"PK\x06\x06":
            entries = struct.unpack("<Q", z[32:40])[0]
            cd_size, cd_off = struct.unpack("<QQ", z[40:56])

    return _curl(url, cd_off, cd_off + cd_size - 1), entries


def parse_entries(cd):
    out, p = [], 0
    while p < len(cd) and cd[p:p + 4] == b"PK\x01\x02":
        (_v, _vn, _flag, method, _mt, _md, crc, csize, usize,
         nlen, elen, clen, _disk, _ia, _ea, lho) = struct.unpack(
            "<HHHHHHIIIHHHHHII", cd[p + 4:p + 46])
        name = cd[p + 46:p + 46 + nlen].decode("utf-8", "replace")
        extra = cd[p + 46 + nlen:p + 46 + nlen + elen]

        q = 0
        while q + 4 <= len(extra):
            hid, hsz = struct.unpack("<HH", extra[q:q + 4])
            body = extra[q + 4:q + 4 + hsz]
            if hid == 0x0001:  # campo ZIP64, so traz o que estourou 32 bits
                o = 0
                if usize == 0xFFFFFFFF:
                    usize = struct.unpack("<Q", body[o:o + 8])[0]; o += 8
                if csize == 0xFFFFFFFF:
                    csize = struct.unpack("<Q", body[o:o + 8])[0]; o += 8
                if lho == 0xFFFFFFFF:
                    lho = struct.unpack("<Q", body[o:o + 8])[0]; o += 8
            q += 4 + hsz

        out.append(dict(name=name, method=method, crc=crc,
                        csize=csize, usize=usize, lho=lho))
        p += 46 + nlen + elen + clen
    return out


def data_offset(url, entry):
    """Offset real dos dados: o local header tem tamanhos proprios de nome/extra."""
    lh = _curl(url, entry["lho"], entry["lho"] + 29)
    if lh[:4] != b"PK\x03\x04":
        raise SystemExit(f"local header invalido para {entry['name']}")
    nlen, elen = struct.unpack("<HH", lh[26:30])
    return entry["lho"] + 30 + nlen + elen


def cmd_list(args):
    url = DRIVE.format(args.file_id)
    size = remote_size(url)
    cd, n = central_directory(url, size)
    entries = [e for e in parse_entries(cd) if not e["name"].endswith("/")]
    total = sum(e["usize"] for e in entries)
    print(f"{size/1e9:.2f} GB no Drive · {n} entradas · "
          f"{total/1e9:.2f} GB descompactado\n")
    for e in sorted(entries, key=lambda e: -e["usize"]):
        kind = "stored" if e["method"] == 0 else f"method={e['method']}"
        print(f"{e['usize']/1e6:10.1f} MB  {kind:8}  {e['name']}")


def cmd_get(args):
    url = DRIVE.format(args.file_id)
    size = remote_size(url)
    cd, _ = central_directory(url, size)
    matches = [e for e in parse_entries(cd) if e["name"] == args.name]
    if not matches:
        matches = [e for e in parse_entries(cd) if args.name in e["name"]]
    if len(matches) != 1:
        for e in matches:
            print(" ", e["name"], file=sys.stderr)
        raise SystemExit(f"{len(matches)} entradas casaram com {args.name!r}; "
                         "preciso de exatamente uma")

    e = matches[0]
    start = data_offset(url, e)
    end = start + e["csize"] - 1
    print(f"baixando {e['name']} ({e['usize']/1e6:.1f} MB) -> {args.dest}",
          file=sys.stderr)

    if e["method"] == 0:
        _curl(url, start, end, out=args.dest)
    else:
        raw = _curl(url, start, end)
        with open(args.dest, "wb") as fh:
            fh.write(zlib.decompress(raw, -15))
    print(args.dest)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="lista o conteudo do ZIP remoto")
    p_list.add_argument("file_id")
    p_list.set_defaults(func=cmd_list)

    p_get = sub.add_parser("get", help="extrai um arquivo do ZIP remoto")
    p_get.add_argument("file_id")
    p_get.add_argument("name", help="nome exato no ZIP, ou trecho unico dele")
    p_get.add_argument("dest")
    p_get.set_defaults(func=cmd_get)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    # deixa o script se comportar bem sob `| head`
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
