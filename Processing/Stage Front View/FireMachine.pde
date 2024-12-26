public class FireMachine {
    private int x;
    private int y;
    ArrayList<Particle> particles;

    public FireMachine (int x, int y) {
        this.x = x;
        this.y = y;
        this.particles = new ArrayList<Particle>();
    }

    public void drawSmoke(int intensity) {
        if (intensity > 0) {
            for (int i = 0; i <= intensity; i++) {
                Particle p = new Particle(this.x, this.y);
                particles.add(p);
            }

            for (int i = 0; i < particles.size(); i++) {
                particles.get(i).move(intensity);
                particles.get(i).draw();
                if (particles.get(i).alpha <= 0) {
                    particles.remove(i);
                    i--;
                }
            }
        }
    }

}
