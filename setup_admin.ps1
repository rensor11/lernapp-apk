# PowerShell Script zum Setup des Admin-Benutzers
# Dieses Script erstellt/aktualisiert den Admin-Benutzer in der SQLite-Datenbank

param(
    [string]$DbPath = "lernapp.db"
)

# Lade SQLite-Assembly
Add-Type -AssemblyName System.Data.SQLite

# Erstelle eine Verbindung zur Datenbank
$connectionString = "Data Source=$DbPath;Version=3;"
$connection = New-Object System.Data.SQLite.SQLiteConnection($connectionString)
$connection.Open()

$command = $connection.CreateCommand()

# Prüfe ob admin bereits existiert
$command.CommandText = "SELECT id, username FROM users WHERE username = 'admin'"
$reader = $command.ExecuteReader()
$adminExists = $reader.Read()
$adminId = if ($adminExists) { $reader["id"] } else { $null }
$reader.Close()

if ($adminExists) {
    Write-Host "✅ Admin-Benutzer existiert bereits (ID: $adminId)"
} else {
    Write-Host "➕ Erstelle neuen Admin-Benutzer"
    $command.CommandText = @"
    INSERT INTO users (username, password_hash, created_at, home_access_allowed, smarthome_access_allowed, lernapp_access_allowed) 
    VALUES ('admin', 'placeholder_hash', datetime('now'), 1, 1, 1)
"@
    $command.ExecuteNonQuery() | Out-Null
    
    # Hole die ID des neu erstellten Benutzers
    $command.CommandText = "SELECT id FROM users WHERE username = 'admin'"
    $adminId = $command.ExecuteScalar()
    Write-Host "✅ Admin-Benutzer erstellt (ID: $adminId)"
}

# Lese die Admin-Konfiguration
$command.CommandText = "SELECT id, username, home_access_allowed, smarthome_access_allowed, lernapp_access_allowed FROM users WHERE id = $adminId"
$reader = $command.ExecuteReader()
$reader.Read()

Write-Host "`n✅ Admin-Benutzer Konfiguration:"
Write-Host "  ID: $($reader["id"])"
Write-Host "  Username: $($reader["username"])"
Write-Host "  Home Cloud: $(if ($reader["home_access_allowed"] -eq 1) { '✓' } else { '✗' })"
Write-Host "  Smart Home: $(if ($reader["smarthome_access_allowed"] -eq 1) { '✓' } else { '✗' })"
Write-Host "  Lernapp: $(if ($reader["lernapp_access_allowed"] -eq 1) { '✓' } else { '✗' })"

$reader.Close()
$connection.Close()

Write-Host "`n✅ Admin-Setup abgeschlossen!"
