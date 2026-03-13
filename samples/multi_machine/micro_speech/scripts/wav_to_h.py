"""
Converts a 16-bit WAV audio file into a C header file containing the raw
samples.
"""

import struct
import sys
import wave

if len(sys.argv) != 3:
    print("Usage: python wav_to_h.py <input.wav> <output.h>")
    sys.exit(1)

in_file, out_file = sys.argv[1], sys.argv[2]

try:
    with wave.open(in_file, "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        num_frames = wav.getnframes()

        if sample_width != 2:
            print(f"Error: Expected 16-bit audio, got {sample_width * 8}-bit.")
            sys.exit(1)

        if sample_rate != 16000:
            print(f"Warning: Audio is {sample_rate}Hz. App expects 16000Hz.")

        raw_frames = wav.readframes(num_frames)
        samples = struct.unpack(f"<{num_frames * channels}h", raw_frames)

        if channels > 1:
            print("Stereo detected. Stripping to mono...")
            samples = samples[::channels]

except Exception as e:
    print(f"Error reading {in_file}: {e}")
    sys.exit(1)

try:
    with open(out_file, "w") as f:
        f.write("const int16_t g_audio_sample[] = {\n    ")

        for i, val in enumerate(samples):
            f.write(f"{val},")
            if (i + 1) % 12 == 0:
                f.write("\n    ")
            else:
                f.write(" ")

        f.write("\n};\n")
    print(f"Success! {len(samples)} samples written to {out_file}")
except Exception as e:
    print(f"Error writing to {out_file}: {e}")
