package id.veyrion.hud;

import org.bukkit.Bukkit;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.plugin.Plugin;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Reads races from AwakeningCutscene (by reflection, so only the races that exist in that jar are used)
 * and remembers who finished an awakening.
 */
final class RaceTracker {
    private final VeyrionHud plugin;
    private final Plugin awakening;
    private final File file;
    private final Map<UUID, String> races = new HashMap<>();   // uuid -> enum name (BEAST...)

    private Class<?> raceClass;
    private Object[] raceValues = new Object[0];
    private Field displayField, currentField, raceField, targetField, completedField, tickField;
    private int total = Integer.MAX_VALUE;

    private Object active;
    private Object pendingRace;
    private UUID pendingTarget;
    private boolean done;
    private int maxTick;

    RaceTracker(VeyrionHud plugin, Plugin awakening) {
        this.plugin = plugin;
        this.awakening = awakening;
        this.file = new File(plugin.getDataFolder(), "races.yml");
        load();
        try {
            ClassLoader cl = awakening.getClass().getClassLoader();
            raceClass = Class.forName("com.awakening.Race", true, cl);
            raceValues = raceClass.getEnumConstants();
            displayField = raceClass.getDeclaredField("display");
            displayField.setAccessible(true);

            currentField = awakening.getClass().getDeclaredField("current");
            currentField.setAccessible(true);

            Class<?> cs = Class.forName("com.awakening.AwakeningCutscene", true, cl);
            raceField = cs.getDeclaredField("race");       raceField.setAccessible(true);
            targetField = cs.getDeclaredField("target");   targetField.setAccessible(true);
            completedField = cs.getDeclaredField("completed"); completedField.setAccessible(true);
            tickField = cs.getDeclaredField("tick");       tickField.setAccessible(true);
            try {
                Field t = cs.getDeclaredField("TOTAL");
                t.setAccessible(true);
                total = t.getInt(null);
            } catch (Throwable ignored) {}
        } catch (Throwable t) {
            plugin.getLogger().warning("Gagal hook AwakeningCutscene (reflection): " + t);
            plugin.getLogger().warning("Ras tetap bisa di-set manual: /veyrionhud setrace <player> <ras>");
            currentField = null;
        }
    }

    /** Called every tick. */
    void poll() {
        if (currentField == null) return;
        try {
            Object cur = currentField.get(awakening);
            if (cur != null) {
                if (cur != active) {
                    active = cur;
                    pendingRace = raceField.get(cur);
                    Object t = targetField.get(cur);
                    pendingTarget = (t instanceof Player p) ? p.getUniqueId() : null;
                    done = false;
                    maxTick = 0;
                }
                if (completedField.getBoolean(cur)) done = true;
                maxTick = Math.max(maxTick, tickField.getInt(cur));
            } else if (active != null) {
                if (pendingRace != null && pendingTarget != null && (done || maxTick >= total - 2)) {
                    set(pendingTarget, ((Enum<?>) pendingRace).name());
                }
                active = null;
                pendingRace = null;
                pendingTarget = null;
            }
        } catch (Throwable t) {
            plugin.getLogger().warning("RaceTracker error: " + t);
            currentField = null;
        }
    }

    /** All race names from the jar (BEAST, DRAGON, ELF, HUMAN) - nothing extra. */
    String[] raceNames() {
        String[] n = new String[raceValues.length];
        for (int i = 0; i < n.length; i++) n[i] = ((Enum<?>) raceValues[i]).name();
        return n;
    }

    /** Returns enum name or null. */
    String raceName(UUID id) { return races.get(id); }

    /** Display text from the jar (e.g. "Beast"), or null. */
    String display(UUID id) {
        String name = races.get(id);
        if (name == null) return null;
        for (Object o : raceValues) {
            if (((Enum<?>) o).name().equals(name)) {
                try { return (String) displayField.get(o); } catch (Throwable ignored) {}
                return name.charAt(0) + name.substring(1).toLowerCase();
            }
        }
        return null;
    }

    /** @return false if the race name is unknown (only races from the jar are accepted). */
    boolean set(UUID id, String raceOrNone) {
        if (raceOrNone == null || raceOrNone.equalsIgnoreCase("none")) {
            races.remove(id);
            save();
            return true;
        }
        for (String n : raceNames()) {
            if (n.equalsIgnoreCase(raceOrNone)) {
                races.put(id, n);
                save();
                return true;
            }
        }
        return false;
    }

    private void load() {
        if (!file.exists()) return;
        YamlConfiguration y = YamlConfiguration.loadConfiguration(file);
        for (String k : y.getKeys(false)) {
            try { races.put(UUID.fromString(k), y.getString(k)); } catch (IllegalArgumentException ignored) {}
        }
    }

    private void save() {
        YamlConfiguration y = new YamlConfiguration();
        races.forEach((u, r) -> y.set(u.toString(), r));
        try {
            plugin.getDataFolder().mkdirs();
            y.save(file);
        } catch (IOException e) {
            plugin.getLogger().warning("Gagal simpan races.yml: " + e.getMessage());
        }
    }
}
