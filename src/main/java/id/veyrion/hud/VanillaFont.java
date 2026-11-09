package id.veyrion.hud;

/** Advance width (px) of vanilla default-font glyphs, used to compute exact HUD offsets. */
final class VanillaFont {
    private VanillaFont() {}

    static int width(String s) {
        int w = 0;
        for (int i = 0; i < s.length(); i++) w += width(s.charAt(i));
        return w;
    }

    static int width(char c) {
        switch (c) {
            case ' ': return 4;
            case '!': case ',': case '.': case ':': case ';': case 'i': case '|': return 2;
            case '\'': case 'l': case '`': return 3;
            case 'I': case 't': return 4;
            case '(': case ')': case '[': case ']': case '{': case '}': case '*':
            case '<': case '>': case 'f': case 'k': case '"': return 5;
            case '@': case '~': return 7;
            default: return 6;
        }
    }
}
