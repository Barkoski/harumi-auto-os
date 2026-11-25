package com.harumi.autoos.ai;
import android.content.Context;
import java.io.*;
public final class ModelAssets {
    // TODO: remover models-v1 (e outras pastas models-*) apos confirmar que nao ha mais uso; nao apagar automaticamente.
    private static final Object LOCK = new Object();
    public static File prepare(Context context) throws IOException {
        synchronized (LOCK) { // Activity recriada nao pode copiar em paralelo
            File root = new File(context.getFilesDir(), "models-v2");
            File ready = new File(root, ".ready");
            String version = "v2:" + signature(context, "models");
            if (!version.equals(read(ready))) {
                if (!root.exists() && !root.mkdirs()) throw new IOException("Sem espaço para preparar modelos.");
                if (ready.exists() && !ready.delete()) throw new IOException("Falha ao concluir instalação dos modelos.");
                copy(context, "models", root);
                try (OutputStream out = new FileOutputStream(ready)) { out.write(version.getBytes("UTF-8")); }
                if (!version.equals(read(ready))) throw new IOException("Falha ao concluir instalação dos modelos.");
            }
            return root;
        }
    }
    private static String read(File f) {
        if (!f.isFile()) return null;
        try (BufferedReader in = new BufferedReader(new InputStreamReader(new FileInputStream(f), "UTF-8"))) { return in.readLine(); } catch (IOException e) { return null; }
    }
    /** Tamanho total + quantidade dos assets: barato e muda quando o pacote de modelos muda. */
    private static String signature(Context c, String asset) throws IOException {
        long[] t = new long[2]; sum(c, asset, t); return t[0] + ":" + t[1];
    }
    private static void sum(Context c, String asset, long[] t) throws IOException {
        String[] children = c.getAssets().list(asset);
        if (children != null && children.length > 0) { for (String child : children) sum(c, asset+"/"+child, t); return; }
        long len = -1;
        try (android.content.res.AssetFileDescriptor fd = c.getAssets().openFd(asset)) { len = fd.getLength(); } catch (IOException compressed) { }
        if (len < 0) try (InputStream in = c.getAssets().open(asset)) { len = in.available(); }
        t[0] += len; t[1]++;
    }
    private static void copy(Context c, String asset, File to) throws IOException {
        String[] children = c.getAssets().list(asset);
        if (children != null && children.length > 0) {
            if (!to.exists() && !to.mkdirs()) throw new IOException("Não foi possível criar a pasta dos modelos.");
            for (String child : children) copy(c, asset+"/"+child, new File(to, child));
        } else {
            try (InputStream input=c.getAssets().open(asset); OutputStream output=new FileOutputStream(to)) {
                byte[] b=new byte[1024*256]; int n; while ((n=input.read(b))>=0) output.write(b,0,n);
            }
        }
    }
}
