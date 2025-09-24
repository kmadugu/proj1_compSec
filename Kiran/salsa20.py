import numpy
import sys

def rotate_left(val, shift):
    return ((val << shift) & 0xFFFFFFFF) | ((val & 0xFFFFFFFF) >> (32 - shift))

def quarterround(var0, var1, var2, var3):
    result_array = numpy.zeros(4, dtype=numpy.int32)
    result_array[1] = var1 ^ rotate_left((numpy.array(var0).astype(numpy.int32) + numpy.array(var3).astype(numpy.int32)), 7)
    result_array[2] = var2 ^ rotate_left((result_array[1] + numpy.array(var0).astype(numpy.int32)), 9)
    result_array[3] = var3 ^ rotate_left((result_array[2] + result_array[1]), 13)
    result_array[0] = var0 ^ rotate_left((result_array[3] + result_array[2]), 18)
    #print(result_array)
    return result_array


def rowround(input_array):
    result_array = [0] * 16
    row_indices = [(0, 1, 2, 3), (5, 6, 7, 4), (10, 11, 8, 9), (15, 12, 13, 14)]
    
    for i, (a, b, c, d) in enumerate(row_indices):
        quarter_round_result = quarterround(input_array[a], input_array[b], input_array[c], input_array[d])
        for j, val in enumerate(quarter_round_result):
            result_array[row_indices[i][j]] = val
    
    return result_array


def columnround(state):
    result_array = [0] * 16
    
    column_indices = [(0, 4, 8, 12), (5, 9, 13, 1), (10, 14, 2, 6), (15, 3, 7, 11)]
    
    for i, (a, b, c, d) in enumerate(column_indices):
        quarter_round_result = quarterround(state[a], state[b], state[c], state[d])
        for j, val in enumerate(quarter_round_result):
            result_array[column_indices[i][j]] = val
    
    return result_array

def doubleround(x):
     for i in range(6):
        return rowround(columnround(x))


def littleendian(b):
   # print("Little",b[0] + (b[1] << 8) + (b[2] << 16) + (b[3] << 24))
    result =  b[0] + (b[1] << 8) + (b[2] << 16) + (b[3] << 24)
    #signed_int = struct.unpack('<i', bytes(b))[0]
    #print(signed_int)
    return result

def invert_littleendian(word):

    b0 = word & 0xFF
    b1 = (word >> 8) & 0xFF
    b2 = (word >> 16) & 0xFF
    b3 = (word >> 24) & 0xFF
    #print(b0, b1, b2, b3)
    return b0, b1, b2, b3

def Salsa20(x):
    x_words = [littleendian(x[i:i+4]) for i in range(0, len(x), 4)]
    z_words = x_words.copy()
    
    max_length = max(len(x_words), len(z_words))
    x_words += [0] * (max_length - len(x_words))
    z_words += [0] * (max_length - len(z_words))

    for _ in range(6):
        z_words = doubleround(z_words)

    result = []
    for i in range (len(x_words)):
        inverted_word = invert_littleendian(z_words[i] + x_words[i])
        #print(inverted_word)
        result.extend(inverted_word)

    return result



def Salsa20_expansion_8(k, nonce):
    x1 = (101, 120, 112, 97)
    x2 = (110, 100, 32, 48)
    x3 = (56, 45, 98, 121)
    x4 = (116, 101, 32, 107)
   # print(x1 + tuple(k) + (0,) * 8 + x2 + tuple(n) + x3 + tuple(k) + (0,) * 8 + x4)
    nonce = nonce[:16]
    padding_length = 16 - len(nonce)
    nonce += bytes([0] *padding_length)
    expanded_key = x1 + tuple(k) +tuple(k)+ x2 + tuple(nonce) + x3 + tuple(k) + tuple(k) + x4
    return Salsa20(expanded_key)

def Salsa20_expansion_32(k0, k1, nonce):
    x1 = (101, 120, 112, 97)
    x2 = (110, 100, 32, 51)
    x3 = (50, 45, 98, 121)
    x4 = (116, 101, 32, 107)
    
    nonce = nonce[:16]
    padding_length = 16 - len(nonce)
    nonce += bytes([0] *padding_length)
    expanded_key = x1 + tuple(k0) + x2 + tuple(nonce) + x3 + tuple(k1) + x4
    return Salsa20(expanded_key)

def Salsa20_expansion_16(k, nonce):
    x1 = (101, 120, 112, 97)
    x2 = (110, 100, 32, 49)
    x3 = (54, 45, 98, 121)
    x4 = (116, 101, 32, 107)
    
    nonce = nonce[:16]
    padding_length = 16 - len(nonce)
    nonce += bytes([0] *padding_length)
    expanded_key = x1 + tuple(k) + x2 + tuple(nonce) + x3 + tuple(k) + x4
    print(expanded_key)
    return Salsa20(expanded_key)



def salsa20_encryption(key_length_bits, key, nonce, message):
    stream_index = 0
    n = nonce[:]

    if stream_index % 64 != 0:
        if key_length_bits == 64:
            keystream = Salsa20_expansion_8(key, n)
        elif key_length_bits == 128:
            keystream = Salsa20_expansion_16(key, n)
        elif key_length_bits == 256:
            keystream = Salsa20_expansion_32(key[:16], key[16:], n)

    encrypted = list(message[:])

    for i in range(len(message)):
        if (stream_index + i) % 64 == 0:
            if key_length_bits == 8:
                keystream = Salsa20_expansion_8(key, n)
            elif key_length_bits == 16:
                keystream = Salsa20_expansion_16(key, n)
            elif key_length_bits == 32:
                keystream = Salsa20_expansion_32(key[:16], key[16:], n)

        encrypted[i] ^= keystream[(stream_index + i) % 64]
    #print(encrypted)
    return encrypted

if __name__ == "__main__":
    key_length = int(sys.argv[1])
    key_hex = sys.argv[2]
    nonce_hex = sys.argv[3]
    plaintext_hex = sys.argv[4]
    key_length_array = key_length // 8

    key_bytes = bytes.fromhex(key_hex)
    int_key_of_hex = [byte for byte in key_bytes]

    nonce_bytes = bytes.fromhex(nonce_hex)
    int_nonce_of_hex = [byte for byte in nonce_bytes]

    message_bytes = bytes.fromhex(plaintext_hex)
    int_message_of_bytes= [byte for byte in message_bytes]

    ciphertext_bytes = salsa20_encryption(key_length_array, int_key_of_hex, int_nonce_of_hex, int_message_of_bytes)
    #hash_key = Salsa20(ciphertext_bytes)

    ciphertext_bytes = bytes(ciphertext_bytes)
    print("Encryption_value:", ciphertext_bytes.hex())

