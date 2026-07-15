import sys
import struct
import glob

def clear_execstack(filename):
    try:
        with open(filename, 'r+b') as f:
            elf_header = f.read(64)
            if elf_header[:4] != b'\x7fELF':
                return
                
            is_64 = elf_header[4] == 2
            endian = '<' if elf_header[5] == 1 else '>'
            
            if is_64:
                unpacked = struct.unpack_from(endian + 'QQQIHHHHHH', elf_header, 24)
            else:
                unpacked = struct.unpack_from(endian + 'IIIIHHHHHH', elf_header, 24)
                
            e_phoff = unpacked[1]
            e_phentsize = unpacked[5]
            e_phnum = unpacked[6]

            for i in range(e_phnum):
                f.seek(e_phoff + i * e_phentsize)
                ph = f.read(e_phentsize)
                p_type = struct.unpack_from(endian + 'I', ph, 0)[0]
                
                if p_type == 0x6474e551: # PT_GNU_STACK
                    if is_64:
                        p_flags = struct.unpack_from(endian + 'I', ph, 4)[0]
                        p_flags &= ~1 # Clear executable flag (PF_X)
                        f.seek(e_phoff + i * e_phentsize + 4)
                        f.write(struct.pack(endian + 'I', p_flags))
                    else:
                        p_flags = struct.unpack_from(endian + 'I', ph, 24)[0]
                        p_flags &= ~1
                        f.seek(e_phoff + i * e_phentsize + 24)
                        f.write(struct.pack(endian + 'I', p_flags))
                    print(f"Successfully cleared execstack on: {filename}")
                    break
    except Exception as e:
        print(f"Could not process {filename}: {e}")

if __name__ == '__main__':
    for pattern in sys.argv[1:]:
        for file in glob.glob(pattern, recursive=True):
            clear_execstack(file)
