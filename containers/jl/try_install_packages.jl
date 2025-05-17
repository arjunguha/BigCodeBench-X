# Tries to install packages, and suppresses errors when installation files.
# We receive the list of packages in a file, one per line.
using Pkg

# Get the input file path from command line arguments
if length(ARGS) != 1
    error("Usage: julia try_install_packages.jl <packages_file>")
end

packages_file = ARGS[1]

# Read packages from file
packages = readlines(packages_file)

failures = String[]
successes = String[]

# Try to install each package
for pkg in packages
    pkg = strip(pkg)  # Remove any whitespace
    if !isempty(pkg)  # Skip empty lines
        try
            println("Installing $pkg...")
            Pkg.add(pkg)
            println("Successfully installed $pkg")
            push!(successes, pkg)
        catch e
            println("Failed to install $pkg: $(sprint(showerror, e))")
            push!(failures, pkg)
        end
    end
end

println("Successes:")
for pkg in successes
    println(pkg)
end

println("Failures:")
for pkg in failures
    println(pkg)
end
