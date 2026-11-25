package com.harumi.autoos;
import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.media.*;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.speech.tts.TextToSpeech;
import android.view.*;
import android.webkit.*;
import android.widget.*;
import androidx.webkit.WebViewAssetLoader;
import com.harumi.autoos.domain.ModuleRouter;
import com.harumi.autoos.ai.*;
import com.harumi.autoos.navigation.NavigationGateway;
import com.harumi.autoos.diagnostics.DiagnosticMonitor;
import com.harumi.autoos.oem.*;
import com.harumi.autoos.connectivity.ConnectivityMonitor;
import com.harumi.autoos.location.GnssLocationSource;
import com.harumi.autoos.location.LocationSource;
import com.harumi.autoos.location.NavigationFeed;
import com.harumi.autoos.location.ReplayLocationSource;
import org.json.JSONObject;
import java.io.ByteArrayInputStream;
import java.util.*;

public class MainActivity extends Activity {
    private WebView web;
    private LinearLayout root;
    private int webRestarts;
    private String appVersion = "desconhecida";
    private final DiagnosticMonitor diagnostics = new DiagnosticMonitor();
    private boolean listenAfterResume;
    private AppAssignmentStore store;
    private OemAppGateway apps;
    private AppCatalogGateway appCatalog;
    private final ModuleRouter router = new ModuleRouter();
    private AssistantController assistant;
    private ConnectivityMonitor connectivity;
    private String assistantStatus="Pronta para conversar · IA local";
    private boolean assistantBusy;
    private boolean foreground;
    private AudioManager audio;
    private AudioFocusRequest audioRequest;
    private static final String ORIGIN = "https://appassets.androidplatform.net";
    private static final String PAGE = ORIGIN + "/assets/index.html";
    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        pendingVoice = b == null && isVoiceIntent(getIntent());
        getWindow().setStatusBarColor(Color.rgb(24, 21, 30));
        getWindow().setNavigationBarColor(Color.rgb(24, 21, 30));
        store = new AppAssignmentStore(this); apps = new OemAppGateway(this); appCatalog=new AppCatalogGateway(this,apps);
        audio = (AudioManager) getSystemService(AUDIO_SERVICE);
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        LinearLayout recoveryBar=new LinearLayout(this);recoveryBar.setGravity(Gravity.CENTER_VERTICAL);recoveryBar.setBackgroundColor(Color.rgb(24,21,30));
        TextView title=new TextView(this);title.setText("Harumi Auto OS");title.setTextColor(Color.rgb(213,160,192));title.setTextSize(13);title.setGravity(Gravity.CENTER_VERTICAL);title.setPadding(18,0,0,0);recoveryBar.addView(title,new LinearLayout.LayoutParams(0,-1,1));
        Button recovery=new Button(this);recovery.setText("Interface de fábrica");recovery.setAllCaps(false);recovery.setPadding(16,0,16,0);recovery.setTextSize(12);recovery.setTextColor(Color.rgb(240,215,231));recovery.setBackgroundColor(Color.rgb(40,33,47));recovery.setOnClickListener(v->openOemHome());recoveryBar.addView(recovery,new LinearLayout.LayoutParams(-2,-1));
        root.addView(recoveryBar,new LinearLayout.LayoutParams(-1,(int)(44*getResources().getDisplayMetrics().density)));
        appVersion = versionName();
        buildWeb();
        setContentView(root);
        connectivity=new ConnectivityMonitor(this,this::publish);
        assistant=new AssistantController(this,new AssistantController.Listener() {
            public void state(String status,boolean busy) { assistantStatus=status;assistantBusy=busy;publish(); }
            public void message(String role,String text) {
                if(web!=null) web.evaluateJavascript("window.harumiMessage && window.harumiMessage("+JSONObject.quote(role)+","+JSONObject.quote(text)+")",null);
            }
            public void partial(String text){if(web!=null)web.evaluateJavascript("window.harumiPartial && window.harumiPartial("+JSONObject.quote(text)+")",null);}
            public void dictation(String text){if(web!=null)web.evaluateJavascript("window.harumiDictation && window.harumiDictation("+JSONObject.quote(text)+")",null);}
            public void wake(){if(web!=null)web.evaluateJavascript("window.harumiOpenAssistant && window.harumiOpenAssistant()",null);}
            public boolean micAllowed(){return checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)==android.content.pm.PackageManager.PERMISSION_GRANTED;}
            public boolean canHandle(LocalCommandParser.Command command) {
                switch(command.action()) {
                    case MUSIC: return store.get("MUSIC")!=null||!apps.listFor("MUSIC").isEmpty();
                    case ROUTE: return true; // navegação interna sempre existe
                    default: return true;
                }
            }
            public void action(LocalCommandParser.Command command) {
                switch(command.action()) {
                    case MAP: if(web!=null)web.evaluateJavascript("window.harumiRoadMap && window.harumiRoadMap.open(false)",null);break;
                    case MUSIC: launch("MUSIC");break;
                    case ROUTE_BETWEEN: String[] endpoints=command.destination().split("\\n",2); if(endpoints.length==2&&web!=null)web.evaluateJavascript("window.harumiRoadMap && window.harumiRoadMap.plan("+JSONObject.quote(endpoints[0])+","+JSONObject.quote(endpoints[1])+")",null);break;
                    case ROUTE: if(web!=null)web.evaluateJavascript("window.harumiRoadMap && window.harumiRoadMap.navigateTo("+JSONObject.quote(command.destination())+")",null);break;
                    case WIFI_SETTINGS: safeStart(new Intent(Settings.ACTION_WIFI_SETTINGS));break;
                    case BLUETOOTH_SETTINGS: safeStart(new Intent(Settings.ACTION_BLUETOOTH_SETTINGS));break;
                    default: break;
                }
            }
        },diagnostics);
    }
    private String versionName() {
        try { String v = getPackageManager().getPackageInfo(getPackageName(), 0).versionName; return v == null || v.isBlank() ? "desconhecida" : v; }
        catch (Exception e) { return "desconhecida"; }
    }
    private void buildWeb() {
        try {
            web = new WebView(this);
            root.addView(web, new LinearLayout.LayoutParams(-1, 0, 1));
            configureWeb();
        } catch (RuntimeException e) {
            web = null;
            TextView error = new TextView(this); error.setText(R.string.webview_missing); error.setTextSize(22); root.addView(error);
        }
    }
    private void configureWeb() {
        com.harumi.autoos.navigation.MapNetworkGateway mapNetwork = new com.harumi.autoos.navigation.MapNetworkGateway(this, appVersion);
        if ((getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0) WebView.setWebContentsDebuggingEnabled(true);
        WebSettings s = web.getSettings();
        s.setCacheMode(WebSettings.LOAD_NO_CACHE);
        s.setJavaScriptEnabled(true); s.setAllowFileAccess(false); s.setAllowContentAccess(false);
        s.setBlockNetworkLoads(true); s.setDomStorageEnabled(false); s.setGeolocationEnabled(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setMediaPlaybackRequiresUserGesture(false); s.setSupportMultipleWindows(false);
        WebViewAssetLoader loader = new WebViewAssetLoader.Builder().addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this)).build();
        web.addJavascriptInterface(new Bridge(), "HarumiNative");
        web.setWebViewClient(new WebViewClient() {
            private boolean allowed(Uri u) { return "https".equals(u.getScheme()) && "appassets.androidplatform.net".equals(u.getHost()) && u.getPort() == -1 && u.getUserInfo() == null && u.getPath() != null && u.getPath().startsWith("/assets/"); }
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                if (allowed(r.getUrl())) { String iconPath=r.getUrl().getPath();if(iconPath!=null&&iconPath.matches("/assets/app-icons/[a-z0-9-]{1,32}\\.png")){String id=iconPath.substring("/assets/app-icons/".length(),iconPath.length()-4);byte[] icon;try{icon=appCatalog.icon(id);}catch(RuntimeException|OutOfMemoryError e){icon=null;}if(icon==null)return new WebResourceResponse("image/png",null,404,"Not Found",Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));return new WebResourceResponse("image/png",null,new ByteArrayInputStream(icon));} WebResourceResponse maps=mapNetwork.intercept(r.getUrl()); if(maps!=null)return maps; WebResourceResponse response = loader.shouldInterceptRequest(r.getUrl()); if (response != null) return response; }
                return new WebResourceResponse("text/plain", "UTF-8", 403, "Blocked", Collections.emptyMap(), new ByteArrayInputStream(new byte[0]));
            }
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) { return true; }
            @Override public void onPageFinished(WebView v, String url) { if (PAGE.equals(url)) { pageLoaded = true; publish(); runPendingVoice(); } }
            @Override public boolean onRenderProcessGone(WebView v, RenderProcessGoneDetail d) {
                v.removeJavascriptInterface("HarumiNative"); if (v.getParent() instanceof android.view.ViewGroup) ((android.view.ViewGroup)v.getParent()).removeView(v); v.destroy(); web = null;
                if (!isFinishing()) { if (++webRestarts <= 3) buildWeb(); message(web != null ? "A interface foi reiniciada." : "A interface foi encerrada. Use o botão \"Interface de fábrica\" na barra superior."); } return true;
            }
        });
        web.setOnLongClickListener(v -> true);
        web.loadUrl(PAGE);
    }
    public final class Bridge {
        @JavascriptInterface public void dispatch(String action, String module) {
            if (!router.permits(action) || (module != null && module.length() > ("assistant.ask".equals(action)?1600:32))) return;
            runOnUiThread(() -> { if (foreground && web != null && PAGE.equals(web.getUrl())) handle(action, module); });
        }
    }
    private void handle(String action, String module) {
        String target = router.moduleFor(action);
        if (target != null) { if ("CAMERA360".equals(target)) {
            new AlertDialog.Builder(this).setTitle("Abrir app de câmeras").setMessage("Este atalho abre o aplicativo escolhido. Compatibilidade com a central e vídeo de ré ainda não foram homologados.").setPositiveButton("Abrir", (d,w) -> launch(target)).setNegativeButton("Cancelar", null).show();
        } else launch(target); return; }
        switch (action) {
            case "launcher.list": web.evaluateJavascript("window.harumiLauncherUpdate && window.harumiLauncherUpdate({apps:"+appCatalog.launcherInventory()+",catalog:"+appCatalog.inventory()+"})",null);break;
            case "launcher.open": appCatalog.launchInstalled(module);break;
            case "catalog.list": web.evaluateJavascript("window.harumiAppsUpdate && window.harumiAppsUpdate("+appCatalog.inventory().toString()+")",null);break;
            case "catalog.open": appCatalog.open(module);break;
            case "catalog.store": appCatalog.store(module);break;
            case "catalog.assign": appCatalog.assign(module);break;
            case "catalog.all": appCatalog.all();break;
            case "apps.choose": if (router.validModule(module)) choose(module); break;
            case "apps.clear": if (router.validModule(module)) { store.clear(module); publish(); } break;
            case "settings.open.android": safeStart(new Intent(Settings.ACTION_SETTINGS)); break;
            case "settings.open.home": safeStart(new Intent(Settings.ACTION_HOME_SETTINGS)); break;
            case "oem.home": openOemHome(); break;
            case "device.read.basic": showProfile(); break;
            case "voice.greet": assistant.greet(); break;
            case "assistant.ask": assistant.submit(module); break;
            case "assistant.cancel.quiet": assistant.cancel(); break;
            case "assistant.cancel": assistant.cancelWithFeedback(); break;
            case "assistant.finish.listen": assistant.finishListening();break;
            case "media.previous": mediaKey(KeyEvent.KEYCODE_MEDIA_PREVIOUS);break;
            case "media.playpause": mediaKey(KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE);break;
            case "media.next": mediaKey(KeyEvent.KEYCODE_MEDIA_NEXT);break;
            case "assistant.listen": requestListening(); break;
            case "wake.toggle": assistant.setWakeEnabled(!assistant.wakeEnabled());if(assistant.wakeEnabled())askMicForWake();publish(); break;
            case "wake.learn": if(checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)==android.content.pm.PackageManager.PERMISSION_GRANTED)assistant.learnWake();else askMicForWake(); break;
            // Bancada (somente build de depuracao): simula o texto ouvido pelo reconhecedor.
            case "wake.test": if((getApplicationInfo().flags&android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)!=0&&module!=null&&assistant.wakeMatches(module))assistant.onWake(); break;
            case "nav.start": navStart(); break;
            case "nav.stop": stopNav(); break;
            case "nav.say": if (module != null && module.matches("[a-z0-9_]{1,32}")) navigationVoice(module); break;
            case "nav.replay": navReplay("desvio".equals(module)?"debug/trip-desvio.nmea":"debug/trip.nmea"); break;
            case "connection.wifi": safeStart(new Intent(Settings.ACTION_WIFI_SETTINGS)); break;
            case "connection.bluetooth": safeStart(new Intent(Settings.ACTION_BLUETOOTH_SETTINGS)); break;
            default: break;
        }
    }
    // Sem enableOnBackInvokedCallback no manifest, onBackPressed continua sendo chamado. Painel aberto fecha primeiro; senao comportamento padrao.
    @Override public void onBackPressed() {
        if (web == null) { super.onBackPressed(); return; }
        web.evaluateJavascript("window.harumiBack&&window.harumiBack()", r -> { if (!"true".equals(r)) defaultBack(); });
    }
    private void defaultBack() { if (!isFinishing() && !isDestroyed()) MainActivity.super.onBackPressed(); }
    private void mediaKey(int code){audio.dispatchMediaKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN,code));audio.dispatchMediaKeyEvent(new KeyEvent(KeyEvent.ACTION_UP,code));}
    private void choose(String module) {
        List<android.content.pm.ResolveInfo> choices = apps.list();
        if (choices.isEmpty()) { message("Nenhum aplicativo visível disponível. Use a interface de fábrica."); return; }
        String[] labels = new String[choices.size() + 1];
        for (int i=0; i<choices.size(); i++) labels[i] = choices.get(i).loadLabel(getPackageManager()) + " (" + choices.get(i).activityInfo.packageName + ")";
        labels[choices.size()] = "Limpar associação";
        new AlertDialog.Builder(this).setTitle("Escolher app · " + module).setItems(labels, (d,which) -> {
            if (which == choices.size()) store.clear(module); else store.set(module, apps.component(choices.get(which)).flattenToString()); publish();
        }).setNegativeButton("Cancelar", null).show();
    }
    private void launch(String module) {
        if ("NAV".equals(module) || "MUSIC".equals(module)) { openAppPicker(module, false); return; }
        if (!apps.open(store.get(module))) { message("Escolha um aplicativo disponível para este atalho."); choose(module); }
    }
    private void openAppPicker(String module, boolean all) {
        List<android.content.pm.ResolveInfo> choices = all ? apps.list() : apps.listFor(module);
        String saved = store.get(module);
        // A manually assigned OEM app must remain available even without category intents.
        if (!all && saved != null) for (android.content.pm.ResolveInfo i : apps.list()) {
            if (apps.component(i).flattenToString().equals(saved) && choices.stream().noneMatch(c -> apps.component(c).equals(apps.component(i)))) choices.add(0, i);
        }
        if (choices.isEmpty() && !all) {
            new AlertDialog.Builder(this).setTitle("Nenhum app identificado nesta categoria")
                .setMessage("A Harumi mostra os aplicativos instalados no Android da central. Configure ou instale seu app pela loja ou interface de fábrica.")
                .setPositiveButton("Ver todos os apps", (d,w) -> openAppPicker(module,true)).setNegativeButton("Fechar",null).show(); return;
        }
        if (choices.isEmpty()) { message("Nenhum aplicativo instalado disponível para abrir."); return; }
        String[] labels = new String[choices.size()];
        for (int i=0;i<choices.size();i++) labels[i] = choices.get(i).loadLabel(getPackageManager()).toString() + (apps.component(choices.get(i)).flattenToString().equals(saved) ? " · favorito" : "");
        AlertDialog.Builder dialog = new AlertDialog.Builder(this).setTitle("NAV".equals(module)?"Abrir navegação":"Abrir música e rádio")
            .setItems(labels,(d,w) -> { if (!apps.open(apps.component(choices.get(w)).flattenToString())) message("Este aplicativo não está disponível."); })
            .setNegativeButton("Cancelar",null);
        if (!all) dialog.setNeutralButton("Outros apps",(d,w)->openAppPicker(module,true));
        dialog.show();
    }
    private void publish() {
        if (web == null) return;
        JSONObject state = new JSONObject();
        try {
            for (String m : new String[]{"NAV","MUSIC","CAMERA360"}) state.put(m,
                "CAMERA360".equals(m) ? apps.label(store.get(m)) : store.get(m)==null ? "Apps instalados · tocar para escolher" : apps.label(store.get(m))+" · escolher app");
            state.put("device", android.os.Build.MANUFACTURER + " " + android.os.Build.MODEL);
            state.put("version", appVersion);
            state.put("animation",com.harumi.autoos.domain.AvatarState.from(assistantStatus,assistantBusy));
            state.put("connectivity",connectivity==null?"Conexão ainda não verificada":connectivity.summary());
            state.put("assistantStatus",assistantStatus);
            state.put("assistantBusy",assistantBusy);
            state.put("diagnostics",diagnostics.status());
            state.put("wake",assistant!=null&&assistant.wakeEnabled()?"on":"off");
            web.evaluateJavascript("window.harumiUpdate && window.harumiUpdate(" + state.toString() + ")", null);
        } catch (Exception ignored) { message("Não foi possível atualizar os atalhos."); }
    }
    private void showProfile() {
        JSONObject j = DeviceProfileCollector.collect(this); StringBuilder text = new StringBuilder();
        Iterator<String> keys = j.keys(); while (keys.hasNext()) { String k=keys.next(); text.append(k).append(": ").append(j.optString(k)).append("\n\n"); }
        new AlertDialog.Builder(this).setTitle("Compatibilidade do dispositivo").setMessage(text.toString())
            .setPositiveButton("Salvar relatório",(d,w)->{
                Intent save=new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("application/json").putExtra(Intent.EXTRA_TITLE,"Harumi-compatibilidade.json");
                try{startActivityForResult(save,202);}catch(ActivityNotFoundException e){message("Seletor de arquivos não disponível neste Android.");}
            }).setNegativeButton("Fechar",null).show();
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=202||result!=RESULT_OK||data==null||data.getData()==null)return;
        try(java.io.OutputStream output=getContentResolver().openOutputStream(data.getData(),"wt")){
            if(output==null)throw new java.io.IOException("Sem destino");
            output.write(DeviceProfileCollector.collect(this).toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            message("Relatório salvo no local escolhido. Nenhum envio automático.");
        }catch(Exception e){message("Não foi possível salvar o relatório.");}
    }
    private void safeStart(Intent i) { try { startActivity(i); } catch (ActivityNotFoundException | SecurityException e) { message("Esta tela não está disponível nesta versão do Android."); } }
    private void openOemHome() {
        try { startActivity(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); }
        catch (ActivityNotFoundException | SecurityException e) { message("Abra as configurações e selecione a interface de fábrica."); safeStart(new Intent(Settings.ACTION_SETTINGS)); }
    }
    private void requestListening() {
        if(checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)!=android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO},101);
        } else assistant.listen();
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results) {
        super.onRequestPermissionsResult(request,permissions,results);
        if(request==103){boolean fine=false;for(int i=0;i<permissions.length&&i<results.length;i++)if(android.Manifest.permission.ACCESS_FINE_LOCATION.equals(permissions[i])&&results[i]==android.content.pm.PackageManager.PERMISSION_GRANTED)fine=true;if(fine)beginNav(new GnssLocationSource(this),true);else navUnavailable("Permita a localização precisa para navegar.");return;}
        if(request==102){if(results.length>0&&results[0]==android.content.pm.PackageManager.PERMISSION_GRANTED){if(assistant!=null)assistant.startWake();}else message("Sem o microfone, o “Oi Harumi” fica desligado. Você pode conversar por toque ou texto.");return;}
        if(request==101 && results.length>0 && results[0]==android.content.pm.PackageManager.PERMISSION_GRANTED) {
            listenAfterResume=true;
            if(foreground&&assistant!=null){listenAfterResume=false;listenNow();}
        } else if(request==101) message("Microfone não autorizado. Você pode conversar por texto.");
    }
    // Navegação própria: GPS -> NavigationFeed (1 Hz) -> window.harumiNav. Localização só é pedida em nav.start.
    private NavigationFeed navFeed;
    private void navJs(String js){if(web!=null)web.evaluateJavascript(js,null);}
    private void navUnavailable(String reason){navJs("window.harumiNav && window.harumiNav.unavailable("+JSONObject.quote(reason)+")");}
    private void navStart(){
        if(checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)!=android.content.pm.PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{android.Manifest.permission.ACCESS_FINE_LOCATION,android.Manifest.permission.ACCESS_COARSE_LOCATION},103);return;}
        beginNav(new GnssLocationSource(this),true);
    }
    private void beginNav(LocationSource source,boolean seedLastKnown){
        stopNav();
        navFeed=new NavigationFeed(source,System::currentTimeMillis,new NavigationFeed.Sink() {
            public void fix(String json){navJs("window.harumiNav && window.harumiNav.fix("+json+")");}
            public void unavailable(String reason){navUnavailable(reason);}
        });
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        if(seedLastKnown)navFeed.seed(NavigationFeed.lastKnown(this));
        navFeed.start();
    }
    private void stopNav(){
        if(navFeed!=null){navFeed.stop();navFeed=null;}
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }
    /** Bancada (somente build de depuração): reproduz um percurso de assets/debug (gerado por scripts/bench/make_trip.py) a 1 Hz pelo mesmo feed. */
    private void navReplay(String asset){
        if((getApplicationInfo().flags&android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)==0)return;
        List<String> lines=new ArrayList<>();
        try(java.io.BufferedReader r=new java.io.BufferedReader(new java.io.InputStreamReader(getAssets().open(asset),java.nio.charset.StandardCharsets.UTF_8))){String l;while((l=r.readLine())!=null)if(!l.isBlank())lines.add(l);}
        catch(java.io.IOException e){navUnavailable("Trajeto de teste indisponível.");return;}
        android.os.Handler h=new android.os.Handler(android.os.Looper.getMainLooper());
        beginNav(ReplayLocationSource.fromNmea(lines,1000,System::currentTimeMillis,h::postDelayed),false);
    }
    /** Fala de navegação por código curto. Ligado pela tarefa de voz. */
    private com.harumi.autoos.voice.NavigationVoice navVoice;
    private void navigationVoice(String code){if(navVoice==null)navVoice=new com.harumi.autoos.voice.NavigationVoice(this);navVoice.play(code);}
    private boolean askedMicForWake;
    /** "Oi Harumi" precisa do microfone: pede uma vez por abertura do app. */
    private void askMicForWake(){if(!askedMicForWake&&checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)!=android.content.pm.PackageManager.PERMISSION_GRANTED){askedMicForWake=true;requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO},102);}}
    private boolean pendingVoice, pageLoaded;
    private static boolean isVoiceIntent(Intent i){String a=i==null?null:i.getAction();return Intent.ACTION_ASSIST.equals(a)||Intent.ACTION_VOICE_COMMAND.equals(a);}
    /** Botão de voz da central/volante (ASSIST/VOICE_COMMAND): abre o painel e ouve uma vez, quando página, app em primeiro plano e assistente estiverem prontos. */
    private void runPendingVoice(){if(!pendingVoice||!pageLoaded||!foreground||assistant==null||web==null)return;pendingVoice=false;web.evaluateJavascript("window.harumiOpenAssistant && window.harumiOpenAssistant()",null);requestListening();}
    @Override protected void onNewIntent(Intent intent){super.onNewIntent(intent);setIntent(intent);if(isVoiceIntent(intent)){pendingVoice=true;runPendingVoice();}}
    private void listenNow() { if (web != null) web.post(() -> assistant.listen()); else assistant.listen(); }
    private void message(String text) { Toast.makeText(this, text, Toast.LENGTH_LONG).show(); }
    @Override protected void onResume() { super.onResume(); foreground = true;if(web!=null)web.evaluateJavascript("window.harumiApps && window.harumiApps.refresh();window.harumiLauncherRefresh && window.harumiLauncherRefresh()",null);if(web!=null) { web.onResume();web.evaluateJavascript("window.harumiVisibility && window.harumiVisibility(true)",null); } if(assistant!=null){if(assistant.wakeEnabled())askMicForWake();assistant.resume();if(listenAfterResume){listenAfterResume=false;listenNow();}}if(connectivity!=null)connectivity.start();publish();runPendingVoice(); }
    @Override protected void onPause() { foreground = false;if(web!=null) { web.evaluateJavascript("window.harumiVisibility && window.harumiVisibility(false)",null);web.onPause(); } if(assistant!=null)assistant.pause();if(connectivity!=null)connectivity.close();stopNav();super.onPause(); }
    @Override protected void onDestroy() { stopNav();if(navVoice!=null){navVoice.close();navVoice=null;}if(assistant!=null)assistant.close();if(connectivity!=null)connectivity.close(); diagnostics.close(); if (web != null) { web.removeJavascriptInterface("HarumiNative"); web.destroy(); } super.onDestroy(); }
}
