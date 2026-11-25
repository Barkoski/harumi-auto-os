package com.harumi.autoos.connectivity;
import android.content.Context;
import android.net.*;
import android.os.*;
import java.util.*;
public final class ConnectivityMonitor implements AutoCloseable {
    private final ConnectivityManager manager;
    private final Runnable changed;
    private Network active;
    private boolean registered;
    private String summary="Conexão ainda não verificada";
    private final ConnectivityManager.NetworkCallback callback=new ConnectivityManager.NetworkCallback() {
        @Override public void onAvailable(Network network) { active=network;summary="Verificando conexão…";changed.run(); }
        @Override public void onCapabilitiesChanged(Network network,NetworkCapabilities caps) { if(network.equals(active)) update(caps); }
        @Override public void onLost(Network network) { if(network.equals(active)) { active=null;update(null); } }
    };
    public ConnectivityMonitor(Context c,Runnable changed) { manager=(ConnectivityManager)c.getSystemService(Context.CONNECTIVITY_SERVICE);this.changed=changed; }
    public void start() {
        if(registered)return;
        try {
            active=manager.getActiveNetwork();update(active==null?null:manager.getNetworkCapabilities(active));
            manager.registerDefaultNetworkCallback(callback,new Handler(Looper.getMainLooper()));registered=true;
        } catch(SecurityException|IllegalArgumentException e) { summary="Status de rede indisponível nesta central";changed.run(); }
    }
    private void update(NetworkCapabilities caps) {
        if(caps==null)summary=ConnectivitySummary.describe(false,false,false,false,"");
        else {
            List<String> via=new ArrayList<>();
            if(caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI))via.add("Wi-Fi");
            if(caps.hasTransport(NetworkCapabilities.TRANSPORT_BLUETOOTH))via.add("Bluetooth");
            if(caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET))via.add("Ethernet / cabo");
            if(caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR))via.add("Dados móveis");
            if(Build.VERSION.SDK_INT>=31&&caps.hasTransport(NetworkCapabilities.TRANSPORT_USB))via.add("USB");
            if(caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN))via.add("VPN");
            String transport=via.isEmpty()?"Rede informada pelo Android":String.join(" + ",via);
            summary=ConnectivitySummary.describe(true,caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET),caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED),caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_CAPTIVE_PORTAL),transport);
        }
        changed.run();
    }
    public String summary() { return summary; }
    @Override public void close() { if(registered) { try { manager.unregisterNetworkCallback(callback); } catch(IllegalArgumentException|SecurityException ignored) { } registered=false; } }
}
