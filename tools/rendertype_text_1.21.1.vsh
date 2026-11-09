#version 150

in vec3 Position;
in vec4 Color;
in vec2 UV0;
in ivec2 UV2;

uniform sampler2D Sampler2;
uniform mat4 ModelViewMat;
uniform mat4 ProjMat;

out float vertexDistance;
out vec4 vertexColor;
out vec2 texCoord0;

// Veyrion HUD marker colour: R=78 (0x4E), B=36 (text) / 37 (image), G = 92 + rowOffset (GUI px)
// Vanilla drop-shadow of that colour is (19, x, 9) -> hidden.
void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);
    vertexDistance = 0.0;
    vertexColor = Color * texelFetch(Sampler2, UV2 / 16, 0);
    texCoord0 = UV0;

    vec3 c = Color.rgb * 255.0;
    bool real   = abs(c.r - 78.0) < 0.6 && (abs(c.b - 36.0) < 0.6 || abs(c.b - 37.0) < 0.6);
    bool shadow = abs(c.r - 19.0) < 0.6 && abs(c.b - 9.0) < 0.6 ;
    if (real || shadow) {
        float W = floor(2.0 / abs(ProjMat[0][0]) + 0.5);   // GUI-scaled width
        float H = floor(2.0 / abs(ProjMat[1][1]) + 0.5);   // GUI-scaled height
        float row = real ? (c.g - 92.0) : 0.0;
        // text starts at the screen centre (component width = 0) -> push to the right edge
        gl_Position.x += 2.0 * ceil(W / 2.0) / W;
        gl_Position.y -= 2.0 * floor(row + 0.5) / H;
        if (shadow) {
            vertexColor = vec4(0.0);
        } else if (abs(c.b - 36.0) < 0.6) {
            vertexColor = vec4(1.0, 1.0, 1.0, Color.a);   // HUD text colour (putih)
        } else {
            vertexColor = vec4(1.0, 1.0, 1.0, Color.a);                           // pre-coloured image glyphs
        }
    }
}
