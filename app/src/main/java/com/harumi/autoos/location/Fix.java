package com.harumi.autoos.location;
/** Posicao GNSS. Campos opcionais sao null quando o receptor nao informa. */
public record Fix(double lat,double lon,Double altitude,Double speedMps,Double bearing,Double accuracyM,Integer satellites,long timeMs,String source){}
