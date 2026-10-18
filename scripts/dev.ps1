param(
    [ValidateSet("server", "web")]
    [string]$Target = "server"
)

$repoRoot = Resolve-Path "$PSScriptRoot\.."
$settingsPath = Join-Path $repoRoot ".maven-settings.xml"

if ($Target -eq "server") {
    mvn -gs $settingsPath -pl apps/server spring-boot:run "-Dspring-boot.run.profiles=local"
    exit $LASTEXITCODE
}

Push-Location (Join-Path $repoRoot "apps/web")
try {
    npm run dev -- --host 127.0.0.1 --port 3001
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
