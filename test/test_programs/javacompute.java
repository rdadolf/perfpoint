public class javacompute {

    public static void main(String[] args) {
        long acc = 7;
        long i=0;
        for( i=0; i<(1<<29); i++ )
        {
          acc ^= i*(i<<4);
        }
        System.out.println("Computation done"+acc+"\n");
    }

}
