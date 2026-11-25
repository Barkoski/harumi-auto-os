package com.harumi.autoos.navigation;
import java.util.Locale;
public final class RouteCoordinates {
    private RouteCoordinates(){}
    public static String toProviderPath(String value){
        if(value==null||value.length()>100||!value.matches("[-0-9.,]+"))throw new IllegalArgumentException("Invalid coordinates");
        String[] parts=value.split(",",-1);if(parts.length!=4)throw new IllegalArgumentException("Two points required");
        double[] p=new double[4];for(int i=0;i<4;i++){p[i]=Double.parseDouble(parts[i]);if(!Double.isFinite(p[i])||p[i]<(i%2==0?-75:-35)||p[i]>(i%2==0?-30:6))throw new IllegalArgumentException("Outside Brazil bounds");}
        return String.format(Locale.ROOT,"%.6f,%.6f;%.6f,%.6f",p[0],p[1],p[2],p[3]);
    }
    /** Bearing inteiro 0-359 ou null (ausente/invalido => ignorado). */
    public static Integer parseBearing(String value){
        if(value==null||!value.matches("[0-9]{1,3}"))return null;
        int b=Integer.parseInt(value);return b<=359?b:null;
    }
}
