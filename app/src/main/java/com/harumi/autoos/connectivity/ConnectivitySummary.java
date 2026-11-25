package com.harumi.autoos.connectivity;
/** Presentation policy uses observed Android network capabilities, not pairing or cable presence. */
public final class ConnectivitySummary {
    private ConnectivitySummary() { }
    public static String describe(boolean present,boolean internet,boolean validated,boolean captive,String transport) {
        if(!present)return "Sem conexão de rede";
        if(captive&&!validated)return transport+" · entre na rede para acessar a Internet";
        if(internet&&validated)return "Internet disponível · "+transport;
        return transport+" · Internet não confirmada pelo Android";
    }
}
