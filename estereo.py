"""
Nombre: Biel Piqué Marti
"""

import struct

def leer_cabecera(f):
    """Lee la cabecera WAVE de 44 bytes."""
    f.seek(0)
    cabecera = f.read(44)
    if len(cabecera) < 44:
        raise ValueError("El fichero es demasiado corto o no es un WAVE válido.")
    # Formato: RIFF, Size, WAVE, fmt, S1Size, AudioForm, Chan, Rate, ByteRate, Align, Bits, data, S2Size
    formato = '<4sI4s4sIHHIIHH4sI'
    return list(struct.unpack(formato, cabecera))

def escribir_cabecera(num_canales, bits_por_muestra, frecuencia, num_muestras):
    """Genera una cabecera WAVE corregida."""
    block_align = num_canales * bits_por_muestra // 8
    subchunk2_size = num_muestras * block_align
    chunk_size = 36 + subchunk2_size
    byte_rate = frecuencia * block_align
    
    return struct.pack('<4sI4s4sIHHIIHH4sI', 
        b'RIFF', chunk_size, b'WAVE', b'fmt ', 16, 1, 
        num_canales, frecuencia, byte_rate, block_align, 
        bits_por_muestra, b'data', subchunk2_size)

def estereo2mono(ficEste, ficMono, canal=2):
    with open(ficEste, 'rb') as f_in:
        cab = leer_cabecera(f_in)
        if cab[6] != 2: raise ValueError("El fichero no es estéreo.")
        
        datos = f_in.read()
        muestras = struct.unpack(f'<{len(datos)//2}h', datos)
        izq, der = muestras[0::2], muestras[1::2]
        
        if canal == 0: res = izq
        elif canal == 1: res = der
        elif canal == 2: res = [(l + r) // 2 for l, r in zip(izq, der)]
        elif canal == 3: res = [(l - r) // 2 for l, r in zip(izq, der)]
        
        with open(ficMono, 'wb') as f_out:
            f_out.write(escribir_cabecera(1, 16, cab[7], len(res)))
            f_out.write(struct.pack(f'<{len(res)}h', *res))

def codEstereo(ficEste, ficCod):
    with open(ficEste, 'rb') as f_in:
        cab = leer_cabecera(f_in)
        datos = f_in.read()
        muestras = struct.unpack(f'<{len(datos)//2}h', datos)
        izq, der = muestras[0::2], muestras[1::2]
        
        # S = (L+R)/2, D = (L-R)/2
        # Empaquetamos: S en los 16 bits superiores, D en los 16 inferiores
        codificadas = [(((l + r) // 2) << 16) | (((l - r) // 2) & 0xFFFF) 
                       for l, r in zip(izq, der)]
        
        with open(ficCod, 'wb') as f_out:
            f_out.write(escribir_cabecera(1, 32, cab[7], len(codificadas)))
            f_out.write(struct.pack(f'<{len(codificadas)}i', *codificadas))

def decEstereo(ficCod, ficEste):
    with open(ficCod, 'rb') as f_in:
        cab = leer_cabecera(f_in)
        datos = f_in.read()
        # Leemos como enteros de 32 bits ('i')
        muestras_32 = struct.unpack(f'<{len(datos)//4}i', datos)
        
        # Extraer Semisuma (S) y Semidiferencia (D)
        s_lista = [m >> 16 for m in muestras_32]
        # Recuperar signo de 16 bits para D
        d_lista = [struct.unpack('<h', struct.pack('<H', m & 0xFFFF))[0] for m in muestras_32]
        
        # L = S + D, R = S - D
        muestras_est = []
        [(muestras_est.append(s + d), muestras_est.append(s - d)) for s, d in zip(s_lista, d_lista)]
        
        with open(ficEste, 'wb') as f_out:
            f_out.write(escribir_cabecera(2, 16, cab[7], len(muestras_est)//2))
            f_out.write(struct.pack(f'<{len(muestras_est)}h', *muestras_est))