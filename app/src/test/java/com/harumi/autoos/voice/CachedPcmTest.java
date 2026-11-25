package com.harumi.autoos.voice;
import org.junit.Test;
import java.io.*;
import java.nio.*;
import static org.junit.Assert.*;
public class CachedPcmTest {
    private byte[] bytes(float value){return ByteBuffer.allocate(16).order(ByteOrder.LITTLE_ENDIAN).put(new byte[]{'H','A','U','1'}).putInt(24000).putInt(1).putFloat(value).array();}
    @Test public void validLittleEndianAudio()throws Exception{var a=CachedPcm.decode(new ByteArrayInputStream(bytes(.25f)));assertEquals(24000,a.sampleRate());assertEquals(.25f,a.samples()[0],.00001f);}
    @Test public void rejectsTruncationAndNaN()throws Exception{for(byte[] b:new byte[][]{new byte[2],bytes(Float.NaN)})try{CachedPcm.decode(new ByteArrayInputStream(b));fail();}catch(IOException expected){}}
    @Test public void rejectsOversizedAllocation()throws Exception{byte[] b=bytes(0);ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN).putInt(8,Integer.MAX_VALUE);try{CachedPcm.decode(new ByteArrayInputStream(b));fail();}catch(IOException expected){}}
}
