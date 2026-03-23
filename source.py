"""
CLAC Codec - Cole's Lossless Audio Codec
Pure Python implementation
"""
import wave
import struct
import math
import os
import io

# ================================
# BIT STREAM (Low-level bit I/O)
# ================================
class BitStream:
    def __init__(self, filename=None, mode='rb', header_bytes=0, data_bytes=None):
        self.buffer = 0
        self.bits_in_buffer = 0
        self.file = None
        self.data_bytes = data_bytes
        self.byte_idx = 0
        if filename:
            self.file = open(filename, mode)
            if header_bytes > 0 and mode == 'rb':
                self.file.read(header_bytes)

    def write_bit(self, bit):
        self.buffer = (self.buffer << 1) | (bit & 1)
        self.bits_in_buffer += 1
        if self.bits_in_buffer == 8:
            if self.file:
                self.file.write(bytes([self.buffer]))
            self.buffer = 0
            self.bits_in_buffer = 0

    def write_bits(self, value, count):
        for i in range(count - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    def flush(self):
        if self.bits_in_buffer > 0:
            self.buffer <<= (8 - self.bits_in_buffer)
            if self.file:
                self.file.write(bytes([self.buffer]))
            self.buffer = 0
            self.bits_in_buffer = 0

    def read_bit(self):
        if self.bits_in_buffer == 0:
            if self.file:
                byte = self.file.read(1)
            elif self.data_bytes and self.byte_idx < len(self.data_bytes):
                byte = bytes([self.data_bytes[self.byte_idx]])
                self.byte_idx += 1
            else:
                return None
            if not byte:
                return None
            self.buffer = byte[0]
            self.bits_in_buffer = 8
        self.bits_in_buffer -= 1
        return (self.buffer >> self.bits_in_buffer) & 1

    def read_bits(self, count):
        value = 0
        for _ in range(count):
            bit = self.read_bit()
            if bit is None:
                return None
            value = (value << 1) | bit
        return value

    def close(self):
        if self.file:
            self.file.close()

# ================================
# CLAC CODEC (Main Compression Engine)
# ================================
class CLACCodec:
    """Cole's Lossless Audio Codec"""
    MAGIC = b'CLAC'
    HEADER_SIZE = 20
    BLOCK_SIZE = 4096
    STREAM_CHUNK_SAMPLES = 4096

    def encode(self, input_wav, output_clac, progress_callback=None):
        """Encode WAV file to CLAC format"""
        with wave.open(input_wav, 'rb') as wav_in:
            n_channels = wav_in.getnchannels()
            framerate = wav_in.getframerate()
            raw_data = wav_in.readframes(wav_in.getnframes())
        
        samples = list(struct.unpack(f"<{len(raw_data)//2}h", raw_data))
        total = len(samples)
        
        with open(output_clac, 'wb') as f:
            f.write(self.MAGIC)
            f.write(struct.pack('<I', framerate))
            f.write(struct.pack('<H', n_channels))
            f.write(struct.pack('<H', 16))  # bits per sample
            f.write(struct.pack('<Q', total))
        
        bs = BitStream(filename=output_clac, mode='ab')
        last = 0
        for i in range(0, total, self.BLOCK_SIZE):
            block = samples[i:i + self.BLOCK_SIZE]
            self._encode_block(bs, block, last)
            last = block[-1] if block else last
            if progress_callback:
                progress_callback(((i + len(block)) / total) * 100)
        bs.flush()
        bs.close()
        
        orig = os.path.getsize(input_wav)
        comp = os.path.getsize(output_clac)
        return ((orig - comp) / orig) * 100 if orig > 0 else 0

    def _encode_block(self, bs, samples, last):
        """Encode a block of samples using Rice coding"""
        if not samples: 
            return
        
        # Calculate residuals (prediction error)
        residuals = []
        for s in samples:
            residuals.append(s - last)
            last = s
        
        # Calculate optimal Rice parameter k
        avg = sum(abs(r) for r in residuals) / len(residuals)
        k = 0 if avg < 1 else max(0, min(15, int(math.log2(avg))))
        
        # Write block header
        bs.write_bits(k, 4)
        bs.write_bits(len(residuals), 16)
        
        # Rice encode residuals
        for res in residuals:
            # ZigZag encode signed to unsigned
            ures = ((res << 1) ^ (res >> 31)) & 0xFFFFFFFF
            q, r = ures >> k, ures & ((1 << k) - 1)
            
            # Write quotient in unary
            for _ in range(q): 
                bs.write_bit(1)
            bs.write_bit(0)
            
            # Write remainder in binary
            if k > 0: 
                bs.write_bits(r, k)

    def decode(self, input_clac, output_wav=None, progress_callback=None, return_bytes=False):
        """Decode CLAC file to WAV"""
        with open(input_clac, 'rb') as f:
            if f.read(4) != self.MAGIC: 
                raise ValueError("Invalid .clac file")
            framerate = struct.unpack('<I', f.read(4))[0]
            n_channels = struct.unpack('<H', f.read(2))[0]
            f.read(2)  # skip bits per sample
            total = struct.unpack('<Q', f.read(8))[0]
            data = f.read()
        
        bs = BitStream(data_bytes=data)
        samples, last = [], 0
        
        while len(samples) < total:
            k = bs.read_bits(4)
            if k is None: 
                break
            block_len = bs.read_bits(16)
            if block_len is None: 
                break
            
            for _ in range(block_len):
                if len(samples) >= total: 
                    break
                q = 0
                while bs.read_bit() == 1: 
                    q += 1
                r = bs.read_bits(k) if k > 0 else 0
                ures = (q << k) | r
                res = (ures >> 1) ^ -(ures & 1)  # ZigZag decode
                samples.append(max(-32768, min(32767, last + res)))
                last = samples[-1]
            
            if progress_callback: 
                progress_callback((len(samples) / total) * 100)
        
        # Build WAV file
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as w:
            w.setnchannels(n_channels)
            w.setsampwidth(2)
            w.setframerate(framerate)
            w.writeframes(struct.pack(f"<{len(samples)}h", *samples))
        
        wav_bytes = wav_buffer.getvalue()
        
        if return_bytes: 
            return wav_bytes
        elif output_wav:
            with open(output_wav, 'wb') as f: 
                f.write(wav_bytes)
            return True
        return None

    def decode_stream(self, input_clac, chunk_callback, progress_callback=None, stop_flag=None):
        """Stream decode CLAC file (for real-time playback)"""
        with open(input_clac, 'rb') as f:
            if f.read(4) != self.MAGIC: 
                raise ValueError("Invalid .clac file")
            framerate = struct.unpack('<I', f.read(4))[0]
            n_channels = struct.unpack('<H', f.read(2))[0]
            f.read(2)
            total = struct.unpack('<Q', f.read(8))[0]
            data = f.read()
        
        bs = BitStream(data_bytes=data)
        chunk_samples, last, decoded = [], 0, 0
        
        while decoded < total:
            if stop_flag and stop_flag.is_set(): 
                break
            k = bs.read_bits(4)
            if k is None: 
                break
            block_len = bs.read_bits(16)
            if block_len is None: 
                break
            
            for _ in range(block_len):
                if decoded >= total or (stop_flag and stop_flag.is_set()): 
                    break
                q = 0
                while bs.read_bit() == 1: 
                    q += 1
                r = bs.read_bits(k) if k > 0 else 0
                ures = (q << k) | r
                res = (ures >> 1) ^ -(ures & 1)
                chunk_samples.append(max(-32768, min(32767, last + res)))
                last = chunk_samples[-1]
                decoded += 1
                
                if len(chunk_samples) >= self.STREAM_CHUNK_SAMPLES:
                    chunk_callback(struct.pack(f"<{len(chunk_samples)}h", *chunk_samples))
                    chunk_samples = []
            
            if progress_callback: 
                progress_callback((decoded / total) * 100)
        
        if chunk_samples:
            chunk_callback(struct.pack(f"<{len(chunk_samples)}h", *chunk_samples))
        
        return framerate, n_channels, total

    def verify(self, wav1, wav2):
        """Verify two WAV files are identical"""
        with wave.open(wav1, 'rb') as w1, wave.open(wav2, 'rb') as w2:
            return w1.getparams() == w2.getparams() and \
                   w1.readframes(w1.getnframes()) == w2.readframes(w2.getnframes())