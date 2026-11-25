package com.harumi.autoos.location;
import java.util.Optional;
/** Parser NMEA puro (GGA e RMC). A instancia guarda a ultima GGA/RMC para combinar num Fix. */
public final class NmeaParser {
    private static final double KNOT_MPS=0.514444;
    private double[] gga;   // lat, lon, alt(NaN), sats(-1)
    private double[] rmc;   // lat, lon, speedMps(NaN), bearing(NaN)
    /** Alimenta uma frase; devolve Fix se ja ha posicao valida. Frase invalida: empty (estado preservado). */
    public Optional<Fix> feed(String sentence,long nowMs){
        String[] f=fields(sentence);
        if(f==null||f[0].length()<5)return Optional.empty();
        String t=f[0].substring(f[0].length()-3);
        try{
            if(t.equals("GGA"))gga=parseGga(f);
            else if(t.equals("RMC"))rmc=parseRmc(f);
            else return Optional.empty();
        }catch(RuntimeException e){return Optional.empty();}
        double[] p=gga!=null?gga:rmc;
        if(p==null)return Optional.empty();
        Double alt=gga!=null&&!Double.isNaN(gga[2])?gga[2]:null;
        Integer sats=gga!=null&&gga[3]>=0?(int)gga[3]:null;
        Double sp=rmc!=null&&!Double.isNaN(rmc[2])?rmc[2]:null,br=rmc!=null&&!Double.isNaN(rmc[3])?rmc[3]:null;
        return Optional.of(new Fix(p[0],p[1],alt,sp,br,null,sats,nowMs,"NMEA"));
    }
    /** Valida checksum e separa os campos; null se invalida. */
    static String[] fields(String s){
        if(s==null)return null;
        s=s.trim();
        int star=s.lastIndexOf('*');
        if(s.length()<9||s.charAt(0)!='$'||star<0||star!=s.length()-3)return null;
        int cs=0;for(int i=1;i<star;i++)cs^=s.charAt(i);
        try{if(Integer.parseInt(s.substring(star+1),16)!=cs)return null;}catch(NumberFormatException e){return null;}
        return s.substring(1,star).split(",",-1);
    }
    private static double[] parseGga(String[] f){
        if(f.length<10)throw new IllegalArgumentException();
        if(f[6].isEmpty()||f[6].equals("0"))return null;           // sem fix
        double lat=coord(f[2],f[3],2),lon=coord(f[4],f[5],3);
        double alt=f[9].isEmpty()?Double.NaN:Double.parseDouble(f[9]);
        double sats=f[7].isEmpty()?-1:Integer.parseInt(f[7]);
        return new double[]{lat,lon,alt,sats};
    }
    private static double[] parseRmc(String[] f){
        if(f.length<9)throw new IllegalArgumentException();
        if(!f[2].equals("A"))return null;                          // V = invalido
        double lat=coord(f[3],f[4],2),lon=coord(f[5],f[6],3);
        double sp=f[7].isEmpty()?Double.NaN:Double.parseDouble(f[7])*KNOT_MPS;
        double br=f[8].isEmpty()?Double.NaN:Double.parseDouble(f[8]);
        return new double[]{lat,lon,sp,br};
    }
    /** ddmm.mmmm (ou dddmm.mmmm) + hemisferio -> graus decimais. */
    static double coord(String v,String h,int degDigits){
        if(v.length()<degDigits+1||h.length()!=1)throw new IllegalArgumentException();
        double d=Integer.parseInt(v.substring(0,degDigits))+Double.parseDouble(v.substring(degDigits))/60.0;
        if(h.equals("S")||h.equals("W"))d=-d;else if(!h.equals("N")&&!h.equals("E"))throw new IllegalArgumentException();
        return d;
    }
}
