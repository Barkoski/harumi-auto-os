package com.harumi.autoos.voice;
import java.io.*;
import java.nio.*;
public final class CachedPcm {
    public record Audio(float[] samples,int sampleRate) { }
    private CachedPcm() { }
    public static Audio decode(InputStream input) throws IOException {
        byte[] header=read(input,12);
        if(header.length!=12||header[0]!='H'||header[1]!='A'||header[2]!='U'||header[3]!='1')throw new IOException("Invalid audio header");
        ByteBuffer h=ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN);int rate=h.getInt(4),count=h.getInt(8);
        if(rate<8000||rate>48000||count<1||count>(long)rate*30)throw new IOException("Invalid audio bounds");
        byte[] pcm=read(input,count*4);if(pcm.length!=count*4||input.read()!=-1)throw new IOException("Invalid audio length");
        FloatBuffer buffer=ByteBuffer.wrap(pcm).order(ByteOrder.LITTLE_ENDIAN).asFloatBuffer();float[] samples=new float[count];buffer.get(samples);
        for(float value:samples)if(!Float.isFinite(value)||Math.abs(value)>1.01f)throw new IOException("Invalid audio sample");
        return new Audio(samples,rate);
    }
    private static byte[] read(InputStream input,int size)throws IOException{
        byte[] bytes=new byte[size];int offset=0;
        while(offset<size){int n=input.read(bytes,offset,size-offset);if(n<0)throw new EOFException("Truncated cached audio");if(n==0){int value=input.read();if(value<0)throw new EOFException();bytes[offset++]=(byte)value;}else offset+=n;}
        return bytes;
    }
}
