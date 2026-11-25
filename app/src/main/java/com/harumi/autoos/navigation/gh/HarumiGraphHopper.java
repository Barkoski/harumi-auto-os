package com.harumi.autoos.navigation.gh;

import com.graphhopper.GraphHopper;
import com.graphhopper.config.Profile;
import com.graphhopper.routing.WeightingFactory;
import com.graphhopper.routing.ev.BooleanEncodedValue;
import com.graphhopper.routing.ev.DecimalEncodedValue;
import com.graphhopper.routing.weighting.TurnCostProvider;
import com.graphhopper.routing.weighting.Weighting;
import com.graphhopper.routing.weighting.custom.CustomWeighting;
import com.graphhopper.util.PMap;

/**
 * GraphHopper com peso de carro proprio, SEM Janino (o Janino gera bytecode JVM, que o Android nao carrega).
 * Equivale ao car.json padrao: prioridade 0 onde !car_access, velocidade = car_average_speed, distance_influence 90,
 * sem custos de curva. Usado no import no PC (scripts/graphhopper-android/HarumiImport.java) e no Android (OfflineRouter):
 * os dois lados precisam usar exatamente esta classe, senao o grafo CH nao confere.
 * Sem imports do Android: compila na JVM do PC junto com graphhopper-web-11.1.jar.
 */
public class HarumiGraphHopper extends GraphHopper {
    /** Perfil unico; o modelo customizado e ignorado pela fabrica abaixo (vale so para o hash do perfil). */
    public static Profile carProfile() {
        return new Profile("car").setCustomModel(new com.graphhopper.util.CustomModel().setDistanceInfluence(90d));
    }

    @Override
    protected WeightingFactory createWeightingFactory() {
        return (Profile profile, PMap hints, boolean disableTurnCosts) -> carWeighting();
    }

    private Weighting carWeighting() {
        final BooleanEncodedValue access = getEncodingManager().getBooleanEncodedValue("car_access");
        final DecimalEncodedValue speed = getEncodingManager().getDecimalEncodedValue("car_average_speed");
        final double maxSpeed = speed.getMaxOrMaxStorableDecimal();
        CustomWeighting.Parameters p = new CustomWeighting.Parameters(
                (edge, reverse) -> reverse ? edge.getReverse(speed) : edge.get(speed),
                () -> maxSpeed,
                (edge, reverse) -> (reverse ? edge.getReverse(access) : edge.get(access)) ? 1 : 0,
                () -> 1,
                null, 90, 300);
        return new CustomWeighting(TurnCostProvider.NO_TURN_COST_PROVIDER, p);
    }
}
