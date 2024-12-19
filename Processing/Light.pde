public class Light {
    private int x;
    private int y;
    private int radius;

    // Constructor
    public Light(int x, int y, int radius) {
        this.x = x;
        this.y = y;
        this.radius = radius;
    }

    // Method to draw the light
    public void drawLight() {
        ellipseMode(CENTER);
        fill(255);
        ellipse(x, y, radius, radius);
    }
}