package com.harumi.autoos.ai.tools;
import java.util.Map;
public record ToolSpec(String id,RiskClass risk,Map<String,SlotSpec> slots) {
    public ToolSpec { slots=Map.copyOf(slots); }
}
