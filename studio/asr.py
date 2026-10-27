import sys, sherpa_onnx, soundfile as sf, numpy as np
d="sherpa-onnx-whisper-small/"
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=d+"small-encoder.int8.onnx",decoder=d+"small-decoder.int8.onnx",tokens=d+"small-tokens.txt",language="uk",task="transcribe",num_threads=4)
for f in sys.argv[1:]:
    a,sr=sf.read(f,dtype="float32")
    if a.ndim>1: a=a.mean(1)
    # по ~25с шматках
    out=[]
    for i in range(0,len(a),sr*25):
        s=r.create_stream(); s.accept_waveform(sr,a[i:i+sr*25]); r.decode_stream(s); out.append(s.result.text)
    print(f.split('/')[-1],"→"," ".join(out))
