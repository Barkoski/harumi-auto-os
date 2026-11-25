package com.harumi.autoos.location;
/** Histerese de movimento: liga acima de X km/h, desliga abaixo de X-3. Fix ou velocidade ausente mantem o estado. */
public final class SpeedPolicy {
    public static final double DEFAULT_KMH=10;   // a definir pelo Lucas
    static final double HYSTERESIS_KMH=3;        // provisório
    private boolean moving;
    public boolean isMovingAbove(Fix fix,double kmh){
        if(fix==null||fix.speedMps()==null)return moving;
        double v=fix.speedMps()*3.6;
        if(!moving&&v>kmh)moving=true;
        else if(moving&&v<kmh-HYSTERESIS_KMH)moving=false;
        return moving;
    }
    public boolean isMoving(Fix fix){return isMovingAbove(fix,DEFAULT_KMH);}
    public void reset(){moving=false;}
}
