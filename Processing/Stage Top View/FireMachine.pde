public class FireMachine {
    private int x;
    private int y;
    private int radius;

    // Constructor
    public FireMachine(int x, int y, int radius) {
        this.x = x;
        this.y = y;
        this.radius = radius;
    }

    // Method to draw the fire machine
    public void drawFireMachine() {
        ellipseMode(CENTER);
        noStroke();
        fill(160, 160, 160);
        ellipse(x, y, radius, radius);
    }
}
