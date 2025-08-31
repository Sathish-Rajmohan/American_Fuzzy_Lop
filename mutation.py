import random
import struct

INTERESTING_8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127, 255]
INTERESTING_16 = [-32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767, 65535]
INTERESTING_32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647, 4294967295]

def havoc_mutation(conf, seed):
    """
    Feature 4: Havoc mutation with required features
    """
    with open(seed.path, 'rb') as f:
        data = bytearray(f.read())

    if len(data) == 0:
        data = bytearray([0])
    
    data_len = len(data)
    
    num_mutations = random.randint(1, 8)
    
    for _ in range(num_mutations):
        mutation_type = random.randint(1, 6)
        
        if mutation_type == 1:
            if data_len > 0:
                byte_index = random.randint(0, data_len - 1)
                bit_position = random.randint(0, 7)
                data[byte_index] ^= (1 << bit_position)
        
        elif mutation_type == 2:
            if data_len >= 2:
                index = random.randint(0, data_len - 2)
                try:
                    original = struct.unpack('<H', data[index:index+2])[0]
                    if random.choice([True, False]):
                        new_val = (original + random.randint(-1000, 1000)) & 0xFFFF
                    else:
                        new_val = (original - random.randint(1, 1000)) & 0xFFFF
                    struct.pack_into('<H', data, index, new_val)
                except (struct.error, IndexError):
                    pass
        
        elif mutation_type == 3:
            if data_len >= 4:
                index = random.randint(0, data_len - 4)
                try:
                    original = struct.unpack('<I', data[index:index+4])[0]
                    if random.choice([True, False]):
                        new_val = (original + random.randint(-10000, 10000)) & 0xFFFFFFFF
                    else:
                        new_val = (original - random.randint(1, 10000)) & 0xFFFFFFFF
                    struct.pack_into('<I', data, index, new_val)
                except (struct.error, IndexError):
                    pass
        
        elif mutation_type == 4:
            if data_len >= 8:
                index = random.randint(0, data_len - 8)
                try:
                    original = struct.unpack('<Q', data[index:index+8])[0]
                    if random.choice([True, False]):
                        new_val = (original + random.randint(-100000, 100000)) & 0xFFFFFFFFFFFFFFFF
                    else:
                        new_val = (original - random.randint(1, 100000)) & 0xFFFFFFFFFFFFFFFF
                    struct.pack_into('<Q', data, index, new_val)
                except (struct.error, IndexError):
                    pass
        
        elif mutation_type == 5:
            if data_len >= 2:
                index = random.randint(0, data_len - 2)
                value_type = random.choice(['short', 'int', 'long'])
                
                try:
                    if value_type == 'short' and data_len >= 2:
                        new_val = random.choice(INTERESTING_16) & 0xFFFF
                        struct.pack_into('<H', data, index, new_val)
                    elif value_type == 'int' and data_len >= 4 and index <= data_len - 4:
                        new_val = random.choice(INTERESTING_32) & 0xFFFFFFFF
                        struct.pack_into('<I', data, index, new_val)
                    elif value_type == 'long' and data_len >= 8 and index <= data_len - 8:
                        new_val = random.choice(INTERESTING_32) & 0xFFFFFFFFFFFFFFFF
                        struct.pack_into('<Q', data, index, new_val)
                except (struct.error, IndexError):
                    pass
        
        elif mutation_type == 6:
            if data_len > 4:
                chunk_size = random.randint(1, min(16, data_len // 4))
                if data_len >= chunk_size * 2:
                    src_start = random.randint(0, data_len - chunk_size)
                    dst_start = random.randint(0, data_len - chunk_size)
                    
                    if src_start != dst_start:
                        src_chunk = data[src_start:src_start + chunk_size]
                        data[dst_start:dst_start + chunk_size] = src_chunk

    if len(data) == 0:
        data = bytearray([0])

    with open(conf['current_input'], 'wb') as f_out:
        f_out.write(data)