public class Particle {
    private float x;
    private float y;
    private float vx;
    private float vy;
    private int alpha;

    public Particle (int x, int y) {
        this.x = x;
        this.y = y;
        this.vx = random(-1, 1);
        this.vy = random(-5, -1);
        this.alpha = 255;
    }

    public void draw() {
        noStroke();
        fill(255, this.alpha);
        ellipse(x, y, 10, 10);
    }

    public void move(int intensity) {
        this.x += this.vx;
        this.y += this.vy;
        if (intensity == 10) {
            this.alpha--;
        }
        if (intensity == 9) {
            this.alpha -= 2;
        }
        if (intensity == 8) {
            this.alpha -= 3;
        }
        if (intensity == 7) {
            this.alpha -= 4;
        }
        if (intensity == 6) {
            this.alpha -= 5;
        }
        if (intensity == 5) {
            this.alpha -= 6;
        }
        if (intensity == 4) {
            this.alpha -= 7;
        }
        if (intensity == 3) {
            this.alpha -= 8;
        }
        if (intensity == 2) {
            this.alpha -= 9;
        }
        if (intensity == 1) {
            this.alpha -= 10;
        }
    }
}
