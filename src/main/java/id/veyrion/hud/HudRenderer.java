package id.veyrion.hud;

import net.kyori.adventure.key.Key;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.TextColor;
import org.bukkit.Bukkit;
import org.bukkit.OfflinePlayer;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.plugin.RegisteredServiceProvider;

import java.lang.reflect.Method;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

/**
 * Builds the boss-bar title component.
 *
 * The whole component has total advance width 0, so the client starts drawing exactly at the
 * screen centre; the shader (marker colour) then moves every glyph to the right screen edge and
 * down by the row offset encoded in the colour. Everything is in GUI pixels => identical at every GUI scale.
 */
final class HudRenderer {
    private static final Key SPACE = Key.key("veyrion", "space");
    private static final Key ICONS = Key.key("veyrion", "icons");
    private static final Key LOGO = Key.key("veyrion", "logo");
    private static final Key TITLE = Key.key("veyrion", "title");

    private final VeyrionHud plugin;
    private final RaceTracker races;

    private Object economy;
    private Method getBalance;

    HudRenderer(VeyrionHud plugin, RaceTracker races) {
        this.plugin = plugin;
        this.races = races;
    }

    // ------------------------------------------------------------------ build
    Component render(Player p) {
        FileConfiguration c = plugin.getConfig();
        int margin = c.getInt("layout.margin-right", 22);
        int logoY = c.getInt("layout.logo-center-y", 58);
        int logoGap = c.getInt("layout.logo-title-gap", 4);
        int rowY = c.getInt("layout.row-start-y", 100);
        int rowH = c.getInt("layout.row-height", 18);
        int ti = c.getInt("layout.text-icon-gap", 3);
        int gg = c.getInt("layout.group-gap", 6);

        ZonedDateTime now = ZonedDateTime.now(ZoneId.of(c.getString("timezone", "Asia/Jakarta")));
        String date = now.format(DateTimeFormatter.ofPattern(c.getString("date-format", "dd/MM/yyyy"), Locale.US));
        String time = now.format(DateTimeFormatter.ofPattern(c.getString("time-format", "HH:mm 'WIB'"), Locale.US));
        int online = Bukkit.getOnlinePlayers().size();
        String players = online + " " + c.getString("players-label", "Players");
        String money = formatMoney(p, c.getString("money-format", "$#,##0"));

        UUID id = p.getUniqueId();
        String raceText = races.display(id);
        String raceKey = races.raceName(id);
        if (raceText == null) { raceText = c.getString("no-race-text", "-"); raceKey = null; }

        List<Component> out = new ArrayList<>();

        // --- row 0: [TITLE] [LOGO]
        Row r0 = new Row();
        r0.image(TITLE, '\ue001', Generated.TITLE_ADV, imgK(logoY, Generated.TITLE_H));
        r0.gap(logoGap);
        r0.image(LOGO, '\ue000', Generated.LOGO_ADV, imgK(logoY, Generated.LOGO_H));
        r0.emit(out, margin);

        // --- row 1: date + calendar + time + clock
        int y1 = rowY;
        Row r1 = new Row();
        r1.text(date, textK(y1));
        r1.gap(ti);
        r1.icon("calendar", imgK(y1, Generated.ICON_H));
        r1.gap(gg);
        r1.text(time, textK(y1));
        r1.gap(ti);
        r1.icon("clock", imgK(y1, Generated.ICON_H));
        r1.emit(out, margin);

        // --- row 2: online
        int y2 = rowY + rowH;
        Row r2 = new Row();
        r2.text(players, textK(y2));
        r2.gap(ti);
        r2.icon("players", imgK(y2, Generated.ICON_H));
        r2.emit(out, margin);

        // --- row 3: race (text + its own icon)
        int y3 = rowY + rowH * 2;
        Row r3 = new Row();
        r3.text(raceText, textK(y3));
        if (raceKey != null && iconIndex(raceKey.toLowerCase(Locale.ROOT)) >= 0) {
            r3.gap(ti);
            r3.icon(raceKey.toLowerCase(Locale.ROOT), imgK(y3, Generated.ICON_H));
        }
        r3.emit(out, margin);

        // --- row 4: money
        int y4 = rowY + rowH * 3;
        Row r4 = new Row();
        r4.text(money, textK(y4));
        r4.gap(ti);
        r4.icon("coin", imgK(y4, Generated.ICON_H));
        r4.emit(out, margin);

        return Component.empty().children(out);
    }

