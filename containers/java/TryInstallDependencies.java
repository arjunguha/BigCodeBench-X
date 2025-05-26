import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.TimeUnit;

public class TryInstallDependencies {
    private static final String JAVA_DEPS_PATH = "/java_deps";
    
    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java TryInstallDependencies <dependencies_file>");
            System.exit(1);
        }
        
        String dependenciesFile = args[0];
        List<String> successes = new ArrayList<>();
        List<String> failures = new ArrayList<>();
        
        try {
            List<String> dependencies = Files.readAllLines(Paths.get(dependenciesFile));
            
            for (String dependency : dependencies) {
                dependency = dependency.trim();
                if (!dependency.isEmpty()) {
                    if (installDependency(dependency)) {
                        successes.add(dependency);
                        System.out.println("Successfully installed: " + dependency);
                    } else {
                        failures.add(dependency);
                        System.out.println("Failed to install: " + dependency);
                    }
                }
            }
            
            System.out.println("\nSuccesses:");
            for (String success : successes) {
                System.out.println(success);
            }
            
            System.out.println("\nFailures:");
            for (String failure : failures) {
                System.out.println(failure);
            }
            
        } catch (IOException e) {
            System.err.println("Error reading dependencies file: " + e.getMessage());
            System.exit(1);
        }
    }
    
    private static boolean installDependency(String dependency) {
        try {
            System.out.println("Installing " + dependency + "...");

            // Use Maven to download the dependency directly to JAVA_DEPS_PATH
            ProcessBuilder pb = new ProcessBuilder(
                "mvn", "dependency:copy",
                "-Dartifact=" + dependency,
                "-DoutputDirectory=" + JAVA_DEPS_PATH
            );

            pb.redirectErrorStream(true);

            Process process = pb.start();

            // Read and print Maven output
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }

            boolean success = process.waitFor(60, TimeUnit.SECONDS) && process.exitValue() == 0;

            if (success) {
                System.out.println("Successfully installed: " + dependency);
            } else {
                System.out.println("Failed to install: " + dependency);
            }

            return success;

        } catch (Exception e) {
            System.out.println("Exception installing " + dependency + ": " + e.getMessage());
            return false;
        }
    }
}
