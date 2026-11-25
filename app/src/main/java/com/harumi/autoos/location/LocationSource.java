package com.harumi.autoos.location;
public interface LocationSource {
    interface Listener{void onFix(Fix fix);void onUnavailable(String reason);}
    void start(Listener listener);
    void stop();
}