    // ------------------------------------------------------------------ values (also used by PlaceholderAPI)
    String date() {
        FileConfiguration c = plugin.getConfig();
        return ZonedDateTime.now(ZoneId.of(c.getString("timezone", "Asia/Jakarta")))
                .format(DateTimeFormatter.ofPattern(c.getString("date-format", "dd/MM/yyyy"), Locale.US));
    }

    String time() {
        FileConfiguration c = plugin.getConfig();
        return ZonedDateTime.now(ZoneId.of(c.getString("timezone", "Asia/Jakarta")))
                .format(DateTimeFormatter.ofPattern(c.getString("time-format", "HH:mm 'WIB'"), Locale.US));
    }

    String playersText() {
        return Bukkit.getOnlinePlayers().size() + " " + plugin.getConfig().getString("players-label", "Players");
    }

    String money(OfflinePlayer p) { return formatMoney(p, plugin.getConfig().getString("money-format", "$#,##0")); }

    // ------------------------------------------------------------------ helpers
    /** vertical marker for vanilla text whose visual centre should be at yCenter (text is drawn at y=3, 7px tall) */
    private static int textK(int yCenter) { return clampK(yCenter - 7); }

    /** vertical marker for an image glyph (ascent == height) centred at yCenter */
    private static int imgK(int yCenter, int height) { return clampK(yCenter - 10 + Math.round(height / 2f)); }

    private static int clampK(int k) { return Math.max(0, Math.min(163, k)); }

    private static int iconIndex(String name) {
        for (int i = 0; i < Generated.ICON_NAMES.length; i++) if (Generated.ICON_NAMES[i].equals(name)) return i;
        return -1;
    }

    private static TextColor marker(int k, int blue) { return TextColor.color(78, 92 + k, blue); }

    private static Component space(int px) {
        if (px == 0) return Component.empty();
        int a = Math.min(Math.abs(px), 2047);
        char base = px > 0 ? (char) 0xF100 : (char) 0xF200;
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 11; i++) if (((a >> i) & 1) != 0) sb.append((char) (base + i));
        return Component.text(sb.toString()).font(SPACE);
    }

    private static final class Row {
        final List<Component> parts = new ArrayList<>();
        int width;

        void text(String s, int k) {
            parts.add(Component.text(s).color(marker(k, 36)));
            width += VanillaFont.width(s);
        }

        void image(Key font, char ch, int adv, int k) {
            parts.add(Component.text(String.valueOf(ch)).font(font).color(marker(k, 37)));
            width += adv;
        }

        void icon(String name, int k) {
            int idx = iconIndex(name);
            if (idx < 0) return;
            image(ICONS, (char) (Generated.ICON_BASE + idx), Generated.ICON_ADV, k);
        }

        void gap(int px) { parts.add(space(px)); width += px; }

        /** start at -(margin+width) from the right edge, draw, then rewind so the line nets to 0 */
        void emit(List<Component> out, int margin) {
            out.add(space(-(margin + width)));
            out.addAll(parts);
            out.add(space(margin));
        }
    }

    // ------------------------------------------------------------------ money (Vault via reflection, optional)
    private String formatMoney(OfflinePlayer p, String pattern) {
        double bal = 0;
        try {
            if (economy == null && Bukkit.getPluginManager().getPlugin("Vault") != null) {
                Class<?> eco = Class.forName("net.milkbowl.vault.economy.Economy");
                RegisteredServiceProvider<?> rsp = Bukkit.getServicesManager().getRegistration(eco);
                if (rsp != null) {
                    economy = rsp.getProvider();
                    getBalance = eco.getMethod("getBalance", OfflinePlayer.class);
                }
            }
            if (economy != null) bal = ((Number) getBalance.invoke(economy, p)).doubleValue();
        } catch (Throwable ignored) {
            economy = null;
        }
        DecimalFormat df = new DecimalFormat(pattern, DecimalFormatSymbols.getInstance(Locale.US));
        return df.format(bal);
    }
}
