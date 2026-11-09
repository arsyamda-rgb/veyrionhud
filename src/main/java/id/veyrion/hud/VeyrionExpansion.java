package id.veyrion.hud;

import me.clip.placeholderapi.expansion.PlaceholderExpansion;
import org.bukkit.OfflinePlayer;
import org.bukkit.configuration.file.FileConfiguration;

import java.util.Locale;

/** %veyrion_date% %veyrion_time% %veyrion_online% %veyrion_race% %veyrion_race_id% %veyrion_money% */
final class VeyrionExpansion extends PlaceholderExpansion {
    private final VeyrionHud plugin;
    private final HudRenderer renderer;
    private final RaceTracker races;

    VeyrionExpansion(VeyrionHud plugin, HudRenderer renderer, RaceTracker races) {
        this.plugin = plugin;
        this.renderer = renderer;
        this.races = races;
    }

    @Override public String getIdentifier() { return "veyrion"; }
    @Override public String getAuthor() { return "Veyrion"; }
    @Override public String getVersion() { return plugin.getDescription().getVersion(); }
    @Override public boolean persist() { return true; }

    @Override
    public String onRequest(OfflinePlayer player, String params) {
        FileConfiguration c = plugin.getConfig();
        switch (params.toLowerCase(Locale.ROOT)) {
            case "date": return renderer.date();
            case "time": return renderer.time();
            case "online": return renderer.playersText();
            case "money": return renderer.money(player);
            case "race": {
                if (player == null) return c.getString("no-race-text", "-");
                String d = races.display(player.getUniqueId());
                return d == null ? c.getString("no-race-text", "-") : d;
            }
            case "race_id": {
                if (player == null) return "none";
                String n = races.raceName(player.getUniqueId());
                return n == null ? "none" : n.toLowerCase(Locale.ROOT);
            }
            default: return null;
        }
    }
}
