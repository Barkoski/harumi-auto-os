package com.harumi.autoos.navigation;

/** Recolore tiles OSM claros para a paleta escura da Harumi (classe por cor + tinta por luminancia); mantenha identico a scripts/serve_map_preview.py. */
public final class TileTint {
    private TileTint(){}
    static final int LAND=0x26222b,WATER=0x232a33,GREEN=0x2a2d2b,ROAD=0x6b5c6e,MAJOR=0x8a7589,BUILDING=0x2d2831,LABEL=0xb9a6b8;
    public static int[] tint(int[] argb,boolean far){
        int[] out=new int[argb.length];
        for(int i=0;i<argb.length;i++)out[i]=tintPixel(argb[i],far);
        return out;
    }
    static int tintPixel(int p,boolean far){
        int r=(p>>16)&255,g=(p>>8)&255,b=p&255,lum=(299*r+587*g+114*b)/1000,m=Math.min(r,Math.min(g,b)),base;
        if(g>r+10&&g>b)base=GREEN;
        else if(r>=200&&r-b>=40)base=MAJOR;
        else{
            if(m>=233)base=mix(LAND,ROAD,Math.min(256,(m-233)*256/22));
            else if(m>=201)base=mix(BUILDING,LAND,(m-201)*256/32);
            else base=BUILDING;
            base=mix(base,WATER,Math.min(256,Math.max(0,b-r-4)*256/36));}
        int c=mix(base,LABEL,Math.max(0,130-lum)*256/130);
        if(far)c=mix(c,LAND,77);
        return (p&0xff000000)|c;
    }
    private static int mix(int a,int b,int t){
        int rr=(((a>>16)&255)*(256-t)+((b>>16)&255)*t+128)>>8,gg=(((a>>8)&255)*(256-t)+((b>>8)&255)*t+128)>>8,bb=((a&255)*(256-t)+(b&255)*t+128)>>8;
        return (rr<<16)|(gg<<8)|bb;
    }
}
