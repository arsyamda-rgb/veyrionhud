package id.veyrion.hud;

import net.kyori.adventure.bossbar.BossBar;
import net.kyori.adventure.text.Component;
import org.bukkit.Bukkit;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitTask;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

public final class VeyrionHud extends JavaPlugin implements Listener {
    private final Map<UUID, BossBar> bars = new HashMap<>();
    private final Map<UUID, Component> last = new HashMap<>();
    private RaceTracker races;
    private HudRenderer renderer;
    private BukkitTask updateTask, pollTask;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        races = new RaceTracker(this, Bukkit.getPluginManager().getPlugin("AwakeningCutscene"));
        renderer = new HudRenderer(this, races);
        Bukkit.getPluginManager().registerEvents(this, this);
        if (Bukkit.getPluginManager().getPlugin("PlaceholderAPI") != null) {
            new VeyrionExpansion(this, renderer, races).register();
            getLogger().info("Placeholder PlaceholderAPI terdaftar: %veyrion_date% %veyrion_time% %veyrion_online% %veyrion_race% %veyrion_race_id% %veyrion_money%");
        }
        startTasks();
        if (bossbarMode()) for (Player p : Bukkit.getOnlinePlayers()) show(p);
    }

    /** true = HUD lewat bossbar + shader (mode lama). false = HUD lewat BetterHud (default). */
    private boolean bossbarMode() { return getConfig().getBoolean("bossbar-hud.enabled", false); }

    @Override
    public void onDisable() {
        stopTasks();
        for (Player p : Bukkit.getOnlinePlayers()) hide(p);
        bars.clear();
        last.clear();
    }

    private void startTasks() {
        pollTask = Bukkit.getScheduler().runTaskTimer(this, races::poll, 1L, 1L);
        long every = Math.max(1, getConfig().getInt("update-ticks", 20));
        if (bossbarMode()) updateTask = Bukkit.getScheduler().runTaskTimer(this, this::updateAll, 20L, every);
    }

    private void stopTasks() {
        if (pollTask != null) pollTask.cancel();
        if (updateTask != null) updateTask.cancel();
    }

    private void updateAll() {
        for (Player p : Bukkit.getOnlinePlayers()) update(p);
    }

    private void show(Player p) {
        Component c = renderer.render(p);
        BossBar bar = BossBar.bossBar(c, 0f, BossBar.Color.WHITE, BossBar.Overlay.PROGRESS);
        BossBar old = bars.put(p.getUniqueId(), bar);
        if (old != null) p.hideBossBar(old);
        last.put(p.getUniqueId(), c);
        p.showBossBar(bar);
    }

    private void hide(Player p) {
        BossBar bar = bars.remove(p.getUniqueId());
        last.remove(p.getUniqueId());
        if (bar != null) p.hideBossBar(bar);
    }

    private void update(Player p) {
        BossBar bar = bars.get(p.getUniqueId());
        if (bar == null) { show(p); return; }
        Component c = renderer.render(p);
        if (!c.equals(last.get(p.getUniqueId()))) {
            bar.name(c);
            last.put(p.getUniqueId(), c);
        }
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent e) {
        Player p = e.getPlayer();
        if (!bossbarMode()) return;
        if (getConfig().getBoolean("resource-pack.enabled", false)) sendPack(p);
        Bukkit.getScheduler().runTaskLater(this, () -> { if (p.isOnline()) show(p); }, 10L);
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        hide(e.getPlayer());
    }

    private void sendPack(Player p) {
        String url = getConfig().getString("resource-pack.url", "");
        if (url.isBlank()) return;
        byte[] hash = null;
        String sha1 = getConfig().getString("resource-pack.sha1", "").trim();
        if (sha1.length() == 40) {
            hash = new byte[20];
            for (int i = 0; i < 20; i++) hash[i] = (byte) Integer.parseInt(sha1.substring(i * 2, i * 2 + 2), 16);
        }
        Component prompt = Component.text(getConfig().getString("resource-pack.prompt", ""));
        p.setResourcePack(url, hash, prompt, getConfig().getBoolean("resource-pack.required", true));
    }

    // ------------------------------------------------------------------ /veyrionhud
    @Override
    public boolean onCommand(CommandSender s, Command cmd, String label, String[] a) {
        if (!s.hasPermission("veyrionhud.admin")) { s.sendMessage("Kamu tidak punya izin."); return true; }
        if (a.length == 0) { s.sendMessage("/veyrionhud <reload|race [player]|setrace <player> <ras|none>>"); return true; }
        switch (a[0].toLowerCase(Locale.ROOT)) {
            case "reload" -> {
                reloadConfig();
                stopTasks();
                startTasks();
                if (bossbarMode()) for (Player p : Bukkit.getOnlinePlayers()) show(p);
                s.sendMessage("VeyrionHUD config direload.");
            }
            case "race" -> {
                Player t = a.length > 1 ? Bukkit.getPlayerExact(a[1]) : (s instanceof Player p ? p : null);
                if (t == null) { s.sendMessage("Player tidak ditemukan."); return true; }
                String d = races.display(t.getUniqueId());
                s.sendMessage(t.getName() + ": " + (d == null ? "(belum punya ras)" : d));
            }
            case "setrace" -> {
                if (a.length < 3) { s.sendMessage("/veyrionhud setrace <player> <" + String.join("|", races.raceNames()).toLowerCase(Locale.ROOT) + "|none>"); return true; }
                Player t = Bukkit.getPlayerExact(a[1]);
                if (t == null) { s.sendMessage("Player harus online."); return true; }
                if (!races.set(t.getUniqueId(), a[2])) { s.sendMessage("Ras tidak dikenal."); return true; }
                update(t);
                s.sendMessage("Ras " + t.getName() + " diubah.");
            }
            default -> s.sendMessage("Subcommand tidak dikenal.");
        }
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender s, Command cmd, String alias, String[] a) {
        List<String> out = new ArrayList<>();
        if (a.length == 1) {
            for (String x : List.of("reload", "race", "setrace")) if (x.startsWith(a[0].toLowerCase(Locale.ROOT))) out.add(x);
        } else if (a.length == 2 && !a[0].equalsIgnoreCase("reload")) {
            for (Player p : Bukkit.getOnlinePlayers()) out.add(p.getName());
        } else if (a.length == 3 && a[0].equalsIgnoreCase("setrace")) {
            for (String r : races.raceNames()) out.add(r.toLowerCase(Locale.ROOT));
            out.add("none");
        }
        return out;
    }
}
