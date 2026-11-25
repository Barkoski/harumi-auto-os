package com.harumi.autoos.location;
import java.util.function.LongSupplier;
public final class FixAssessor {
    static final long MAX_AGE_MS=5000;      // provisório
    static final double MAX_ACCURACY_M=30;  // provisório
    static final int MIN_SATELLITES=4;      // provisório
    private final LongSupplier clock;
    public FixAssessor(LongSupplier clock){this.clock=clock;}
    public FixQuality assess(Fix f){
        if(f==null)return FixQuality.SEM_FIX;
        if(clock.getAsLong()-f.timeMs()>MAX_AGE_MS)return FixQuality.VELHO;
        if((f.accuracyM()!=null&&f.accuracyM()>MAX_ACCURACY_M)||(f.satellites()!=null&&f.satellites()<MIN_SATELLITES))return FixQuality.FRACO;
        return FixQuality.OK;
    }
}
